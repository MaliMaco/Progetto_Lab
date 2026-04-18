from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Set
from crawler import parser_run
import asyncio
import re
import os
import json
from pathlib import Path
from evaluator import TokenEvaluator


app = FastAPI(title="Backend API")

pattern_domain = r'^(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})(?::\d+)?'
domains_path = os.path.join(Path(__file__).parent.parent, 'domains.json')

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
    token_level_eval: Dict[str,Dict[str,int]]


@app.get("/parse")
def parse(url: str) -> ParseOutput:
    if result.status_code == 404:
        return HTTPException(status_code=404, detail="URL irrangiugibile.")
    result = asyncio.run(parser_run(url))
    pattern_title = r'<(?:title|(?:div\s+class=["\'](?:title|header)["\'][^>]*>\s*<h[1-6]))[^>]*>\s*(?:<[^>]+>)?\s*(.*?)\s*(?:</[^>]+>)?\s*</(?:title|h[1-6])>'
    match = re.search(pattern_title, result.html)
    title = match.group(1)
    match = re.search(pattern_domain, url)
    domain = match.group(1)
    with open(domains_path, 'r') as dm_file:
        text = dm_file.read()
        domains = json.load(text)
        if domain not in domains['domains']:
            return HTTPException(status_code=400, detail="Dominio non supportato.")
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
        parsed_text=md_text
    )
    
@app.get("/domains")
def get_domains() -> DomainsResponse:
    with open(domains_path, 'r') as dm_file:
        text = dm_file.read()
        domini = json.load(text)
    return DomainsResponse(
        domains=domini
        )
    

@app.get("/gold_standard")
def get_gold_standard(url:str):
    match = re.search(pattern_domain, url)
    domain = match.group(1)
    with open(domains_path, 'r') as dm_file:
        text = dm_file.read()
        domains = json.load(text)
        if domain not in domains['domains']:
            return HTTPException(status_code=400, detail="Dominio non supportato.")
    GS_path = os.path.join(Path(__file__).parent.parent,f"gs_data/{domain}/GS.json")
    with open(GS_path, 'r', encoding="UTF-8") as GS_file:
        gs = GS_file.read()
        for single_gs in gs:
            true_gs = json.load(single_gs)
            if true_gs['url'] == url:
                return GSResponse(url=url,
                            title=true_gs['title'], 
                            domain=true_gs['domain'],
                            html_text=true_gs['html_text'], 
                            gold_text=true_gs['gold_text']
                                )
        return HTTPException(status_code=400, detail="URL non presente nel GS.")
    

@app.get("/full_gold_standard")
def get_full_gold_standard(url: str):
    match = re.search(pattern_domain, url)
    domain = match.group(1)
    with open(domains_path, 'r') as dm_file:
        text = dm_file.read()
        domains = json.load(text)
        if domain not in domains['domains']:
            return HTTPException(status_code=400, detail="Dominio non supportato.")
        
    GS_path = os.path.join(Path(__file__).parent.parent,f"gs_data/{domain}/GS.json")
    full_gs = []
    with open(GS_path, 'r', encoding="UTF-8") as GS_file:
        gs = GS_file.read()
        for gs_elem in gs:
            golden_standard = json.load(gs_elem)
            full_gs.append(golden_standard)
        return FullGSResponse(gold_standard=full_gs)

@app.post("/evaluate")
def evaluate(request: EvaluateRequest) -> EvaluateResponse:
    parsed_set = TokenEvaluator.token_parsed_text(request.parsed_text)
    gold_set = TokenEvaluator.token_gold_text(request.gold_text)
    payload = TokenEvaluator.evaluate(parsed_text=parsed_set,gold_text=gold_set)
    return EvaluateResponse(token_level_eval=payload)

@app.get("/full_gs_eval")
def get_full_gs_eval(url: str) -> EvaluateResponse:
    full_gs_response = get_full_gold_standard(url=url)
    sum_precision = 0
    sum_recall = 0
    sum_f1 = 0
    gs_number = 0
    for gs in full_gs_response:
        result = parse(url)
        evaluation = evaluate(EvaluateRequest(result.parsed_text, gs['gold_text']))
        sum_precision += evaluation.token_level_eval.get("precision")
        sum_recall += evaluation.token_level_eval.get("recall")
        sum_f1 += evaluation.token_level_eval.get("f1")
        gs_number += 1

    precision = sum_precision/gs_number
    recall = sum_recall/gs_number
    f1 = sum_f1/gs_number

    full_gs_token_eval = {
        "token_level_eval": {
            "precision": precision,
            "recall": recall,
            "f1": f1
        }
    }

    return EvaluateResponse(token_level_eval=full_gs_token_eval)
