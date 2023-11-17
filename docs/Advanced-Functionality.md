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
