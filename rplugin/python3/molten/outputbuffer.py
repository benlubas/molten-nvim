from typing import List, Optional, Union

from pynvim import Nvim
from pynvim.api import Buffer, Window

from molten.images import Canvas
from molten.outputchunks import Output, OutputStatus
from molten.options import MoltenOptions
from molten.utils import Position


class OutputBuffer:
    nvim: Nvim
    canvas: Canvas

    output: Output

    display_buf: Buffer
    display_win: Optional[Window]

    options: MoltenOptions

    def __init__(self, nvim: Nvim, canvas: Canvas, options: MoltenOptions):
        self.nvim = nvim
        self.canvas = canvas

        self.output = Output(None)

        self.display_buf = self.nvim.buffers[self.nvim.funcs.nvim_create_buf(False, True)]
        self.display_win = None

        self.options = options

    def _buffer_to_window_lineno(self, lineno: int) -> int:
        win_top = self.nvim.funcs.line("w0")
        assert isinstance(win_top, int)
        # handle folds
        # (code modified from image.nvim https://github.com/3rd/image.nvim/blob/16f54077ca91fa8c4d1239cc3c1b6663dd169092/lua/image/renderer.lua#L254)
        offset = 0
        if self.nvim.current.window.options["foldenable"]:
            i = win_top
            while i <= lineno:
                fold_start = self.nvim.funcs.foldclosed(i)
                fold_end = self.nvim.funcs.foldclosedend(i)
                if fold_start != -1 and fold_end != -1:
                    offset += fold_end - fold_start
                    i = fold_end + 1
                else:
                    i += 1

        return lineno - win_top + 1 - offset

    def _get_header_text(self, output: Output) -> str:
        if output.execution_count is None:
            execution_count = "..."
        else:
            execution_count = str(output.execution_count)

        if output.status == OutputStatus.HOLD:
            status = "* On Hold"
        elif output.status == OutputStatus.DONE:
            if output.success:
                status = "✓ Done"
            else:
                status = "✗ Failed"
        elif output.status == OutputStatus.RUNNING:
            status = "... Running"
        else:
            raise ValueError("bad output.status: %s" % output.status)

        if output.old:
            old = "[OLD] "
        else:
            old = ""

        return f"{old}Out[{execution_count}]: {status}"

    def enter(self, anchor: Position) -> None:
        if self.display_win is None:
            if self.options.enter_output_behavior == "open_then_enter":
                self.show(anchor)
                return
            elif self.options.enter_output_behavior == "open_and_enter":
                self.show(anchor)
                self.nvim.funcs.nvim_set_current_win(self.display_win)
                return
        elif self.options.enter_output_behavior != "no_open":
            self.nvim.funcs.nvim_set_current_win(self.display_win)

    def clear_interface(self) -> None:
        if self.display_win is not None:
            self.nvim.funcs.nvim_win_close(self.display_win, True)
            self.canvas.clear()
            self.display_win = None

    def set_win_option(self, option: str, value) -> None:
        if self.display_win:
            self.nvim.api.set_option_value(
                option,
                value,
                {"scope": "local", "win": self.display_win.handle},
            )

    def show(self, anchor: Position) -> None:
        win = self.nvim.current.window
        win_col = win.col
        win_row = self._buffer_to_window_lineno(anchor.lineno + 1)
        win_width = win.width
        win_height = win.height

        border_w, border_h = border_size(self.options.output_win_border)

        win_height -= border_h
        win_width -= border_w

        # Clear buffer:
        self.nvim.funcs.deletebufline(self.display_buf.number, 1, "$")
        # Add output chunks to buffer
        lines_str = ""
        lineno = 0
        # images are rendered with virtual lines by image.nvim
        virtual_lines = 0

        if self.options.output_win_cover_gutter:
            sign_col_width = 0
        else:
            sign_col_width = self.nvim.funcs.getwininfo(win.handle)[0]["textoff"]

        shape = (
            win_col + sign_col_width,
            win_row,
            win_width - sign_col_width,
            win_height,
        )
        if len(self.output.chunks) > 0:
            for chunk in self.output.chunks:
                chunktext, virt_lines = chunk.place(
                    self.display_buf.number,
                    self.options,
                    lineno,
                    shape,
                    self.canvas,
                )
                lines_str += chunktext
                lineno += chunktext.count("\n")
                virtual_lines += virt_lines

            lines = handle_progress_bars(lines_str)
            lineno = len(lines)
        else:
            lines = [lines_str]

        self.display_buf[0] = self._get_header_text(self.output)
        self.display_buf.append(lines)

        # Open output window
        # assert self.display_window is None
        if win_row < win_height:
            win_opts = {
                "relative": "win",
                "row": shape[1],
                "col": shape[0],
                "width": shape[2],
                "height": min(win_height - win_row, lineno + virtual_lines + 1),
                "border": self.options.output_win_border,
                "focusable": False,
            }
            if self.options.output_win_style:
                win_opts["style"] = self.options.output_win_style

            if self.display_win is None or not self.display_win.valid:  # open a new window
                self.display_win = self.nvim.api.open_win(
                    self.display_buf.number,
                    False,
                    win_opts,
                )
                hl = self.options.output_win_highlight
                self.set_win_option("winhighlight", f"Normal:{hl},NormalNC:{hl}")
                self.set_win_option("wrap", self.options.wrap_output)
                self.canvas.present()
            else:  # move the current window
                self.display_win.api.set_config(win_opts)


def handle_progress_bars(line_str: str) -> List[str]:
    """Progress bars like tqdm use special chars (`\\r`) and some trick to work
    This is fine for the terminal, but in a text editor we have so do some extra work
    """
    actual_lines = []
    lines = line_str.split("\n")
    for line in lines:
        parts = line.split("\r")
        last = parts[-1]
        if last != "":
            actual_lines.append(last)
            lines = actual_lines

    return actual_lines


def border_size(border: Union[str, List[str], List[List[str]]]):
    width, height = 0, 0
    match border:
        case list(b):
            height += border_char_size(1, b)
            height += border_char_size(5, b)
            width += border_char_size(7, b)
            width += border_char_size(3, b)
        case "rounded" | "single" | "double" | "solid":
            height += 2
            width += 2
        case "shadow":
            height += 1
            width += 1
    return width, height


def border_char_size(index: int, border: Union[List[str], List[List[str]]]):
    match border[index % len(border)]:
        case str(ch) | [str(ch), _]:
            return len(ch)
        case _:
            return 0
