import math
import jupyter_client


def create_info_window(nvim, molten_kernels, buffers, initialized):
    buf = nvim.current.buffer.number
    info_buf = nvim.api.create_buf(False, True)
    kernel_info = jupyter_client.kernelspec.KernelSpecManager().get_all_specs()  # type: ignore

    info_buf[0] = " press q or <esc> to close this window"
    info_buf.api.add_highlight(-1, "Comment", 0, 0, -1)
    info_buf.append(["", " Molten Info"])
    info_buf.api.add_highlight(-1, "Title", len(info_buf) - 1, 0, -1)

    # Status
    if initialized:
        info_buf.append(" Initialized: true")
        info_buf.api.add_highlight(-1, "String", len(info_buf) - 1, 14, -1)
    else:
        info_buf.append(" Initialized: false")
        info_buf.api.add_highlight(-1, "Error", len(info_buf) - 1, 14, -1)

    info_buf.append("")

    # Kernel Information
    buf_kernels = [x.kernel_id for x in buffers[buf]] if buf in buffers else []
    other_buf_kernels = set(molten_kernels.keys()) - set(buf_kernels)
    other_kernels = set(kernel_info.keys()) - set(molten_kernels.keys())

    if len(buf_kernels) > 0:
        info_buf.append([f" {len(buf_kernels)} active kernel(s), attached to current buffer:", ""])
        for kernel, spec in filter(lambda x: x[0] in buf_kernels, kernel_info.items()):
            running_buffers = map(lambda x: str(x.number), molten_kernels[kernel].buffers)
            running = f"(running, bufnr: [{', '.join(running_buffers)}])"
            draw_kernel_info(info_buf, running, kernel, spec)

    if len(other_buf_kernels) > 0:
        info_buf.append(
            [f" {len(other_buf_kernels)} active kernels(s), not attached to this buffer:", ""]
        )
        for kernel, spec in filter(lambda x: x[0] in other_buf_kernels, kernel_info.items()):
            running_buffers = map(lambda x: str(x.number), molten_kernels[kernel].buffers)
            running = f"(running, bufnr: [{', '.join(running_buffers)}])"
            draw_kernel_info(info_buf, running, kernel, spec)

    if len(other_kernels) > 0:
        info_buf.append([f" {len(other_kernels)} inactive kernel(s):", ""])
        for kernel, spec in filter(lambda x: x[0] in other_kernels, kernel_info.items()):
            draw_kernel_info(info_buf, "", kernel, spec)

    nvim_width = nvim.api.get_option("columns")
    nvim_height = nvim.api.get_option("lines")
    height = math.floor(nvim_height * 0.75)
    width = math.floor(nvim_width * 0.80)

    win_opts = {
        "relative": "editor",
        "row": nvim_height / 2 - (height / 2),
        "col": nvim_width / 2 - (width / 2),
        "width": width,
        "height": height,
        "focusable": True,
        "style": "minimal",
    }

    # set keymaps
    info_buf.api.set_keymap("n", "q", ":q<CR>", {"silent": True, "noremap": True})
    info_buf.api.set_keymap("n", "<ESC>", ":q<CR>", {"silent": True, "noremap": True})

    # open the window
    _info_window = nvim.api.open_win(
        info_buf.number,
        True,
        win_opts,
    )


def draw_kernel_info(buf, running, kernel_name, spec):
    buf.append(f" Kernel: {kernel_name} {running}")
    buf.api.add_highlight(-1, "Title", len(buf) - 1, 8, 9 + len(kernel_name))
    buf.append(f"   language:     {spec['spec']['language']}")
    buf.api.add_highlight(-1, "LspInfoFiletype", len(buf) - 1, 16, -1)
    buf.append(f"   cmd:          {' '.join(spec['spec']['argv'])}")
    buf.api.add_highlight(-1, "String", len(buf) - 1, 16, -1)
    buf.append([f"   resource_dir: {spec['resource_dir']}", ""])
