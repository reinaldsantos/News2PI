# 🤖 Agentic Newsroom: Framework de Micro-Agentes com IA

Este repositório contém a infraestrutura base para o projeto de **Programação Avançada em Python** (50 Horas). O objetivo é construir um portal de notícias inteligente e colaborativo, onde cada aluno desenvolve um agente autónomo capaz de extrair, processar e sumarizar informações da web.

---

## 🎯 Objetivo do Projeto
Desenvolver um sistema agêntico que utilize:
* **POO Avançada**: Herança e Classes Abstratas.
* **Programação Assíncrona**: Uso de `asyncio` e `httpx` para alta performance.
* **Inteligência Artificial**: Integração com modelos do **Hugging Face** (`transformers`).
* **Web Scraping/APIs**: Captura de dados em tempo real.

---

## 🛠️ Estrutura do Repositório

```text
.
├── main.py                # Orquestrador Central (Professor)
├── news_framework.py      # Classe Base e Contrato (Não alterar)
├── requirements.txt       # Dependências do projeto
└── agents/                # 📂 PASTA DOS ALUNOS
    └── seu_nome_agent.py  # Onde deves criar o teu agente



Como Começar (Instalação)
Clonar o Repositório:

Bash
git clone [URL_DO_TEU_REPOSITORIO]
cd agent-news-project
Criar e Ativar Ambiente Virtual:

Bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
Instalar Dependências:

Bash
pip install -r requirements.txt
Correr o Servidor:

Bash
python main.py
Acede a http://127.0.0.1:8080 no teu navegador.

📝 Guia de Implementação (Para o Aluno)
Todos os agentes devem ser criados dentro da pasta /agents e devem herdar de BaseNewsAgent.

Exemplo de Estrutura:
Cria um ficheiro chamado agents/meu_tema_agent.py:

Python
from news_framework import BaseNewsAgent
import httpx
from transformers import pipeline

class MeuAgente(BaseNewsAgent):
    async def collect_data(self):
        # 1. Escolher uma fonte (API ou Site)
        # 2. Extrair Title, Content e URL
        return {
            "title": "Título da Notícia",
            "content": "Conteúdo bruto para ser processado...",
            "url": "[https://fonte-da-noticia.com](https://fonte-da-noticia.com)"
        }

    async def process_with_ai(self, data):
        # 1. Escolher um modelo no Hugging Face (ex: summarization)
        # 2. Gerar o resumo e guardar em data["summary"]
        summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
        resumo = summarizer(data["content"], max_length=50, min_length=10)
        
        data["summary"] = resumo[0]['summary_text']
        self.metadata["confidence"] = 0.9  # Define a confiança na extração
        return data
📊 Critérios de Avaliação
Robustez: O agente trata erros de conexão?

Assincronismo: Uso correto de await e httpx.

Qualidade da IA: O resumo faz sentido? O modelo é adequado?

Clean Code: Código organizado e seguindo as normas da PEP 8.

💡 Notas Importantes
Na primeira execução, o download dos modelos de IA pode demorar alguns minutos.

Garante que o teu ficheiro termina em _agent.py para ser detetado automaticamente pelo servidor.

Projeto desenvolvido para a UC de Programação Avançada - 2.º Ano.