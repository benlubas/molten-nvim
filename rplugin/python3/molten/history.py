from typing import Dict, List, Tuple
from pynvim import Nvim

from pynvim.api import Buffer
from molten.code_cell import CodeCell
from molten.images import Canvas
from molten.options import MoltenOptions
from molten.outputchunks import Output
from molten.utils import notify_error


class HistoryBuffer:
    buf: Buffer | None
    canvas: Canvas
    histories: Dict[CodeCell, List[Tuple[str, Output]]]
    nvim: Nvim
    options: MoltenOptions

    def __init__(self, nvim: Nvim, options: MoltenOptions, canvas: Canvas, hl_ns: int) -> None:
        self.buf = None
        self.canvas = canvas
        self.histories = {}
        self.nvim = nvim
        self.options = options
        self.hl_ns = hl_ns

    def add(self, cell: CodeCell, code: str, output: Output):
        if cell in self.histories:
            self.histories[cell].append((code, output))
        else:
            self.histories[cell] = [(code, output)]

    def remove(self, cell: CodeCell):
        del self.histories[cell]

    def get_history(self, query: str, cell: CodeCell | None):
        match query:
            case "cell":
                if cell is None:
                    return
                return {cell: self.histories[cell]}
            case "all":
                return self.histories

    def create_cell_history_buffer(self, cell: CodeCell, language: str) -> Buffer | None:
        """Creates the history buffer for the given cell. If the buffer is open in a window, the
        buffer will refresh and scroll to the bottom"""

        if cell not in self.histories:
            notify_error(self.nvim, "Couldn't find code cell history, please try again")
            return

        if self.buf:
            self.canvas.clear(bufnr=self.buf.handle)
            self.buf.api.set_lines(0, -1, False, [])
        else:
            self.buf = self.nvim.buffers[self.nvim.funcs.nvim_create_buf(False, True)]

        lines = []
        output_ranges = []

        for code, output in self.histories[cell]:
            new_lines, output_range = self.generate_history_lines(
                language, code, output, len(lines)
            )
            lines.extend(new_lines)
            output_ranges.append(output_range)

        self.buf[0] = lines[0]
        self.buf.append(lines[1:])
        self.nvim.api.set_option_value(
            "filetype", "markdown.molten_history", {"buf": self.buf.handle}
        )
        self.nvim.api.set_option_value("buflisted", False, {"buf": self.buf.handle})
        for r in output_ranges:
            for line in range(r[0], r[1]):
                self.buf.api.add_highlight(self.hl_ns, "comment", line, 0, -1)

        win = self.nvim.funcs.bufwinid(self.buf.handle)
        if win != -1:
            self.nvim.api.win_set_cursor(win, (len(self.buf), 0))
            self.canvas.present()

        return self.buf

    def generate_history_lines(
        self, lang, code, output: Output, offset
    ) -> Tuple[List[str], Tuple[int, int]]:
        if self.buf is None:
            return [], (0, 0)
        lines = []
        # add the code in a markdown cell with the appropriate language
        lines.append("━" * 80)
        lines.append(f"```{lang}")
        lines.extend(code.split("\n"))
        lines.append(f"```")

        out_start = offset + len(lines)

        # add output
        lines.append(output.get_header_text())
        for chunk in output.chunks:
            output_text, _ = chunk.place(
                self.buf.handle,
                self.options,
                0,
                len(lines) - 1 + offset,
                # NOTE: it doesn't really matter what we pass for shape, the width is the only
                # value used, and it's only used to predict window height, which we don't use
                (0, 0, 100, 0),
                self.canvas,
                False,
            )
            lines.extend(output_text.rstrip("\n").split("\n"))

        return lines, (out_start, offset + len(lines))

    def update_history_buffer(self, cell: CodeCell, language: str) -> Buffer | None:
        if not self.buf or not self.buf.api.is_valid():
            return

        self.create_cell_history_buffer(cell, language)

    def clear(self):
        """close an open history buffer"""
        if self.buf:
            self.canvas.clear(bufnr=self.buf.handle)
            if self.buf.api.is_valid():
                self.buf.api.delete({})
        self.buf = None

    def open_split(self, cell: CodeCell, language: str):
        self.clear()

        self.create_cell_history_buffer(cell, language)

        if self.buf is None:
            return

        self.nvim.command("90vs")
        self.nvim.current.window.api.set_buf(self.buf)
        self.nvim.current.window.api.set_cursor((len(self.buf), 0))
        self.canvas.present()
