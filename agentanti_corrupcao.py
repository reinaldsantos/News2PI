"""
agentanti_corrupcao.py
Agente autónomo que envia notícias para o Blogue Corrupção.
Compatível com o sistema Agentic News Hub EPF 2.º Ano.
"""

from typing import List, Optional

import requests

SERVER_URL = "http://localhost:8080"


class AgenteCorrupcao:
    def __init__(self, nome_agente: str, server_url: str = SERVER_URL):
        self.nome = nome_agente
        self.server_url = server_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def enviar_noticia(
        self,
        titulo: str,
        conteudo: str,
        categoria: str = "Corrupção",
        prioridade: str = "normal",
        tags: Optional[List[str]] = None,
        url_imagem: str = "",
    ) -> dict:
        """Publica uma notícia no servidor central."""
        payload = {
            "title": titulo,
            "content": conteudo,
            "category": categoria,
            "source": self.nome,
            "author": self.nome,
            "priority": prioridade,
            "tags": tags or [],
            "image_url": url_imagem,
        }
        response = self.session.post(
            f"{self.server_url}/api/news",
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        resultado = response.json()
        if resultado.get("success"):
            print(f"[{self.nome}] Notícia publicada: ID {resultado['id']}")
        return resultado

    def listar_noticias(self, categoria: str = "", pagina: int = 1) -> list:
        """Obtém notícias do servidor."""
        params = {"page": pagina, "per_page": 20}
        if categoria:
            params["category"] = categoria
        response = self.session.get(
            f"{self.server_url}/api/news",
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("items", [])

    def estatisticas(self) -> dict:
        """Retorna estatísticas do servidor."""
        response = self.session.get(f"{self.server_url}/api/stats", timeout=10)
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    agente = AgenteCorrupcao("Agente_EPF_Alpha")

    agente.enviar_noticia(
        titulo="Nova investigação ao Ministério das Obras Públicas por contratos irregulares",
        conteudo=(
            "O Ministério Público abriu hoje uma investigação formal após receber "
            "denúncias de irregularidades em contratos de obra pública avaliados em "
            "mais de 80 milhões de euros. Segundo fontes próximas do processo, os "
            "contratos foram adjudicados sem concurso público e a preços acima do "
            "mercado. A investigação envolve três empresas privadas e dois funcionários "
            "de alto escalão do ministério."
        ),
        categoria="Corrupção",
        prioridade="breaking",
        tags=["ministério", "obras-públicas", "MP", "contratos", "investigação"],
    )

    print("\nÚltimas notícias de Corrupção:")
    for noticia in agente.listar_noticias(categoria="Corrupção"):
        print(f"  [{noticia['priority'].upper()}] {noticia['title']} - {noticia['source']}")

    stats = agente.estatisticas()
    print(
        f"\nEstatísticas: {stats['total_articles']} artigos | "
        f"{stats['breaking_news']} urgentes | {stats['active_agents']} agentes"
    )
