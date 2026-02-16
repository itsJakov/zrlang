from typing import Optional

from .symbols import Symbol
from .types import Type


class Scope:
    def __init__(self, parent: Optional['Scope'] = None):
        self.parent: Optional[Scope] = parent
        self.symbols: dict[str, Symbol] = {}
        self.return_type: Optional[Type] = None

    # Returns False if symbol already exists in this scope
    def define(self, symbol: Symbol) -> bool:
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def lookup(self, name: str) -> Optional[Symbol]:
        symbol = self.symbols.get(name)
        if symbol is not None:
            return symbol
        if self.parent is not None:
            return self.parent.lookup(name)
        return None