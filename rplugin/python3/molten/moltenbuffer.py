from contextlib import AbstractContextManager
from typing import IO, Callable, List, Optional, Dict, Tuple
from queue import Queue
import hashlib

from pynvim import Nvim
from pynvim.api import Buffer
from molten.code_cell import CodeCell

from molten.options import MoltenOptions
from molten.images import Canvas
from molten.position import Position
from molten.utils import notify_info, notify_warn
from molten.outputbuffer import OutputBuffer
from molten.outputchunks import OutputChunk, OutputStatus
from molten.runtime import JupyterRuntime


class MoltenKernel:
    """Handles a Single Kernel that can be attached to multiple buffers
    Other MoltenKernels can be attached to the same buffers"""

    nvim: Nvim
    canvas: Canvas
    highlight_namespace: int
    extmark_namespace: int
    buffers: List[Buffer]

    runtime: JupyterRuntime

    kernel_id: str
    """name unique to this specific jupyter runtime. Only used within Molten. Human Readable"""

    outputs: Dict[CodeCell, OutputBuffer]
    current_output: Optional[CodeCell]
    queued_outputs: "Queue[CodeCell]"

    selected_cell: Optional[CodeCell]
    should_show_floating_win: bool
    updating_interface: bool

    options: MoltenOptions

    def __init__(
        self,
        nvim: Nvim,
        canvas: Canvas,
        highlight_namespace: int,
        extmark_namespace: int,
        main_buffer: Buffer,
        options: MoltenOptions,
        kernel_name: str,
        kernel_id: str,
    ):
        self.nvim = nvim
        self.canvas = canvas
        self.highlight_namespace = highlight_namespace
        self.extmark_namespace = extmark_namespace
        self.buffers = [main_buffer]

        self._doautocmd("MoltenInitPre")

        self.runtime = JupyterRuntime(nvim, kernel_name, options)
        self.kernel_id = kernel_id

        self.outputs = {}
        self.current_output = None
        self.queued_outputs = Queue()

        self.selected_cell = None
        self.should_show_floating_win = False
        self.updating_interface = False

        self.options = options

    def _doautocmd(self, autocmd: str, opts: Dict = {}) -> None:
        assert " " not in autocmd
        opts["pattern"] = autocmd
        self.nvim.api.exec_autocmds("User", opts)
        # self.nvim.command(f"doautocmd User {autocmd}")

    def add_nvim_buffer(self, buffer: Buffer) -> None:
        self.buffers.append(buffer)

    def deinit(self) -> None:
        self._doautocmd("MoltenDeinitPre")
        self.runtime.deinit()
        self._doautocmd("MoltenDeinitPost")

    def interrupt(self) -> None:
        self.runtime.interrupt()

    def restart(self, delete_outputs: bool = False) -> None:
        if delete_outputs:
            self.outputs = {}
            self.clear_interface()
            self.clear_open_output_windows()
            self.clear_virt_outputs()

        self.runtime.restart()

    def run_code(self, code: str, span: CodeCell) -> None:
        if not self.try_delete_overlapping_cells(span):
            return
        self.runtime.run_code(code)

        self.outputs[span] = OutputBuffer(
            self.nvim, self.canvas, self.extmark_namespace, self.options
        )
        self.queued_outputs.put(span)

        self.selected_cell = span

        if not self.options.virt_text_output:
            self.should_show_floating_win = True

        self.update_interface()

        self._check_if_done_running()

    def reevaluate_all(self) -> None:
        for span in sorted(self.outputs.keys(), key=lambda s: s.begin):
            code = span.get_text(self.nvim)
            self.run_code(code, span)

    def reevaluate_cell(self) -> bool:
        self.selected_cell = self._get_selected_span()
        if self.selected_cell is None:
            return False

        code = self.selected_cell.get_text(self.nvim)

        self.run_code(code, self.selected_cell)
        return True

    def open_in_browser(self, silent=False) -> bool:
        """Open the HTML output of the currently selected cell in the browser.
        Returns: True if we're in a cell, False otherwise"""
        self.selected_cell = self._get_selected_span()
        if self.selected_cell is None:
            return False

        filepath = write_html_from_chunks(
            self.outputs[self.selected_cell].output.chunks, self.runtime._alloc_file
        )
        if filepath is None:
            if not silent:
                notify_warn(self.nvim, "No HTML output to open.")
            return True

        opencmd = self.options.open_cmd
        import platform

        if opencmd is None:
            match platform.system():
                case "Darwin":
                    opencmd = "open"
                case "Linux":
                    opencmd = "xdg-open"
                case "Windows":
                    opencmd = "start"

        if opencmd is None:
            notify_warn(self.nvim, f"Can't open in browser, OS unsupported: {platform.system()}")
        else:
            import subprocess

            subprocess.run([opencmd, filepath])

        return True

    def _check_if_done_running(self) -> None:
        # TODO: refactor
        is_idle = (self.current_output is None or not self.current_output in self.outputs) or (
            self.current_output is not None
            and self.outputs[self.current_output].output.status == OutputStatus.DONE
        )
        if is_idle and not self.queued_outputs.empty():
            key = self.queued_outputs.get_nowait()
            self.current_output = key

    def tick(self) -> None:
        self._check_if_done_running()

        was_ready = self.runtime.is_ready()
        if self.current_output is None or not self.current_output in self.outputs:
            did_stuff = self.runtime.tick(None)
        else:
            output = self.outputs[self.current_output].output
            starting_status = output.status
            did_stuff = self.runtime.tick(output)

            if (
                self.options.auto_open_html_in_browser
                and starting_status != OutputStatus.DONE
                and output.status == OutputStatus.DONE
            ):
                self.open_in_browser(silent=True)
        if did_stuff:
            self.update_interface()
        if not was_ready and self.runtime.is_ready():
            self._doautocmd(
                "MoltenKernelReady",
                opts={
                    "data": {
                        "kernel_id": self.kernel_id,
                    }
                },
            )
            notify_info(
                self.nvim, f"Kernel '{self.runtime.kernel_name}' (id: {self.kernel_id}) is ready."
            )

    def enter_output(self) -> None:
        if self.selected_cell is not None:
            if self.options.enter_output_behavior != "no_open":
                self.should_show_floating_win = True
            self.should_show_floating_win = self.outputs[self.selected_cell].enter(
                self.selected_cell.end
            )

    def _get_cursor_position(self) -> Position:
        _, lineno, colno, _, _ = self.nvim.funcs.getcurpos()
        return Position(self.nvim.current.buffer.number, lineno - 1, colno - 1)

    def clear_interface(self) -> None:
        if self.updating_interface:
            return

        for buffer in self.buffers:
            self.nvim.funcs.nvim_buf_clear_namespace(
                buffer.number,
                self.highlight_namespace,
                0,
                -1,
            )

    def clear_open_output_windows(self) -> None:
        for output in self.outputs.values():
            output.clear_float_win()

    def clear_virt_outputs(self) -> None:
        for cell, output in self.outputs.items():
            output.clear_virt_output(cell.bufno)

    def _get_selected_span(self) -> Optional[CodeCell]:
        current_position = self._get_cursor_position()
        selected = None
        for span in reversed(self.outputs.keys()):
            if current_position in span:
                selected = span
                break

        return selected

    def try_delete_overlapping_cells(self, span: CodeCell) -> bool:
        """Delete the code cells in this kernel that overlap with the given span, if overlapping
        a currently running cell, return False
        Returns:
            False if the span overlaps with a currently running cell, True otherwise
        """
        for output_span in list(self.outputs.keys()):
            if output_span.overlaps(span):
                if not self._delete_cell(output_span):
                    return False
        return True

    def _delete_cell(self, cell: CodeCell, quiet=False) -> bool:
        """Delete the given cell if it exists _and_ isn't running. If the cell is running, display
        an error and return False, otherwise return True"""
        if cell in self.outputs and self.outputs[cell].output.status == OutputStatus.RUNNING:
            if not quiet:
                notify_warn(
                    self.nvim,
                    "Cannot delete a running cell. Wait for it to finish or use :MoltenInterrupt before creating an overlapping cell.",
                )
            return False
        self.outputs[cell].clear_float_win()
        self.outputs[cell].clear_virt_output(cell.bufno)
        cell.clear_interface(self.highlight_namespace)
        del self.outputs[cell]
        if self.current_output == cell:
            self.current_output = None
        if self.selected_cell == cell:
            self.selected_cell = None
        return True

    def delete_current_cell(self) -> None:
        self.selected_cell = self._get_selected_span()
        if self.selected_cell is None:
            return
        self._delete_cell(self.selected_cell)
        self.selected_cell = None

    def clear_empty_spans(self) -> None:
        for span in list(self.outputs.keys()):
            if span.empty():
                self._delete_cell(span, quiet=True)

    def update_interface(self) -> None:
        buffer_numbers = [buf.number for buf in self.buffers]
        if self.nvim.current.buffer.number not in buffer_numbers:
            return

        if self.nvim.current.window.buffer.number not in buffer_numbers:
            return

        self.updating_interface = True
        self.clear_empty_spans()
        new_selected_cell = self._get_selected_span()

        # Clear the cell we just left
        if self.selected_cell != new_selected_cell and self.selected_cell is not None:
            if self.selected_cell in self.outputs:
                self.outputs[self.selected_cell].clear_float_win()
            self.selected_cell.clear_interface(self.highlight_namespace)

        if new_selected_cell is None:
            self.should_show_floating_win = False

        self.selected_cell = new_selected_cell

        if self.selected_cell is not None:
            self._show_selected(self.selected_cell)

        if self.options.virt_text_output:
            for span, output in self.outputs.items():
                output.show_virtual_output(span.end)

        self.canvas.present()

        self.updating_interface = False

    def on_cursor_moved(self, scrolled=False) -> None:
        new_selected_cell = self._get_selected_span()

        if (
            self.selected_cell is None
            and new_selected_cell is not None
            and self.options.auto_open_output
        ):
            self.should_show_floating_win = True

        if self.selected_cell == new_selected_cell and new_selected_cell is not None:
            if (
                scrolled
                and new_selected_cell.end.lineno < self.nvim.funcs.line("w$")
                and self.should_show_floating_win
            ):
                self.update_interface()
            return

        self.update_interface()

    def _show_selected(self, span: CodeCell) -> None:
        """Show the selected cell. Can only have a selected cell in the current buffer"""
        buf = self.nvim.current.buffer
        if buf.number not in [b.number for b in self.buffers]:
            return

        if span.begin.lineno == span.end.lineno:
            self.nvim.funcs.nvim_buf_add_highlight(
                buf.number,
                self.highlight_namespace,
                self.options.hl.cell,
                span.begin.lineno,
                span.begin.colno,
                span.end.colno,
            )
        else:
            self.nvim.funcs.nvim_buf_add_highlight(
                buf.number,
                self.highlight_namespace,
                self.options.hl.cell,
                span.begin.lineno,
                span.begin.colno,
                -1,
            )
            for lineno in range(span.begin.lineno + 1, span.end.lineno):
                self.nvim.funcs.nvim_buf_add_highlight(
                    buf.number,
                    self.highlight_namespace,
                    self.options.hl.cell,
                    lineno,
                    0,
                    -1,
                )
            self.nvim.funcs.nvim_buf_add_highlight(
                buf.number,
                self.highlight_namespace,
                self.options.hl.cell,
                span.end.lineno,
                0,
                span.end.colno,
            )

        if self.should_show_floating_win:
            self.outputs[span].show_floating_win(span.end)
        else:
            self.outputs[span].clear_float_win()

    def _get_content_checksum(self) -> str:
        return hashlib.md5(
            "\n".join(self.nvim.current.buffer.api.get_lines(0, -1, True)).encode("utf-8")
        ).hexdigest()


def write_html_from_chunks(
    chunks: List[OutputChunk],
    alloc_file: Callable[
        [str, str],
        "AbstractContextManager[Tuple[str, IO[bytes]]]",
    ],
) -> Optional[str]:
    """Build an HTML file from the given chunks.
    Returns: the filepath of the HTML file, or none if there is no HTML output in the chunks
    """
    html = ""
    for chunk in chunks:
        if (
            chunk.output_type == "display_data"
            and chunk.jupyter_data
            and "text/html" in chunk.jupyter_data
        ):
            html += chunk.jupyter_data["text/html"]

    if html != "":
        with alloc_file("html", "w") as (path, file):
            file.write(html)  # type: ignore
        return path
    return None
