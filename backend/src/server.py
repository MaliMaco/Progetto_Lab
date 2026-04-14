from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

app = FastAPI(title="Backend API")

@app.get("/parse")
def parse():
    pass

@app.get("/domains")
def get_domains():
    pass

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