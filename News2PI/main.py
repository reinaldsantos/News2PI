# -*- coding: utf-8 -*-

import asyncio
import json
import re
import uuid
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

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
subscribers: List[asyncio.Queue] = []


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


async def broadcast(event_type: str, item: Dict[str, Any]):
    if not subscribers:
        return

    message = f"event: {event_type}\ndata: {json.dumps(item, ensure_ascii=False)}\n\n"
    stale: List[asyncio.Queue] = []
    for queue in subscribers:
        try:
            queue.put_nowait(message)
        except asyncio.QueueFull:
            stale.append(queue)

    for queue in stale:
        if queue in subscribers:
            subscribers.remove(queue)


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


RSS_FEEDS = [
    "https://rss.cnn.com/rss/edition.rss",
    "https://sicnoticias.pt/rss",
]

CATEGORY_MAP = {
    "world": "Internacional",
    "politics": "Política",
    "business": "Economia",
    "technology": "Tecnologia",
    "sport": "Desporto",
    "sports": "Desporto",
    "justice": "Justiça",
    "health": "Sociedade",
    "investigation": "Investigação",
    "corrupcao": "Corrupção",
}


def slugify(value: str) -> str:
    value = str(value or "").strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"(^-|-$)", "", value)


def parse_rss_datetime(value: Optional[str]) -> str:
    if not value:
        return datetime.utcnow().isoformat() + "Z"
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc)
        return dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    except Exception:
        return datetime.utcnow().isoformat() + "Z"


def rss_item_exists(url: str, title: str) -> bool:
    normalized_url = (url or "").strip().lower()
    normalized_title = (title or "").strip().lower()
    return any(
        (item.get("url", "").strip().lower() == normalized_url)
        or (item.get("title", "").strip().lower() == normalized_title)
        for item in database
    )


def normalize_rss_category(value: str) -> str:
    if not value:
        return "Internacional"
    key = str(value).strip().lower()
    return CATEGORY_MAP.get(key, value.title())


def fetch_rss_feed(url: str) -> List[Dict[str, Any]]:
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            xml = response.read()

        root = ET.fromstring(xml)
        channel = root.find("channel")
        if channel is None:
            return []

        stories: List[Dict[str, Any]] = []
        for item in channel.findall("item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            description = (item.findtext("description") or "").strip()
            category = normalize_rss_category(item.findtext("category") or "")
            pub_date = parse_rss_datetime(item.findtext("pubDate") or "")
            image_url = ""
            enclosure = item.find("enclosure")
            if enclosure is not None and enclosure.attrib.get("type", "").startswith("image"):
                image_url = enclosure.attrib.get("url", "").strip()

            stories.append({
                "id": str(uuid.uuid4()),
                "title": title,
                "content": description,
                "category": category,
                "source": url,
                "author": "Importador RSS",
                "tags": [],
                "image_url": image_url,
                "priority": "normal",
                "timestamp": pub_date,
                "views": 0,
                "status": "published",
                "url": link,
            })
        return stories
    except Exception as exc:
        print(f"RSS import error for {url}: {exc}")
        return []


async def rss_import_worker():
    while True:
        seed_data()
        for feed in RSS_FEEDS:
            for story in fetch_rss_feed(feed):
                if rss_item_exists(story["url"], story["title"]):
                    continue
                database.insert(0, story)
                await broadcast("new_article", story)
        await asyncio.sleep(60 * 5)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(rss_import_worker())


@app.get("/noticias/{category}/{slug}", response_class=HTMLResponse)
def article_page(request: Request, category: str, slug: str):
    seed_data()
    return templates.TemplateResponse("index.html", {"request": request, "categories": CATEGORIES})


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    seed_data()
    return templates.TemplateResponse("index.html", {"request": request, "categories": CATEGORIES})


@app.get("/submit", response_class=HTMLResponse)
def submit(request: Request):
    return templates.TemplateResponse("submit.html", {"request": request, "categories": CATEGORIES})


@app.post("/publish")
async def publish_news(request: Request, x_token: Optional[str] = Header(None)):
    if x_token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token invalido")

    entry = normalize_publish_payload(await request.json())
    if not entry.title or not entry.summary or not entry.url:
        raise HTTPException(status_code=422, detail="title, summary e url sao obrigatorios")

    database.insert(0, entry_to_article(entry))
    await broadcast("new_article", database[0])
    return {"ok": True, "total": len(database)}


@app.get("/api/news")
def get_news(
    category: str = "",
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
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
    await broadcast("new_article", item)
    return {"success": True, "id": item["id"]}


@app.post("/api/news/{news_id}/view")
def increment_view(news_id: str):
    for item in database:
        if item["id"] == news_id:
            item["views"] = int(item.get("views", 0)) + 1
            return {"success": True, "views": item["views"]}
    raise HTTPException(status_code=404, detail="Not found")


@app.get("/api/stats")
def stats():
    seed_data()
    return {
        "total_articles": len(database),
        "breaking_news": sum(1 for item in database if item.get("priority") == "breaking"),
        "active_agents": len({item.get("source") for item in database if item.get("source")}),
    }


@app.get("/api/stream")
async def stream():
    queue: asyncio.Queue = asyncio.Queue(maxsize=20)
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
