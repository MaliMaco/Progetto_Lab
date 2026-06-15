from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests
from pathlib import Path
import os

app = FastAPI(title="Frontend API")

'''
Web UI implementata con FastAPI e Jinja2 per il rendering dinamico dei contenuti.

L'interfaccia web in HTML offre la possibilità di :

* parsare un URL e, se l'URL appartiene ad un dominio supportato, di poter testare mediante menù a tendina 
  i valori associati della entry nel Gold Standard oppure, se non è una entry del Gold Standard, 
  di poter comunque vedere il testo parsato e l'HTML grezzo della pagina.
    
* Di selezionare il dominio del quale si vuole vedere il Gold Standard direttamente attraverso un menù a tendina.

* Di poter osservare il testo parsato dal crawler in formato markdown, l'HTML grezzo del sito presente nella entry del Gold Standard,
  il gold text presente nella stessa entry e le metriche di valutazione tramite chiamata ad evaluate.
'''

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

    """
    Recupera la lista Gold Standard dal backend per il dominio dato.
    """

    try:
        r = requests.get(f"{BASE_URL}/gold_standard_urls", params={"domain": domain})
        r.raise_for_status()
        return r.json().get("gold_standard_urls", [])
    except Exception as e:
        print("Errore fetch GS urls:", e)
        return []


def base_context(request: Request, **kwargs) -> dict:

    """
    Costruisce il contesto base comune a tutte le response.
    Tale contesto presenta:
    * request: richiesta necessaria a Jinja2 per il rendering dinamico.
    * domains: lista dei domini per popolare il menù a tendina.
    * parsed: l'oggetto di classe ParseOutput.
    * gold: l'entry del Golden Standard dell'URL analizzato.
    * gs_urls: lista degli urls di un dominio.
    * eval: oggetto di classe EvaluateResponse.
    * judge: oggetto di classe JudgeEvaluateResponse.
    * error: messaggio di errore da stampare.
    * selected_domain: dominio selezionato nel menù.
    * prefill_url: URL da inserire nel campo testo dell'input alla scelta.
    * local_mode: valore local per POST /post_parse, sarà lasciato sempre a True.
    """

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



@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    '''
    * GET /home: renderizza con Jinja2 la Home del Frontend, recuperando lo status dei docker attraverso il metodo apposito.
    '''

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


'''
Le funzioni seguenti si occupano della pagina che parsa e restituisce la valutazione
dei vari url dato un dominio. È possibile scegliere un dominio grazie al menù a tendina 
oppure usare direttamente un url.
'''

@app.get("/parser", response_class=HTMLResponse)
def parser_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=base_context(request)
    )


@app.post("/select_domain", response_class=HTMLResponse)
def select_domain(request: Request, domain_select: str = Form("")):

    """
    Endpoint chiamato dal bottone "Vai al GS".
    Non avvia il parser: recupera solo il Gold Standard del dominio scelto
    e lo passa al template, tenendo selezionato il dominio nel menu.
    Pre-compila anche il campo URL con la prima entry disponibile del Gold Standard,
    potendo così cliccare Parse senza dover copiare l'URL.
    """

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
    
    '''
    Funzione che si occupa di recuperare tutti gli elementi 
    da renderizzare dinamicamente tramite Jinja2.
    '''

    '''
    Se viene inserita una stringa vuota o più spazi.
    '''
    if not url or not url.strip():
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context=base_context(request, error="Inserisci un URL.")
        )
    
    '''
    Se l'URL inviato non è direttamente un dominio oppure presenta una forma errata, come https:domain e casi simili.
    '''

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
    
    '''
    Se è inserita una stringa alfanumerica senza dominio.
    '''

    if not domain:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context=base_context(request, error="URL non valido.")
        )
    
    '''
    Se il dominio non è supportato.
    '''

    if domain not in domains:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context=base_context(request, error="Dominio non supportato.")
        )

    use_local = local_mode == "true"

    '''
    Chiamata alla POST /posta_parse per recuperare il parsed_text e l'HTML.
    '''
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
    
    '''
    Vengono recuperati gli urls del dominio.
    '''

    gs_urls = fetch_gs_urls(domain)

    '''
    Estrazione del Gold Standard associato all'URL inserito.
    '''

    gold_entry = None
    try:
        gs_response = requests.get(f"{BASE_URL}/gold_standard", params={"url": url})
        gs_response.raise_for_status()
        gold_entry = gs_response.json()
    except Exception:
        pass

    '''
    Valutazione della entry da parte di evaluate ed evaluate_judge.
    '''

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


'''
Le funzioni seguenti si occupano della pagina che permette di:
    *   parsare un url mostrando l'HTML della pagina web relativa e di inserire 
        il gold text estratto dall'url o dall'HTML al fine di creare una nuova entry nel DB.
    *   di eliminare le entry dalla tabella gold_standard.
'''

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
    """
    Scarica l'HTML dell'URL inserito con parsing live e lo mostra per la costruzione del GS.
    """

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
    """
    Salva web_resource + gold_standard nel DB.
    """

    error = None
    success = None

    if not gs_url.strip() or not gs_html.strip() or not gold_text.strip():
        error = "URL, HTML e gold text sono tutti obbligatori."
    else:
        '''
        Si aggiunge prima la entry in web_resource.
        '''
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

        '''
        Dopodiché si aggiunge la entry in gold_standard.
        '''
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
    """
    Elimina una entry dal gold_standard.
    """

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
    """
    Aggiorna la lista delle entry per il dominio selezionato.
    """

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


'''
Le funzioni seguenti si occupano della pagina che mostra le statistiche dell'intero progetto, 
come le tabelle presenti nel database con i vari domini salvati ed il numero di url salvati per dominio
e le tabelle che contengono, per dominio, la media delle metriche ottenute attraverso evaluate ed evaluate_judge.
'''

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