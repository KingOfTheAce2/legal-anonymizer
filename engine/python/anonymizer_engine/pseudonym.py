from typing import Dict


class PseudonymMapper:
    def __init__(self) -> None:
        self._counters: Dict[str, int] = {}
        self._mapping: Dict[str, str] = {}

    def pseudonymise(self, entity_type: str, value: str) -> str:
        key = f"{entity_type}:{value}"

        if key in self._mapping:
            return self._mapping[key]

        count = self._counters.get(entity_type, 0) + 1
        self._counters[entity_type] = count

        token = f"{entity_type}_{count:03d}"
        self._mapping[key] = token
        return token
