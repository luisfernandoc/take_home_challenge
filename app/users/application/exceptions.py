class PokemonNotFoundError(Exception):
    """The id does not match with an excisting Pokemon"""


class PokemonProviderUnavailableError(Exception):
    """It was not posible to get a valid response from the provider"""
