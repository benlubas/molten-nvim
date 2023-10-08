import os

from pynvim import Nvim
from typing import Optional, Union, List

from molten.utils import notify_error


class MoltenOptions:
    auto_open_output: bool
    wrap_output: bool
    output_window_border: Union[str, List[str]]
    output_window_style: Optional[str]
    show_mimetype_debug: bool
    cell_highlight_group: str
    output_win_highlight: str
    save_path: str
    image_provider: str
    copy_output: bool
    enter_output_behavior: str
    nvim: Nvim

    def __init__(self, nvim: Nvim):
        self.nvim = nvim
        # fmt: off
        CONFIG_VARS = [
            ("molten_auto_open_output", True),
            ("molten_wrap_output", False),
            ("molten_output_window_border", "none"),
            ("molten_output_window_style", "minimal"),
            ("molten_show_mimetype_debug", False),
            ("molten_cell_highlight_group", "CursorLine"),
            ("molten_output_win_highlight", "NormalFloat"),
            ("molten_save_path", os.path.join(nvim.funcs.stdpath("data"), "molten")),
            ("molten_image_provider", "none"),
            ("molten_copy_output", False),
            ("molten_enter_output_behavior", "open_then_enter")
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
