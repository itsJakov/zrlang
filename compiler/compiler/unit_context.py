# Compilation Unit Context
class UnitContext:
    _strings: dict[str, str] = {} # string -> symbol
    string_data: str = ""
    _offset: int = 0

    def string_sym(self, string: str) -> str:
        existing = self._strings.get(string)
        if existing is not None:
            return existing

        sym = f"$strings+{self._offset}"
        self._strings[string] = sym

        self.string_data += string + "\\0"
        self._offset += len(string) + 1 # +1 for the null terminator

        return sym