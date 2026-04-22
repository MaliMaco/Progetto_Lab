from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests
from pathlib import Path
import re
import os

app = FastAPI(title="Frontend API")

gold = None
gs_list = []
domains = [
        "en.wikipedia.org",
        "ecb.europa.eu",
        "apps.apple.com",
        "tandfonline.com"
    ]

pattern_domain = r'^(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})(?::\d+)?'

BASE_DIR = Path(__file__).parent.parent
templates = Jinja2Templates(directory=BASE_DIR/"templates")

BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8003")


def extract_domain(url):
    match = re.search(pattern_domain, url)
    return match.group(1) if match else None



@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html", 
        context={
            "request" : request,
            "parsed": None,
            "gold": gold,
            "gs_list": gs_list,
            "eval": None
        })

@app.post("/parse_ui", response_class=HTMLResponse)
def parse_ui(request: Request, url: str = Form(None)):
    if url == None or not url.strip():
        return templates.TemplateResponse(
        request=request,
        name="index.html", 
        context={
            "request": request,
            "error": "Inserisci un URL."
        })
    
    domain = extract_domain(url)

    if not domain:
        return templates.TemplateResponse(
        request=request,
        name="index.html", 
        context={
            "request": request,
            "error": "URL non valido."
        })
    
    if domain not in domains:
        return templates.TemplateResponse(
            request=request,
            name="index.html", 
            context={
                "request": request,
                "error": "Dominio non supportato."
             })

    response = requests.get(f"{BASE_URL}/parse", params={"url":url})
    if (response.raise_for_status()) == 404:
        print("Allarme!!! Errore: ", response.raise_for_status())
    parsed = response.json()

    domain = extract_domain(url)


    if domain: 
        try:
            response =  requests.get(
                f"{BASE_URL}/full_gold_standard",
                params={"url": url}
            )

            response.raise_for_status()
            gs_data = response.json()

            gs_list = gs_data.get("gold_standard",[])
        except Exception as e:
            gs_list = []
            print("Errore: ", e)

    try:
        response = requests.get(
            f"{BASE_URL}/gold_standard",
            params={"url": url}
        )

        response.raise_for_status()
        gold = response.json()
    except Exception as e:
        gold = None
        print("Errore: ", e)

    eval_result = None
    if gold and parsed:
        try:
            response = requests.post(
                f"{BASE_URL}/evaluate",
                json={
                    "md_text": parsed["md_text"],
                    "gold_text": gold["gold_text"]
                }
            )
            response.raise_for_status()
            eval_result = response.json()
        except Exception as e:
            eval_result = None
            print("Errore evaluate: ", e)


    return templates.TemplateResponse(
        request=request,
        name="index.html", 
        context={
        "request": request,
        "parsed": parsed,
        "gold": gold,
        "gs_list": gs_list,
        "eval": eval_result
    })