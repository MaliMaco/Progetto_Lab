from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager, contextmanager
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from crawler import parser_run, html_parser_run
from pathlib import Path
from evaluator import TokenEvaluator
from remove_markdown import remove_markdown
from bs4 import BeautifulSoup
import mariadb
import datetime
import time
import asyncio
import html
import os
import json
import requests

@asynccontextmanager
async def lifespan(app):

    conn = None

    for _ in range(10):
        try:
            conn = mariadb.connect(
            host="database",
            port=3306,
            user="root",
            password="biar",
            database="db_progetto"
            )
            break
        except mariadb.Error as e:
            print(f"Connection failed: {e}")
            time.sleep(2)

    if conn is None:
        raise RuntimeError("Could not connect to MariaDB")
    
    check_stability(conn=conn)
    
    dm_file = open(domains_path, 'r', encoding="UTF-8")
    domains = json.load(dm_file)
    data = domains["domains"]
    dm_file.close()

    cursor = conn.cursor()

    try:
        ollama_response = requests.post(
            f"{OLLAMA_URL}/api/pull",
            json={
                "model": "llama3.2:3b"
            }
        )
        ollama_response.raise_for_status()
    except Exception as e:
        print(f"Ollama error: {e}")

    try:
        for domain in data:
            GS_path = os.path.join(Path(__file__).parent.parent.parent,f"gs_data/{domain}/GS.json")
            GS_time = os.path.getctime(GS_path)
            c_datestamp = datetime.datetime.fromtimestamp(GS_time)
            response = get_full_gold_standard(domain=domain).gold_standard
            for gs in response:
                cursor.execute(web_insert_query, 
                    (gs['url'], gs['domain'], gs['title'],
                     gs['html_text'], c_datestamp)
                               )
                cursor.execute(gold_insert_query, 
                    (gs['url'], gs['gold_text'],
                     c_datestamp)
                               )
                conn.commit()

                try:
                    parsed = await html_parser_run(gs['html_text'], domain)
                    parsed_text = parsed.markdown
                except Exception as e:
                    print(f"Parsing iniziale fallito per {gs['url']}: {e}")
                    continue
 
                try:
                    eval_result = evaluate(
                        EvaluateRequest(
                            parsed_text=parsed_text,
                            gold_text=gs['gold_text']
                        )
                    )
                    cursor.execute(eval_insert_query, (
                        gs['url'],
                        eval_result.token_level_eval["precision"],
                        eval_result.token_level_eval["recall"],
                        eval_result.token_level_eval["f1"],
                        c_datestamp
                    ))
                    conn.commit()
                except Exception as e:
                    print(f"Evaluate iniziale fallito per {gs['url']}: {e}")
 
                try:
                    judge_result = evaluate_judge(
                        JudgeEvaluateRequest(
                            parsed_text=parsed_text,
                            gold_text=gs['gold_text']
                        )
                    )
                    cursor.execute(llm_insert_query, (
                        gs['url'],
                        judge_result.judge_score,
                        judge_result.judge_feedback,
                        c_datestamp
                    ))
                    conn.commit()
                except Exception as e:
                    print(f"Evaluate_judge iniziale fallito per {gs['url']}: {e}")
    finally:
        cursor.close()
    
    yield
    conn.close()

@contextmanager
def get_db_conn():
    conn = mariadb.connect(
        host="database",
        port=3306,
        user="root",
        password="biar",
        database="db_progetto"
    )
    try:
        yield conn
    finally:
        conn.close()

OLLAMA_URL = "http://ollama:11434"

app = FastAPI(title="Backend API", lifespan=lifespan)


'''
Server di logica implementato con FastAPI che rende disponibili gli endpoint secondo la speficica dei professori.
All'interno dei singoli metodi è presente una descrizione riassiuntiva delle funzionalità implementate.
'''

def check_stability(conn):
    is_stable = False
    try:
        # Ping the server to check connectivity
        conn.ping()
        
        # Execute a simple query to verify query processing
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        if result and result[0] == 1:
            is_stable = True
            return is_stable
        else:
            return is_stable
            
    except mariadb.Error as e:
        print(f"Database error: {e}")
        return is_stable
    finally:
        if 'cursor' in locals():
            cursor.close()

