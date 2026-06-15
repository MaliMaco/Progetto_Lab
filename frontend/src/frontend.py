from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests
from pathlib import Path
import os

app = FastAPI(title="Frontend API")

STUDENTS = ["1805660", "2106747", "2128556"]

BASE_DIR = Path(__file__).parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8003")

domains = [
    "en.wikipedia.org",
    "www.ecb.europa.eu",
    "www.tandfonline.com",
    "apps.apple.com"
]


def extract_domain(url: str) -> str:
    parts = url.split("/")
    return parts[2] if len(parts) > 2 else ""


def fetch_gs_urls(domain: str) -> list:
    try:
        r = requests.get(f"{BASE_URL}/gold_standard_urls", params={"domain": domain})
        r.raise_for_status()
        return r.json().get("gold_standard_urls", [])
    except Exception as e:
        print("Errore fetch GS urls:", e)
        return []


def base_context(request: Request, **kwargs) -> dict:
    return {
        "request": request,
        "domains": domains,
        "parsed": None,
        "gold": None,
        "gs_urls": [],
        "eval": None,
        "judge": None,
        "error": None,
        "selected_domain": None,
        "prefill_url": None,
        "local_mode": False,
        **kwargs
    }


# ── HOME ──────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    try:
        r = requests.get(f"{BASE_URL}/status")
        r.raise_for_status()
        status = r.json()
    except Exception:
        status = {"backend": "error", "database": "error", "ollama": "error"}

    try:
        r = requests.get(f"{BASE_URL}/domains")
        r.raise_for_status()
        domain_list = r.json().get("domains", [])
    except Exception:
        domain_list = domains

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "request": request,
            "students": STUDENTS,
            "status": status,
            "domains": domain_list,
        }
    )


# ── PARSER & EVALUATION ───────────────────────────────────────────────────────

@app.get("/parser", response_class=HTMLResponse)
def parser_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=base_context(request)
    )


@app.post("/select_domain", response_class=HTMLResponse)
def select_domain(request: Request, domain_select: str = Form("")):
    if not domain_select:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context=base_context(request, error="Seleziona un dominio.")
        )

    gs_urls = fetch_gs_urls(domain_select)
    first_url = gs_urls[0] if gs_urls else None

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=base_context(
            request,
            gs_urls=gs_urls,
            selected_domain=domain_select,
            prefill_url=first_url,
        )
    )


@app.post("/parse_ui", response_class=HTMLResponse)
def parse_ui(
    request: Request,
    url: str = Form(None),
    domain_select: str = Form(""),
    local_mode: str = Form("false")
):
    if not url or not url.strip():
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context=base_context(request, error="Inserisci un URL.")
        )

    if url in domains:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context=base_context(request, error="Inserito un URL composto da solo dominio.")
        )

    try:
        domain = extract_domain(url)
    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context=base_context(request, error="Inserisci un URL valido.")
        )

    if not domain:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context=base_context(request, error="URL non valido.")
        )

    if domain not in domains:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context=base_context(request, error="Dominio non supportato.")
        )

    use_local = local_mode == "true"

    # Chiamata POST /parse
    try:
        parse_response = requests.post(
            f"{BASE_URL}/parse",
            json={"url": url, "local": use_local}
        )
        parse_response.raise_for_status()
        parsed = parse_response.json()
    except requests.HTTPError as e:
        detail = ""
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context=base_context(request, error=f"Errore parsing: {detail}")
        )
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context=base_context(request, error=f"Errore parsing: {e}")
        )

    gs_urls = fetch_gs_urls(domain)

    # GET /gold_standard
    gold_entry = None
    try:
        gs_response = requests.get(f"{BASE_URL}/gold_standard", params={"url": url})
        gs_response.raise_for_status()
        gold_entry = gs_response.json()
    except Exception:
        pass

    # POST /evaluate
    eval_result = None
    judge_result = None
    if gold_entry and parsed:
        try:
            ev_response = requests.post(
                f"{BASE_URL}/evaluate",
                json={
                    "parsed_text": parsed["parsed_text"],
                    "gold_text": gold_entry["gold_text"]
                }
            )
            ev_response.raise_for_status()
            eval_result = ev_response.json()
        except Exception as e:
            print("Errore evaluate:", e)

        # POST /evaluate_judge
        try:
            judge_response = requests.post(
                f"{BASE_URL}/evaluate_judge",
                json={
                    "parsed_text": parsed["parsed_text"],
                    "gold_text": gold_entry["gold_text"]
                }
            )
            judge_response.raise_for_status()
            judge_result = judge_response.json()
        except Exception as e:
            print("Errore evaluate_judge:", e)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=base_context(
            request,
            parsed=parsed,
            gold=gold_entry,
            gs_urls=gs_urls,
            eval=eval_result,
            judge=judge_result,
            selected_domain=domain,
            local_mode=use_local,
        )
    )


# ── GOLD STANDARD BUILDER ────────────────────────────────────────────────────

@app.get("/gs_page", response_class=HTMLResponse)
def gs_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="gs_page.html",
        context={
            "request": request,
            "domains": domains,
            "selected_domain": None,
            "gs_urls": [],
            "html_preview": None,
            "fetched_url": None,
            "error": None,
            "success": None,
        }
    )


