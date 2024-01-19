from typing import Type, Optional, Dict, Any
import os
from pynvim import Nvim

from pynvim.api import Buffer
from molten.code_cell import CodeCell
from molten.position import DynamicPosition

from molten.utils import MoltenException
from molten.options import MoltenOptions
from molten.outputchunks import OutputStatus, Output, to_outputchunk
from molten.outputbuffer import OutputBuffer
from molten.moltenbuffer import MoltenKernel


class MoltenIOError(Exception):
    @classmethod
    def assert_has_key(
        cls, data: Dict[str, Any], key: str, type_: Optional[Type[Any]] = None
    ) -> Any:
        if key not in data:
            raise cls(f"Missing key: {key}")
        value = data[key]
        if type_ is not None and not isinstance(value, type_):
            raise cls(
                f"Incorrect type for key '{key}': expected {type_.__name__}, \
                got {type(value).__name__}"
            )
        return value


def get_default_save_file(options: MoltenOptions, buffer: Buffer) -> str:
    # XXX: this is string containment checking. Beware.
    if "nofile" in buffer.options["buftype"]:
        raise MoltenException("Buffer does not correspond to a file")

    mangled_name = buffer.name.replace("%", "%%").replace("/", "%")

    return os.path.join(options.save_path, mangled_name + ".json")


def load(nvim: Nvim, moltenbuffer: MoltenKernel, nvim_buffer: Buffer, data: Dict[str, Any]) -> None:
    MoltenIOError.assert_has_key(data, "content_checksum", str)

    if moltenbuffer._get_content_checksum() != data["content_checksum"]:
        raise MoltenIOError("Buffer contents' checksum does not match!")

    MoltenIOError.assert_has_key(data, "cells", list)
    for cell in data["cells"]:
        MoltenIOError.assert_has_key(cell, "span", dict)
        MoltenIOError.assert_has_key(cell["span"], "begin", dict)
        MoltenIOError.assert_has_key(cell["span"]["begin"], "lineno", int)
        MoltenIOError.assert_has_key(cell["span"]["begin"], "colno", int)
        MoltenIOError.assert_has_key(cell["span"], "end", dict)
        MoltenIOError.assert_has_key(cell["span"]["end"], "lineno", int)
        MoltenIOError.assert_has_key(cell["span"]["end"], "colno", int)
        begin_position = DynamicPosition(
            moltenbuffer.nvim,
            moltenbuffer.extmark_namespace,
            nvim_buffer.number,
            cell["span"]["begin"]["lineno"],
            cell["span"]["begin"]["colno"],
        )
        end_position = DynamicPosition(
            moltenbuffer.nvim,
            moltenbuffer.extmark_namespace,
            nvim_buffer.number,
            cell["span"]["end"]["lineno"],
            cell["span"]["end"]["colno"],
            right_gravity=True,
        )
        span = CodeCell(nvim, begin_position, end_position)

        # XXX: do we really want to have the execution count here?
        #      what happens when the counts start to overlap?
        MoltenIOError.assert_has_key(cell, "execution_count", int)
        output = Output(cell["execution_count"])

        MoltenIOError.assert_has_key(cell, "status", int)
        output.status = OutputStatus(cell["status"])

        MoltenIOError.assert_has_key(cell, "success", bool)
        output.success = cell["success"]

        MoltenIOError.assert_has_key(cell, "chunks", list)
        for chunk in cell["chunks"]:
            MoltenIOError.assert_has_key(chunk, "data", dict)
            MoltenIOError.assert_has_key(chunk, "metadata", dict)
            output.chunks.append(
                to_outputchunk(
                    nvim,
                    moltenbuffer.runtime._alloc_file,
                    chunk["data"],
                    chunk["metadata"],
                    moltenbuffer.options,
                )
            )

        output.old = True
        output.status = OutputStatus.DONE

        moltenbuffer.outputs[span] = OutputBuffer(
            moltenbuffer.nvim,
            moltenbuffer.canvas,
            moltenbuffer.extmark_namespace,
            moltenbuffer.options,
        )
        moltenbuffer.outputs[span].output = output


def save(molten_kernel: MoltenKernel, nvim_buffer: int) -> Dict[str, Any]:
    """Save the current kernel state for the given buffer."""
    return {
        "version": 1,
        "kernel": molten_kernel.runtime.kernel_name,
        "content_checksum": molten_kernel._get_content_checksum(),
        "cells": [
            {
                "span": {
                    "begin": {
                        "lineno": span.begin.lineno,
                        "colno": span.begin.colno,
                    },
                    "end": {
                        "lineno": span.end.lineno,
                        "colno": span.end.colno,
                    },
                },
                "execution_count": output.output.execution_count,
                "status": output.output.status.value,
                "success": output.output.success,
                "chunks": [
                    {
                        "data": chunk.jupyter_data,
                        "metadata": chunk.jupyter_metadata,
                    }
                    for chunk in output.output.chunks
                    if chunk.jupyter_data is not None and chunk.jupyter_metadata is not None
                ],
            }
            for span, output in molten_kernel.outputs.items()
            if span.begin.bufno == nvim_buffer
        ],
    }
