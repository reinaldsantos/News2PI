from news_framework import BaseNewsAgent
import asyncio

class AgenteDemo(BaseNewsAgent):
    async def collect_data(self):
        # Simulamos uma espera de rede de 1 segundo
        await asyncio.sleep(1)
        return {
            "title": "Primeiro Agente Operacional",
            "content": "Este é um teste do sistema agêntico para o 2.º ano.",
            "url": "http://localhost:8000"
        }

    async def process_with_ai(self, data):
        # Simulamos o tempo de resposta de uma IA
        await asyncio.sleep(0.5)
        data["summary"] = "O sistema está configurado e pronto para receber os agentes dos alunos!"
        return data