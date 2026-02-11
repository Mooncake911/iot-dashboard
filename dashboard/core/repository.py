from abc import ABC, abstractmethod
from typing import List, Dict, Any


class Repository(ABC):
    @abstractmethod
    def fetch_data(self, limit: int) -> List[Dict[str, Any]]:
        """Fetch data from the repository."""
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Возвращает строку с описанием источника данных (напр. 'DB.Collection')"""
        pass
