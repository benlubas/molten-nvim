from typing import Union, List

from pynvim import Nvim


class MoltenException(Exception):
    pass


def nvimui(func):  # type: ignore
    def inner(self, *args, **kwargs):  # type: ignore
        try:
            func(self, *args, **kwargs)
        except MoltenException as err:
            self.nvim.err_write("[Molten] " + str(err) + "\n")

    return inner


def _notify(nvim: Nvim, msg: str, log_level: str) -> None:
    lua = f"""
        vim.schedule_wrap(function()
            vim.notify("[Molten] {msg}", vim.log.levels.{log_level}, {{}})
        end)()
    """
    nvim.exec_lua(lua)


def notify_info(nvim: Nvim, msg: str) -> None:
    """Use the vim.notify API to display an info message."""
    _notify(nvim, msg, "INFO")


def notify_warn(nvim: Nvim, msg: str) -> None:
    """Use the vim.notify API to display a warning message."""
    _notify(nvim, msg, "WARN")


def notify_error(nvim: Nvim, msg: str) -> None:
    """Use the vim.notify API to display an error message."""
    _notify(nvim, msg, "ERROR")


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

    extmark_id: int

    def __init__(
        self,
        nvim: Nvim,
        extmark_namespace: int,
        bufno: int,
        lineno: int,
        colno: int,
    ):
        self.nvim = nvim
        self.extmark_namespace = extmark_namespace

        self.bufno = bufno
        self.extmark_id = self.nvim.funcs.nvim_buf_set_extmark(
            self.bufno, extmark_namespace, lineno, colno, {}
        )

    def __del__(self) -> None:
        self.nvim.funcs.nvim_buf_del_extmark(self.bufno, self.extmark_namespace, self.extmark_id)

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


class Span:
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
