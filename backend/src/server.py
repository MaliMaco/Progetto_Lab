from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from crawler import parser_run, html_parser_run
import asyncio
import re
import os
import json
from pathlib import Path
from evaluator import TokenEvaluator
from remove_markdown import remove_markdown
from bs4 import BeautifulSoup

app = FastAPI(title="Backend API")

pattern_domain = r'^(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})(?::\d+)?'
domains_path = os.path.join(Path(__file__).parent.parent.parent, 'domains.json')

class ParseInput(BaseModel):
    url: str
    html_text: str

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

class FullGSResponse(BaseModel):
    gold_standard: List[Dict[str,str]]

class DomainsResponse(BaseModel):
    domains: List[str]

class EvaluateRequest(BaseModel):
    parsed_text: str
    gold_text: str

class EvaluateResponse(BaseModel):
    token_level_eval: Dict[str,float]


@app.get("/parse")
def parse(url: str) -> ParseOutput:
    match = re.search(pattern_domain, url)
    domain = match.group(1)
    result = asyncio.run(parser_run(url))
    if result.status_code == 404:
        raise HTTPException(status_code=404, detail="URL irrangiugibile.")
    if result.status_code == 500:
        raise HTTPException(status_code=500, detail="Dominio non supportato.")
    with open(domains_path, 'r', encoding="UTF-8") as dm_file:
        domains = json.load(dm_file)
        if domain not in domains['domains']:
            raise HTTPException(status_code=400, detail="Dominio non supportato.")
    html_text = result.html
    soup = BeautifulSoup(html_text, "html.parser")
    title_tag = soup.find("h1", id="firstHeading") or soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""
    md_text = remove_markdown(result.markdown)
    md_text = re.sub(r'\(\s*https?://[^)]*\)', ' ', md_text)
    md_text = re.sub(r'[\u2018\u2019\u201a\u201b\u2032]', "'", md_text)
    md_text = re.sub(r'[\u201c\u201d\u201e\u201f]', '"', md_text)
    md_text = re.sub(r'[\u2013\u2014\u2015]', '-', md_text)
    md_text = re.sub(r'[^\x00-\x7F\u00C0-\u024F\u20AC\u00e8]', '', md_text)
    md_text = re.sub(r'(?<=[^\s])\u00f9(?=[A-ZÀÈÉÌÒÙ])', ' ', md_text)
    md_text = re.sub(r"[^a-zA-Z0-9\u00C0-\u00FF\s']", ' ', md_text)
    md_text = re.sub(r'\s+', ' ', md_text).strip()
    return ParseOutput(
        url=url, 
        domain=domain, 
        title=title, 
        html_text=html_text, 
        parsed_text=md_text
    )

@app.post("/parse")
def post_parse(input: ParseInput) -> ParseOutput:
    match = re.search(pattern_domain, input.url)
    domain = match.group(1)
    with open(domains_path, 'r', encoding="UTF-8") as dm_file:
        domains = json.load(dm_file)
        if domain not in domains['domains']:
            raise HTTPException(status_code=400, detail="Dominio non supportato.")
    
    html_text = input.html_text
    result = asyncio.run(html_parser_run("raw://"+input.html_text))
    soup = BeautifulSoup(html_text, "html.parser")
    title_tag = soup.find("h1", id="firstHeading") or soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""
    md_text = remove_markdown(result.markdown)
    md_text = re.sub(r'\(\s*https?://[^)]*\)', ' ', md_text)
    md_text = re.sub(r'[\u2018\u2019\u201a\u201b\u2032]', "'", md_text)
    md_text = re.sub(r'[\u201c\u201d\u201e\u201f]', '"', md_text)
    md_text = re.sub(r'[\u2013\u2014\u2015]', '-', md_text)
    md_text = re.sub(r'[^\x00-\x7F\u00C0-\u024F\u20AC\u00e8]', '', md_text)
    md_text = re.sub(r'(?<=[^\s])\u00f9(?=[A-ZÀÈÉÌÒÙ])', ' ', md_text)
    md_text = re.sub(r"[^a-zA-Z0-9\u00C0-\u00FF\s']", ' ', md_text)
    md_text = re.sub(r'\s+', ' ', md_text).strip()
    return ParseOutput(
        url=input.url, 
        domain=domain, 
        title=title, 
        html_text=input.html_text, 
        parsed_text=md_text
    )
    
