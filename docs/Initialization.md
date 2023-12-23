# Initialization

Two points. The _plugin_ is initialized on the fist action that you take that requires it. This
fetches all of the options that molten defines, and caches their values. From this point onward,
setting `vim.g.molten_...` will not work, and you need to use the `MoltenUpdateOption` function.

This is different to what I'll call "kernel initialization", where a jupyter kernel is associated to
the current buffer. This is done by the MoltenInit command.

## :MoltenInit

`:MoltenInit ["shared"] [kernel]` is the command that you run if you'd like to "initialize"
a kernel. This associates the kernel to the current buffer.

When run with no arguments, the command will list kernels that are not running, followed by kernels
that _are_ running in other buffers. The latter are prefixed with the text `(shared)`. Selecting
a kernel that looks like `(shared) python3` is the same as running the command `:MoltenInit shared
python3`.

## Auto Initialization

Some commands require a kernel attached to the buffer to work. Of these commands, some will auto
initialize (prompt the users as if `:MoltenInit` had been called, on selection, will initialize the
kernel, and then after the kernel is initialized, run the original command with the new kernel).
Here's a list of commands that will auto initialize:

- `MoltenEvaluateLine`
- `MoltenEvaluateVisual`
- `MoltenEvaluateOperator`
- `MoltenEvaluateArgument`
- `MoltenImportOutput`
