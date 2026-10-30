from typing import Protocol

class PokemonClient(Protocol):
    def get_name_by_id(self, pokemon_id: int) -> str:
        """Gets the name of a Pokemon by its ID"""
        ...
