# маппинг без дикт.

from collections.abc import MutableMapping


class SpisokPar(MutableMapping):
    #пары лежат в обычном списке

    def __init__(self, entries=None):
        self.entries = entries or []

    @property
    def entries(self):
        return list(self._entries)

    @entries.setter
    def entries(self, value):
        self._entries = []
        for key, item in value:
            self[key] = item

    def __getitem__(self, key):
        for saved_key, value in self._entries:
            if saved_key == key:
                return value
        raise KeyError(key)

    def __setitem__(self, key, value):
        for index, entry in enumerate(self._entries):
            if entry[0] == key:
                self._entries[index] = (key, value)
                return
        self._entries.append((key, value))

    def __delitem__(self, key):
        for index, entry in enumerate(self._entries):
            if entry[0] == key:
                del self._entries[index]
                return
        raise KeyError(key)

    def __iter__(self):
        for key, _ in self._entries:
            yield key

    def __len__(self):
        return len(self._entries)

    def __contains__(self, key):
        for saved_key, _ in self._entries:
            if saved_key == key:
                return True
        return False

    def __eq__(self, other):
        if not isinstance(other, SpisokPar):
            return NotImplemented
        return self._entries == other._entries

    def __repr__(self):
        return f"SpisokPar({self._entries!r})"

    def __str__(self):
        return ", ".join(str(key) for key, _ in self._entries)

    def __bool__(self):
        return bool(self._entries)
