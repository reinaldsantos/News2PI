# -*- coding: utf-8 -*-

import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI()

API_TOKEN = "epf2026_secret"
CATEGORIES = ["Corrupção", "Política", "Justiça", "Economia", "Internacional", "Sociedade", "Investigação"]
database: List[Dict[str, Any]] = []

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return """
    <html>
        <head><title>EPF News Hub - Ativo</title></head>
        <body style='font-family:sans-serif; text-align:center; padding-top:50px; background:#f4f6f9;'>
            <h1 style='color:#1e293b;'>🚀 EPF News Hub Backend está VIVO!</h1>
            <p style='color:#64748b;'>O servidor FastAPI na Vercel está a responder com sucesso absoluto.</p>
            <div style='background:white; padding:20px; display:inline-block; border-radius:8px; border:1px solid #e2e8f0;'>
                <strong>Próximo passo:</strong> O teu ficheiro <code>templates/index.html</code> tem um bug de sintaxe.<br>
                Verifica onde usas as categorias no HTML!
            </div>
        </body>
    </html>
    """

@app.get("/submit", response_class=HTMLResponse)
def submit(request: Request):
    return "<h3>Página de submissão (Modo de segurança ativo)</h3>"

@app.get("/api/news")
def get_news(category: str = "", page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
    items = list(database)
    return {"items": items, "total": len(items)}

@app.get("/api/stats")
def stats():
    return {"total_articles": len(database), "breaking_news": 0, "active_agents": 0}
