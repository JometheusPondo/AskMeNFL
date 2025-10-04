from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generateSQL(self, query: str) -> str:
        pass

    @abstractmethod
    def getProviderName(self) -> str:
        pass






# Separate function to utilize any LLM service
def anyProvider(provider: LLMProvider, query: str):
    sql = provider.generateSQL(query)
    print(f"Using {provider.getProviderName()}")
    return sql