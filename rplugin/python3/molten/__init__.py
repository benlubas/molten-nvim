import json
import os
from typing import Any, Dict, List, Optional, Tuple

import pynvim
from molten.images import Canvas, get_canvas_given_provider
from molten.io import MoltenIOError, get_default_save_file, load, save
from molten.moltenbuffer import MoltenBuffer
from molten.options import MoltenOptions
from molten.outputbuffer import OutputBuffer
from molten.runtime import get_available_kernels
from molten.utils import DynamicPosition, MoltenException, Span, nvimui
from pynvim import Nvim


@pynvim.plugin
class Molten:
    nvim: Nvim
    canvas: Optional[Canvas]
    initialized: bool

    highlight_namespace: int
    extmark_namespace: int

    buffers: Dict[int, MoltenBuffer]

    timer: Optional[int]

    options: MoltenOptions

    def __init__(self, nvim: Nvim):
        self.nvim = nvim
        self.initialized = False

        self.canvas = None
        self.buffers = {}
        self.timer = None

    def _initialize(self) -> None:
        assert not self.initialized

        self.options = MoltenOptions(self.nvim)

        self.canvas = get_canvas_given_provider(self.options.image_provider, self.nvim)
        self.canvas.init()

        self.highlight_namespace = self.nvim.funcs.nvim_create_namespace("molten-highlights")
        self.extmark_namespace = self.nvim.funcs.nvim_create_namespace("molten-extmarks")

        self.timer = self.nvim.eval("timer_start(500, 'MoltenTick', {'repeat': -1})")  # type: ignore

        self._set_autocommands()

        self.initialized = True

    def _set_autocommands(self) -> None:
        self.nvim.command("augroup molten")
        self.nvim.command("autocmd CursorMoved  * call MoltenOnCursorMoved()")
        self.nvim.command("autocmd CursorMovedI * call MoltenOnCursorMoved()")
        self.nvim.command("autocmd WinScrolled  * call MoltenOnWinScrolled()")
        self.nvim.command("autocmd BufEnter     * call MoltenUpdateInterface()")
        self.nvim.command("autocmd BufLeave     * call MoltenClearInterface()")
        self.nvim.command("autocmd BufUnload    * call MoltenOnBufferUnload()")
        self.nvim.command("autocmd ExitPre      * call MoltenOnExitPre()")
        self.nvim.command("augroup END")

    def _deinitialize(self) -> None:
        for molten in self.buffers.values():
            molten.deinit()
        if self.canvas is not None:
            self.canvas.deinit()
        if self.timer is not None:
            self.nvim.funcs.timer_stop(self.timer)

    def _initialize_if_necessary(self) -> None:
        if not self.initialized:
            self._initialize()

    def _get_molten(self, requires_instance: bool) -> Optional[MoltenBuffer]:
        maybe_molten = self.buffers.get(self.nvim.current.buffer.number)
        if requires_instance and maybe_molten is None:
            raise MoltenException(
                "Molten is not initialized; run `:MoltenInit <kernel_name>` to \
                initialize."
            )
        return maybe_molten

    def _clear_interface(self) -> None:
        if not self.initialized:
            return

        for molten in self.buffers.values():
            molten.clear_interface()
        assert self.canvas is not None
        self.canvas.present()

    def _update_interface(self) -> None:
        if not self.initialized:
            return

        molten = self._get_molten(False)
        if molten is None:
            return

        molten.update_interface()

    def _on_cursor_moved(self, scrolled=False) -> None:
        if not self.initialized:
            return

        molten = self._get_molten(False)
        if molten is None:
            return

        molten.on_cursor_moved(scrolled)

    def _ask_for_choice(self, preface: str, options: List[str]) -> Optional[str]:
        index = self.nvim.funcs.inputlist(
            [preface] + [f"{i+1}. {option}" for i, option in enumerate(options)]
        )
        if index == 0:
            return None
        else:
            return options[index - 1]

    def _initialize_buffer(self, kernel_name: str) -> MoltenBuffer:
        assert self.canvas is not None
        molten = MoltenBuffer(
            self.nvim,
            self.canvas,
            self.highlight_namespace,
            self.extmark_namespace,
            self.nvim.current.buffer,
            self.options,
            kernel_name,
        )

        self.buffers[self.nvim.current.buffer.number] = molten
        molten._doautocmd("MoltenInitPost")

        return molten

    @pynvim.command("MoltenInit", nargs="?", sync=True, complete="file")  # type: ignore
    @nvimui  # type: ignore
    def command_init(self, args: List[str]) -> None:
        self._initialize_if_necessary()

        if args:
            kernel_name = args[0]
            self._initialize_buffer(kernel_name)
        else:
            PROMPT = "Select the kernel to launch:"
            available_kernels = get_available_kernels()
            if self.nvim.exec_lua("return vim.ui.select ~= nil"):
                self.nvim.exec_lua(
                    """
                        vim.ui.select(
                            {%s},
                            {prompt = "%s"},
                            function(choice)
                                if choice ~= nil then
                                    vim.cmd("MoltenInit " .. choice)
                                end
                            end
                        )
                    """
                    % (
                        ", ".join(repr(x) for x in available_kernels),
                        PROMPT,
                    )
                )
            else:
                kernel_name = self._ask_for_choice(
                    PROMPT,
                    available_kernels,  # type: ignore
                )
                if kernel_name is not None:
                    self.command_init([kernel_name])

    def _deinit_buffer(self, molten: MoltenBuffer) -> None:
        molten.deinit()
        del self.buffers[molten.buffer.number]

    @pynvim.command("MoltenDeinit", nargs=0, sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_deinit(self) -> None:
        self._initialize_if_necessary()

        molten = self._get_molten(True)
        assert molten is not None

        self._clear_interface()

        self._deinit_buffer(molten)

    def _do_evaluate(self, pos: Tuple[Tuple[int, int], Tuple[int, int]]) -> None:
        self._initialize_if_necessary()

        molten = self._get_molten(True)
        assert molten is not None

        bufno = self.nvim.current.buffer.number
        span = Span(
            DynamicPosition(self.nvim, self.extmark_namespace, bufno, *pos[0]),
            DynamicPosition(self.nvim, self.extmark_namespace, bufno, *pos[1]),
        )

        code = span.get_text(self.nvim)

        molten.run_code(code, span)

    def _do_evaluate_expr(self, expr):
        self._initialize_if_necessary()

        molten = self._get_molten(True)
        assert molten is not None
        bufno = self.nvim.current.buffer.number
        span = Span(
            DynamicPosition(self.nvim, self.extmark_namespace, bufno, 0, 0),
            DynamicPosition(self.nvim, self.extmark_namespace, bufno, 0, 0),
        )
        molten.run_code(expr, span)

    @pynvim.command("MoltenUpdateOption", nargs="?", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_update_option(self, args: List[str]) -> None:
        molten = self._get_molten(True)
        assert molten is not None

        if len(args) == 2:
            option, value = args
            molten.options.update_option(option, value)
        else:
            self.nvim.api.notify(
                "Improper usage of :MoltenUpdateOption, expected 2 arguments, option and value",
                pynvim.logging.INFO,
                {"title": "Molten"},
            )

    @pynvim.command("MoltenEnterOutput", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_enter_output_window(self) -> None:
        molten = self._get_molten(True)
        assert molten is not None
        molten.enter_output()

    @pynvim.command("MoltenEvaluateArgument", nargs=1, sync=True)
    @nvimui
    def commnand_molten_evaluate_argument(self, expr) -> None:
        assert len(expr) == 1
        self._do_evaluate_expr(expr[0])

    @pynvim.command("MoltenEvaluateVisual", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_evaluate_visual(self) -> None:
        _, lineno_begin, colno_begin, _ = self.nvim.funcs.getpos("'<")
        _, lineno_end, colno_end, _ = self.nvim.funcs.getpos("'>")
        span = (
            (
                lineno_begin - 1,
                min(colno_begin, len(self.nvim.funcs.getline(lineno_begin))) - 1,
            ),
            (
                lineno_end - 1,
                min(colno_end, len(self.nvim.funcs.getline(lineno_end))),
            ),
        )

        self._do_evaluate(span)

    @pynvim.function("MoltenEvaluateRange", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def evaulate_range(self, *args) -> None:
        # self.nvim.current.line = f"args: {args}"
        start_line, end_line = args[0]
        span = (
            (start_line - 1, 0),
            (end_line - 1, len(self.nvim.funcs.getline(end_line))),
        )
        self._do_evaluate(span)

    @pynvim.command("MoltenEvaluateOperator", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_evaluate_operator(self) -> None:
        self._initialize_if_necessary()

        self.nvim.options["operatorfunc"] = "MoltenOperatorfunc"
        self.nvim.feedkeys("g@")

    @pynvim.command("MoltenEvaluateLine", nargs=0, sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_evaluate_line(self) -> None:
        _, lineno, _, _, _ = self.nvim.funcs.getcurpos()
        lineno -= 1

        span = ((lineno, 0), (lineno, -1))

        self._do_evaluate(span)

    @pynvim.command("MoltenReevaluateCell", nargs=0, sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_evaluate_cell(self) -> None:
        self._initialize_if_necessary()

        molten = self._get_molten(True)
        assert molten is not None

        molten.reevaluate_cell()

    @pynvim.command("MoltenInterrupt", nargs=0, sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_interrupt(self) -> None:
        molten = self._get_molten(True)
        assert molten is not None

        molten.interrupt()

    @pynvim.command("MoltenRestart", nargs=0, sync=True, bang=True)  # type: ignore # noqa
    @nvimui  # type: ignore
    def command_restart(self, bang: bool) -> None:
        molten = self._get_molten(True)
        assert molten is not None

        molten.restart(delete_outputs=bang)

    @pynvim.command("MoltenDelete", nargs=0, sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_delete(self) -> None:
        self._initialize_if_necessary()

        molten = self._get_molten(True)
        assert molten is not None

        molten.delete_cell()

    @pynvim.command("MoltenShowOutput", nargs=0, sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_show_output(self) -> None:
        self._initialize_if_necessary()

        molten = self._get_molten(True)
        assert molten is not None

        molten.should_open_display_window = True
        self._update_interface()

    @pynvim.command("MoltenHideOutput", nargs=0, sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_hide_output(self) -> None:
        molten = self._get_molten(True)
        assert molten is not None

        molten.should_open_display_window = False
        self._clear_interface()

    @pynvim.command("MoltenSave", nargs="?", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_save(self, args: List[str]) -> None:
        self._initialize_if_necessary()

        if args:
            path = args[0]
        else:
            path = get_default_save_file(self.options, self.nvim.current.buffer)

        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        molten = self._get_molten(True)
        assert molten is not None

        with open(path, "w") as file:
            json.dump(save(molten), file)

    @pynvim.command("MoltenLoad", nargs="?", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_load(self, args: List[str]) -> None:
        self._initialize_if_necessary()

        if args:
            path = args[0]
        else:
            path = get_default_save_file(self.options, self.nvim.current.buffer)

        if self.nvim.current.buffer.number in self.buffers:
            raise MoltenException("Molten is already initialized; MoltenLoad initializes Molten.")

        with open(path) as file:
            data = json.load(file)

        molten = None

        try:
            MoltenIOError.assert_has_key(data, "version", int)
            if (version := data["version"]) != 1:
                raise MoltenIOError(f"Bad version: {version}")

            MoltenIOError.assert_has_key(data, "kernel", str)
            kernel_name = data["kernel"]

            molten = self._initialize_buffer(kernel_name)

            load(molten, data)

            self._update_interface()
        except MoltenIOError as err:
            if molten is not None:
                self._deinit_buffer(molten)

            raise MoltenException("Error while doing Molten IO: " + str(err))

    # Internal functions which are exposed to VimScript

    @pynvim.function("MoltenClearInterface", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def function_clear_interface(self, _: Any) -> None:
        self._clear_interface()

    @pynvim.function("MoltenOnBufferUnload", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def function_on_buffer_unload(self, _: Any) -> None:
        abuf_str = self.nvim.funcs.expand("<abuf>")
        if not abuf_str:
            return

        molten = self.buffers.get(int(abuf_str))
        if molten is None:
            return

        self._deinit_buffer(molten)

    @pynvim.function("MoltenOnExitPre", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def function_on_exit_pre(self, _: Any) -> None:
        self._deinitialize()

    @pynvim.function("MoltenTick", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def function_molten_tick(self, _: Any) -> None:
        self._initialize_if_necessary()

        molten = self._get_molten(False)
        if molten is None:
            return

        molten.tick()

    @pynvim.function("MoltenUpdateInterface", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def function_update_interface(self, _: Any) -> None:
        self._update_interface()

    @pynvim.function("MoltenOnCursorMoved", sync=True)
    @nvimui
    def function_on_cursor_moved(self, _) -> None:
        self._on_cursor_moved()

    @pynvim.function("MoltenOnWinScrolled", sync=True)
    @nvimui
    def function_on_win_scrolled(self, _) -> None:
        self._on_cursor_moved(scrolled=True)

    @pynvim.function("MoltenOperatorfunc", sync=True)
    @nvimui
    def function_molten_operatorfunc(self, args) -> None:
        if not args:
            return

        kind = args[0]

        _, lineno_begin, colno_begin, _ = self.nvim.funcs.getpos("'[")
        _, lineno_end, colno_end, _ = self.nvim.funcs.getpos("']")

        if kind == "line":
            colno_begin = 1
            colno_end = -1
        elif kind == "char":
            pass
        else:
            raise MoltenException(f"this kind of selection is not supported: '{kind}'")

        span = (
            (
                lineno_begin - 1,
                min(colno_begin, len(self.nvim.funcs.getline(lineno_begin))) - 1,
            ),
            (
                lineno_end - 1,
                min(colno_end, len(self.nvim.funcs.getline(lineno_end))),
            ),
        )

        self._do_evaluate(span)

    @pynvim.function("MoltenDefineCell", sync=True)
    def function_molten_define_cell(self, args: List[int]) -> None:
        if not args:
            return

        self._initialize_if_necessary()
        molten = self._get_molten(True)
        assert molten is not None
        assert self.canvas is not None

        start = args[0]
        end = args[1]
        bufno = self.nvim.current.buffer.number
        span = Span(
            DynamicPosition(self.nvim, self.extmark_namespace, bufno, start - 1, 0),
            DynamicPosition(self.nvim, self.extmark_namespace, bufno, end - 1, -1),
        )
        molten.outputs[span] = OutputBuffer(self.nvim, self.canvas, self.options)
