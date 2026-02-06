import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend, StoreBackend, CompositeBackend, StateBackend
from langgraph.store.memory import InMemoryStore

load_dotenv()

class AgentFactory:
    """
    Factory class to create deep agents with various backends.
    """

    def __init__(self, model: ChatOpenAI) -> None:
        self.model = model

    def create_agent(self, backend: str, store: InMemoryStore = None) -> 'DeepAgent':
        """
        Create a deep agent with the specified backend.
        
        :param backend: The backend type to use.
        :param store: Optional store for persistent data.
        :return: An instance of the deep agent.
        """
        try:
            if backend == 'filesystem':
                return create_deep_agent(model=self.model, backend=FilesystemBackend(root_dir='./', virtual_mode=True))
            elif backend == 'store':
                return create_deep_agent(model=self.model, backend=StoreBackend(), store=store)
            elif backend == 'composite':
                return create_deep_agent(model=self.model, backend=CompositeBackend(default=StateBackend(), routes={}))
            else:
                raise ValueError(f'Unknown backend type: {backend}')
        except Exception as e:
            print(f'Error creating agent: {e}')
            raise

class BackendManager:
    """
    Manages different backends for the agents.
    """

    def __init__(self) -> None:
        self.store = InMemoryStore()

    def setup_filesystem_backend(self) -> FilesystemBackend:
        """
        Set up a filesystem backend.
        
        :return: An instance of FilesystemBackend.
        """
        try:
            os.makedirs('./agent_files', exist_ok=True)
            return FilesystemBackend(root_dir='./agent_files', virtual_mode=True)
        except Exception as e:
            print(f'Error setting up filesystem backend: {e}')
            raise

    def setup_store_backend(self) -> StoreBackend:
        """
        Set up a store backend.
        
        :return: An instance of StoreBackend.
        """
        return StoreBackend()

    def setup_composite_backend(self) -> CompositeBackend:
        """
        Set up a composite backend.
        
        :return: An instance of CompositeBackend.
        """
        return CompositeBackend(default=StateBackend(), routes={})

# Example usage
if __name__ == '__main__':
    model = ChatOpenAI(model='gpt-4o-mini', temperature=0)
    factory = AgentFactory(model=model)
    backend_manager = BackendManager()
    agent = factory.create_agent('filesystem')
    # Further agent usage can be implemented here.