from typing import Dict, List, Tuple
from pynvim import Nvim

from pynvim.api import Buffer
from molten.code_cell import CodeCell
from molten.outputchunks import Output
from molten.utils import notify_error

# TODO: what do I want this to look like...

# general ideas:
# use folding to show only the first line of code + a few lines of output or an image

# option 1:
# Floating window below the current cell that shows history inside (enter the window and scroll
# through) This would only contain history for that one cell

# option 2:
# A split that shows all of the history of the entire kernel so far


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
                return { cell : self.histories[cell] }
            case "all":
                return self.histories

    def create_cell_history_buffer(self, cell: CodeCell, kernel) -> Buffer | None:
        if cell not in self.histories:
            notify_error(self.nvim, "Couldn't find code cell history, please try again")
            return
        self.buf = self.nvim.buffers[self.nvim.funcs.nvim_create_buf(False, True)]

        lines = []
        lang = kernel.runtime.kernel_manager.kernel_spec.language  # type: ignore

        for code, output in self.histories[cell]:
            # add the code in a markdown cell with the appropriate language
            lines.append(f"```{lang}")
            lines.extend(code.split("\n"))
            lines.append(f"```")

            # add output
            for chunk in output.chunks:
                output_text, _ = chunk.place(
                    self.buf,
                    kernel.options,
                    0,
                    len(lines) - 1,
                    # NOTE: it doesn't really matter what we pass for shape, the width is the only
                    # value used, and it's not going to matter
                    (0, 0, 100, 0),
                    kernel.canvas,
                    False,
                )
                lines.extend(output_text.split("\n"))

        self.buf[0] = lines[0]
        self.buf.append(lines[1:])
        self.nvim.api.set_option_value("filetype", "markdown.molten_history", {"buf": self.buf.handle})
        self.nvim.api.set_option_value("buflisted", False, {"buf": self.buf.handle})

        return self.buf

    def close(self):
        """ close an open history buffer """
        if self.buf and self.buf.api.is_valid():
            self.buf.api.delete({})

    def open_split(self, cell: CodeCell, kernel):
        self.close()

        self.create_cell_history_buffer(cell, kernel)

        if self.buf is None:
            return

        self.nvim.command("90vs")
        self.nvim.current.window.api.set_buf(self.buf)
        self.nvim.current.window.api.set_cursor((len(self.buf), 0))
        kernel.canvas.present()
