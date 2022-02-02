import os
from typing import Any


class BaseCache:
    def __init__(self, folder: str):
        self.folder = folder
    
    def save_state(self, state_name: str, state: Any):
        raise NotImplementedError()
    
    def load_state(self, state_name: str) -> Any:
        raise NotImplementedError()
    
    def is_state(self, filename: str) -> bool:
        try:
            self.load_state(filename)
            return True
        except:
            return False
    
    def _list_state_names(self) -> list[str]:
        return [
            filename for filename in os.listdir(self.folder)
            if self.is_state(filename)
        ]

    def contains(self, state_name: str) -> bool:
        return state_name in self._list_state_names()
    
    def contains_multiple(self, state_names: list[str]) -> list[bool]:
        cached_state_names = set(self._list_state_names())
        return [state_name in cached_state_names for state_name in state_names]

    def aggregate_states(self, states: list[Any]) -> Any:
        return states
    
    def load(self):
        states = [
            self.load_state(state_name)
            for state_name in self._list_state_names()
        ]

        return self.aggregate_states(states)