@app.get("/domains")
def get_domains() -> DomainsResponse:
    with open(domains_path, 'r', encoding="UTF-8") as dm_file:
        domini = json.load(dm_file)
    return DomainsResponse(
        domains=domini['domains']
        )
    

@app.get("/gold_standard")
def get_gold_standard(url:str) -> GSResponse:
    match = re.search(pattern_domain, url)
    domain = match.group(1)
    with open(domains_path, 'r', encoding="UTF-8") as dm_file:
        domains = json.load(dm_file)
        if domain not in domains['domains']:
            raise HTTPException(status_code=400, detail="Dominio non supportato.")
    GS_path = os.path.join(Path(__file__).parent.parent.parent,f"gs_data/{domain}/GS.json")
    with open(GS_path, 'r', encoding="UTF-8") as GS_file:
        gs = json.load(GS_file)
        for single_gs in gs:
            if single_gs['url'] == url:
                return GSResponse(url=url,
                            title=single_gs['title'], 
                            domain=single_gs['domain'],
                            html_text=single_gs['html_text'], 
                            gold_text=single_gs['gold_text']
                                )
        raise HTTPException(status_code=400, detail="URL non presente nel GS.")
    

@app.get("/full_gold_standard")
def get_full_gold_standard(domain: str) -> FullGSResponse:
    with open(domains_path, 'r', encoding="UTF-8") as dm_file:
        domains = json.load(dm_file)
        if domain not in domains['domains']:
            raise HTTPException(status_code=400, detail="Dominio non supportato.")
        
    GS_path = os.path.join(Path(__file__).parent.parent.parent,f"gs_data/{domain}/GS.json")
    full_gs = []
    with open(GS_path, 'r', encoding="UTF-8") as GS_file:
        gs = json.load(GS_file)
        for gs_elem in gs:
            full_gs.append(gs_elem)
        return FullGSResponse(gold_standard=full_gs)


@app.post("/evaluate")
def evaluate(request: EvaluateRequest) -> EvaluateResponse:
    clean_gold_text = re.sub(r'[\u2018\u2019\u201a\u201b\u2032]', "'", request.gold_text)
    clean_gold_text = re.sub(r"[^\w\s'\"]", ' ', clean_gold_text)
    clean_gold_text = re.sub(r'[.,?!:;]', ' ', clean_gold_text)   
    clean_gold_text = re.sub(r'\[\d+\]', '', clean_gold_text)
    clean_gold_text = re.sub(r'\s+', ' ', clean_gold_text).strip()
    parsed_set = TokenEvaluator.token_parsed_text(request.parsed_text.lower())
    gold_set = TokenEvaluator.token_gold_text(clean_gold_text.lower())
    payload = TokenEvaluator.evaluate(parsed_text=parsed_set,gold_text=gold_set)
    return EvaluateResponse(token_level_eval=payload)

@app.get("/full_gs_eval")
def get_full_gs_eval(domain: str) -> EvaluateResponse:
    with open(domains_path, 'r', encoding="UTF-8") as dm_file:
        domains = json.load(dm_file)
        if domain not in domains['domains']:
            raise HTTPException(status_code=400, detail="Dominio non supportato.")
    
    full_gs_response = get_full_gold_standard(domain=domain).gold_standard
    sum_precision = 0.0
    sum_recall = 0.0
    sum_f1 = 0.0
    gs_number = 0
    for gs in full_gs_response:
        result = parse(gs['url'])
        evaluation = evaluate(EvaluateRequest(parsed_text=result.parsed_text, gold_text=gs['gold_text']))
        sum_precision += evaluation.token_level_eval.get("precision")
        sum_recall += evaluation.token_level_eval.get("recall")
        sum_f1 += evaluation.token_level_eval.get("f1")
        gs_number += 1

    precision = sum_precision/gs_number
    recall = sum_recall/gs_number
    f1 = sum_f1/gs_number

    payload = {
            "precision": precision,
            "recall": recall,
            "f1": f1
    }

    return EvaluateResponse(token_level_eval=payload)