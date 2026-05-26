# -*- coding: utf-8 -*-

import asyncio
import json
import uuid
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI()

# Definição robusta de caminhos para a Vercel
BASE_DIR = Path(__file__).resolve().parent
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

API_TOKEN = "epf2026_secret"
CATEGORIES = [
    "Corrupção",
    "Política",
    "Justiça",
    "Economia",
    "Internacional",
    "Sociedade",
    "Investigação",
]

database: List[Dict[str, Any]] = []

class NewsEntry(BaseModel):
    agent_name: str
    topic: str
    title: str
    summary: str
    url: str
    confidence: float = 0.0

def read_field(data: dict, *names: str, default=None):
    for name in names:
        value = data.get(name)
        if value is not None:
            return value
    return default

def parse_confidence(value: Any) -> float:
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0

def normalize_publish_payload(data: dict) -> NewsEntry:
    return NewsEntry(
        agent_name=read_field(data, "agent_name", "nome_do_agente", default="anonimo"),
        topic=read_field(data, "topic", "tópico", "topico", default="geral"),
        title=read_field(data, "title", "título", "titulo", default=""),
        summary=read_field(data, "summary", "resumo", "content", default=""),
        url=str(read_field(data, "url", default="")).strip(),
        confidence=parse_confidence(read_field(data, "confidence", "confiança", "confianca", default=0.0)),
    )

def entry_to_article(entry: NewsEntry) -> Dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "title": entry.title,
        "content": entry.summary,
        "category": entry.topic,
        "source": entry.agent_name,
        "author": entry.agent_name,
        "tags": [],
        "image_url": "",
        "priority": "normal",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "views": 0,
        "status": "published",
        "url": entry.url,
        "confidence": entry.confidence,
    }

def article_from_api_payload(data: dict) -> Dict[str, Any]:
    title = str(read_field(data, "title", "título", "titulo", default="")).strip()
    content = str(read_field(data, "content", "summary", "resumo", default="")).strip()
    category = str(read_field(data, "category", "topic", "tópico", "topico", default="Geral")).strip() or "Geral"
    source = str(read_field(data, "source", "agent_name", "nome_do_agente", default="Anónimo")).strip() or "Anónimo"
    author = str(read_field(data, "author", "autor", default=source)).strip() or source
    tags = read_field(data, "tags", default=[])

    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "category": category,
        "source": source,
        "author": author,
        "tags": tags if isinstance(tags, list) else [],
        "image_url": str(read_field(data, "image_url", "url", default="")).strip(),
        "priority": str(read_field(data, "priority", default="normal")).strip() or "normal",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "views": 0,
        "status": "published",
    }

def seed_data():
    if database:
        return
    samples = [
        {
            "title": "Ministério da Saúde alvo de investigação por contratos suspeitos",
            "content": "O Ministério Público abriu uma investigação formal após denúncias de irregularidades em contratos de fornecimento de equipamentos médicos durante a pandemia.",
            "category": "Corrupção",
            "source": "Agente_EPF",
            "author": "Investigador Alpha",
            "tags": ["saúde", "contratos", "MP"],
            "priority": "breaking",
            "views": 234,
        },
        {
            "title": "Ex-autarca condenado por peculato agrava recurso no Supremo",
            "content": "O Tribunal da Relação de Lisboa confirmou a condenação do antigo presidente de câmara por desvio de fundos municipais.",
            "category": "Justiça",
            "source": "Tribunal Relação Lisboa",
            "author": "Redação",
            "tags": ["autarquia", "condenação"],
            "priority": "high",
            "views": 89,
        },
    ]
    now = datetime.utcnow().isoformat() + "Z"
    for item in samples:
        database.append({
            "id": str(uuid.uuid4()),
            "image_url": "",
            "timestamp": now,
            "status": "published",
            **item,
        })

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    try:
        seed_data()
        return templates.TemplateResponse("index.html", {"request": request, "categories": CATEGORIES})
    except Exception as e:
        return HTMLResponse(content=f"<h3>Erro ao carregar template index.html: {str(e)}</h3>", status_code=500)

@app.get("/submit", response_class=HTMLResponse)
def submit(request: Request):
    try:
        return templates.TemplateResponse("submit.html", {"request": request, "categories": CATEGORIES})
    except Exception as e:
        return HTMLResponse(content=f"<h3>Erro ao carregar template submit.html: {str(e)}</h3>", status_code=500)

@app.post("/publish")
async def publish_news(request: Request, x_token: Optional[str] = Header(None)):
    if x_token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token invalido")
    entry = normalize_publish_payload(await request.json())
    if not entry.title or not entry.summary or not entry.url:
        raise HTTPException(status_code=422, detail="title, summary e url sao obrigatorios")
    database.insert(0, entry_to_article(entry))
    return {"ok": True, "total": len(database)}

@app.get("/api/news")
def get_news(category: str = "", page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
    seed_data()
    items = list(database)
    if category and category != "Todas":
        items = [item for item in items if item.get("category") == category]
    items.sort(key=lambda item: item["timestamp"], reverse=True)
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "items": items[start:end],
        "total": len(items),
        "page": page,
        "per_page": per_page,
        "has_more": end < len(items),
    }

@app.post("/api/news")
async def post_news(request: Request):
    item = article_from_api_payload(await request.json())
    if not item["title"] or not item["content"]:
        raise HTTPException(status_code=400, detail="Titulo e conteudo sao obrigatorios")
    database.insert(0, item)
    return {"success": True, "id": item["id"]}

@app.get("/api/stats")
def stats():
    seed_data()
    return {
        "total_articles": len(database),
        "breaking_news": sum(1 for item in database if item.get("priority") == "breaking"),
        "active_agents": len({item.get("source") for item in database if item.get("source")}),
    }

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": f"Erro interno no worker Python da Vercel: {str(exc)}"})
