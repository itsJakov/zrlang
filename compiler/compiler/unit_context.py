# Compilation Unit Context
class UnitContext:
    _strings: dict[str, int] = {} # string -> offset
    string_data: str = ""
    _offset: int = 0

    def string_offset(self, string: str) -> int:
        existing = self._strings.get(string)
        if existing is not None:
            return existing

        offset = self._offset

        self.string_data += string + "\\0"
        self._offset += len(string) + 1  # +1 for the null terminator

        return offset

    def string_sym(self, string: str) -> str:
        offset = self.string_offset(string)
        return f"$strings+{offset}"