# Molten

Molten is a fork of [Magma](https://www.github.com/dccsillag/magma-nvim), a plugin for running code interactively with the jupyter kernel. I owe a _large_ portion of the functionality of this plugin to Magma. As they say, I stand on the shoulders of giants.

https://github.com/benlubas/molten-nvim/assets/56943754/6266efa4-a6e4-46f1-8e15-96495a6b6fe8

## Features

- Send code to run asynchronously in the jupyter kernel
- Supports any language with a Jupyter Kernel (in theory, they haven't all been tested)
- See output in a floating window right below the code
- Send code from multiple buffers to the same kernel
- See output in real time, without flicker
- Python virtual environment support
- Renders images, plots, and LaTeX to the terminal
- Very customizable

## Requirements

- NeoVim 9.4+, nightly recommended
- Python 3.10+
- [image.nvim](https://github.com/3rd/image.nvim) is only required if you want to render images
- Required Python packages (can be installed in a venv. [read more](https://github.com/benlubas/molten-nvim/wiki/Virtual-Environments)):
  - [`pynvim`](https://github.com/neovim/pynvim) (for the Remote Plugin API)
  - [`jupyter_client`](https://github.com/jupyter/jupyter_client) (for interacting with Jupyter)
- Optional Python packages:
  - [`cairosvg`](https://cairosvg.org/) (for displaying SVG images with transparency)
    - If you don't need transparency, image.nvim can render svg images perfectly fine
  - [`pnglatex`](https://pypi.org/project/pnglatex/) (for displaying TeX formulas)
  - `plotly` and `kaleido` (for displaying Plotly figures)
  - `pyperclip` if you want to use `molten_copy_output`

You can run `:checkhealth` to see what you have installed.

**Note:** Python packages which are used only for the display of some specific kind of output are only imported when that output actually appears.

## Quick-start

See the [Wiki Quick-start Guide](https://www.github.com/benlubas/molten-nvim/wiki/Quick-Start-Guide)

The Wiki also contains more in depth setup information/guides.

## Usage

When you execute some code, it will create a _cell_. You can recognize a cell because it will be highlighted when your cursor is in it.

A cell is delimited using two extmarks (see `:h api-extended-marks`), so each cell will adjust when editing
text within it's boundaries.

When your cursor is in a cell (i.e., you have an _active cell_), a floating window may be shown below the cell, reporting output. This is the _display window_, or _output window_. (To see more about whether a window is shown or not, see `:MoltenShowOutput` and `g:molten_auto_open_output`). When you cursor is not in any cell, no cell is active.

The active cell is chosen from newest to oldest. That means that you can have a cell within another cell, and if the one within is newer, then that one will be selected. (Same goes for merely overlapping cells).

The output window has a header, containing the execution count and execution state (i.e., whether the cell is waiting to be run, running, has finished successfully or has finished with an error). Below the header output is shown.

Jupyter provides a rich set of outputs. To see what we can currently handle, see [Output Chunks](#output-chunks).

### Commands

 Molten provides a bunch of user commands as an interface to the user. It is recommended to map most of them to keys, as explained in [Keybindings](#keybindings).

Here is a list of the commands and their arguments. Args in `[]` are optional, args in `""` are
literal.

| Command                   | Arguments             | Description                        |
|---------------------------|-----------------------|------------------------------------|
| `MoltenInit`              | `["shared"] [kernel]` | Initialize a kernel for the current buffer. If `shared` is passed as the first value, this buffer will use an already running kernel. If no kernel is given, prompts the user. |
| `MoltenDeinit`            | none                  | De-initialize the current buffer's runtime and molten instance. (called automatically on vim close/buffer unload) |
| `MoltenEvaluateLine`      | none                  | Evaluate the current line |
| `MoltenEvaluateVisual`    | none                  | Evaluate the visual selection (**cannot be called with a range!**) |
| `MoltenEvaluateOperator`  | none                  | Evaluate text selected by the following operator. see [keymaps](#keymaps) for useage |
| `MoltenReevaluateCell`    | none                  | Re-evaluate the active cell (including new code) |
| `MoltenDelete`            | none                  | Delete the active cell (does nothing if there is no active cell) |
| `MoltenShowOutput`        | none                  | Shows the output window for the active cell |
| `MoltenHideOutput`        | none                  | Hide currently open output window |
| `MoltenEnterOutput`       | none                  | Move into the active cell's output window. Opens but does not enter the output if it's not open. **must be called with `noautocmd`** (see [keymaps](#keymaps) for example) |
| `MoltenInterrupt`         | none                  | Sends a keyboard interrupt to the kernel which stops any currently running code. (does nothing if there's no current output) |
| `MoltenRestart`           | `[!]`                 | Shuts down a restarts the current kernel. Deletes all outputs if used with a bang |
| `MoltenSave`              | `[path]`              | Save the current cells and evaluated outputs into a JSON file. When path is specified, save the file to `path`, otherwise save to `g:molten_save_path` |
| `MoltenLoad`              | `["shared"] [path]`   | Loads cell locations and output from a JSON file generated by `MoltenSave`. path functions the same as `MoltenSave`. If `shared` is specified, the buffer shares an already running kernel. |

## Keybindings

The commands above should be mapped to keys for the best experience. There are more detailed setups
in the [Wiki](https://github.com/benlubas/molten-nvim/wiki), but here are some example bindings.
Pay attention to `MoltenEvaluateVisual` and `MoltenEnterOutput`, as they need to be run in...odd
ways.

### Example Run Binds

```lua
vim.keymap.set("n", "<localleader>R", ":MoltenEvaluateOperator<CR>",
    { silent = true, noremap = true, desc = "run operator selection" })
vim.keymap.set("n", "<localleader>rl", ":MoltenEvaluateLine<CR>",
    { silent = true, noremap = true, desc = "evaluate line" })
vim.keymap.set("n", "<localleader>rc", ":MoltenReevaluateCell<CR>",
    { silent = true, noremap = true, desc = "re-evaluate cell" })
vim.keymap.set("v", "<localleader>r", ":<C-u>MoltenEvaluateVisual<CR>gv",
    { silent = true, noremap = true, desc = "evaluate visual selection" })
```

### Other example mappings

```lua
vim.keymap.set("n", "<localleader>rd", ":MoltenDelete<CR>",
    { silent = true, noremap = true, desc = "molten delete cell" })
vim.keymap.set("n", "<localleader>oh", ":MoltenHideOutput<CR>",
    { silent = true, noremap = true, desc = "hide output" })
vim.keymap.set("n", "<localleader>os", ":noautocmd MoltenEnterOutput<CR>",
    { silent = true, noremap = true, desc = "show/enter output" })
```

## Configuration

Configuration is done with variables. Below you'll find a table of all the potential configuration
variable, their values, and a brief description.

**the default value is wrapped in `()`**

| Variable                                      | Values                                                      | Description                                |
|----------------------                         |-------------------                                          |--------------------------------------------|
| `g:molten_auto_open_output`                   | (`true`) \| `false`                                         | Automatically open the output window when your cursor moves over a cell |
| `g:molten_copy_output`                        | `true` \| (`false`)                                         | Copy evaluation output to clipboard automatically (requires [`pyperclip`](#requirements))|
| `g:molten_enter_output_behavior`              | (`"open_then_enter"`) \| `"open_and_enter"` \| `"no_open`   | The behavior of [MoltenEnterOutput](#moltenenteroutput) |
| `g:molten_image_provider`                     | (`"none"`) \| `"image_nvim"`                                | How image are displayed |
| `g:molten_output_crop_border`                 | (`true`) \| `false`                                         | 'crops' the bottom border of the output window when it would otherwise just sit at the bottom of the screen |
| `g:molten_output_show_more`                   | `true` \| (`false`)                                         | When the window can't display the entire contents of the output buffer, shows the number of extra lines in the window footer (requires nvim 10.0+ and a window border) |
| `g:molten_output_win_border`                  | (`{ "", "━", "", "" }`) \| any value for `border` in `:h nvim_open_win()`| Some border features will not work if you don't specify your border as a table. see border option of `:h nvim_open_win()` |
| `g:molten_output_win_cover_gutter`            | (`true`) \| `false`                                         | Should the output window cover the gutter (numbers and sign col), or not. If you change this, you probably also want to change `molten_output_win_style` |
| `g:molten_output_win_hide_on_leave`           | (`true`) \| `false`                                         | After leaving the output window (via `:q` or switching windows), do not attempt to redraw the output window |
| `g:molten_output_win_max_height`              | (`999999`) \| int                                           | Max height of the output window |
| `g:molten_output_win_max_width`               | (`999999`) \| int                                           | Max width of the output window |
| `g:molten_output_win_style`                   | (`false`) \| `"minimal"`                                    | Value passed to the `style` option in `:h nvim_open_win()` |
| `g:molten_save_path`                          | (`stdpath("data").."/molten"`) \| any path to a folder      | Where to save/load data with `:MoltenSave` and `:MoltenLoad` |
| `g:molten_use_border_highlights`              | `true` \| (`false`)                                         | When true, uses different highlights for output border depending on the state of the cell (running, done, error). see [highlights](#highlights) |
| `g:molten_wrap_output`                        | `true` \| (`false`)                                         | Wrap text in output windows |
| [DEBUG] `g:molten_show_mimetype_debug`        | `true` \| (`false`)                                         | Before any non-iostream output chunk, the mime-type for that output chunk is shown. Meant for debugging/plugin devlopment |


## Highlights

You can change highlights like so:

```lua
-- see :h nvim_set_hl for the values of opts
-- I would recommend using `link` to link the values to colors from your color scheme
vim.api.nvim_set_hl(0, "MoltenOutputBorder", { opts })
```

Here is a complete list of the highlight groups that Molten uses, and their default values

- `MoltenOutputBorder` = `FloatBorder`: default border
- `MoltenOutputBorderFail` = `MoltenOutputBorder`: border of a failed output window
- `MoltenOutputBorderSuccess` = `MoltenOutputBorder`: border of a successfully run output window
- `MoltenOutputWin` = `NormalFloat`: the innards of the output window
- `MoltenOutputWinNC` = `MoltenOutputWin`: a "Non-Current" output window
- `MoltenOutputFooter` = `FloatFooter`: the "x more lines" text
- `MoltenCell` = `CursorLine`: applied to code that makes up a cell

## Autocommands

We provide some `User` autocommands (see `:help User`) for further customization. They are:

- `MoltenInitPre`: runs right before `MoltenInit` initialization happens for a buffer
- `MoltenInitPost`: runs right after `MoltenInit` initialization happens for a buffer
- `MoltenDeinitPre`: runs right before `MoltenDeinit` de-initialization happens for a buffer
- `MoltenDeinitPost`: runs right after `MoltenDeinit` de-initialization happens for a buffer

<details>
  <summary>Lua Usage</summary>

There isn't very good documentation (at the time of writing) on using User Autocommands in lua, so
here is an example of attaching molten specific mappings to the buffer after initialization

```lua
vim.api.nvim_create_autocmd("User", {
  pattern = "MoltenInitPost",
  callback = function()
    vim.keymap.set("v", "<localleader>r", ":<C-u>MoltenEvaluateVisual<CR>gv",
      { desc = "execute visual selection", buffer = true, silent = true })
    -- more mappings here
  end,
})
```

Similarly, you could remove these mappings on `MoltenDeinitPost`

</details>

## Functions

### MoltenEvaluateRange

There is a provided function `MoltenEvaluateRange(start_line, end_line)` which evaluates the code
between the given line numbers (inclusive). This is intended for use in scripts.

<details>
  <summary>Example Usage</summary>

```lua
vim.fn.MoltenEvaluateRange(1, 23)
```

</details>

### MoltenUpdateOption

Because Molten is a remote plugin, options are loaded and cached at initialization. This avoids
making an unnecessary number of RPC calls if we were to fetch configuration values every time we
needed to use them. This comes with the trade-off of not being able to update config values on the
fly... can you see where this is going

This function lets you update a configuration value after initialization, and the new value will
take effect immediately.

<details>
  <summary>Example Usage</summary>

```lua
-- these are the same!
vim.fn.MoltenUpdateOption("auto_open_output", true)
vim.fn.MoltenUpdateOption("molten_auto_open_output", true)
```

</details>

## Extras

### Output Chunks

In the Jupyter protocol, most output-related messages provide a dictionary of mime-types which can be used to display the data. Theoretically, a `text/plain` field (i.e., plain text) is always present, so we (theoretically) always have that fallback.

Here is a list of the currently handled mime-types:

- `text/plain`: Plain text. Shown as text in the output window's buffer.
- `image/*`: Molten attempts to render any `image` mimetype by sending it to image.nvim. In theory,
this means that Molten can handle any image format that ImageMagick supports, though I've only
tested common formats
- `application/vnd.plotly.v1+json`: A Plotly figure. Rendered into a PNG with [Plotly](https://plotly.com/python/) + [Kaleido](https://github.com/plotly/Kaleido)
- `text/latex`: A LaTeX formula. Rendered into a PNG with [pnglatex](https://pypi.org/project/pnglatex/)

This already provides quite a bit of basic functionality, but if you find a use case for a mime-type that isn't currently supported, feel free to open an issue and/or PR!
