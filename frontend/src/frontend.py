from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import requests
from pathlib import Path
import re 

app = FastAPI(title="Frontend API")
pattern_domain = r'^(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})(?::\d+)?'


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR/"templates"))

BASE_URL = "http://0.0.0.0:8003"


pattern_domain = r'^(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})(?::\d+)?'

def extract_domain(url):
    match = re.search(pattern_domain, url)
    return match.group(1) if match else None



@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request" : request
    })

@app.get("/parse_ui")
def parse_ui(request: Request, url: str):
    parsed = requests.get(f"{BASE_URL}/parse", params={"url":url}).json()

    domain = extract_domain(url)

    gold = None
    gs_list = []

    if domain: 
        try:
            gs_data = requests.get(
                f"{BASE_URL}/full_gold_standard",
                params={"domain": domain}
            ).json()

            gs_list = gs_data.get("gold_standard",[])
        except:
            gs_list = []

    try:
        gold = requests.get(
            f"{BASE_URL}/gold_standard",
            params={"url": url}
        ).json()
    except:
        gold = None

    return templates.TemplateResponse("index.html", {
        "request": request,
        "parsed": parsed,
        "gold": gold,
        "gs_list": gs_list
    })
        
    









