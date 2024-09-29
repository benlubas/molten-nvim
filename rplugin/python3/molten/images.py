from typing import Dict, Set
from abc import ABC, abstractmethod

from pynvim import Nvim
from molten.options import MoltenOptions

from molten.utils import notify_warn, MoltenException


class Canvas(ABC):
    @abstractmethod
    def init(self) -> None:
        """
        Initialize the canvas.

        This will be called before the canvas is ever used.
        """

    @abstractmethod
    def deinit(self) -> None:
        """
        Deinitialize the canvas.

        The canvas will not be used after this operation.
        """

    @abstractmethod
    def present(self) -> None:
        """
        Present the canvas.

        This is called only when a redraw is necessary -- so, if desired, it
        can be implemented so that `clear` and `add_image` only queue images as
        to be drawn, and `present` actually performs the operations, in order
        to reduce flickering.
        """

    @abstractmethod
    def img_size(self, identifier: str) -> Dict[str, int]:
        """
        Get the height of an image in terminal rows.
        """

    @abstractmethod
    def add_image(
        self,
        path: str,
        identifier: str,
        x: int,
        y: int,
        bufnr: int,
        winnr: int | None = None,
    ) -> str:
        """
        Add an image to the canvas.
        Takes effect after a call to present()

        Parameters
        - path: str
          Path to the image we want to show
        - x: int
          Column number of where the image is supposed to be drawn at (top-left
          corner).
        - y: int
          Row number of where the image is supposed to be drawn at (top-right
          corner).
        - bufnr: int
          The buffer number for the buffer in which to draw the image.

        Returns:
        str the identifier for the image
        """

    @abstractmethod
    def remove_image(self, identifier: str) -> None:
        """
        Remove an image from the canvas. In practice this is just hiding the image
        Takes effect after a call to present()

        Parameters
        - identifier: str
          The identifier for the image to remove.
        """


class NoCanvas(Canvas):
    def __init__(self) -> None:
        pass

    def init(self) -> None:
        pass

    def deinit(self) -> None:
        pass

    def present(self) -> None:
        pass

    def img_size(self, _indentifier: str) -> Dict[str, int]:
        return {"height": 0, "width": 0}

    def add_image(
        self,
        _path: str,
        _identifier: str,
        _x: int,
        _y: int,
        _bufnr: int,
        _winnr: int,
    ) -> None:
        pass

    def remove_image(self, _identifier: str) -> None:
        pass


class ImageNvimCanvas(Canvas):
    nvim: Nvim
    to_make_visible: Set[str]
    to_make_invisible: Set[str]
    visible: Set[str]

    def __init__(self, nvim: Nvim):
        self.nvim = nvim
        self.visible = set()
        self.to_make_visible = set()
        self.to_make_invisible = set()
        self.next_id = 0

    def init(self) -> None:
        self.nvim.exec_lua("_image = require('load_image_nvim').image_api")
        self.nvim.exec_lua("_image_utils = require('load_image_nvim').image_utils")
        self.image_api = self.nvim.lua._image
        self.image_utils = self.nvim.lua._image_utils

    def deinit(self) -> None:
        self.image_api.clear_all()

    def present(self) -> None:
        # images to both show and hide should be ignored
        to_work_on = self.to_make_visible.difference(
            self.to_make_visible.intersection(self.to_make_invisible)
        )
        self.to_make_invisible.difference_update(self.to_make_visible)
        for identifier in self.to_make_invisible:
            self.image_api.clear(identifier)

        for identifier in to_work_on:
            size = self.img_size(identifier)
            self.image_api.render(identifier, size)

        self.visible.update(self.to_make_visible)
        self.to_make_invisible.clear()
        self.to_make_visible.clear()

    def img_size(self, identifier: str) -> Dict[str, int]:
        return self.image_api.image_size(identifier)

    def add_image(
        self,
        path: str,
        identifier: str,
        x: int,
        y: int,
        bufnr: int,
        winnr: int | None = None,
    ) -> str:
        img = self.image_api.from_file(
            path,
            {
                "id": identifier,
                "buffer": bufnr,
                "with_virtual_padding": True,
                "x": x,
                "y": y,
                "window": winnr,
            },
        )
        self.to_make_visible.add(img)
        return img

    def remove_image(self, identifier: str) -> None:
        self.to_make_invisible.add(identifier)


class WeztermCanvas(Canvas):
    """A canvas for using Wezterm's imgcat functionality to render images/plots"""

    nvim: Nvim
    split_dir: str | None
    split_size: int | None
    to_make_visible: Set[str]
    to_make_invisible: Set[str]
    visible: Set[str]

    def __init__(self, nvim: Nvim, split_dir: str | None, split_size: int | None):
        self.nvim = nvim
        self.split_dir = split_dir
        self.split_size = split_size
        self.visible = set()
        self.to_make_visible = set()
        self.to_make_invisible = set()
        self.initial_pane_id: int | None = None
        self.image_pane: int | None = None

    def init(self) -> None:
        self.nvim.exec_lua("_wezterm = require('load_wezterm_nvim').wezterm_api")
        self.wezterm_api = self.nvim.lua._wezterm
        self.initial_pane_id = self.wezterm_api.get_pane_id()

    def deinit(self) -> None:
        """Closes the terminal split that was opened with MoltenInit"""
        self.wezterm_api.close_image_pane(str(self.image_pane).strip())

    def present(self) -> None:
        to_work_on = self.to_make_visible.difference(
            self.to_make_visible.intersection(self.to_make_invisible)
        )
        self.to_make_invisible.difference_update(self.to_make_visible)

        for identifier in to_work_on:
            self.wezterm_api.send_image(
                identifier,
                str(self.image_pane).strip(),
                str(self.initial_pane_id).strip(),
            )

        self.visible.update(self.to_make_visible)
        self.to_make_invisible.clear()
        self.to_make_visible.clear()

    def img_size(self, _indentifier: str) -> Dict[str, int]:
        return {"height": 0, "width": 0}

    def add_image(
        self,
        path: str,
        identifier: str,
        _x: int,
        _y: int,
        _bufnr: int,
        _winnr: int,
    ) -> str | dict[str, str]:
        """Adds an image to the queue to be rendered by Wezterm via the place method"""
        img = {"path": path, "id": identifier}
        self.to_make_visible.add(img["path"])
        return img

    def remove_image(self, identifier: str) -> None:
        pass

    def wezterm_split(self):
        """Splits the terminal based on config preferences at molten kernel init if
        supplied, otherwise resort to default values. Returns the pane id of the new
        split to allow sending/moving between the panes correctly.
        """
        self.image_pane = self.wezterm_api.wezterm_molten_init(
            self.initial_pane_id, self.split_dir, self.split_size
        )


def get_canvas_given_provider(
    nvim: Nvim, options: MoltenOptions
) -> Canvas:
    name = options.image_provider

    if name == "none":
        return NoCanvas()
    elif name == "image.nvim":
        return ImageNvimCanvas(nvim)
    elif name == "wezterm":
        if options.auto_open_output:
            raise MoltenException(
                "'wezterm' as an image provider does not currently support molten_auto_open_output = true, please set it to false or use a different image provider"
            )
        return WeztermCanvas(nvim, options.split_direction, options.split_size)
    else:
        notify_warn(nvim, f"unknown image provider: `{name}`")
        return NoCanvas()
