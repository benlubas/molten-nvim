# Too Quick State Guide

In stark contrast to the other guide, this one will be really quick (I promise).

## Install Python deps:
- [`pynvim`](https://github.com/neovim/pynvim) (for the Remote Plugin API)
- [`jupyter_client`](https://github.com/jupyter/jupyter_client) (for interacting with Jupyter)

Make sure that neovim can find these (refer to [venv guide](Virtual-Environments) if you have
trouble)

## Install the plugin (lazy.nvim example)
```lua
{
    "benlubas/molten-nvim",
    version = "^1.0.0", -- use version <2.0.0 to avoid breaking changes
    build = ":UpdateRemotePlugins",
    init = function()
        -- this is an example, not a default. Please see the readme for more configuration options
        vim.g.molten_output_win_max_height = 12
    end,
},
```

## Simple usage

- Make sure you have a jupyter kernel available
- Open a file (ie. python file if you have a python jupyter kernel)
- `:MoltenInit`
- `:MoltenEvaluateLine`

Congrats! You've run some code with Molten!

See the README for more information about how to configure and use the plugin. See the [venv
guide](Virtual-Environments) if you don't want to install python packages globally, and see the [not
so quick start guide](Not-So-Quick-Start-Guide) for information about setting up image rendering.

> [!WARNING]
> Windows users see [the windows page](./Windows.md)
