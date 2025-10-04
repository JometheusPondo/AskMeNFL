from llm.provider import LLMProvider

class OllamaProvider(LLMProvider):
    def generateSQL(self, query: str) -> str:
        pass

    def getProviderName(self) -> str:
        return "Ollama GPT-OSS"