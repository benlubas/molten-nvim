import bisect
class SortedDict(dict):
    """A dictionary that keeps track of keys in sorted order.
    """

    sorted_keys: list

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sorted_keys = sorted(super().keys())

    def __setitem__(self, __key, __value) -> None:
        if __key not in self:
            bisect.insort_left(self.sorted_keys, __key)
        return super().__setitem__(__key, __value)

    def __delitem__(self, __key) -> None:
        self.sorted_keys.remove(__key)
        return super().__delitem__(__key)

    def __iter__(self):
        return iter(self.sorted_keys)

    # TODO: do the values return in sorted order?
    def values(self):
        return super().values()

    def keys(self):
        return self.sorted_keys

    def items(self):
        return [(key, self[key]) for key in self.sorted_keys]
