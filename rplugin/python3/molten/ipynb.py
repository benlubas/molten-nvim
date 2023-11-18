from pynvim.api import Buffer, Nvim
from molten.code_cell import CodeCell
from molten.moltenbuffer import MoltenKernel
import os
import nbformat

from molten.utils import MoltenException, notify_error, notify_info, notify_warn

NOTEBOOK_VERSION = 4


def get_default_export_file(nvim: Nvim, buffer: Buffer) -> str:
    # WARN: this is string containment checking, not array containment checking.
    if "nofile" in buffer.options["buftype"]:
        raise MoltenException("Buffer does not correspond to a file")

    file_name = nvim.funcs.expand("%")
    cwd = nvim.funcs.getcwd()
    full_path = os.path.join(cwd, file_name)
    return f"{os.path.splitext(full_path)[0]}.ipynb"


def export_outputs(nvim: Nvim, kernel: MoltenKernel, filepath: str, overwrite: bool):
    """Export outputs of the current file/kernel to a .ipynb file with the given name."""

    if not filepath.endswith(".ipynb"):
        filepath += ".ipynb"

    if not os.path.exists(filepath):
        notify_warn(nvim, f"Cannot export to file: {filepath} because it does not exist.")
        return

    nb = nbformat.read(filepath, as_version=NOTEBOOK_VERSION)

    molten_cells = sorted(kernel.outputs.items(), key=lambda x: x[0])

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
    clean_nb = nvim.lua._remove_comments(nb_cell["source"], lang)
    clean_molten = nvim.lua._remove_comments(molten_contents + "\n", lang)
    return clean_nb == clean_molten
