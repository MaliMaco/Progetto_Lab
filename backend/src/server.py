from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from crawler import parser_run, html_parser_run
import asyncio
import html
import os
import json
from pathlib import Path
from evaluator import TokenEvaluator
from remove_markdown import remove_markdown
from bs4 import BeautifulSoup


app = FastAPI(title="Backend API")


'''
Server di logica implementato con FastAPI che rende disponibili gli endpoint secondo la speficica dei professori.
All'interno dei singoli metodi è presente una descrizione riassiuntiva delle funzionalità implementate.
'''


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

    '''
    * GET /parse: invoca il crawler sull'URL dato in input e restituisce un oggetto di tipo ParseOutput.
    In base al dominio di appartenenza dell'URL verrà usata una configurazione opportuna del crawler.
    Se l'URL è irraggiungibile o se il dominio non è supportato restituisce un errore.
    '''

    url_list = url.split("/")
    domain = url_list[2]
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
    md_text = result.markdown
    soup = BeautifulSoup(html_text, "html.parser")
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text(strip=True)
    else:
        div_title = soup.find('div', class_='title')
        title = div_title.get_text(strip=True) if div_title else "Nessun titolo"
    return ParseOutput(
        url=url, 
        domain=domain, 
        title=title, 
        html_text=html_text, 
        parsed_text=md_text
    )

@app.post("/parse")
def post_parse(input: ParseInput) -> ParseOutput:

    '''
    * POST /parse: invoca il crawler sull'HTML grezzo passato insieme all'URL associato mediante un oggetto di tipo ParseInput 
        e restituisce un oggetto di tipo ParseOutput. l'URL è necessario per estrarre il dominio di appartenenza al fine di poter
        decidere, come per l'endpoint GET /parse una configurazione adatta del parser.
        Lancia un errore se il dominio non è supportato.
    '''

    url_list = input.url.split("/")
    domain = url_list[2]
    with open(domains_path, 'r', encoding="UTF-8") as dm_file:
        domains = json.load(dm_file)
        if domain not in domains['domains']:
            raise HTTPException(status_code=400, detail="Dominio non supportato.")
    
    html_text = input.html_text
    result = asyncio.run(html_parser_run(input.html_text, domain))
    soup = BeautifulSoup(html_text, "html.parser")
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text(strip=True)
    else:
        div_title = soup.find('div', class_='title')
        title = div_title.get_text(strip=True) if div_title else "Nessun titolo"
    md_text = result.markdown
    return ParseOutput(
        url=input.url, 
        domain=domain, 
        title=title, 
        html_text=input.html_text, 
        parsed_text=md_text
    )
    
@app.get("/domains")
def get_domains() -> DomainsResponse:

    '''
    * GET /domains: restituisce la lista dei domini parsati tramite un oggetto di classe DomainsResponse.
        La lista contiene i domini parsabili con successo contenuti nel file domains.json
    '''

    with open(domains_path, 'r', encoding="UTF-8") as dm_file:
        domini = json.load(dm_file)
    return DomainsResponse(
        domains=domini['domains']
        )
    

@app.get("/gold_standard")
def get_gold_standard(url: str) -> GSResponse:

    '''
    * GET /gold_standard: preso in input un URL cerca la entry associata nel Gold Standard del dominio e 
        restituisce un oggetto di tipo GSResponse. Se l'URL non ha un entry associata oppure il dominio non 
        è presente viene lanciato un errore.
    '''

    url_list = url.split("/")
    domain = url_list[2]
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

    '''
    * GET /full_gold_standard: preso in input un dominio restituisce un oggetto FullGSResponse contenente la lista
        di tutte le entry del Gold Standard per il dominio dato in input.
        Lancia un errore se il dominio non è supportato.
    '''

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

    '''
    * POST /evaluate: preso in input un oggetto di classe EvaluateRequest contenente il testo parsato risultante di uno dei metodi /parse
        ed il gold text contenuto nel gold standard associato restituisce le metriche di evaluation wrappate in un oggetto di classe EvaluateResponse.
        Se il parsed text o il gold text o entrambi risultano vuoti, verrà restituita una valutazione nulla.
    '''

    if not request.parsed_text or not request.gold_text:
        payload = {
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0
            }
        return EvaluateResponse(token_level_eval=payload)
    
    md_text = html.unescape(remove_markdown(request.parsed_text))

    clean_gold_text = request.gold_text

    parsed_set = TokenEvaluator.token_parsed_text(md_text.lower())
    gold_set = TokenEvaluator.token_gold_text(clean_gold_text.lower())
    payload = TokenEvaluator.evaluate(parsed_text=parsed_set,gold_text=gold_set)
    return EvaluateResponse(token_level_eval=payload)

@app.get("/full_gs_eval")
def get_full_gs_eval(domain: str) -> EvaluateResponse:

    '''
    * GET /full_gs_eval: dato un dominio in input, restituisce la valutazione complessiva del Gold Standard associato a tale dominio
        calcolando la media delle metriche di valutazione delle singole entry wrappandole in un oggetto di classe EvaluateResponse.
        Lancia un errore se il dominio in input non è supportato.
    '''

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
        try:
            result = parse(
                gs['url']
            )
            evaluation = evaluate(
                EvaluateRequest(
                    parsed_text=result.parsed_text, 
                    gold_text=gs['gold_text']
                    )
                )
            sum_precision += evaluation.token_level_eval.get("precision")
            sum_recall += evaluation.token_level_eval.get("recall")
            sum_f1 += evaluation.token_level_eval.get("f1")
            gs_number += 1
        except HTTPException:
            #gs_number += 1
            continue
        except Exception:
            #gs_number += 1
            continue

    precision = sum_precision/gs_number if gs_number > 0 else 0.0
    recall = sum_recall/gs_number if gs_number > 0 else 0.0
    f1 = sum_f1/gs_number if gs_number > 0 else 0.0

    payload = {
            "precision": precision,
            "recall": recall,
            "f1": f1
    }

    return EvaluateResponse(token_level_eval=payload)