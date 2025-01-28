from datetime import datetime
from typing import Any, List, Optional, Tuple, Union

from pynvim import Nvim
from pynvim.api import Buffer, Window

from molten.images import Canvas
from molten.outputchunks import ImageOutputChunk, Output, OutputStatus
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
    virt_text_id: Optional[int]
    displayed_status: OutputStatus

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
        self.virt_text_id = None
        self.displayed_status = OutputStatus.HOLD

        self.options = options
        self.nvim.exec_lua("_ow = require('output_window')")
        self.lua = self.nvim.lua._ow

    def _buffer_to_window_lineno(self, lineno: int) -> int:
        return self.lua.calculate_window_position(lineno)

    def _get_header_text(self, output: Output) -> str:
        if output.execution_count is None:
            execution_count = "..."
        else:
            execution_count = str(output.execution_count)

        match output.status:
            case OutputStatus.HOLD:
                status = "* On Hold"
            case OutputStatus.DONE:
                if output.success:
                    status = "✓ Done"
                else:
                    status = "✗ Failed"
            case OutputStatus.RUNNING:
                status = "... Running"
            case OutputStatus.NEW:
                status = ""
            case _:
                raise ValueError("bad output.status: %s" % output.status)

        if output.old:
            old = "[OLD] "
        else:
            old = ""

        if not output.old and self.options.output_show_exec_time and output.start_time:
            start = output.start_time
            end = output.end_time if output.end_time is not None else datetime.now()
            diff = end - start

            days = diff.days
            hours = diff.seconds // 3600
            minutes = diff.seconds // 60
            seconds = diff.seconds - hours * 3600 - minutes * 60
            microseconds = diff.microseconds

            time = ""

            # Days
            if days:
                time += f"{days}d "
            if hours:
                time += f"{hours}hr "
            if minutes:
                time += f"{minutes}m "

            # Microseconds is an int, roundabout way to round to 2 digits
            time += f"{seconds}.{int(round(microseconds, -4) / 10000)}s"
        else:
            time = ""

        if output.status == OutputStatus.NEW:
            return f"Out[_]: Never Run"
        else:
            return f"{old}Out[{execution_count}]: {status} {time}".rstrip()

    def enter(self, anchor: Position) -> bool:
        entered = False
        if self.display_win is None:
            if self.options.enter_output_behavior == "open_then_enter":
                self.show_floating_win(anchor)
            elif self.options.enter_output_behavior == "open_and_enter":
                self.show_floating_win(anchor)
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

    def clear_float_win(self) -> None:
        if self.display_win is not None:
            if self.display_win.valid:
                self.nvim.funcs.nvim_win_close(self.display_win, True)
            self.display_win = None
            redraw = False
            for chunk in self.output.chunks:
                if isinstance(chunk, ImageOutputChunk) and chunk.img_identifier is not None:
                    self.canvas.remove_image(chunk.img_identifier)
                    redraw = True
            if redraw:
                self.canvas.present()
        if self.display_virt_lines is not None:
            del self.display_virt_lines
            self.display_virt_lines = None

    def clear_virt_output(self, bufnr: int) -> None:
        if self.virt_text_id is not None:
            self.nvim.funcs.nvim_buf_del_extmark(bufnr, self.extmark_namespace, self.virt_text_id)
        # clear the image too
        redraw = False
        for chunk in self.output.chunks:
            if isinstance(chunk, ImageOutputChunk) and chunk.img_identifier is not None:
                self.canvas.remove_image(chunk.img_identifier)
                redraw = True
        if redraw:
            self.canvas.present()

    def set_win_option(self, option: str, value) -> None:
        if self.display_win:
            self.nvim.api.set_option_value(
                option,
                value,
                {"scope": "local", "win": self.display_win.handle},
            )

    def build_output_text(self, shape, buf: int, virtual: bool) -> Tuple[List[str], int]:
        lineno = 1 # we add a status line at the top in the end
        lines_str = ""
        # images are rendered with virtual lines by image.nvim
        virtual_lines = 0
        if len(self.output.chunks) > 0:
            x = 0
            for chunk in self.output.chunks:
                y = lineno
                if virtual:
                    y = shape[1]
                chunktext, virt_lines = chunk.place(
                    buf,
                    self.options,
                    x,
                    y,
                    shape,
                    self.canvas,
                    virtual,
                    winnr=self.nvim.current.window.handle if virtual else None,
                )
                lines_str += chunktext
                lineno += chunktext.count("\n")
                virtual_lines += virt_lines
                x = len(lines_str) - lines_str.rfind("\n")

            limit = self.options.limit_output_chars
            if limit and len(lines_str) > limit:
                lines_str = lines_str[:limit]
                lines_str += f"\n...truncated to {limit} chars\n"

            lines = lines_str.split("\n")
            lineno = len(lines) + virtual_lines
        else:
            lines = []

        # Remove trailing empty lines
        while len(lines) > 0 and lines[-1] == "":
            lines.pop()

        lines.insert(0, self._get_header_text(self.output))
        return lines, len(lines) - 1 + virtual_lines

    def show_virtual_output(self, anchor: Position) -> None:
        if self.displayed_status == OutputStatus.DONE and self.virt_text_id is not None:
            return
        offset = self.calculate_offset(anchor) if self.options.cover_empty_lines else 0
        self.displayed_status = self.output.status

        buf = self.nvim.buffers[anchor.bufno]

        # clear the existing virtual text
        if self.virt_text_id is not None:
            self.nvim.funcs.nvim_buf_del_extmark(
                anchor.bufno, self.extmark_namespace, self.virt_text_id
            )
            self.virt_text_id = None

        win = self.nvim.current.window
        win_info = self.nvim.funcs.getwininfo(win.handle)[0]
        win_col = win_info["wincol"]
        win_row = anchor.lineno + offset
        win_width = win_info["width"] - win_info["textoff"]
        win_height = win_info["height"]
        last = self.nvim.funcs.line("$")

        if self.options.virt_lines_off_by_1 and win_row < last - 1:
            win_row += 1

        if win_row > last:
            win_row = last

        shape = (
            win_col,
            win_row,
            win_width,
            win_height,
        )
        lines, _ = self.build_output_text(shape, anchor.bufno, True)
        l = len(lines)
        if l > self.options.virt_text_max_lines:
            lines = lines[: self.options.virt_text_max_lines - 1]
            lines.append(f"󰁅 {l - self.options.virt_text_max_lines + 1} More Lines ")

        self.virt_text_id = buf.api.set_extmark(
            self.extmark_namespace,
            win_row,
            0,
            {
                "virt_lines": [[(line, self.options.hl.virtual_text)] for line in lines],
            },
        )
        self.canvas.present()

    def calculate_offset(self, anchor: Position) -> int:
        offset = 0
        lineno = anchor.lineno
        while lineno > 0:
            current_line = self.nvim.funcs.nvim_buf_get_lines(
                anchor.bufno,
                lineno,
                lineno + 1,
                False,
            )[0]
            is_comment = False
            for x in self.options.cover_lines_starting_with:
                if current_line.startswith(x):
                    is_comment = True
                    break
            if current_line != "" and not is_comment:
                return offset
            else:
                lineno -= 1
                offset -= 1
        # Only get here if current_pos.lineno == 0
        return 0

    def show_floating_win(self, anchor: Position) -> None:
        win = self.nvim.current.window
        win_col = 0
        offset = 0
        if self.options.cover_empty_lines:
            offset = self.calculate_offset(anchor)
            win_row = self._buffer_to_window_lineno(anchor.lineno + offset) + 1
        else:
            win_row = self._buffer_to_window_lineno(anchor.lineno + 1)

        if win_row <= 0:  # anchor position is off screen
            return
        win_width = win.width
        win_height = win.height

        border_w, border_h = border_size(self.options.output_win_border)

        win_height -= border_h
        win_width -= border_w

        # Clear buffer:
        self.display_buf.api.set_lines(0, -1, False, [])

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
        lines, real_height = self.build_output_text(shape, self.display_buf.number, False)

        # You can't append lines normally, there will be a blank line at the top
        self.display_buf[0] = lines[0]
        self.display_buf.append(lines[1:])
        self.nvim.api.set_option_value(
            "filetype", "molten_output", {"buf": self.display_buf.handle}
        )

        # Open output window
        # assert self.display_window is None
        if win_row < win_height:
            border = self.options.output_win_border
            max_height = min(real_height + 1, self.options.output_win_max_height)
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
                self.display_virt_lines = None

            if self.options.output_virt_lines or self.options.cover_empty_lines:
                virt_lines_y = anchor.lineno
                if self.options.cover_empty_lines:
                    virt_lines_y += offset
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