web_insert_query = (
    "INSERT INTO "
    "web_resources (url, domain, title, html_text, created_at) "
    "VALUES (?, ?, ?, ?, ?) "
    "ON DUPLICATE KEY UPDATE "
    "domain = VALUES(domain), "
    "title = VALUES(title), "
    "html_text = VALUES(html_text), "
    "created_at = VALUES(created_at)"
)

gold_insert_query = (
    "INSERT INTO "
    "gold_standard (url, gold_text, created_at) "
    "VALUES (?, ?, ?) "
    "ON DUPLICATE KEY UPDATE "
    "gold_text = VALUES(gold_text), "
    "created_at = VALUES(created_at)"
)

eval_insert_query = (
    "INSERT INTO "
    "evaluations (url, precision_score, recall_score, f1_score, created_at) "
    "VALUES (?, ?, ?, ?, ?) "
    "ON DUPLICATE KEY UPDATE "
    "precision_score = VALUES(precision_score), "    
    "recall_score = VALUES(recall_score), "
    "f1_score = VALUES(f1_score), "
    "created_at = VALUES(created_at)"
)

llm_insert_query = (
    "INSERT INTO "
    "llm_judgments (url, score, verdict, created_at) "
    "VALUES (?, ?, ?, ?) "
    "ON DUPLICATE KEY UPDATE "
    "score = VALUES(score), "
    "verdict = VALUES(verdict), "
    "created_at = VALUES(created_at)"
)

domains_path = os.path.join(Path(__file__).parent.parent.parent, 'domains.json')


class ParseInput(BaseModel):
    url: str
    local: Optional[bool]

class AddWebInput(BaseModel):
    url: str
    html_text: str

class AddGoldInput(BaseModel):
    url: str
    gold_text: str

class AddWebOutput(BaseModel):
    status: str

class AddGoldOutput(BaseModel):
    status: str

class DeleteWebInput(BaseModel):
    url: str

class DeleteGoldInput(BaseModel):
    url: str

class DeleteWebOutput(BaseModel):
    status: str

class DeleteGoldOutput(BaseModel):
    status: str

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

class GSURLSResponse(BaseModel):
    gold_standard_urls: List[str]

class FullGSResponse(BaseModel):
    gold_standard: List[Dict[str,str]]

class DomainsResponse(BaseModel):
    domains: List[str]

class EvaluateRequest(BaseModel):
    parsed_text: str
    gold_text: str

class EvaluateResponse(BaseModel):
    token_level_eval: Dict[str,float]

class JudgeEvaluateRequest(BaseModel):
    parsed_text: str
    gold_text: str

class JudgeEvaluateResponse(BaseModel):
    model_name: str
    judge_score: int
    judge_feedback: str

class FullGSEvaluateResponse(BaseModel):
    token_level_eval: Dict[str,float]
    judge_score: float

class DBStatsResponse(BaseModel):
    web_resources: Dict[str, int] = {}
    gold_standard: Dict[str, int] = {}
    avg_eval: Dict[str, Any] = {}
    avg_eval_judge: Dict[str, Any] = {}

class DBSchemaResponse(BaseModel):
    web_resources: Dict[str, str] = {}
    gold_standard: Dict[str, str] = {}
    evaluations: Dict[str, str] = {}
    llm_judgments: Dict[str, str] = {}

