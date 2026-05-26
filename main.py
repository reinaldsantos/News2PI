# -- coding: utf-8 --

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

API_TOKEN = "epf2026_secret"
CATEGORIES = ["Todas", "Corrupção", "Política", "Justiça", "Economia", "Internacional", "Sociedade", "Investigação"]

database: List[Dict[str, Any]] = []
subscribers: List[asyncio.Queue] = []


class NewsEntry(BaseModel):
    agent_name: str
    topic: str
    title: str
    summary: str
    url: str
    confidence: float = 0.0


def normalize_publish_payload(data: dict) -> NewsEntry:
    return NewsEntry(
        agent_name=str(data.get("agent_name", "anonimo")),
        topic=str(data.get("topic", "geral")),
        title=str(data.get("title", "")),
        summary=str(data.get("summary", "")),
        url=str(data.get("url", "")),
        confidence=float(str(data.get("confidence", 0)).replace(",", ".")),
    )


def entry_to_article(entry: NewsEntry) -> Dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "title": entry.title,
        "content": entry.summary,
        "category": entry.topic,
        "source": entry.agent_name,
        "author": entry.agent_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "views": 0,
        "url": entry.url,
    }


async def broadcast(event_type: str, item: Dict[str, Any]):
    for queue in subscribers[:]:
        try:
            queue.put_nowait(f"event: {event_type}\ndata: {json.dumps(item, ensure_ascii=False)}\n\n")
        except:
            subscribers.remove(queue)


def seed_data():
    if database:
        return
    database.append({
        "id": str(uuid.uuid4()),
        "title": "Bem-vindo ao News2PI",
        "content": "Portal de notícias ativo. Os agentes vão começar a enviar notícias em breve.",
        "category": "Sociedade",
        "source": "Sistema",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "views": 0,
    })


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    seed_data()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "categories": CATEGORIES,
        "articles": database
    })


@app.get("/submit", response_class=HTMLResponse)
def submit_form(request: Request):
    return templates.TemplateResponse("submit.html", {
        "request": request,
        "categories": CATEGORIES
    })


@app.post("/publish")
async def publish_news(request: Request, x_token: Optional[str] = Header(None)):
    if x_token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token invalido")
    
    entry = normalize_publish_payload(await request.json())
    if not entry.title or not entry.summary or not entry.url:
        raise HTTPException(status_code=422, detail="title, summary e url sao obrigatorios")
    
    article = entry_to_article(entry)
    database.insert(0, article)
    await broadcast("new_article", article)
    return {"ok": True, "total": len(database)}


@app.get("/api/news")
def get_news(category: str = ""):
    seed_data()
    items = database
    if category and category != "Todas":
        items = [item for item in items if item.get("category") == category]
    return {"items": items, "total": len(items)}


@app.get("/api/stats")
def stats():
    seed_data()
    return {"total_articles": len(database)}


@app.get("/api/stream")
async def stream():
    queue = asyncio.Queue()
    subscribers.append(queue)
    
    async def events():
        try:
            yield "event: connected\ndata: {}\n\n"
            while True:
                try:
                    yield await asyncio.wait_for(queue.get(), timeout=25)
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        finally:
            if queue in subscribers:
                subscribers.remove(queue)
    
    return StreamingResponse(events(), media_type="text/event-stream")