@app.post("/gs_fetch_html", response_class=HTMLResponse)
def gs_fetch_html(
    request: Request,
    gs_domain: str = Form(""),
    gs_url: str = Form(""),
):
    """Scarica l'HTML dell'URL inserito e lo mostra per la costruzione del GS."""

    error = None
    html_preview = None

    if not gs_url.strip():
        error = "Inserisci un URL."
    else:
        try:
            parse_resp = requests.post(
                f"{BASE_URL}/parse",
                json={"url": gs_url.strip(), "local": False}
            )
            parse_resp.raise_for_status()
            data = parse_resp.json()
            html_preview = data.get("html_text", "")
        except requests.HTTPError as e:
            try:
                error = e.response.json().get("detail", str(e))
            except Exception:
                error = str(e)
        except Exception as e:
            error = str(e)

    gs_urls = fetch_gs_urls(gs_domain) if gs_domain else []

    return templates.TemplateResponse(
        request=request,
        name="gs_page.html",
        context={
            "request": request,
            "domains": domains,
            "selected_domain": gs_domain,
            "gs_urls": gs_urls,
            "html_preview": html_preview,
            "fetched_url": gs_url.strip() if not error else None,
            "error": error,
            "success": None,
        }
    )


@app.post("/gs_submit", response_class=HTMLResponse)
def gs_submit(
    request: Request,
    gs_domain: str = Form(""),
    gs_url: str = Form(""),
    gs_html: str = Form(""),
    gold_text: str = Form(""),
):
    """Salva web_resource + gold_standard nel DB."""

    error = None
    success = None

    if not gs_url.strip() or not gs_html.strip() or not gold_text.strip():
        error = "URL, HTML e gold text sono tutti obbligatori."
    else:
        # Prima aggiungi web_resource
        try:
            wr_resp = requests.post(
                f"{BASE_URL}/add_web_resource",
                json={"url": gs_url.strip(), "html_text": gs_html.strip()}
            )
            wr_resp.raise_for_status()
        except requests.HTTPError as e:
            try:
                error = "Errore add_web_resource: " + e.response.json().get("detail", str(e))
            except Exception:
                error = str(e)
        except Exception as e:
            error = str(e)

        # Poi aggiungi gold_standard
        if not error:
            try:
                gs_resp = requests.post(
                    f"{BASE_URL}/add_gold_standard",
                    json={"url": gs_url.strip(), "gold_text": gold_text.strip()}
                )
                gs_resp.raise_for_status()
                success = f"Entry aggiunta con successo per: {gs_url.strip()}"
            except requests.HTTPError as e:
                try:
                    error = "Errore add_gold_standard: " + e.response.json().get("detail", str(e))
                except Exception:
                    error = str(e)
            except Exception as e:
                error = str(e)

    gs_urls = fetch_gs_urls(gs_domain) if gs_domain else []

    return templates.TemplateResponse(
        request=request,
        name="gs_page.html",
        context={
            "request": request,
            "domains": domains,
            "selected_domain": gs_domain,
            "gs_urls": gs_urls,
            "html_preview": None,
            "fetched_url": None,
            "error": error,
            "success": success,
        }
    )


@app.post("/gs_delete", response_class=HTMLResponse)
def gs_delete(
    request: Request,
    gs_domain: str = Form(""),
    delete_url: str = Form(""),
):
    """Elimina una entry dal gold_standard."""

    error = None
    success = None

    try:
        del_resp = requests.delete(
            f"{BASE_URL}/gold_standard",
            json={"url": delete_url}
        )
        del_resp.raise_for_status()
        success = f"Entry eliminata: {delete_url}"
    except requests.HTTPError as e:
        try:
            error = e.response.json().get("detail", str(e))
        except Exception:
            error = str(e)
    except Exception as e:
        error = str(e)

    gs_urls = fetch_gs_urls(gs_domain) if gs_domain else []

    return templates.TemplateResponse(
        request=request,
        name="gs_page.html",
        context={
            "request": request,
            "domains": domains,
            "selected_domain": gs_domain,
            "gs_urls": gs_urls,
            "html_preview": None,
            "fetched_url": None,
            "error": error,
            "success": success,
        }
    )


@app.post("/gs_select_domain", response_class=HTMLResponse)
def gs_select_domain(
    request: Request,
    gs_domain: str = Form(""),
):
    """Aggiorna la lista GS per il dominio selezionato."""

    gs_urls = fetch_gs_urls(gs_domain) if gs_domain else []

    return templates.TemplateResponse(
        request=request,
        name="gs_page.html",
        context={
            "request": request,
            "domains": domains,
            "selected_domain": gs_domain,
            "gs_urls": gs_urls,
            "html_preview": None,
            "fetched_url": None,
            "error": None,
            "success": None,
        }
    )


# ── STATS ─────────────────────────────────────────────────────────────────────

@app.get("/stats_page", response_class=HTMLResponse)
def stats_page(request: Request):
    stats = None
    error = None

    try:
        r = requests.get(f"{BASE_URL}/db_stats")
        r.raise_for_status()
        raw = r.json()
        stats = raw.get("db_status", raw)
    except Exception as e:
        error = f"Impossibile recuperare le statistiche: {e}"
        return templates.TemplateResponse(
            request=request,
            name="stats_page.html",
            context={"request": request, "stats": None, "domains": domains, "error": error}
        )

    if stats.get("evaluations") == {} or stats.get("llm_judgments") == {}:
        for domain in domains:
            try:
                requests.get(f"{BASE_URL}/full_gs_eval", params={"domain": domain})
            except Exception as e:
                print(f"Errore full_gs_eval per {domain}: {e}")

        try:
            r = requests.get(f"{BASE_URL}/db_stats")
            r.raise_for_status()
            stats = r.json().get("db_status", {})
        except Exception as e:
            error = f"Errore secondo fetch db_stats: {e}"

    return templates.TemplateResponse(
        request=request,
        name="stats_page.html",
        context={
            "request": request,
            "stats": stats,
            "domains": domains,
            "error": error,
        }
    )