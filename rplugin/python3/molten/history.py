from typing import Dict, List, Tuple
from pynvim import Nvim

from pynvim.api import Buffer
from molten.code_cell import CodeCell
from molten.outputchunks import Output
from molten.utils import notify_error


class HistoryBuffer:
    histories: Dict[CodeCell, List[Tuple[str, Output]]]
    nvim: Nvim
    buf: Buffer | None

    def __init__(self, nvim: Nvim, histories) -> None:
        self.histories = histories
        self.nvim = nvim
        self.buf = None

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

    def create_cell_history_buffer(self, cell: CodeCell, kernel) -> Buffer | None:
        if cell not in self.histories:
            notify_error(self.nvim, "Couldn't find code cell history, please try again")
            return

        # self.nvim.out_write("called\n")
        if self.buf:
            self.buf.api.set_lines(0, -1, False, [])
        else:
            # self.nvim.out_write("new buffer\n")
            self.buf = self.nvim.buffers[self.nvim.funcs.nvim_create_buf(False, True)]
        # self.nvim.out_write("hi there\n")

        lines = []
        output_ranges = []
        lang = kernel.runtime.kernel_manager.kernel_spec.language  # type: ignore

        for code, output in self.histories[cell]:
            new_lines, output_range = self.generate_history_lines(
                lang, code, output, kernel, len(lines)
            )
            lines.extend(new_lines)
            output_ranges.append(output_range)

        self.buf[0] = lines[0]
        self.buf.append(lines[1:])
        self.nvim.api.set_option_value(
            "filetype", "markdown.molten_history", {"buf": self.buf.handle}
        )
        self.nvim.api.set_option_value("buflisted", False, {"buf": self.buf.handle})
        self.nvim.out_write(f"{output_ranges=}\n")
        for r in output_ranges:
            for line in range(r[0], r[1]):
                self.buf.api.add_highlight(kernel.highlight_namespace, "comment", line, 0, -1)

        return self.buf

    def generate_history_lines(
        self, lang, code, output: Output, kernel, offset
    ) -> Tuple[List[str], Tuple[int, int]]:
        if self.buf is None:
            return [], (0, 0)
        lines = []
        # add the code in a markdown cell with the appropriate language
        lines.append(f"```{lang}")
        lines.extend(code.split("\n"))
        lines.append(f"```")

        out_start = offset + len(lines)

        # add output
        lines.append(output.get_header_text())
        for chunk in output.chunks:
            output_text, _ = chunk.place(
                self.buf.handle,
                kernel.options,
                0,
                len(lines) - 1 + offset,
                # NOTE: it doesn't really matter what we pass for shape, the width is the only
                # value used, and it's only used to predict window height, which we don't use
                (0, 0, 100, 0),
                kernel.canvas,
                False,
            )
            lines.extend(output_text.rstrip("\n").split("\n"))

        lines.append("━" * 80)
        return lines, (out_start, offset + len(lines) - 1)

    def update_history_buffer(self, cell: CodeCell, kernel) -> Buffer | None:
        if not self.buf or not self.buf.api.is_valid():
            return

        self.create_cell_history_buffer(cell, kernel)

    def clear(self, kernel):
        """close an open history buffer"""
        if self.buf:
            kernel.canvas.clear(buf=self.buf.handle)
        if self.buf and self.buf.api.is_valid():
            self.buf.api.delete({})
        self.buf = None

    def open_split(self, cell: CodeCell, kernel):
        self.clear(kernel)

        self.create_cell_history_buffer(cell, kernel)

        if self.buf is None:
            return

        self.nvim.command("90vs")
        self.nvim.current.window.api.set_buf(self.buf)
        self.nvim.current.window.api.set_cursor((len(self.buf), 0))
        kernel.canvas.present()
