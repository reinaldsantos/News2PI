# -*- coding: utf-8 -*-

import httpx
import json
from bs4 import BeautifulSoup
from transformers import pipeline


class WorldClimateAgent:
    def __init__(self):
        self.agent_name = "WorldClimateAgent"
        self.topic = "world_climate"

        # IA (BART)
        self.summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn"
        )

    # ----------------------------
    # SCRAPING NOTÍCIAS
    # ----------------------------
    def collect_data(self):
        url = "https://www.bbc.com/news/world"
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            response = httpx.get(url, headers=headers, timeout=10)
        except Exception as e:
            print("Erro ao aceder ao site:", e)
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.find_all("a")

        for a in articles:
            text = a.get_text(strip=True)
            href = a.get("href")

            if (
                text
                and href
                and "/news/" in href
                and len(text) > 40
                and "LIVE" not in text
            ):
                if href.startswith("http"):
                    url_final = href
                else:
                    url_final = "https://www.bbc.com" + href

                return {
                    "title": text,
                    "url": url_final
                }

        return None

    # ----------------------------
    # IA (SUMARIZAÇÃO)
    # ----------------------------
    def process_with_ai(self, text):
        try:
            result = self.summarizer(
                text,
                max_length=30,
                min_length=10,
                do_sample=False
            )
            return result[0]["summary_text"]
        except Exception as e:
            print("Erro IA:", e)
            return text

    # ----------------------------
    # CLIMA SIMULADO
    # ----------------------------
    def get_weather(self):
        return "Clear sky, 22°C (simulated)"

    # ----------------------------
    # EXECUÇÃO PRINCIPAL
    # ----------------------------
    def run(self):
        print("AGENT A CORRER...")

        data = self.collect_data()

        if not data:
            print("Nenhuma notícia encontrada")
            return

        summary = self.process_with_ai(data["title"])
        weather = self.get_weather()

        # 🔥 PAYLOAD FINAL (COMPATÍVEL COM O BACKEND DO PROFESSOR)
        payload = {
            "title": data["title"],
            "summary": summary,              # ✔ obrigatório
            "url": data["url"],
            "topic": self.topic,
            "agent_name": self.agent_name    # ✔ obrigatório
        }

        print("\nRESULTADO FINAL:")
        print(payload)

        # ----------------------------
        # JSON LOCAL
        # ----------------------------
        with open("latest_news.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        print("\nJSON guardado em latest_news.json")

        # ----------------------------
        # ENVIO PARA API
        # ----------------------------
        try:
            response = httpx.post(
                "http://127.0.0.1:8080/publish",
                headers={
                    "x-token": "epf2026_secret"
                },
                json=payload,
                timeout=10
            )

            print("\nENVIADO PARA O BLOG:", response.status_code)

            if response.status_code != 200:
                print("ERRO BACKEND:")
                print(response.text)

        except Exception as e:
            print("Erro ao enviar para API:", e)


# ----------------------------
# EXECUÇÃO
# ----------------------------
if __name__ == "__main__":
    agent = WorldClimateAgent()
    agent.run()