class StatusResponse(BaseModel):
    backend: str
    database: str
    ollama: str


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
            
    try:
        with get_db_conn() as conn:

            if input.local == False:

                crawl_result = asyncio.run(parser_run(input.url))
                html_text = crawl_result.html
                result = asyncio.run(html_parser_run(html_text, domain))

            else:

                web_select_query = "SELECT html_text " \
                            "FROM web_resources " \
                            "WHERE url = ?"

                with conn.cursor() as cursor:
                    try:
                        cursor.execute(
                            web_select_query,
                            (input.url,)
                        )
                        result = cursor.fetchone()
                        html_text = result[0]
                        result = asyncio.run(html_parser_run(html_text, domain))
                    except:
                        raise HTTPException(status_code=400, detail="URL non presente nel DB.")

            
            soup = BeautifulSoup(html_text, "html.parser")
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
            else:
                div_title = soup.find('div', class_='title')
                title = div_title.get_text(strip=True) if div_title else "Nessun titolo"
            md_text = result.markdown

            with conn.cursor() as cursor:
                cursor.execute(web_insert_query, (
                    input.url,
                    domain,
                    title,
                    html_text,
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                )
            conn.commit()

    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ParseOutput(
        url=input.url, 
        domain=domain, 
        title=title, 
        html_text=html_text, 
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
        restituisce un oggetto di tipo GSResponse. Le informazioni vengono caricate dal DB dockerizzato. 
        Se l'URL non ha un entry associata oppure il dominio non è presente viene lanciato un errore.
    '''

    url_list = url.split("/")
    domain = url_list[2]
    
    '''
    with open(domains_path, 'r', encoding="UTF-8") as dm_file:
        domains = json.load(dm_file)
        if domain not in domains['domains']:
            raise HTTPException(status_code=400, detail="Dominio non supportato.")
    '''
    
    try:
        with get_db_conn() as conn:
            gold_select_query = "SELECT gold_text " \
                        "FROM gold_standard " \
                        "WHERE url = ?"
            
            web_select_query = "SELECT title, domain, html_text " \
                            "FROM web_resources " \
                            "WHERE url = ?"

            with conn.cursor() as cursor:

                cursor.execute(gold_select_query, (url, ))
                result = cursor.fetchone()
                if result != None:
                    gold_result = result[0]
                
                cursor.execute(web_select_query, (url, ))
                result = cursor.fetchone()
                if result != None:
                    print("title, domain and html_text present")
                    title_result = result[0]
                    domain_result = result[1]
                    html_text_result = result[2]

    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    except:
        raise HTTPException(status_code=400, detail="URL non presente nel GS.")
    
    return GSResponse(url=url,
                        title=title_result, 
                        domain=domain_result,
                        html_text=html_text_result, 
                        gold_text=gold_result
                    )
    

@app.get("/gold_standard_urls")
def get_gold_standard_urls(domain: str) -> GSURLSResponse:
    with open(domains_path, 'r', encoding="UTF-8") as dm_file:
        domains = json.load(dm_file)
        if domain not in domains['domains']:
            raise HTTPException(status_code=400, detail="Dominio non supportato.")
        
    select_query = "SELECT gold_standard.url " \
                    "FROM web_resources join gold_standard " \
                    "on web_resources.url = gold_standard.url " \
                    "WHERE web_resources.domain = ?;"

    try:
        with get_db_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(select_query, (domain, ))
                result = cursor.fetchall()
                urls_list = list()
                for elem in result:
                    urls_list.append(elem[0])

    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

    return GSURLSResponse(
        gold_standard_urls=urls_list
    )


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


@app.post("/evaluate_judge")
def evaluate_judge(request: JudgeEvaluateRequest) -> JudgeEvaluateResponse:

    if not request.parsed_text or not request.gold_text:
        return JudgeEvaluateResponse(
            model_name="qwen3",
            judge_score=0,
            judge_feedback="I testi sono vuoti."
        )
    
    cleaned_md_text = html.unescape(remove_markdown(request.parsed_text))

    cleaned_parsed_text = TokenEvaluator.normalize(cleaned_md_text.lower())
    cleaned_gold_text = TokenEvaluator.normalize(request.gold_text.lower())

    payload = {
        "model": "llama3.2:3b",
        "messages": [ 
            {
            "role": "system", 
            "content": '''
            Restituisci SOLO JSON valido.
            Sei un esperto nel confronto di testi.
            Confronta parsed_text e gold_text considerando SOLO 
            quanti token hanno in comune.
            NON considerare grammatica, sintassi o significato.
            Scala voto:
            1 = testi completamente diversi
            2 = pochi token in comune
            3 = circa metà token in comune
            4 = molti token in comune
            5 = testi quasi identici
            Restituisci SOLO un JSON con:
            - voto (intero)
            - feedback (stringa)
            '''
            },
            {
            "role": "user", 
            "content": f'''parsed_text: {cleaned_parsed_text[800:0]}. 
            gold_text: {cleaned_gold_text[800:0]}.
            Restituisci un voto ed un feedback.'''
            } 
            ],
        "raw": True,
        "format": {
            "type": "object",
            "properties": {
            "voto": {
                "type": "integer"
            },
            "feedback": {
                "type": "string"
            }
            },
            "required": ["voto", "feedback"]
        },
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 200
        }
        }

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json=payload
    )
    response.raise_for_status()

    raw_response = response.json()

    raw_json_string = raw_response["message"]["content"].strip()

    try:
        parsed_response = json.loads(raw_json_string)

        llm_score = parsed_response["voto"]
        llm_feedback = parsed_response["feedback"]

    except json.JSONDecodeError:

        llm_score = 0
        llm_feedback = (
            f"Errore parsing JSON LLM: {raw_json_string}"
        )

    return JudgeEvaluateResponse(
        model_name=raw_response['model'],
        judge_score=llm_score,
        judge_feedback=llm_feedback
    )


@app.get("/full_gs_eval")
def get_full_gs_eval(domain: str) -> FullGSEvaluateResponse:

    '''
    * GET /full_gs_eval: dato un dominio in input, restituisce la valutazione complessiva del Gold Standard associato a tale dominio
        calcolando la media delle metriche di valutazione delle singole entry wrappandole in un oggetto di classe EvaluateResponse.
        Lancia un errore se il dominio in input non è supportato.
    '''

    with open(domains_path, 'r', encoding="UTF-8") as dm_file:
        domains = json.load(dm_file)
        if domain not in domains['domains']:
            raise HTTPException(status_code=400, detail="Dominio non supportato.")
    
    full_gs_response = get_gold_standard_urls(domain=domain).gold_standard_urls
    sum_precision = 0.0
    sum_recall = 0.0
    sum_f1 = 0.0
    sum_judge_score = 0.0
    gs_number = 0

    for elem in full_gs_response:
        try:
            
            gs_response = get_gold_standard(elem)

            result = post_parse(
                        ParseInput(
                            url=gs_response.url,
                            local=True
                        )
                    )

            try:
                with get_db_conn() as conn:

                    with conn.cursor() as cursor:

                        cursor.execute(
                            "SELECT precision_score, recall_score, f1_score FROM evaluations WHERE url = ?",
                            (elem, )
                        )

                        result_evaluations = cursor.fetchone()

                        cursor.execute(
                            "SELECT score, verdict FROM llm_judgments WHERE url = ?",
                            (elem, )
                        )

                        result_llm = cursor.fetchone()
                        
                        if result_evaluations is not None:

                            evaluation = EvaluateResponse(
                                token_level_eval={
                                    "precision": result_evaluations[0],
                                    "recall": result_evaluations[1],
                                    "f1": result_evaluations[2]
                                }
                            )

                        else:

                            evaluation = evaluate(
                                EvaluateRequest(
                                    parsed_text=result.parsed_text, 
                                    gold_text=gs_response.gold_text
                                )
                            )
                            
                            cursor.execute(eval_insert_query, (
                                gs_response.url,
                                evaluation.token_level_eval["precision"],
                                evaluation.token_level_eval["recall"],
                                evaluation.token_level_eval["f1"],
                                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                )
                            )

                        if result_llm is not None:

                            evaluation_judge = JudgeEvaluateResponse(
                                model_name="llama3.2:3b",
                                judge_score=result_llm[0],
                                judge_feedback=result_llm[1]
                            )
                        
                        else:

                            evaluation_judge = evaluate_judge(
                                JudgeEvaluateRequest(
                                    parsed_text=result.parsed_text, 
                                    gold_text=gs_response.gold_text
                                )
                            )

                            cursor.execute(llm_insert_query, (
                                gs_response.url,
                                evaluation_judge.judge_score,
                                evaluation_judge.judge_feedback,
                                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                )
                            )

                    conn.commit()

            except mariadb.Error as e:
                raise HTTPException(status_code=500, detail=str(e))

            sum_precision += evaluation.token_level_eval.get("precision")
            sum_recall += evaluation.token_level_eval.get("recall")
            sum_f1 += evaluation.token_level_eval.get("f1")
            sum_judge_score += evaluation_judge.judge_score
            gs_number += 1

        except HTTPException as e:
            continue

        except Exception:
            continue

    precision = sum_precision/gs_number if gs_number > 0 else 0.0
    recall = sum_recall/gs_number if gs_number > 0 else 0.0
    f1 = sum_f1/gs_number if gs_number > 0 else 0.0
    judge_score = sum_judge_score/gs_number if gs_number > 0 else 0.0

    payload = {
            "precision": precision,
            "recall": recall,
            "f1": f1
    }

    return FullGSEvaluateResponse(
        token_level_eval=payload,
        judge_score=judge_score
        )


@app.post("/add_web_resource")
def add_web_resource(input: AddWebInput) -> AddWebOutput:

    url_list = input.url.split("/")
    domain = url_list[2]

    soup = BeautifulSoup(input.html_text, "html.parser")
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text(strip=True)
    else:
        div_title = soup.find('div', class_='title')
        title = div_title.get_text(strip=True) if div_title else "Nessun titolo"

    data = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with get_db_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(web_insert_query, 
                    (input.url, domain, title, input.html_text, data)
                    )
        
            conn.commit()

    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return AddWebOutput(status="ok")


@app.post("/add_gold_standard")
def add_gold_standard(input: AddGoldInput) -> AddGoldOutput:

    try:
        with get_db_conn() as conn:
            with conn.cursor() as cursor:
                data = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                cursor.execute(gold_insert_query, (input.url, input.gold_text, data))
        
            conn.commit()

    except mariadb.IntegrityError as e:
        if e.errno == 1452:
            raise HTTPException(status_code=400, detail="URL assente in web_resources: PK-ERROR")
        else:
            raise HTTPException(status_code=400, detail="Errore nella query")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return AddGoldOutput(status="ok")


@app.delete("/web_resource")
def delete_web_resource(input: DeleteWebInput) -> DeleteWebOutput:
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cursor:

                delete_query = "DELETE FROM web_resources WHERE url = ?"
                cursor.execute(delete_query, (input.url, ))
            
            conn.commit()

    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

    return DeleteWebOutput(status="ok")



@app.delete("/gold_standard")
def delete_gold_standard(input: DeleteGoldInput) -> DeleteGoldOutput:

    try:
        with get_db_conn() as conn:
            with conn.cursor() as cursor:

                delete_query = "DELETE FROM gold_standard WHERE url = ?"
                cursor.execute(delete_query, (input.url, ))

                if cursor.rowcount == 0:
                    conn.rollback()
                    return DeleteGoldOutput(status="error")
    
            conn.commit()

    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

    return DeleteGoldOutput(status="ok")


@app.get("/db_stats")
def get_db_stats() -> DBStatsResponse:
    web_resources = dict()
    gold_standard = dict()
    evaluations = dict()
    llm_judgments = dict()
    avg_eval = dict()
    avg_eval_judge = dict()

    web_count_query = "SELECT domain, count(*) " \
    "FROM web_resources " \
    "GROUP BY domain"

    gold_count_query = "SELECT domain, count(*) " \
    "FROM gold_standard as g JOIN web_resources as w on g.url = w.url " \
    "GROUP BY domain"

    eval_count_query = "SELECT domain, count(*) " \
    "FROM evaluations as e JOIN web_resources as w on e.url = w.url " \
    "GROUP BY domain"

    llm_count_query = "SELECT domain, count(*) " \
    "FROM llm_judgments as l JOIN web_resources as w on l.url = w.url " \
    "GROUP BY domain"

    avg_eval_query = "SELECT w.domain, sum(e.precision_score), sum(e.recall_score), sum(e.f1_score), count(w.url) " \
    "FROM evaluations as e JOIN web_resources as w on e.url = w.url " \
    "GROUP BY w.domain"
    
    avg_eval_judge_query = "SELECT w.domain, sum(score), count(w.url) " \
    "FROM llm_judgments as l JOIN web_resources as w on l.url = w.url " \
    "GROUP BY domain"

    try:
        with get_db_conn() as conn:

            with conn.cursor() as cursor:

                #web_resources
                cursor.execute(web_count_query)
                result = cursor.fetchall()
                for elem in result:
                    web_resources[elem[0]] = elem[1]

                #gold_standard
                cursor.execute(gold_count_query)
                result = cursor.fetchall()
                for elem in result:
                    gold_standard[elem[0]] = elem[1]
                '''
                #evaluations
                cursor.execute(eval_count_query)
                result = cursor.fetchall()
                try:
                    for elem in result:
                        evaluations[elem[0]] = elem[1]
                except:
                    print("Tabella evaluations vuota, " \
                    "esegui una full_gs_eval per generare delle valutazioni " \
                    "o farne un aggiornamento")

                #llm_judgments
                cursor.execute(llm_count_query)
                result = cursor.fetchall()
                try:
                    for elem in result:
                        llm_judgments[elem[0]] = elem[1]
                except:
                    print("Tabella llm_judgments vuota, " \
                    "esegui una full_gs_eval per generare delle valutazioni " \
                    "o farne un aggiornamento")
                '''
                #avg_eval
                cursor.execute(avg_eval_query)
                result = cursor.fetchall()
                try:
                    for elem in result:
                        avg_eval[elem[0]] = {
                            "token_level_eval": {
                                "precision": elem[1]/elem[4] if elem[4] > 0 else 0.0,
                                "recall": elem[2]/elem[4] if elem[4] > 0 else 0.0,
                                "f1": elem[3]/elem[4] if elem[4] > 0 else 0.0
                            }
                            }
                except:
                    print("Tabella eva vuota, " \
                    "esegui una full_gs_eval per generare delle valutazioni " \
                    "o farne un aggiornamento")

                #avg_eval_judge (aspetta per Ollama)
                cursor.execute(avg_eval_judge_query)
                result = cursor.fetchall()
                for elem in result:
                    avg_eval_judge[elem[0]] = {
                        "judge_score": elem[1]/elem[2] if elem[2] > 0 else 0.0
                        }
                    
    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

    return DBStatsResponse(
        web_resources=web_resources,
        gold_standard=gold_standard,
        avg_eval=avg_eval,
        avg_eval_judge=avg_eval_judge
    )
        

@app.get("/db_schema")
def get_db_schema() -> DBSchemaResponse:
    try:
        """
        Legge lo schema reale del DB da information_schema e lo restituisce
        nel formato richiesto.
        """
        query = """
            SELECT
                c.TABLE_NAME,
                c.COLUMN_NAME,
                c.COLUMN_TYPE,
                c.COLUMN_KEY,
                k.REFERENCED_TABLE_NAME,
                k.REFERENCED_COLUMN_NAME
            FROM information_schema.COLUMNS c
            LEFT JOIN information_schema.KEY_COLUMN_USAGE k
                ON  k.TABLE_SCHEMA          = c.TABLE_SCHEMA
                AND k.TABLE_NAME            = c.TABLE_NAME
                AND k.COLUMN_NAME           = c.COLUMN_NAME
                AND k.REFERENCED_TABLE_NAME IS NOT NULL
            WHERE c.TABLE_SCHEMA = %s
            ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION
        """

        try:
            with get_db_conn() as conn:

                cursor = conn.cursor()
                cursor.execute(query, ("db_progetto",))
                rows = cursor.fetchall()
                cursor.close()

                schema: dict = {}

                for table, column, col_type, col_key, ref_table, ref_col in rows:
                    if table not in schema:
                        schema[table] = {}

                    parts = [col_type]
                    if col_key == "PRI":
                        parts.append("PK")
                    if ref_table:                                    # è una FK
                        parts.append(f"FK({ref_table}.{ref_col})")

                    schema[table][column] = ", ".join(parts)

                return DBSchemaResponse(
                    **schema
                )
            
        except mariadb.Error as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/status")
def get_status() -> StatusResponse:
    """
    Controlla la raggiungibilità di backend, database e ollama.
    """

    try:
        with get_db_conn() as conn:

            backend_status = "ok"

            database_status = "error"
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                database_status = "ok"
            except Exception:
                pass

            ollama_status = "error"
            try:
                import requests
                r = requests.get("http://ollama:11434", timeout=3)
                if r.status_code < 500:
                    ollama_status = "ok"
            except Exception:
                pass

    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

    return StatusResponse(
        backend=backend_status,
        database=database_status,
        ollama=ollama_status
    )