
from typing import List, Union

from pynvim import Nvim
from molten.position import DynamicPosition, Position


class CodeCell:
    begin: Union[Position, DynamicPosition]
    end: Union[Position, DynamicPosition]
    bufno: int

    def __init__(
        self,
        begin: Union[Position, DynamicPosition],
        end: Union[Position, DynamicPosition],
    ):
        self.begin = begin
        self.end = end
        assert self.begin.bufno == self.end.bufno

    def __contains__(self, pos: Union[Position, DynamicPosition]) -> bool:
        return self.begin.bufno == pos.bufno and self.begin <= pos and pos < self.end

    def get_text(self, nvim: Nvim) -> str:
        assert self.begin.bufno == self.end.bufno
        bufno = self.begin.bufno

        lines: List[str] = nvim.funcs.nvim_buf_get_lines(
            bufno, self.begin.lineno, self.end.lineno + 1, True
        )

        if len(lines) == 1:
            return lines[0][self.begin.colno : self.end.colno]
        else:
            return "\n".join(
                [lines[0][self.begin.colno :]] + lines[1:-1] + [lines[-1][: self.end.colno]]
            )
