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
from datetime import datetime

from pynvim import Nvim


from molten.images import Canvas
from molten.options import MoltenOptions
from molten.utils import notify_error


class OutputChunk(ABC):
    jupyter_data: Optional[Dict[str, Any]] = None
    jupyter_metadata: Optional[Dict[str, Any]] = None
    # extra keys that are used to write data to jupyter notebook files (ie. for error outputs)
    extras: Dict[str, Any] = {}
    output_type: str

    @abstractmethod
    def place(
        self,
        bufnr: int,
        options: MoltenOptions,
        col: int,
        lineno: int,
        shape: Tuple[int, int, int, int],
        canvas: Canvas,
        hard_wrap: bool,
        winnr: int | None = None,
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
        self.output_type = "display_data"

    def __repr__(self) -> str:
        return f'TextOutputChunk("{self.text}")'

    def place(
        self,
        _bufnr: int,
        options: MoltenOptions,
        col: int,
        _lineno: int,
        shape: Tuple[int, int, int, int],
        _canvas: Canvas,
        hard_wrap: bool,
        winnr: int | None = None,
    ) -> Tuple[str, int]:
        text = clean_up_text(self.text)
        extra_lines = 0
        if options.wrap_output:  # count the number of extra lines this will need when wrapped
            win_width = shape[2]
            if hard_wrap:
                lines = []
                splits = []
                # Assume this is a progress bar, or similar, we shouldn't try to wrap it
                if text.find("\r") != -1:
                    return text, 0
                for line in text.split("\n"):
                    index = 0
                    if len(line) + col > win_width:
                        splits.append(line[: win_width - col])
                        line = line[win_width - col :]

                    for _ in range(len(line) // win_width):
                        splits.append(line[index * win_width : (index + 1) * win_width])
                        index += 1
                    splits.append(line[index * win_width :])

                lines.extend(splits)
                text = "\n".join(lines)
            else:
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
        self.output_type = "error"


class AbortedOutputChunk(TextLnOutputChunk):
    def __init__(self) -> None:
        super().__init__("<Kernel aborted with no error message.>")


class ImageOutputChunk(OutputChunk):
    def __init__(self, img_path: str):
        self.img_path = img_path
        self.output_type = "display_data"
        self.img_identifier = None

    def place(
        self,
        bufnr: int,
        options: MoltenOptions,
        _col: int,
        lineno: int,
        _shape: Tuple[int, int, int, int],
        canvas: Canvas,
        virtual: bool,
        winnr: int | None = None,
    ) -> Tuple[str, int]:
        loc = options.image_location
        if not (loc == "both" or (loc == "virt" and virtual) or (loc == "float" and not virtual)):
            return "", 0

        self.img_identifier = canvas.add_image(
            self.img_path,
            f"{'virt-' if virtual else ''}{self.img_path}",
            0,
            lineno,
            bufnr,
            winnr,
        )
        # images are rendered into virtual lines following the current line,
        # which also needs to exist as the extmark is placed there
        return " \n", canvas.img_size(self.img_identifier)["height"]


class OutputStatus(Enum):
    HOLD = 0
    """Waiting to run this cell"""
    RUNNING = 1
    """Currently running, waiting for code to finish running"""
    DONE = 2
    """Code has already been run"""
    NEW = 3
    """Cell was created, nothing run, no output"""


class Output:
    execution_count: Optional[int]
    chunks: List[OutputChunk]
    status: OutputStatus
    success: bool
    old: bool
    start_time: datetime | None
    end_time: datetime | None

    _should_clear: bool

    def __init__(self, execution_count: Optional[int]):
        self.execution_count = execution_count
        self.status = OutputStatus.HOLD
        self.chunks = []
        self.success = True
        self.old = False

        self.start_time = None
        self.end_time = None

        self._should_clear = False

    def merge_text_chunks(self):
        """Merge the last two chunks if they are text chunks, and text on a line before \r
        character, this is b/c outputs before a \r aren't shown, and so, should be deleted"""
        if (
            len(self.chunks) >= 2
            and isinstance((c1 := self.chunks[-2]), TextOutputChunk)
            and isinstance((c2 := self.chunks[-1]), TextOutputChunk)
        ):
            c1.text += c2.text
            c1.text = "\n".join([re.sub(r".*\r", "", x) for x in c1.text.split("\n")[:-1]])
            c1.jupyter_data = {"text/plain": c1.text}
            self.chunks.pop()
        elif len(self.chunks) > 0 and isinstance((c1 := self.chunks[0]), TextOutputChunk):
            c1.text = "\n".join([re.sub(r".*\r", "", x) for x in c1.text.split("\n")[:-1]])


def to_outputchunk(
    nvim: Nvim,
    alloc_file: Callable[
        [str, str],
        "AbstractContextManager[Tuple[str, IO[bytes]]]",
    ],
    data: Dict[str, Any],
    metadata: Dict[str, Any],
    options: MoltenOptions,
) -> OutputChunk:
    def _to_image_chunk(path: str) -> OutputChunk:
        return ImageOutputChunk(path)

    # Output chunk functions:
    def _from_image(extension: str, imgdata: bytes) -> OutputChunk:
        import base64

        with alloc_file(extension, "wb") as (path, file):
            file.write(base64.b64decode(str(imgdata)))
        return _to_image_chunk(path)

    def _from_image_svgxml(svg: str) -> OutputChunk:
        try:
            import cairosvg

            with alloc_file("png", "wb") as (path, file):
                cairosvg.svg2png(svg, write_to=file)
            return _to_image_chunk(path)
        except ImportError:
            with alloc_file("svg", "w") as (path, file):
                file.write(svg)  # type: ignore
            return _to_image_chunk(path)

    def _from_application_plotly(figure_json: Any) -> OutputChunk:
        from plotly.io import from_json

        # NOTE: import this to cause an import exception which we catch. instead of a different
        # error in `write_image`
        import kaleido  # type: ignore
        import json

        figure = from_json(json.dumps(figure_json))

        with alloc_file("png", "wb") as (path, file):
            figure.write_image(file, engine="kaleido")
        return _to_image_chunk(path)

    def _from_latex(tex: str) -> OutputChunk:
        from pnglatex import pnglatex

        try:
            with alloc_file("png", "w") as (path, _):
                pass
            pnglatex(tex, path)
            return _to_image_chunk(path)
        except ValueError:
            notify_error(nvim, f"pnglatex was unable to render image from LaTeX: {tex}")
            return _from_plaintext(tex)

    def _from_plaintext(text: str) -> OutputChunk:
        return TextLnOutputChunk(text)

    chunk = None
    # if options.image_provider != "none":
    # handle these mimetypes first, since they require Molten to render them
    special_mimetypes = [
        ("image/svg+xml", _from_image_svgxml),
        ("application/vnd.plotly.v1+json", _from_application_plotly),
        ("text/latex", _from_latex),
    ]

    for mimetype, process_func in special_mimetypes:
        try:
            maybe_data = None
            if data is not None:
                maybe_data = data.get(mimetype)
            if maybe_data is not None:
                chunk = process_func(maybe_data)  # type: ignore
                break
        except ImportError:
            continue

    if chunk is None and data is not None:
        # handle arbitrary images
        for mimetype in data.keys():
            match mimetype.split("/"):
                case ["image", extension]:
                    chunk = _from_image(extension, data[mimetype])
                    break

    if chunk is None:
        # fallback to plain text if there's nothing else
        if data is not None and data.get("text/plain"):
            chunk = _from_plaintext(data["text/plain"])
        else:
            if data == None:
                data = {}
            chunk = BadOutputChunk(list(data.keys()))

    chunk.jupyter_data = data
    chunk.jupyter_metadata = metadata

    return chunk
