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
    buf_kernels = buffers[buf] if buf in buffers else []
    other_buf_kernels = set(molten_kernels.keys()) - set(map(lambda x: x.kernel_id, buf_kernels))
    other_kernels = set(kernel_info.keys()) - set(molten_kernels.keys())

    if len(buf_kernels) > 0:
        info_buf.append([f" {len(buf_kernels)} active kernel(s), attached to current buffer:", ""])
        for m_kernel in buf_kernels:
            running_buffers = map(lambda x: str(x.number), m_kernel.buffers)
            running = f"(running, bufnr: [{', '.join(running_buffers)}])"
            spec = m_kernel.runtime.kernel_manager.kernel_spec
            draw_kernel_info(
                info_buf, running, m_kernel.kernel_id, spec.language, spec.argv, spec.resource_dir
            )

    if len(other_buf_kernels) > 0:
        info_buf.append(
            [f" {len(other_buf_kernels)} active kernels(s), not attached to this buffer:", ""]
        )
        for kernel_id in other_buf_kernels:
            m_kernel = molten_kernels[kernel_id]
            running_buffers = map(lambda x: str(x.number), m_kernel.buffers)
            running = f"(running, bufnr: [{', '.join(running_buffers)}])"
            spec = m_kernel.runtime.kernel_manager.kernel_spec
            draw_kernel_info(
                info_buf, running, m_kernel.kernel_id, spec.language, spec.argv, spec.resource_dir
            )

    if len(other_kernels) > 0:
        info_buf.append([f" {len(other_kernels)} inactive kernel(s):", ""])
        for kernel, spec in filter(lambda x: x[0] in other_kernels, kernel_info.items()):
            draw_kernel_info(
                info_buf,
                "",
                kernel,
                spec["spec"]["language"],
                spec["spec"]["argv"],
                spec["resource_dir"],
            )

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
    info_buf.api.set_keymap("n", "q", ":q<CR>", {"silent": True})
    info_buf.api.set_keymap("n", "<ESC>", ":q<CR>", {"silent": True})

    # open the window
    nvim.api.open_win(
        info_buf.number,
        True,
        win_opts,
    )


def draw_kernel_info(buf, running, kernel_name, language, argv, resource_dir):
    buf.append(f" Kernel: {kernel_name} {running}")
    buf.api.add_highlight(-1, "Title", len(buf) - 1, 8, 9 + len(kernel_name))
    buf.append(f"   language:     {language}")
    buf.api.add_highlight(-1, "LspInfoFiletype", len(buf) - 1, 16, -1)
    buf.append(f"   cmd:          {' '.join(argv)}")
    buf.api.add_highlight(-1, "String", len(buf) - 1, 16, -1)
    buf.append([f"   resource_dir: {resource_dir}", ""])
