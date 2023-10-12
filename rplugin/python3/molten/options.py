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

    defaults = {
        border_norm: "FloatBorder",
        border_succ: border_norm,
        border_fail: border_norm,
        win: "NormalFloat",
        win_nc: win,
        foot: "FloatFooter",
        cell: "CursorLine",
    }

class MoltenOptions:
    auto_open_output: bool
    copy_output: bool
    enter_output_behavior: str
    image_provider: str
    output_crop_border: bool
    output_show_more: bool
    output_win_border: Union[str, List[str]]
    output_win_cover_gutter: bool
    output_win_max_height: int
    output_win_max_width: int
    output_win_style: Optional[str]
    save_path: str
    use_border_highlights: bool
    wrap_output: bool
    show_mimetype_debug: bool
    nvim: Nvim
    hl: HL

    def __init__(self, nvim: Nvim):
        self.nvim = nvim
        self.hl = HL()
        # fmt: off
        CONFIG_VARS = [
            ("molten_auto_open_output", True),
            ("molten_copy_output", False),
            ("molten_enter_output_behavior", "open_then_enter"),
            ("molten_image_provider", "none"),
            ("molten_output_crop_border", True),
            ("molten_output_show_more", True),
            ("molten_output_win_border", [ "", "━", "", "" ]),
            ("molten_output_win_cover_gutter", True),
            ("molten_output_win_max_height", 999999),
            ("molten_output_win_max_width", 999999),
            ("molten_output_win_style", False),
            ("molten_save_path", os.path.join(nvim.funcs.stdpath("data"), "molten")),
            ("molten_use_border_highlights", False),
            ("molten_wrap_output", False),
            ("molten_show_mimetype_debug", False),
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
