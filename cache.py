import json
import os
from typing import Any

from base import Diploma


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


class DiplomaListCache(BaseCache):
    def _diploma_to_json(self, diploma: Diploma) -> dict:
        return {
            "title": diploma.title,
            "educational_programme": diploma.educational_programme,
            "year": diploma.year,
            "abstract": diploma.abstract,
            "level": diploma.level,
            "faculty": diploma.faculty
        }
    
    def _json_to_diploma(self, diploma_json: dict) -> Diploma:
        return Diploma(
            title=diploma_json["title"],
            educational_programme=diploma_json["educational_programme"],
            year=diploma_json["year"],
            abstract=diploma_json["abstract"],
            level=diploma_json["level"],
            faculty=diploma_json["faculty"]
        )
    
    def save_state(self, state_name: str, state: list[Diploma]):
        json_data = [self._diploma_to_json(diploma) for diploma in state]
        with open(os.path.join(self.folder, state_name), "w+") as f:
            json.dump(json_data, f)
    
    def load_state(self, state_name: str) -> list[Diploma]:
        with open(os.path.join(self.folder, state_name)) as f:
            json_data = json.load(f)
        
        return [self._json_to_diploma(diploma_json) for diploma_json in json_data]
    
    def aggregate_states(self, states: list[list[Diploma]]) -> list[dict]:
        result = []
        for diploma_list in states:
            for diploma in diploma_list:
                result.append(self._diploma_to_json(diploma))
        return result
