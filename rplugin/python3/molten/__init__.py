import json
import os
from typing import Any, Dict, List, Optional, Tuple
from itertools import chain

import pynvim
from pynvim.api import Buffer
from molten.code_cell import CodeCell
from molten.images import Canvas, get_canvas_given_provider
from molten.io import MoltenIOError, get_default_save_file, load, save
from molten.moltenbuffer import MoltenKernel
from molten.options import MoltenOptions
from molten.outputbuffer import OutputBuffer
from molten.position import DynamicPosition
from molten.runtime import get_available_kernels
from molten.utils import MoltenException, notify_error, notify_info, notify_warn, nvimui
from pynvim import Nvim


@pynvim.plugin
class Molten:
    """The plugin class. Provides an interface for interacting with the plugin via vim functions,
    user commands and user autocommands.

    Invariants that must be maintained in order for this plugin to work:
    - Any CodeCell which belongs to some MoltenKernel _a_ never overlaps with any CodeCell which
      belongs to some MoltenKernel _b_.
    """

    nvim: Nvim
    canvas: Optional[Canvas]
    initialized: bool

    highlight_namespace: int
    extmark_namespace: int

    timer: Optional[int]

    options: MoltenOptions

    # list of nvim buf numbers to a list of MoltenKernels 'attached' to that buffer
    buffers: Dict[int, List[MoltenKernel]]
    # list of kernel names to the MoltenKernel object that handles that kernel
    # duplicate names are sufixed with (n)
    molten_kernels: Dict[str, MoltenKernel]

    def __init__(self, nvim: Nvim):
        self.nvim = nvim
        self.initialized = False

        self.canvas = None
        self.buffers = {}
        self.timer = None
        self.molten_kernels = {}

    def _initialize(self) -> None:
        assert not self.initialized

        self.options = MoltenOptions(self.nvim)

        self.canvas = get_canvas_given_provider(self.options.image_provider, self.nvim)
        self.canvas.init()

        self.highlight_namespace = self.nvim.funcs.nvim_create_namespace("molten-highlights")
        self.extmark_namespace = self.nvim.funcs.nvim_create_namespace("molten-extmarks")

        self.timer = self.nvim.eval("timer_start(500, 'MoltenTick', {'repeat': -1})")  # type: ignore

        self._setup_highlights()
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

    def _setup_highlights(self) -> None:
        self.nvim.exec_lua("_hl_utils = require('hl_utils')")
        hl_utils = self.nvim.lua._hl_utils
        hl_utils.set_default_highlights(self.options.hl.defaults)

    def _deinitialize(self) -> None:
        for molten_kernels in self.buffers.values():
            for molten_kernel in molten_kernels:
                molten_kernel.deinit()
        if self.canvas is not None:
            self.canvas.deinit()
        if self.timer is not None:
            self.nvim.funcs.timer_stop(self.timer)

    def guard_init(self) -> None:
        if not self.initialized:
            raise MoltenException("Molten is not initialized; run `:MoltenInit` to initialize.")

    def _initialize_if_necessary(self) -> None:
        if not self.initialized:
            self._initialize()

    def _get_current_buf_kernels(self, requires_instance: bool) -> Optional[List[MoltenKernel]]:
        maybe_molten = self.buffers.get(self.nvim.current.buffer.number)
        if requires_instance and (maybe_molten is None or len(maybe_molten) == 0):
            raise MoltenException("Molten is not initialized; run `:MoltenInit` to initialize.")
        return maybe_molten

    def _clear_interface(self) -> None:
        if not self.initialized:
            return

        for molten_kernels in self.buffers.values():
            for molten_kernel in molten_kernels:
                molten_kernel.clear_interface()
                molten_kernel.clear_open_output_windows()

        assert self.canvas is not None
        self.canvas.present()

    def _update_interface(self) -> None:
        """Called on load, show_output/hide_output and buf enter"""
        if not self.initialized:
            return

        molten_kernels = self._get_current_buf_kernels(False)
        if molten_kernels is None:
            return

        for m in molten_kernels:
            m.update_interface()

    def _on_cursor_moved(self, scrolled=False) -> None:
        if not self.initialized:
            return

        molten_kernels = self._get_current_buf_kernels(False)
        if molten_kernels is None:
            return

        for m in molten_kernels:
            m.on_cursor_moved(scrolled)

    def _initialize_buffer(self, kernel_name: str, shared=False) -> MoltenKernel:
        assert self.canvas is not None
        if shared:  # use an existing molten kernel, for a new neovim buffer
            molten = self.molten_kernels.get(kernel_name)
            if molten is not None:
                molten.add_nvim_buffer(self.nvim.current.buffer)
                self.buffers[self.nvim.current.buffer.number] = [molten]
                return molten

            notify_warn(
                self.nvim,
                f"No running kernel {kernel_name} to share. Continuing with a new kernel.",
            )

        kernel_id = kernel_name
        if self.molten_kernels.get(kernel_name) is not None:
            kernel_id = f"{kernel_name}_{len(self.molten_kernels)}"

        molten = MoltenKernel(
            self.nvim,
            self.canvas,
            self.highlight_namespace,
            self.extmark_namespace,
            self.nvim.current.buffer,
            self.options,
            kernel_name,
            kernel_id,
        )

        self.add_kernel(self.nvim.current.buffer, kernel_id, molten)
        molten._doautocmd("MoltenInitPost")

        return molten

    def add_kernel(self, buffer: Buffer, kernel_id: str, kernel: MoltenKernel):
        """Add a new MoltenKernel to be tracked by Molten.
        - Adds the new kernel to the buffer list for the given buffer
        - Adds the new kernel to the molten_kernels list, with a suffix if the name is already taken
        """
        if self.buffers.get(buffer.number) is None:
            self.buffers[buffer.number] = [kernel]
        else:
            self.buffers[buffer.number].append(kernel)

        self.molten_kernels[kernel_id] = kernel

    @pynvim.command("MoltenInit", nargs="*", sync=True, complete="file")  # type: ignore
    @nvimui  # type: ignore
    def command_init(self, args: List[str]) -> None:
        self._initialize_if_necessary()

        shared = False
        if len(args) > 0 and args[0] == "shared":
            shared = True
            args = args[1:]

        if len(args) > 0:
            kernel_name = args[0]
            self._initialize_buffer(kernel_name, shared=shared)
        else:
            PROMPT = "Select the kernel to launch:"
            available_kernels = get_available_kernels()

            if len(available_kernels) == 0:
                notify_error(self.nvim, "Unable to find any kernels to launch.")
                return

            if shared:
                # Only show kernels that are already tracked by Molten
                available_kernels = list(
                    filter(lambda x: x in self.molten_kernels.keys(), available_kernels)
                )

            if len(available_kernels) == 0:
                notify_error(
                    self.nvim,
                    "No running kernels to share. Please use :MoltenInit without the shared option.",
                )
                return

            lua = f"""
                vim.schedule_wrap(function()
                    vim.ui.select(
                        {{{", ".join(repr(x) for x in available_kernels)}}},
                        {{prompt = "{PROMPT}"}},
                        function(choice)
                            if choice ~= nil then
                                vim.schedule_wrap(function()
                                    vim.cmd("MoltenInit {'shared ' if shared else ''}" .. choice)
                                end)()
                            end
                        end
                    )
                end)()
            """
            self.nvim.exec_lua(lua, async_=False)

    def _deinit_buffer(self, molten_kernels: List[MoltenKernel]) -> None:
        # Have to copy this to get around reference issues
        for kernel in [x for x in molten_kernels]:
            kernel.deinit()
            for buf in kernel.buffers:
                self.buffers[buf.number].remove(kernel)
                if len(self.buffers[buf.number]) == 0:
                    del self.buffers[buf.number]
            del self.molten_kernels[kernel.kernel_id]

    @pynvim.command("MoltenDeinit", nargs=0, sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_deinit(self) -> None:
        self._initialize_if_necessary()

        kernels = self._get_current_buf_kernels(True)
        assert kernels is not None

        self._clear_interface()

        self._deinit_buffer(kernels)

    @pynvim.command("MoltenInfo", nargs=0, sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_info(self) -> None:
        buf = self.nvim.current.buffer.number
        buf_kernels = [x.kernel_id for x in self.buffers[buf]] if buf in self.buffers else []
        text = f"=== Molten Info ===\n"
        text += f"state: {'initialized' if self.initialized else 'uninitialized'}\n"
        text += f"available kernels: {get_available_kernels()}\n"
        if self.initialized:
            text += f"kernel(s) attached to buffer: {buf_kernels}\n"
            text += f"all running kernels: {list(self.molten_kernels.keys())}\n"

        self.nvim.out_write(text)

    def _do_evaluate(self, kernel_name: str, pos: Tuple[Tuple[int, int], Tuple[int, int]]) -> None:
        self._initialize_if_necessary()

        kernels = self._get_current_buf_kernels(True)
        assert kernels is not None

        kernel = None
        for k in kernels:
            if k.kernel_id == kernel_name:
                kernel = k
                break
        if kernel is None:
            raise MoltenException(f"Kernel {kernel_name} not found")

        bufno = self.nvim.current.buffer.number
        span = CodeCell(
            self.nvim,
            DynamicPosition(self.nvim, self.extmark_namespace, bufno, *pos[0]),
            DynamicPosition(self.nvim, self.extmark_namespace, bufno, *pos[1]),
        )

        code = span.get_text(self.nvim)

        kernel.run_code(code, span)
        # delete overlapping cells from other kernels. Maintains the invariant that all code cells
        # from different kernels are disjoint
        for k in kernels:
            if k.kernel_id != kernel.kernel_id:
                k.delete_overlapping_cells(span)

    def _do_evaluate_expr(self, kernel_name: str, expr):
        self._initialize_if_necessary()

        kernels = self._get_current_buf_kernels(True)
        assert kernels is not None

        kernel = None
        for kernel in kernels:
            if kernel.kernel_id == kernel_name:
                kernel = kernel
                break
        if kernel is None:
            raise MoltenException(f"Kernel {kernel_name} not found")

        bufno = self.nvim.current.buffer.number
        cell = CodeCell(
            self.nvim,
            DynamicPosition(self.nvim, self.extmark_namespace, bufno, 0, 0),
            DynamicPosition(self.nvim, self.extmark_namespace, bufno, 0, 0),
        )

        kernel.run_code(expr, cell)

    @pynvim.function("MoltenUpdateOption", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def function_update_option(self, args) -> None:
        self.guard_init()

        if len(args) == 2:
            option, value = args
            self.options.update_option(option, value)
        else:
            notify_error(
                self.nvim,
                f"Wrong number of arguments passed to :MoltenUpdateOption, expected 2, given {len(args)}",
            )

    @pynvim.command("MoltenEnterOutput", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_enter_output_window(self) -> None:
        molten_kernels = self._get_current_buf_kernels(True)
        assert molten_kernels is not None

        # We can do this iff we ensure that different kernels don't contain code cells that overlap
        for kernel in molten_kernels:
            kernel.enter_output()

    @pynvim.command("MoltenEvaluateArgument", nargs="*", sync=True)  # type: ignore
    @nvimui
    def commnand_molten_evaluate_argument(self, args: List[str]) -> None:
        if len(args) > 0 and args[0] in map(
            lambda x: x.kernel_id, self.buffers[self.nvim.current.buffer.number]
        ):
            self._do_evaluate_expr(args[0], " ".join(args[1:]))
        else:
            self.kernel_check("MoltenEvaluateArgument", " ".join(args), self.nvim.current.buffer)

    @pynvim.command("MoltenEvaluateVisual", nargs="*", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_evaluate_visual(self, args) -> None:
        if len(args) > 0:
            kernel = args[0]
        else:
            self.kernel_check("MoltenEvaluateVisual", "", self.nvim.current.buffer)
            return
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

        self._do_evaluate(kernel, span)

    @pynvim.function("MoltenEvaluateRange", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def evaulate_range(self, args) -> None:
        start_col, end_col = 1, 0
        kernel = None
        span = args
        if type(args[0]) == str:
            kernel = args[0]
            span = args[1:]

        if len(span) == 2:
            start_line, end_line = span
        elif len(span) == 4:
            start_line, end_line, start_col, end_col = span
        else:
            notify_error(self.nvim, f"Invalid args passed to MoltenEvaluateRange. Got: {args}")
            return

        if not kernel:
            self.kernel_check(
                "call MoltenEvaluateRange('",
                f"', {start_line}, {end_line}, {start_col}, {end_col})",
                self.nvim.current.buffer,
            )
            return

        span = (
            (start_line - 1, start_col - 1),
            (end_line - 1, end_col - 1),
        )

        self._do_evaluate(kernel.strip(), span)

    @pynvim.command("MoltenEvaluateOperator", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_evaluate_operator(self) -> None:
        self._initialize_if_necessary()

        self.nvim.options["operatorfunc"] = "MoltenOperatorfunc"
        self.nvim.feedkeys("g@")

    @pynvim.command("MoltenEvaluateLine", nargs="*", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_evaluate_line(self, args: List[str]) -> None:
        _, lineno, _, _, _ = self.nvim.funcs.getcurpos()
        lineno -= 1

        span = ((lineno, 0), (lineno, -1))

        if len(args) > 0 and args[0]:
            self._do_evaluate(args[0], span)
        else:
            self.kernel_check("MoltenEvaluateLine", "", self.nvim.current.buffer)

    def kernel_check(
        self, command: str, command_args: str, buffer: Buffer, kernel_last=False
    ) -> None:
        """Figure out if there is more than one kernel attached to the given buffer. If there is,
        and there is prompt the user for the kernel name, and run the given command with the new
        kernel, and arguments. If there is no kernel, throw an error. If there is one kernel, use
        it"""

        def cmd(kernel_id: str):
            if kernel_last:
                return f"{command} {command_args} {kernel_id}"
            return f"{command} {kernel_id} {command_args}"

        kernels = self.buffers.get(buffer.number)
        if not kernels:
            raise MoltenException(
                "Molten has not been initialized for this buffer. Please run :MoltenInit"
            )
        elif len(kernels) == 1:
            c = cmd(kernels[0].kernel_id)
            self.nvim.command(c)
        else:
            PROMPT = "Please select a kernel:"
            available_kernels = [kernel.kernel_id for kernel in kernels]

            lua = f"""
                vim.schedule_wrap(function()
                    vim.ui.select(
                        {{{", ".join(repr(x) for x in available_kernels)}}},
                        {{prompt = "{PROMPT}"}},
                        function(choice)
                            if choice ~= nil then
                                vim.schedule_wrap(function()
                                    vim.cmd("{cmd('".. choice .."')}")
                                end)()
                            end
                        end
                    )
                end)()
            """
            self.nvim.exec_lua(lua, async_=False)

    @pynvim.command("MoltenReevaluateCell", nargs=0, sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_evaluate_cell(self) -> None:
        self._initialize_if_necessary()

        molten_kernels = self._get_current_buf_kernels(True)
        assert molten_kernels is not None

        # we can do this iff we ensure that different kernels don't contain code cells that overlap
        in_cell = False
        for kernel in molten_kernels:
            if kernel.reevaluate_cell():
                in_cell = True

        if not in_cell:
            notify_error(self.nvim, "Not in a cell")

    @pynvim.command("MoltenInterrupt", nargs="*", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_interrupt(self, args) -> None:
        if len(args) > 0:
            kernel = args[0]
        else:
            self.kernel_check("MoltenInterrupt", "", self.nvim.current.buffer)
            return

        molten_kernels = self._get_current_buf_kernels(True)
        assert molten_kernels is not None
        for molten in molten_kernels:
            if molten.kernel_id == kernel:
                molten.interrupt()
                return

        notify_error(self.nvim, f"Unable to find kernel: {kernel}")

    @pynvim.command("MoltenRestart", nargs="*", sync=True, bang=True)  # type: ignore
    @nvimui  # type: ignore
    def command_restart(self, bang: bool, args) -> None:
        if len(args) > 0:
            kernel = args[0]
        else:
            self.kernel_check(f"MoltenRestart{'!' if bang else ''}", "", self.nvim.current.buffer)
            return

        molten_kernels = self._get_current_buf_kernels(True)
        assert molten_kernels is not None

        for molten in molten_kernels:
            if molten.kernel_id == kernel:
                molten.restart(delete_outputs=bang)
                return
        notify_error(self.nvim, f"Unable to find kernel: {kernel}")

    @pynvim.command("MoltenDelete", nargs=0, sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_delete(self) -> None:
        molten_kernels = self._get_current_buf_kernels(True)
        assert molten_kernels is not None

        for molten in molten_kernels:
            if molten.current_output is not None:
                molten.delete_cell()
                return

    @pynvim.command("MoltenShowOutput", nargs=0, sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_show_output(self) -> None:
        self._initialize_if_necessary()

        molten_kernels = self._get_current_buf_kernels(True)
        assert molten_kernels is not None

        for molten in molten_kernels:
            if molten.current_output is not None:
                molten.should_show_display_window = True
                self._update_interface()
                return

    @pynvim.command("MoltenHideOutput", nargs=0, sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_hide_output(self) -> None:
        molten_kernels = self._get_current_buf_kernels(False)
        if molten_kernels is None:
            # get the current buffer, and then search for it in all molten buffers
            cur_buf = self.nvim.current.buffer
            for moltenbuf in self.buffers.values():
                # if we find it, then we know this is a molten output, and we can safely quit and
                # call hide to hide it
                output_windows = map(
                    lambda x: x.display_buf, chain(*[o.outputs.values() for o in moltenbuf])
                )
                if cur_buf in output_windows:
                    self.nvim.command("q")
                    self.nvim.command(":MoltenHideOutput")
                    return
            return

        for molten in molten_kernels:
            molten.should_show_display_window = False

        self._update_interface()

    @pynvim.command("MoltenSave", nargs="*", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_save(self, args) -> None:
        self._initialize_if_necessary()

        buf = self.nvim.current.buffer
        if len(args) > 0:
            path = args[0]
        else:
            path = get_default_save_file(self.options, buf)

        if len(args) > 1:
            kernel = args[1]
        else:
            self.kernel_check(f"MoltenSave", path, buf, kernel_last=True)
            return

        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        kernels = self._get_current_buf_kernels(True)
        assert kernels is not None
        for molten in kernels:
            if molten.kernel_id == kernel:
                with open(path, "w") as file:
                    json.dump(save(molten, buf.number), file)
                break
        notify_info(self.nvim, f"Saved kernel `{kernel}` to: {path}")

    @pynvim.command("MoltenLoad", nargs="*", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_load(self, args) -> None:
        self._initialize_if_necessary()

        shared = False

        if len(args) > 0 and args[0] == "shared":
            shared = True
            args = args[1:]

        if len(args) > 0:
            path = args[0]
        else:
            path = get_default_save_file(self.options, self.nvim.current.buffer)

        if self.nvim.current.buffer.number in self.buffers:
            raise MoltenException(
                "Molten is already initialized for this buffer; MoltenLoad initializes Molten."
            )

        with open(path) as file:
            data = json.load(file)

        molten = None

        try:
            notify_info(self.nvim, f"Attempting to load from: {path}")

            MoltenIOError.assert_has_key(data, "version", int)
            if (version := data["version"]) != 1:
                raise MoltenIOError(f"Bad version: {version}")

            MoltenIOError.assert_has_key(data, "kernel", str)
            kernel_name = data["kernel"]

            molten = self._initialize_buffer(kernel_name, shared=shared)

            load(self.nvim, molten, self.nvim.current.buffer, data)

            self._update_interface()
        except MoltenIOError as err:
            if molten is not None:
                self._deinit_buffer([molten])

            raise MoltenException("Error while doing Molten IO: " + str(err))

    # Internal functions which are exposed to VimScript

    @pynvim.function("MoltenClearInterface", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def function_clear_interface(self, _: List[Any]) -> None:
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

        molten_kernels = self._get_current_buf_kernels(False)
        if molten_kernels is None:
            return

        for m in molten_kernels:
            m.tick()

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
            colno_end = 0
        elif kind == "char":
            pass
            colno_begin = min(colno_begin, len(self.nvim.funcs.getline(lineno_begin)))
            colno_end = min(colno_end, len(self.nvim.funcs.getline(lineno_end)))
        else:
            raise MoltenException(f"this kind of selection is not supported: '{kind}'")

        span = (
            (lineno_begin, colno_begin),
            (lineno_end, colno_end),
        )

        self.kernel_check(
            "call MoltenEvaluateRange('",
            f"', {span[0][0]}, {span[1][0]}, {span[0][1]}, {span[1][1]})",
            self.nvim.current.buffer,
        )

    @pynvim.function("MoltenDefineCell", sync=True)
    def function_molten_define_cell(self, args: List[int]) -> None:
        if not args:
            return

        self._initialize_if_necessary()
        molten_kernels = self._get_current_buf_kernels(True)
        assert molten_kernels is not None
        assert self.canvas is not None

        start = args[0]
        end = args[1]

        if len(args) == 3:
            kernel = args[2]
        elif len(self.buffers[self.nvim.current.buffer.number]) == 1:
            kernel = self.buffers[self.nvim.current.buffer.number][0].kernel_id
        else:
            raise MoltenException(
                "MoltenDefineCell called without a kernel argument while multiple kernels are active"
            )

        bufno = self.nvim.current.buffer.number
        span = CodeCell(
            self.nvim,
            DynamicPosition(self.nvim, self.extmark_namespace, bufno, start - 1, 0),
            DynamicPosition(self.nvim, self.extmark_namespace, bufno, end - 1, -1),
        )

        for molten in molten_kernels:
            if molten.kernel_id == kernel:
                molten.outputs[span] = OutputBuffer(
                    self.nvim, self.canvas, molten.extmark_namespace, self.options
                )
                break
