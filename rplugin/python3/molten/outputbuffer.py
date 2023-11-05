from typing import Any, List, Optional, Union

from pynvim import Nvim
from pynvim.api import Buffer, Window

from molten.images import Canvas
from molten.outputchunks import Output, OutputStatus
from molten.options import MoltenOptions
from molten.position import DynamicPosition, Position
from molten.utils import notify_error


class OutputBuffer:
    nvim: Nvim
    canvas: Canvas

    output: Output

    display_buf: Buffer
    display_win: Optional[Window]
    display_virt_lines: Optional[DynamicPosition]
    extmark_namespace: int

    options: MoltenOptions
    lua: Any

    def __init__(self, nvim: Nvim, canvas: Canvas, extmark_namespace: int, options: MoltenOptions):
        self.nvim = nvim
        self.canvas = canvas

        self.output = Output(None)

        self.display_buf = self.nvim.buffers[self.nvim.funcs.nvim_create_buf(False, True)]
        self.display_win = None
        self.display_virt_lines = None
        self.extmark_namespace = extmark_namespace

        self.options = options
        self.nvim.exec_lua("_ow = require('output_window')")
        self.lua = self.nvim.lua._ow

    def _buffer_to_window_lineno(self, lineno: int, bufno: int) -> int:
        return self.lua.calculate_window_position(bufno, lineno)

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

    def enter(self, anchor: Position) -> bool:
        entered = False
        if self.display_win is None:
            if self.options.enter_output_behavior == "open_then_enter":
                self.show(anchor)
            elif self.options.enter_output_behavior == "open_and_enter":
                self.show(anchor)
                entered = True
                self.nvim.funcs.nvim_set_current_win(self.display_win)
        elif self.options.enter_output_behavior != "no_open":
            entered = True
            self.nvim.funcs.nvim_set_current_win(self.display_win)
        if entered:
            if self.options.output_show_more:
                self.remove_window_footer()
            if self.options.output_win_hide_on_leave:
                return False
        return True

    def clear_interface(self) -> None:
        if self.display_win is not None:
            self.nvim.funcs.nvim_win_close(self.display_win, True)
            self.canvas.clear()
            self.display_win = None
        if self.display_virt_lines is not None:
            del self.display_virt_lines
            self.display_virt_lines = None

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
        win_row = self._buffer_to_window_lineno(anchor.lineno + 1, anchor.bufno)
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

        sign_col_width = 0
        text_off = self.nvim.funcs.getwininfo(win.handle)[0]["textoff"]
        if not self.options.output_win_cover_gutter:
            sign_col_width = text_off

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
            lines = []

        self.display_buf[0] = self._get_header_text(self.output)
        self.display_buf.append(lines)
        self.nvim.api.set_option_value(
            "filetype", "molten_output", {"buf": self.display_buf.handle}
        )

        # Open output window
        # assert self.display_window is None
        if win_row < win_height:
            border = self.options.output_win_border
            max_height = min(virtual_lines + lineno + 1, self.options.output_win_max_height)
            height = min(win_height - win_row, max_height)

            cropped = False
            if (
                height == win_height - win_row and max_height > height
            ):  # It didn't fit on the screen
                if self.options.output_crop_border and type(border) == list:
                    cropped = True
                    # Expand the border, so top and bottom can change independently
                    border = [border[i % len(border)] for i in range(8)]
                    border[5 % len(border)] = ""
                    height += 1

            if self.options.use_border_highlights:
                border = self.set_border_highlight(border)

            win_opts = {
                "relative": "win",
                "row": shape[1],
                "col": shape[0],
                "width": min(shape[2], self.options.output_win_max_width),
                "height": height,
                "border": border,
                "focusable": False,
            }
            if self.options.output_win_style:
                win_opts["style"] = self.options.output_win_style
            if (
                self.options.output_show_more
                and not cropped
                and height == self.options.output_win_max_height
            ):
                # the entire window size is shown, but the buffer still has more lines to render
                hidden_lines = len(self.display_buf) - height
                if self.options.output_win_cover_gutter and type(border) == list:
                    border_pad = border[5 % len(border)][0] * text_off
                    win_opts["footer"] = [
                        (border_pad, border[5 % len(border)][1]),
                        (f" 󰁅 {hidden_lines} More Lines ", self.options.hl.foot),
                    ]
                else:
                    win_opts["footer"] = [(f" 󰁅 {hidden_lines} More Lines ", self.options.hl.foot)]
                win_opts["footer_pos"] = "left"

            if self.display_win is None or not self.display_win.valid:  # open a new window
                self.display_win = self.nvim.api.open_win(
                    self.display_buf.number,
                    False,
                    win_opts,
                )
                hl = self.options.hl
                self.set_win_option("winhighlight", f"Normal:{hl.win},NormalNC:{hl.win_nc}")
                # TODO: Refactor once MoltenOutputWindowOpen autocommand is a thing.
                # note, the above setting will probably stay there, just so users can set highlights
                # with their other highlights
                self.set_win_option("wrap", self.options.wrap_output)
                self.set_win_option("cursorline", False)
                self.canvas.present()
            else:  # move the current window
                self.display_win.api.set_config(win_opts)

            if self.display_virt_lines is not None:
                del self.display_virt_lines

            if self.options.output_virt_lines:
                virt_lines_y = anchor.lineno
                virt_lines_height = max_height + border_h
                if self.options.virt_lines_off_by_1:
                    virt_lines_y += 1
                    virt_lines_height -= 1
                self.display_virt_lines = DynamicPosition(
                    self.nvim, self.extmark_namespace, anchor.bufno, virt_lines_y, 0
                )
                self.display_virt_lines.set_height(virt_lines_height)

    def set_border_highlight(self, border):
        hl = self.options.hl.border_norm
        if not self.output.success:
            hl = self.options.hl.border_fail
        elif self.output.status == OutputStatus.DONE:
            hl = self.options.hl.border_succ

        if type(border) == str:
            notify_error(
                self.nvim,
                "`use_border_highlights` only works when `output_win_border` is specified as a table",
            )
            return border

        for i in range(len(border)):
            match border[i]:
                case [str(_), *_]:
                    border[i][1] = hl
                case str(_):
                    border[i] = [border[i], hl]

        return border

    def remove_window_footer(self) -> None:
        if self.display_win is not None:
            self.display_win.api.set_config({"footer": ""})


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
