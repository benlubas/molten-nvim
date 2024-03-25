import os

from pynvim import Nvim
from typing import Optional, Union, List
from dataclasses import dataclass

from molten.utils import notify_error


@dataclass
class HL:
    border_norm = "MoltenOutputBorder"
    border_fail = "MoltenOutputBorderFail"
    border_succ = "MoltenOutputBorderSuccess"
    win = "MoltenOutputWin"
    win_nc = "MoltenOutputWinNC"
    foot = "MoltenOutputFooter"
    cell = "MoltenCell"
    virtual_text = "MoltenVirtualText"

    defaults = {
        border_norm: "FloatBorder",
        border_succ: border_norm,
        border_fail: border_norm,
        win: "NormalFloat",
        win_nc: win,
        foot: "FloatFooter",
        cell: "CursorLine",
        virtual_text: "Comment",
    }


class MoltenOptions:
    auto_image_popup: bool
    auto_init_behavior: str
    auto_open_html_in_browser: bool
    auto_open_output: bool
    cover_empty_lines: bool
    cover_lines_starting_with: List[str]
    copy_output: bool
    enter_output_behavior: str
    image_provider: str
    limit_output_chars: int
    open_cmd: Optional[str]
    output_crop_border: bool
    output_show_exec_time: bool
    output_show_more: bool
    output_virt_lines: bool
    output_win_border: Union[str, List[str]]
    output_win_cover_gutter: bool
    output_win_hide_on_leave: bool
    output_win_max_height: int
    output_win_max_width: int
    output_win_style: Optional[str]
    save_path: str
    split_direction: str | None
    split_size: int | None
    show_mimetype_debug: bool
    tick_rate: int
    use_border_highlights: bool
    virt_lines_off_by_1: bool
    virt_text_max_lines: int
    virt_text_output: bool
    wrap_output: bool
    nvim: Nvim
    hl: HL

    def __init__(self, nvim: Nvim):
        self.nvim = nvim
        self.hl = HL()
        # fmt: off
        CONFIG_VARS = [
            ("molten_auto_image_popup", False),
            ("molten_auto_init_behavior", "init"), # "raise" or "init"
            ("molten_auto_open_html_in_browser", False),
            ("molten_auto_open_output", True),
            ("molten_cover_empty_lines", False),
            ("molten_cover_lines_starting_with", []),
            ("molten_copy_output", False),
            ("molten_enter_output_behavior", "open_then_enter"),
            ("molten_image_provider", "none"),
            ("molten_open_cmd", None),
            ("molten_output_crop_border", True),
            ("molten_output_show_exec_time", True),
            ("molten_output_show_more", False),
            ("molten_output_virt_lines", False),
            ("molten_output_win_border", [ "", "━", "", "" ]),
            ("molten_output_win_cover_gutter", True),
            ("molten_limit_output_chars", 1000000),
            ("molten_output_win_hide_on_leave", True),
            ("molten_output_win_max_height", 999999),
            ("molten_output_win_max_width", 999999),
            ("molten_output_win_style", False),
            ("molten_save_path", os.path.join(nvim.funcs.stdpath("data"), "molten")),
            ("molten_split_direction", "right"),
            ("molten_split_size", 40),
            ("molten_show_mimetype_debug", False),
            ("molten_tick_rate", 500),
            ("molten_use_border_highlights", False),
            ("molten_virt_lines_off_by_1", False),
            ("molten_virt_text_max_lines", 12),
            ("molten_virt_text_output", False),
            ("molten_wrap_output", False),
        ]
        # fmt: on

        for name, default in CONFIG_VARS:
            setattr(self, name[7:], nvim.vars.get(name, default))

    def update_option(self, option: str, value):
        if option.startswith("molten_"):
            option = option[7:]
        if hasattr(self, option):
            setattr(self, option, value)
        else:
            notify_error(self.nvim, f"Invalid option passed to MoltenUpdateOption: {option}")
