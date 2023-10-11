from typing import (
    Optional,
    Tuple,
    List,
    Dict,
    Any,
    Callable,
    IO,
)
from contextlib import AbstractContextManager
from enum import Enum
from abc import ABC, abstractmethod
import re

from pynvim import Nvim


from molten.images import Canvas
from molten.options import MoltenOptions
from molten.utils import notify_error


class OutputChunk(ABC):
    jupyter_data: Optional[Dict[str, Any]] = None
    jupyter_metadata: Optional[Dict[str, Any]] = None

    @abstractmethod
    def place(
        self,
        bufnr: int,
        options: MoltenOptions,
        lineno: int,
        shape: Tuple[int, int, int, int],
        canvas: Canvas,
    ) -> Tuple[str, int]:
        pass


# Adapted from [https://stackoverflow.com/a/14693789/4803382]:
ANSI_CODE_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def clean_up_text(text: str) -> str:
    text = ANSI_CODE_REGEX.sub("", text)
    text = text.replace("\r\n", "\n")
    return text


class TextOutputChunk(OutputChunk):
    text: str

    def __init__(self, text: str):
        self.text = text

    def _cleanup_text(self, text: str) -> str:
        return clean_up_text(text)

    def place(
        self,
        _bufnr: int,
        options: MoltenOptions,
        _: int,
        shape: Tuple[int, int, int, int],
        _canvas: Canvas,
    ) -> Tuple[str, int]:
        text = self._cleanup_text(self.text)
        extra_lines = 0
        if options.wrap_output:  # count the number of extra lines this will need when wrapped
            win_width = shape[2]
            for line in text.split("\n"):
                if len(line) > win_width:
                    extra_lines += len(line) // win_width
        return text, extra_lines


class TextLnOutputChunk(TextOutputChunk):
    def __init__(self, text: str):
        super().__init__(text + "\n")


class BadOutputChunk(TextLnOutputChunk):
    def __init__(self, mimetypes: List[str]):
        super().__init__("<No usable MIMEtype! Received mimetypes %r>" % mimetypes)


class MimetypesOutputChunk(TextLnOutputChunk):
    def __init__(self, mimetypes: List[str]):
        super().__init__("[DEBUG] Received mimetypes: %r" % mimetypes)


class ErrorOutputChunk(TextLnOutputChunk):
    def __init__(self, name: str, message: str, traceback: List[str]):
        super().__init__(
            "\n".join(
                [
                    f"[Error] {name}: {message}",
                    "Traceback:",
                ]
                + traceback
            )
        )


class AbortedOutputChunk(TextLnOutputChunk):
    def __init__(self) -> None:
        super().__init__("<Kernel aborted with no error message.>")


class ImageOutputChunk(OutputChunk):
    def __init__(self, img_path: str):
        self.img_path = img_path

    def place(
        self,
        bufnr: int,
        _: MoltenOptions,
        lineno: int,
        _shape: Tuple[int, int, int, int],
        canvas: Canvas,
    ) -> Tuple[str, int]:
        # _x, _y, win_w, win_h = shape
        img = canvas.add_image(
            self.img_path,
            x=0,
            y=lineno + 1,
            bufnr=bufnr,
        )
        return "", canvas.img_size(img)["height"]


class OutputStatus(Enum):
    HOLD = 0
    RUNNING = 1
    DONE = 2


class Output:
    execution_count: Optional[int]
    chunks: List[OutputChunk]
    status: OutputStatus
    success: bool
    old: bool

    _should_clear: bool

    def __init__(self, execution_count: Optional[int]):
        self.execution_count = execution_count
        self.status = OutputStatus.HOLD
        self.chunks = []
        self.success = True
        self.old = False

        self._should_clear = False


def to_outputchunk(
    nvim: Nvim,
    alloc_file: Callable[
        [str, str],
        "AbstractContextManager[Tuple[str, IO[bytes]]]",
    ],
    data: Dict[str, Any],
    metadata: Dict[str, Any],
) -> OutputChunk:
    def _to_image_chunk(path: str) -> OutputChunk:
        return ImageOutputChunk(path)

    # Output chunk functions:
    def _from_image_png(imgdata: bytes) -> OutputChunk:
        import base64

        with alloc_file("png", "wb") as (path, file):
            file.write(base64.b64decode(str(imgdata)))
        return _to_image_chunk(path)

    def _from_image_svgxml(svg: str) -> OutputChunk:
        import cairosvg

        with alloc_file("png", "wb") as (path, file):
            cairosvg.svg2png(svg, write_to=file)
        return _to_image_chunk(path)

    def _from_application_plotly(figure_json: Any) -> OutputChunk:
        from plotly.io import from_json
        import json

        figure = from_json(json.dumps(figure_json))

        with alloc_file("png", "wb") as (path, file):
            figure.write_image(file, engine="kaleido")
        return _to_image_chunk(path)

    def _from_latex(tex: str) -> OutputChunk:
        from pnglatex import pnglatex

        with alloc_file("png", "w") as (path, _):
            pass
        pnglatex(tex, path)
        return _to_image_chunk(path)

    def _from_plaintext(text: str) -> OutputChunk:
        return TextLnOutputChunk(text)

    OUTPUT_CHUNKS = {
        "image/png": _from_image_png,
        "image/svg+xml": _from_image_svgxml,
        "application/vnd.plotly.v1+json": _from_application_plotly,
        "text/latex": _from_latex,
        "text/plain": _from_plaintext,
    }

    chunk = None
    for mimetype, process_func in OUTPUT_CHUNKS.items():
        try:
            maybe_data = data.get(mimetype)
            if maybe_data is not None:
                chunk = process_func(maybe_data)  # type: ignore
                break
        except ImportError:
            continue

    if chunk is None:
        chunk = BadOutputChunk(list(data.keys()))

    chunk.jupyter_data = data
    chunk.jupyter_metadata = metadata

    return chunk
