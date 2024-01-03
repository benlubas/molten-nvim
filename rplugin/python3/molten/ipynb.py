from typing import Dict
from pynvim.api import Buffer, Nvim
from molten.code_cell import CodeCell
from molten.moltenbuffer import MoltenKernel
import os
from molten.outputbuffer import OutputBuffer
from molten.outputchunks import Output, OutputStatus, to_outputchunk
from molten.position import DynamicPosition

from molten.utils import MoltenException, notify_error, notify_info, notify_warn

NOTEBOOK_VERSION = 4


def get_default_import_export_file(nvim: Nvim, buffer: Buffer) -> str:
    # WARN: this is string containment checking, not array containment checking.
    if "nofile" in buffer.options["buftype"]:
        raise MoltenException("Buffer does not correspond to a file")

    file_name = nvim.funcs.expand("%")
    cwd = nvim.funcs.getcwd()
    full_path = os.path.join(cwd, file_name)
    return f"{os.path.splitext(full_path)[0]}.ipynb"


def import_outputs(nvim: Nvim, kernel: MoltenKernel, filepath: str):
    """Import outputs from an .ipynb file with the given name"""
    import nbformat

    if not filepath.endswith(".ipynb"):
        filepath += ".ipynb"

    if not os.path.exists(filepath):
        notify_warn(nvim, f"Cannot import from file: {filepath} because it does not exist.")
        return

    buf_line = 0
    buf = nvim.current.buffer
    buffer_contents = buf[:]
    nb = nbformat.read(filepath, as_version=NOTEBOOK_VERSION)

    molten_outputs: Dict[CodeCell, Output] = {}

    for cell in nb["cells"]:
        if cell["cell_type"] != "code" or "outputs" not in cell:
            continue

        nb_contents = cell["source"].split("\n")
        nb_line = 0
        while buf_line < len(buffer_contents):
            if len(nb_contents) == 0:
                break  # out of while loop
            if nb_contents[nb_line] != buffer_contents[buf_line]:
                # move on to the next buffer line, but reset the nb_line
                nb_line = 0
                buf_line += 1
                continue

            if nb_line >= len(nb_contents) - 1:
                if len(cell["outputs"]) == 0:
                    buf_line += 1
                    break
                # we're done. This is a match, we'll create the output
                output = Output(cell["execution_count"])
                output.old = True
                for output_data in cell["outputs"]:
                    if output_data.get("output_type") == "stream":
                        output.chunks.append(
                            to_outputchunk(
                                nvim,
                                kernel.runtime._alloc_file,
                                { "text/plain": output_data.get("text") },
                                output_data.get("metadata"),
                                kernel.options,
                            )
                        )
                    else:
                        output.chunks.append(
                            to_outputchunk(
                                nvim,
                                kernel.runtime._alloc_file,
                                output_data.get("data"),
                                output_data.get("metadata"),
                                kernel.options,
                            )
                        )
                start = DynamicPosition(
                    nvim,
                    kernel.extmark_namespace,
                    buf.number,
                    buf_line - (len(nb_contents) - 1),
                    0,
                )
                end = DynamicPosition(
                    nvim, kernel.extmark_namespace, buf.number, buf_line, len(buf[buf_line])
                )
                code_cell = CodeCell(nvim, start, end)
                molten_outputs[code_cell] = output
                nb_line = 0
                buf_line += 1
                break  # out of the while loop

            buf_line += 1
            nb_line += 1

    failed = 0
    for span, output in molten_outputs.items():
        if kernel.try_delete_overlapping_cells(span):
            kernel.outputs[span] = OutputBuffer(
                kernel.nvim,
                kernel.canvas,
                kernel.extmark_namespace,
                kernel.options,
            )
            output.status = OutputStatus.DONE
            kernel.outputs[span].output = output
            kernel.update_interface()
        else:
            failed += 1

    loaded = len(molten_outputs) - failed

    if len(molten_outputs) == 0:
        notify_warn(nvim, "No cell outputs to import")
    elif loaded > 0:
        notify_info(nvim, f"Successfully loaded {loaded} outputs cells")
    if failed > 0:
        notify_error(
            nvim, f"Failed to load output for {failed} running cell that would be overridden"
        )


def export_outputs(nvim: Nvim, kernel: MoltenKernel, filepath: str, overwrite: bool):
    """Export outputs of the current file/kernel to a .ipynb file with the given name."""
    import nbformat

    if not filepath.endswith(".ipynb"):
        filepath += ".ipynb"

    if not os.path.exists(filepath):
        notify_warn(nvim, f"Cannot export to file: {filepath} because it does not exist.")
        return

    nb = nbformat.read(filepath, as_version=NOTEBOOK_VERSION)

    molten_cells = sorted(kernel.outputs.items(), key=lambda x: x[0])

    if len(molten_cells) == 0:
        notify_warn(nvim, "No cell outputs to export")
        return

    nb_cells = list(filter(lambda x: x["cell_type"] == "code", nb["cells"]))
    nb_index = 0
    lang = kernel.runtime.kernel_manager.kernel_spec.language  # type: ignore
    for mcell in molten_cells:
        matched = False
        while nb_index < len(nb_cells):
            code_cell, output = mcell
            nb_cell = nb_cells[nb_index]
            nb_index += 1

            if compare_contents(nvim, nb_cell, code_cell, lang):
                matched = True
                outputs = [
                    nbformat.v4.new_output(
                        chunk.output_type,
                        chunk.jupyter_data,
                        **chunk.extras,
                    )
                    if chunk.jupyter_metadata is None
                    else nbformat.v4.new_output(
                        chunk.output_type,
                        chunk.jupyter_data,
                        metadata=chunk.jupyter_metadata,
                        **chunk.extras,
                    )
                    for chunk in output.output.chunks
                ]
                nb_cell["outputs"] = outputs
                nb_cell["execution_count"] = output.output.execution_count
                break  # break out of the while loop

        if not matched:
            notify_error(
                nvim,
                f"No cell matching cell at line: {mcell[0].begin.lineno + 1} in notebook: {filepath}. Bailing.",
            )
            return

    if overwrite:
        write_to = filepath
    else:
        head, tail = os.path.split(filepath)
        write_to = f"{head}/copy-of-{tail}"

    notify_info(nvim, f"Exporting {len(molten_cells)} cell output(s) to {write_to}")
    nbformat.write(nb, write_to)


def compare_contents(nvim: Nvim, nb_cell, code_cell: CodeCell, lang: str) -> bool:
    molten_contents = code_cell.get_text(nvim)
    nvim.exec_lua("_remove_comments = require('remove_comments').remove_comments")
    clean_nb = nvim.lua._remove_comments(nb_cell["source"] + "\n", lang)
    clean_molten = nvim.lua._remove_comments(molten_contents + "\n", lang)
    return clean_nb == clean_molten
