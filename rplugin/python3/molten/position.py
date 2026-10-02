from typing import List, Optional
from weakref import WeakSet

from pynvim import Nvim


class Position:
    bufno: int
    lineno: int
    colno: int

    def __init__(self, bufno: int, lineno: int, colno: int):
        self.bufno = bufno
        self.lineno = lineno
        self.colno = colno

    def __lt__(self, other: "Position") -> bool:
        return (self.lineno, self.colno) < (other.lineno, other.colno)

    def __le__(self, other: "Position") -> bool:
        return (self.lineno, self.colno) <= (other.lineno, other.colno)


class DynamicPosition(Position):
    nvim: Nvim
    extmark_namespace: int
    bufno: int

    extmark_id: Optional[int]

    # Every live position, so that the ones of an unloaded buffer can be found.
    _live: "WeakSet[DynamicPosition]" = WeakSet()

    def __init__(
        self,
        nvim: Nvim,
        extmark_namespace: int,
        bufno: int,
        lineno: int,
        colno: int,
        right_gravity: bool = False,
    ):
        self.nvim = nvim
        self.extmark_namespace = extmark_namespace

        self.bufno = bufno
        self.extmark_id = self.nvim.funcs.nvim_buf_set_extmark(
            self.bufno,
            extmark_namespace,
            lineno,
            colno,
            {"right_gravity": right_gravity, "strict": False},
        )
        DynamicPosition._live.add(self)

    def set_height(self, height: int) -> None:
        self.nvim.funcs.nvim_buf_set_extmark(
            self.bufno,
            self.extmark_namespace,
            self.lineno,
            self.colno,
            {"id": self.extmark_id, "virt_lines": [[("", "Normal")] for _ in range(height)]},
        )

    @classmethod
    def forget_buffer(cls, bufno: int) -> None:
        """The buffer was unloaded: its extmarks are gone and their ids will be
        reused when it is reloaded, so never delete by these ids again."""
        for position in list(cls._live):
            if position.bufno == bufno:
                position.extmark_id = None

    def __del__(self) -> None:
        if self.extmark_id is None:
            return
        # Note, this will not fail if the extmark doesn't exist
        self.nvim.funcs.nvim_buf_del_extmark(self.bufno, self.extmark_namespace, self.extmark_id)

    def __str__(self) -> str:
        return f"DynamicPosition({self.bufno}, {self.lineno}, {self.colno})"

    def __repr__(self) -> str:
        return f"DynamicPosition(bufno={self.bufno}, lineno={self.lineno}, colno={self.colno})"

    def _get_pos(self) -> List[int]:
        out = self.nvim.funcs.nvim_buf_get_extmark_by_id(
            self.bufno, self.extmark_namespace, self.extmark_id, {}
        )
        assert isinstance(out, list) and all(isinstance(x, int) for x in out)
        return out

    @property
    def lineno(self) -> int:  # type: ignore
        return self._get_pos()[0]

    @property
    def colno(self) -> int:  # type: ignore
        return self._get_pos()[1]
