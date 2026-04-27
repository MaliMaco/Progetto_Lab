from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests
from pathlib import Path
import os
from typing import Optional

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

gold = None
gs_list = []
domains = [
    "en.wikipedia.org",
    "www.ecb.europa.eu",
    #"www.tandfonline.com",
    #"apps.apple.com"
]

BASE_DIR = Path(__file__).parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8003")


def extract_domain(url: str) -> str:
    url_list = url.split("/")
    return url_list[2] if len(url_list) > 2 else ""


def fetch_gs_list(domain: str) -> list:
    """
    Recupera la lista Gold Standard dal backend per il dominio dato.
    """
    try:
        response = requests.get(
            f"{BASE_URL}/full_gold_standard",
            params={"domain": domain}
        )
        response.raise_for_status()
        return response.json().get("gold_standard", [])
    except Exception as e:
        print("Errore fetch del GS:", e)
        return []


def base_context(request: Request, **kwargs) -> dict:
    """
    Costruisce il contesto base comune a tutte le response.
    Tale contesto presenta:
    * request: richiesta necessaria a Jinja2 per il rendering dinamico.
    * domains: lista dei domini per popolare il menù a tendina.
    * parsed: l'oggetto di classe ParseOutput.
    * gold: l'entry del Golden Standard dell'URL analizzato.
    * gs_list: il Gold Standard del dominio di interesse.
    * eval: oggetto di classe EvaluateResponse.
    * error: messaggio di errore da stampare.
    * selected_domain: dominio selezionato nel menù.
    * prefill_url: URL da inserire nel campo testo dell'input alla scelta 
    """
    return {
        "request": request,
        "domains": domains,        
        "parsed": None,
        "gold": None,
        "gs_list": [],
        "eval": None,
        "error": None,
        "selected_domain": None,   # dominio attualmente selezionato nel menu
        "prefill_url": None,       # URL da pre-compilare nel campo testo
        **kwargs
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
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

    gs = fetch_gs_list(domain_select)
    first_url = gs[0]["url"] if gs else None

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=base_context(
            request,
            gs_list=gs,
            selected_domain=domain_select,
            prefill_url=first_url,   # pre-compila il campo URL col primo GS
        )
    )


@app.post("/parse_ui", response_class=HTMLResponse)
def parse_ui(
    request: Request,
    url: str = Form(None),
    domain_select: str = Form("") #cattura l'input non necessario.
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
    if url not in domains:
        try:
            domain = extract_domain(url)
        except:
            return templates.TemplateResponse(
            request=request,
            name="index.html",
            context=base_context(request, error="Inserisci un URL valido.")
        )
    else:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context=base_context(request, error="Inserito un URL composto da solo dominio.")
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

    '''
    Per tandfonline usiamo l'HTML nel gold standard nel caso in cui si cada in un blocco di Cloudflare.
    '''
    if domain == "www.tandfonline.com":
        response = requests.get(f"{BASE_URL}/gold_standard", params={"url": url})
        response.raise_for_status()
        gold_data = response.json()
        payload = {"url": url, "html_text": gold_data["html_text"]}
        response = requests.post(f"{BASE_URL}/parse", json=payload)
        response.raise_for_status()
    else:
        response = requests.get(f"{BASE_URL}/parse", params={"url": url})

    parsed = response.json()

    '''
    Viene recuperato l'intero Gold Standard del dominio.
    '''
    gs = fetch_gs_list(domain)

    '''Estrazione della entry del Gold Standard associato all'URL inserito.'''
    gold_entry = None
    try:
        response = requests.get(f"{BASE_URL}/gold_standard", params={"url": url})
        response.raise_for_status()
        gold_entry = response.json()
    except Exception as e:
        print("Errore gold_standard:", e)

    '''
    Valutazione della entry.
    '''
    eval_result = None
    if gold_entry and parsed:
        try:
            response = requests.post(
                f"{BASE_URL}/evaluate",
                json={
                    "parsed_text": parsed["parsed_text"],
                    "gold_text": gold_entry["gold_text"]
                }
            )
            response.raise_for_status()
            eval_result = response.json()
        except Exception as e:
            print("Errore evaluate:", e)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=base_context(
            request,
            parsed=parsed,
            gold=gold_entry,
            gs_list=gs,
            eval=eval_result,
            selected_domain=domain,  # mantiene il dominio selezionato nel menu
        )
    )
