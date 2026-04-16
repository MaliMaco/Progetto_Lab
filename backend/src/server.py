from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any
from crawler import parser_run
import asyncio
import re
import os
from pathlib import Path


app = FastAPI(title="Backend API")


class ParseOutput(BaseModel):
    url: str
    domain: str
    title: str
    html_text: str
    parsed_text: str

class GSResponse(BaseModel):
    url: str
    domain: str
    title: str
    html_text: str
    gold_text: str

class DomainsResponse(BaseModel):
    domains: List[str]


@app.get("/parse")
def parse(url: str) -> ParseOutput:
    result = asyncio.run(parser_run(url))
    pattern_title = r'<title>(.*?)</title>'
    match = re.search(pattern_title, result.html)
    title = match.group(1)
    pattern_domain = r'^(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})(?::\d+)?'
    match = re.search(pattern_domain, url)
    domain = match.group(1)
    html_text = result.html
    md_text = result.markdown
    md_text = re.sub(r'\(\s*https?://[^)]*\)', ' ', md_text)
    md_text = re.sub(r'\[\d+\]', ' ', md_text)
    md_text = re.sub(r'[^a-zA-Z0-9]', ' ', md_text)
    return ParseOutput(
        url=url, 
        domain=domain, 
        title=title, 
        html_text=html_text, 
        md_text=md_text
    )
    
@app.get("/domains")
def get_domains() -> DomainsResponse:
    domini = [
        "en.wikipedia.org",
        "www.ecb.europa.eu",
        "apps.apple.com",
        "tandfonline.com"
            ]
    return DomainsResponse(
        domains=domini
        )
    

@app.get("/gold_standard")
def get_gold_standard(url:str):
    pattern_domain = r'^(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})(?::\d+)?'
    match = re.search(pattern_domain, url)
    domain = match.group(1)
    domains_path = os.path.join(Path(__file__).parent.parent, 'domains.json')
    with open(domains_path, 'r') as dm_file:
        domains = dm_file.read()
        if domain not in domains['domains']:
            return HTTPException(status_code=400, detail="Dominio non supportato.")
    GS_path = os.path.join(Path(__file__).parent.parent,f"gs_data/{domain}/GS.json")
    with open(GS_path, 'r', encoding="UTF-8") as GS_file:
        gs_list = GS_file.read()
        for gs in gs_list:
            if gs['url'] == url:
                return GSResponse(url=url,
                                title=gs['title'], 
                                domain=gs['domain'],
                                html_text=gs['html_text'], 
                                gold_text=gs['gold_text']
                                )
        return HTTPException(status_code=400, detail="url non presente nel GS.")
    

@app.get("/full_gold_standard")
def get_full_gold_standard():
    pass

@app.post("/evaluate")
def evaluate():
    pass

@app.get("/full_gs_eval")
def get_full_gs_eval():
    pass