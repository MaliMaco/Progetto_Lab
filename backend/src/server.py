from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any
from crawler import parser_run
import asyncio
import re

app = FastAPI(title="Backend API")


class ParseOutput(BaseModel):
    url: str
    domain: str
    title: str
    html_text: str
    parsed_text: str

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
def get_gold_standard():
    pass

@app.get("/full_gold_standard")
def get_full_gold_standard():
    pass

@app.post("/evaluate")
def evaluate():
    pass

@app.get("/full_gs_eval")
def get_full_gs_eval():
    pass