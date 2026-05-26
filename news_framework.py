from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import datetime
import asyncio
import logging

# Configuração de Logs para os alunos verem o que corre mal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentFramework")

class BaseNewsAgent(ABC):
    def __init__(self, agent_name: str, topic: str):
        self.agent_name = agent_name
        self.topic = topic
        self.metadata: Dict[str, Any] = {
            "last_run": None,
            "status": "idle",
            "error_log": None,
            "execution_time": 0
        }

    @abstractmethod
    async def collect_data(self) -> Dict[str, Any]:
        """
        OBRIGATÓRIO: Deve retornar dict com 'title', 'content' e 'url'
        """
        pass

    @abstractmethod
    async def process_with_ai(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        OBRIGATÓRIO: Deve usar Hugging Face para adicionar a chave 'summary'
        """
        pass

    async def run(self) -> Dict[str, Any]:
        """Orquestrador do Agente com Timeouts e Gestão de Erros"""
        start_time = asyncio.get_event_loop().time()
        self.metadata["last_run"] = datetime.datetime.now().isoformat()
        
        try:
            logger.info(f"🚀 Agente {self.agent_name} iniciado...")
            
            # 1. Coleta de dados (Timeout de 15s para não travar o server)
            raw_data = await asyncio.wait_for(self.collect_data(), timeout=15.0)
            
            # Validação básica
            if not raw_data or 'content' not in raw_data:
                raise ValueError("Dados incompletos retornados pelo collect_data")

            # 2. Processamento IA
            enriched_data = await self.process_with_ai(raw_data)
            
            self.metadata["status"] = "success"
            self.metadata["execution_time"] = asyncio.get_event_loop().time() - start_time
            
            return {
                "agent": self.agent_name,
                "topic": self.topic,
                "data": enriched_data,
                "metadata": self.metadata
            }

        except Exception as e:
            logger.error(f"❌ Erro no Agente {self.agent_name}: {str(e)}")
            self.metadata["status"] = "error"
            self.metadata["error_log"] = str(e)
            return {
                "agent": self.agent_name,
                "topic": self.topic,
                "error": True,
                "metadata": self.metadata
            }