from functools import total_ordering
from typing import List, Union

from pynvim import Nvim
from molten.position import DynamicPosition, Position


@total_ordering
class CodeCell:
    nvim: Nvim
    begin: Union[Position, DynamicPosition]
    end: Union[Position, DynamicPosition]
    bufno: int

    def __init__(
        self,
        nvim: Nvim,
        begin: Union[Position, DynamicPosition],
        end: Union[Position, DynamicPosition],
    ):
        self.nvim = nvim
        self.begin = begin
        self.end = end
        assert self.begin.bufno == self.end.bufno
        self.bufno = self.begin.bufno

    def __contains__(self, pos: Union[Position, DynamicPosition]) -> bool:
        return self.bufno == pos.bufno and self.begin <= pos and pos < self.end

    def __lt__(self, other: "CodeCell") -> bool:
        return self.begin < other.begin

    def __gt__(self, other: "CodeCell") -> bool:
        return self.begin > other.begin

    def overlaps(self, other: "CodeCell") -> bool:
        return self.bufno == other.bufno and self.begin < other.end and other.begin < self.end

    def __str__(self) -> str:
        return f"CodeCell({self.begin}, {self.end})"

    def __repr__(self) -> str:
        return f"CodeCell(begin={self.begin}, end={self.end})"

    def clear_interface(self, highlight_namespace):
        """Clear the highlight of the code cell"""
        self.nvim.funcs.nvim_buf_clear_namespace(
            self.bufno,
            highlight_namespace,
            self.begin.lineno,
            self.end.lineno + 1,
        )

    def empty(self) -> bool:
        return self.end <= self.begin

    def get_text(self, nvim: Nvim) -> str:
        assert self.begin.bufno == self.end.bufno

        lines: List[str] = nvim.funcs.nvim_buf_get_lines(
            self.bufno, self.begin.lineno, self.end.lineno + 1, False
        )

        if len(lines) == 0:
            return "" # apparently this can happen...
        if len(lines) == 1:
            return lines[0][self.begin.colno : self.end.colno]
        else:
            return "\n".join(
                [lines[0][self.begin.colno :]] + lines[1:-1] + [lines[-1][: self.end.colno]]
            )
