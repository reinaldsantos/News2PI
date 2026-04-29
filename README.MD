# 🤖 Agentic Newsroom: Arquitetura de Micro-Agentes com IA

Este repositório contém o **Hub Central** para o projeto de **Programação Avançada em Python** (50 Horas). Nesta nova fase, o projeto funciona como um ecossistema de micro-serviços: cada aluno desenvolve o seu próprio Agente Independente que envia notícias processadas por IA para o servidor do professor via API.

---

## 🎯 Objetivo do Projeto
Desenvolver um sistema agêntico descentralizado que utilize:
* **APIs & Webhooks**: Comunicação entre servidores via métodos `POST`.
* **Segurança**: Uso de `Headers` e `Tokens` para autenticação de APIs.
* **Programação Assíncrona**: Uso de `asyncio` e `httpx` para não bloquear o servidor.
* **Inteligência Artificial**: Processamento de linguagem natural com **Hugging Face**.

---

## 🛠️ Estrutura do Ecossistema

1. **O Hub (Professor)**: Recebe e exibe as notícias de todos os alunos em tempo real.
2. **Os Agentes (Alunos)**: Cada aluno corre o seu próprio código que "caça" notícias e as "empurra" (Push) para o Hub.

---

## 🚀 Guia de Implementação (Para o Aluno)

### 1. Preparação do Ambiente
```bash
# Criar e ativar ambiente virtual
python -m venv venv
source venv/bin/activate  # Mac/Linux
.\venv\Scripts\activate   # Windows

# Instalar dependências
pip install fastapi uvicorn httpx beautifulsoup4 transformers torch
2. Criar o teu Agente (agents/seu_nome_agent.py)
O teu agente deve herdar da classe base e, no final, enviar os dados para o IP do professor.

Python
from news_framework import BaseNewsAgent
import httpx
import asyncio
from transformers import pipeline

class MeuAgente(BaseNewsAgent):
    async def collect_data(self):
        # TODO: Implementar scraping ou consumo de API aqui
        return {
            "title": "Título da Notícia",
            "content": "Conteúdo bruto extraído...",
            "url": "[https://fonte-original.com](https://fonte-original.com)"
        }

    async def process_with_ai(self, data):
        # TODO: Usar modelo do Hugging Face para resumir
        summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
        resumo = summarizer(data["content"], max_length=50, min_length=10)
        data["summary"] = resumo[0]['summary_text']
        return data

    async def run(self):
        # 1. Coletar e Processar
        raw_data = await self.collect_data()
        final_data = await self.process_with_ai(raw_data)
        
        # 2. Enviar para o Servidor Central (Hub do Professor)
        HUB_URL = "http://[IP_AQUI]:8080/publish"
        HEADERS = {"x-token": "epf2026_secret"}
        
        payload = {
            "agent_name": "Teu Nome",
            "topic": "Tecnologia",
            "title": final_data["title"],
            "summary": final_data["summary"],
            "url": final_data["url"],
            "confidence": 0.95
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(HUB_URL, json=payload, headers=HEADERS)
            print(f"Status do Envio: {response.json()}")

# Para testar o envio
if __name__ == "__main__":
    agente = MeuAgente(agent_name="Nome", topic="Geral")
    asyncio.run(agente.run())
🔐 Dados de Conexão ao Hub
Para que a tua notícia apareça no site da turma, deves usar:

Endpoint: http://[IP_AQUI]:8080/publish

Header de Autenticação: x-token: epf2026_secret

Método: POST

📊 Critérios de Avaliação
Conectividade: O agente consegue comunicar com o servidor central sem erros?

Tratamento de Exceções: O código sobrevive se o site de origem estiver em baixo?

Qualidade da IA: O resumo gerado é coerente com o título?

Autonomia: O agente corre de forma independente no teu computador.

💡 Dica: Podes usar o Uvicorn para criar um mini-servidor local para testares o teu agente antes de enviares a notícia final para o Hub do professor.

Projeto desenvolvido para a UC de Programação Avançada - 2.º Ano.

## Deploy no Vercel

O `requirements.txt` ficou apenas com as dependencias leves necessarias para o site/API:

```txt
fastapi
uvicorn
jinja2
```

As dependencias pesadas dos agentes com IA (`torch`, `transformers`, `beautifulsoup4`, `httpx`) ficam em `requirements-agents.txt`, para uso local. Isto evita que o Vercel ultrapasse o limite de bundle das funcoes Python.
