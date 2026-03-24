import importlib
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from news_framework import BaseNewsAgent
import asyncio

app = FastAPI(title="Agentic News Portal")

def discover_agents():
    agents = []
    # Garante que a pasta existe
    if not os.path.exists("./agents"):
        os.makedirs("./agents")
    
    for file in os.listdir("./agents"):
        if file.endswith(".py") and file != "__init__.py":
            module_name = f"agents.{file[:-3]}"
            try:
                # Recarrega o módulo para apanhar alterações dos alunos
                module = importlib.import_module(module_name)
                importlib.reload(module)
                for name, obj in vars(module).items():
                    if isinstance(obj, type) and issubclass(obj, BaseNewsAgent) and obj is not BaseNewsAgent:
                        agents.append(obj(agent_name=name, topic=name.replace("Agent", "")))
            except Exception as e:
                print(f"Erro ao carregar agente {file}: {e}")
    return agents

@app.get("/", response_class=HTMLResponse)
async def get_blog():
    agents = discover_agents()
    tasks = [agent.run() for agent in agents]
    results = await asyncio.gather(*tasks)

    # Construção manual de um HTML simples e bonito
    html_content = """
    <html>
        <head>
            <title>AI Newsroom - EPF</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
            <style>
                body { max-width: 900px; margin: auto; padding: 20px; }
                .card { border: 1px solid #444; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                .meta { font-size: 0.8em; color: #888; }
                .error { border-color: #ff4444; opacity: 0.7; }
                .tag { background: #005a9e; padding: 2px 8px; border-radius: 4px; font-size: 0.7em; }
            </style>
        </head>
        <body>
            <h1>🤖 Agentic Newsroom <small>EPF 2º Ano</small></h1>
            <hr>
            <div class="feed">
    """

    for res in results:
        if "error" in res:
            html_content += f"""
            <div class="card error">
                <h3>⚠️ Agente: {res['agent']}</h3>
                <p>Erro: {res['error']}</p>
            </div>
            """
        else:
            data = res['data']
            html_content += f"""
            <div class="card">
                <span class="tag">{res['topic']}</span>
                <h2>{data['title']}</h2>
                <p>{data.get('summary', 'Sem resumo disponível.')}</p>
                <div class="meta">
                    Extraído por: <strong>{res['agent']}</strong> | 
                    Confiança: {res['metadata'].get('confidence', 'N/A')} |
                    <a href="{data['url']}" target="_blank">Ver Fonte Original</a>
                </div>
            </div>
            """

    html_content += "</div></body></html>"
    return html_content

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)