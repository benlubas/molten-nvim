This page will go over some of the more "advanced" ways you can use this plugin that aren't covered
in the other docs.

## Connecting to external kernels

Normally, Molten will launch the kernel for you, and close it for you when you exit neovim. However,
you may want to launch a kernel from somewhere else, and connect to it with Molten, and close neovim
while the kernel stays running. This is possible with Molten by specifying the connection file for
the running kernel. This is a JSON file that's printed in the console when starting a kernel with
the `jupyter kernel` command.

### Example

```bash
jupyter kernel --kernel=python3
# [KernelApp] Starting kernel 'molten'
#                             \/ this is the important part
# [KernelApp] Connection file: /home/benlubas/.local/share/jupyter/runtime/kernel-5094b45f-58e4-4fdc-9e68-baf52e7e76a9.json
# [KernelApp] To connect a client: --existing kernel-5094b45f-58e4-4fdc-9e68-baf52e7e76a9.json
# [IPKernelApp] WARNING | debugpy_stream undefined, debugging will not be enabled
```

Then, in neovim I can run the command: `:MoltenInit
/home/benlubas/.local/share/jupyter/runtime/kernel-5094b45f-58e4-4fdc-9e68-baf52e7e76a9.json` to
connect to that kernel. You can then run code on this kernel like normal. When you leave neovim, the
kernel will remain running.

You can also start the server with

```bash
jupyter console --kernel=python3 -f /tmp/your_path_here.json
```

in order to avoid having to copy paste the file path. But this requires jupyter-console to be
installed.

### Remote hosts

> [!NOTE]
> I've not tested this, but it should work

It's also possible to use this method to connect to remove jupyter kernels.

On the remote machine run:

```bash
jupyter console --kernel julia-1.7 --ip 1.2.3.4 -f /tmp/remote-julia.json
```

Again, you can also use `jupyter kernel --kernel=<kernel_name>` but the file path will be a lot
longer

Locally run:

```bash
scp 1.2.3.4:/tmp/remote-julia.json /tmp/remote-julia.json
```

And finally run `:MoltenInit /tmp/remote-julia.json` in neovim.

## Importing/Exporting Outputs to/from ipynb files

> [!NOTE]
> These commands are considered experimental, and while they work well enough to be used, there are
> likely still bugs. If you find one, don't hesitate to create an issue.

In-depth on:
- `:MoltenExportOutput`
- `:MoltenImportOutput`

These commands are intended for use with tools like Quarto, or Jupytext, which convert notebooks to
plaintext, but they're implemented in such a way that the plaintext file format shouldn't matter, as
long as the code contents of the cells match.

### Usage

`:MoltenExportOutput` will create a copy of the notebook, prepended with "copy-of-", while
`:MoltenExportOutput!` will overwrite the existing notebook (with an identical one that just has new
outputs). Existing outputs are deleted (only for the cells that you export).

`:MoltenImportOutput` will import outputs from a notebook file so you can view them in neovim. It
requires a running kernel.

You can specify a file path as the first argument. By default, Molten looks for an existing notebook
with the same name in the same spot. For example, when editing `/path/to/file.md` the default path
is `/path/to/file.ipynb`. If you call `:MoltenExportOutput! /other/file.ipynb`
then Molten will add outputs to `/other/file.ipynb` (`/other/file.ipynb` must already exist).

If there are multiple kernels attached to the buffer when either command is called, you will be
prompted for which kernel to use. You can only export one kernels output at a time, and you can only
import outputs to one kernel at a time.

There is nothing stopping you from exporting outputs from multiple kernels to the same notebook if
you would like.

### Bailing

The export will bail if there is a Molten cell with output that doesn't have a corresponding cell in
the notebook. **Cells are searched for in order.**

If your export is failing, it's probably b/c your notebook and plaintext representation got out of
sync with each other.

Imports do not bail in the same sense because they're fairly harmless. If you accidentally import
an output from the wrong notebook, no data is lost, so molten will let it happen. Molten reports the
number of cells imported, so if that number looks wrong, your import didn't quite work out for some
reason.


### Cell Matching

Cells are matched differently for imports vs exports. We're kinda forced to do this.

#### exports

For exports, cells are matched by code content and **comments are ignored**. As a result, **if you
have two or more code cells that have the same code content, and only the second one has output,
molten will export that output to the first cell in the notebook**.

To avoid this, just don't create cells that are identical. If you must, just execute both before
exporting, they will be correctly lined up.

#### imports

Cells are matched as plaintext, line by line, sequentially. This works pretty well, but results in
quarto cells not being "full" as the metadata comments are not matched. Additionally, markdown text
that is exactly the same as a code cell and that comes before the code cell, will get the output
instead of the code cell (but this is _rare_).
