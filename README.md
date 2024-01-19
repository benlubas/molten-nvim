# Molten

Molten is a fork of [Magma](https://www.github.com/dccsillag/magma-nvim), a plugin for running code
interactively with the jupyter kernel. Molten provides an excellent repl-like experience, and an
incredible notebook-like experience in neovim.

https://github.com/benlubas/molten-nvim/assets/56943754/17ae81c0-306f-4496-bce8-99286e7f21ed

## Feature Highlights

- Send code to run asynchronously in the jupyter kernel
- See output below the code in real time, without flicker, as virtual text or in a floating
window (or both)
- Renders images, plots, and LaTeX in neovim
- Send code from multiple buffers to the same kernel
- Send code from the same buffer to multiple kernels
- Supports any language with a Jupyter Kernel (in theory, they haven't all been tested)
- Python virtual environment support
- Import and Export outputs to and from jupyter notebook files

## Requirements

- NeoVim 9.4+
- Python 3.10+
- [image.nvim](https://github.com/3rd/image.nvim) is only required if you want to render images
- Required Python packages (can be installed in a venv. [read more](./docs/Virtual-Environments.md)):
  - [`pynvim`](https://github.com/neovim/pynvim) (for the Remote Plugin API)
  - [`jupyter_client`](https://github.com/jupyter/jupyter_client) (for interacting with Jupyter)
- Optional Python packages:
  - [`cairosvg`](https://cairosvg.org/) (for displaying SVG images with transparency)
    - If you don't need transparency, image.nvim can render svg images perfectly fine
  - [`pnglatex`](https://pypi.org/project/pnglatex/) (for displaying TeX formulas)
  - `plotly` and `kaleido` (for displaying Plotly figures)
  - `pyperclip` if you want to use `molten_copy_output`
  - `nbformat` for importing and exporting output to jupyter notebooks files

You can run `:checkhealth` to see what you have installed.

**Note:** Optional python packages are only imported when they're used.

## Quick-start

- For the impatient: [Probably Too Quick Start Guide](./docs/Probably-Too-Quick-Start-Guide.md)
- For everyone else: [Not So Quick Start Guide](./docs/Not-So-Quick-Start-Guide.md)
- Windows users also read [this](./docs/Windows.md)
- NixOS users can checkout [this](./docs/NixOS.md)

Configuration information is located [further down](#configuration) in this README.

To setup molten for editing Jupyter Notebook files, see [Notebook Setup](./docs/Notebook-Setup.md).

## Usage

Start by initializing a kernel. This kernel will get a _kernel_id_ which is most commonly just the
name of the kernel. If you try to initialize two kernels with the same name, the second one will be
named `kernel_name_n` where `n` is the total number of kernels that are already initialized.

You execute code by sending it to a kernel, specified by its _kernel_id_ (this is handled
automatically if there is only one option).

When you execute some code, it will create a _cell_. You can recognize a cell because it will be
highlighted when your cursor is in it.

A cell is delimited using two extmarks (see `:h api-extended-marks`), so each cell will adjust when
editing text within its boundaries.

When your cursor is in a cell (i.e., you have an _active cell_), a floating window may be shown
below the cell, reporting output. This is the _floating output window_. (To see more about whether
a window is shown or not, see `:MoltenShowOutput` and `g:molten_auto_open_output`). When you cursor
is not in any cell, no cell is active. When your cursor leaves a cell, its floating output window
will close.

Output may also be displayed as virtual text below a cell. Virtual text output will stay there until
you re-run the cell or delete the cell.

Overlapping cells are not allowed. If you create an overlapping cell, the old cell will be deleted.

The output window has a header, containing the execution count and execution state (i.e., whether
the cell is waiting to be run, running, has finished successfully or has finished with an error).
Below the header, output is shown.

Jupyter provides a rich set of outputs. To see what we can currently handle, see [Output
Chunks](#output-chunks).

### Commands

These user commands are the main interface to the plugin. It is recommended to map most of them to
keys, as explained in [Keybindings](#keybindings).

Here is a list of the commands and their arguments. Args in `[]` are optional, args in `""` are
literal.

When the `kernel` argument is specified as optional the command behaves in the following way:

- if the kernel is specified, send the code to that kernel
- else if there is only one active kernel for the current buffer, send the code to that kernel
- else if there is more than one active kernel for the current buffer, prompt the user for the
  kernel

[Some](./docs/Initialization.md) commands will prompt for a kernel when they require one, but no
kernel is attached to the buffer. This is configurable with the `molten_auto_init_behavior` option.

| Command                   | Arguments             | Description                        |
|-----------------------    |----------------       |------------------------------------|
| `MoltenInfo`              | none                  | Show information about the state of the plugin, initialization status, available kernels, and running kernels |
| `MoltenInit`              | `["shared"] [kernel]` | Initialize a kernel for the current buffer. If `shared` is passed as the first value, this buffer will use an already running kernel. If no kernel is given, prompts the user. |
| `MoltenDeinit`            | none                  | De-initialize the current buffer's runtime and molten instance. (called automatically on vim close/buffer unload) |
| `MoltenGoto`              | `[n]`                 | Go to the `n`th code cell `n` defaults to 1 (1 indexed) |
| `MoltenNext`              | `[n]`                 | Go to the next code cell, or jump `n` code cells `n` defaults to 1. Values wrap. Negative values move backwards |
| `MoltenPrev`              | `[n]`                 | like `Next` but backwards |
| `MoltenEvaluateLine`      | `[kernel]`            | Evaluate the current line |
| `MoltenEvaluateVisual`    | `[kernel]`            | Evaluate the visual selection (**cannot be called with a range!**) |
| `MoltenEvaluateOperator`  | `[kernel]`            | Evaluate text selected by the following operator. see [Keybindings](#keybindings) for useage |
| `MoltenEvaluateArgument`  | `[kernel] code`       | Evaluate given code in the given kernel |
| `MoltenReevaluateCell`    | none                  | Re-evaluate the active cell (including new code) with the same kernel that it was originally evaluated with |
| `MoltenDelete`            | none                  | Delete the active cell (does nothing if there is no active cell) |
| `MoltenShowOutput`        | none                  | Shows the output window for the active cell |
| `MoltenHideOutput`        | none                  | Hide currently open output window |
| `MoltenEnterOutput`       | none                  | Move into the active cell's output window. Opens but does not enter the output if it's not open. **must be called with `noautocmd`** (see [Keybindings](#keybindings) for example) |
| `MoltenInterrupt`         | `[kernel]`            | Sends a keyboard interrupt to the kernel which stops any currently running code. (does nothing if there's no current output) |
| `MoltenOpenInBrowser`     | none                  | Open the current output in the browser. **Currently this only supports cells with `'text/html'` outputs**, configured with `molten_auto_open_html_in_browser` and `molten_open_cmd` |
| `MoltenRestart`           | `[!] [kernel]`        | Shuts down a restarts the kernel. Deletes all outputs if used with a bang |
| `MoltenSave`              | `[path] [kernel]`     | Save the current cells and evaluated outputs into a JSON file. When path is specified, save the file to `path`, otherwise save to `g:molten_save_path`. _currently only saves one kernel per file_ |
| `MoltenLoad`              | `["shared"] [path]`   | Loads cell locations and output from a JSON file generated by `MoltenSave`. path functions the same as `MoltenSave`. If `shared` is specified, the buffer shares an already running kernel. |
| `MoltenExportOutput`      | `[!] [path] [kernel]` | Export outputs from the current buffer and kernel to a jupyter notebook (`.ipynb`) at the given path. [read more](./docs/Advanced-Functionality.md) |
| `MoltenImportOutput`      | `[path] [kernel]`     | Import outputs from a jupyter notebook (`.ipynb`). [read more](./docs/Advanced-Functionality.md) |

## Keybindings

The commands above should be mapped to keys for the best experience.

Pay attention to `MoltenEvaluateVisual` and `MoltenEnterOutput`, as they need to be run in...odd
ways.

### Minimum Suggested

```lua
vim.keymap.set("n", "<localleader>mi", ":MoltenInit<CR>",
    { silent = true, desc = "Initialize the plugin" })
vim.keymap.set("n", "<localleader>e", ":MoltenEvaluateOperator<CR>",
    { silent = true, desc = "run operator selection" })
vim.keymap.set("n", "<localleader>rl", ":MoltenEvaluateLine<CR>",
    { silent = true, desc = "evaluate line" })
vim.keymap.set("n", "<localleader>rr", ":MoltenReevaluateCell<CR>",
    { silent = true, desc = "re-evaluate cell" })
vim.keymap.set("v", "<localleader>r", ":<C-u>MoltenEvaluateVisual<CR>gv",
    { silent = true, desc = "evaluate visual selection" })
```

### Other example mappings

```lua
vim.keymap.set("n", "<localleader>rd", ":MoltenDelete<CR>",
    { silent = true, desc = "molten delete cell" })
vim.keymap.set("n", "<localleader>oh", ":MoltenHideOutput<CR>",
    { silent = true, desc = "hide output" })
vim.keymap.set("n", "<localleader>os", ":noautocmd MoltenEnterOutput<CR>",
    { silent = true, desc = "show/enter output" })
```

## Configuration

Configuration is done with variables. Below you'll find a table of all the potential configuration
variable, their values, and a brief description.

**the default value is wrapped in `()`**

| Variable                                      | Values                                                      | Description                                |
|----------------------                         |-------------------                                          |--------------------------------------------|
| `g:molten_auto_init_behavior`                 | `"raise"` \| (`"init"`)                                     | When set to "raise" commands which would otherwise ask for a kernel when they're run without a running kernel will instead raise an exception. Useful for other plugins that want to use `pcall` and do their own error handling |
| `g:molten_auto_open_html_in_browser`          | `true` \| (`false`)                                         | Automatically open HTML outputs in a browser. related: `molten_open_cmd` |
| `g:molten_auto_open_output`                   | (`true`) \| `false`                                         | Automatically open the floating output window when your cursor moves into a cell |
| `g:molten_copy_output`                        | `true` \| (`false`)                                         | Copy evaluation output to clipboard automatically (requires [`pyperclip`](#requirements))|
| `g:molten_enter_output_behavior`              | (`"open_then_enter"`) \| `"open_and_enter"` \| `"no_open"`  | The behavior of [MoltenEnterOutput](#moltenenteroutput) |
| `g:molten_image_provider`                     | (`"none"`) \| `"image.nvim"`                                | How images are displayed |
| `g:molten_open_cmd`                           | (`nil`) \| Any command                                      | Defaults to `xdg-open` on Linux, `open` on Darwin, and `start` on Windows. But you can override it to whatever you want. The command is called like: `subprocess.run([open_cmd, filepath])` |
| `g:molten_output_crop_border`                 | (`true`) \| `false`                                         | 'crops' the bottom border of the output window when it would otherwise just sit at the bottom of the screen |
| `g:molten_output_show_more`                   | `true` \| (`false`)                                         | When the window can't display the entire contents of the output buffer, shows the number of extra lines in the window footer (requires nvim 10.0+ and a window border) |
| `g:molten_output_virt_lines`                  | `true` \| (`false`)                                         | Pad the main buffer with virtual lines so the floating window doesn't cover anything while it's open |
| `g:molten_output_win_border`                  | (`{ "", "━", "", "" }`) \| any value for `border` in `:h nvim_open_win()`| Some border features will not work if you don't specify your border as a table. see border option of `:h nvim_open_win()` |
| `g:molten_output_win_cover_gutter`            | (`true`) \| `false`                                         | Should the output window cover the gutter (numbers and sign col), or not. If you change this, you probably also want to change `molten_output_win_style` |
| `g:molten_output_win_hide_on_leave`           | (`true`) \| `false`                                         | After leaving the output window (via `:q` or switching windows), do not attempt to redraw the output window |
| `g:molten_output_win_max_height`              | (`999999`) \| int                                           | Max height of the output window |
| `g:molten_output_win_max_width`               | (`999999`) \| int                                           | Max width of the output window |
| `g:molten_output_win_style`                   | (`false`) \| `"minimal"`                                    | Value passed to the `style` option in `:h nvim_open_win()` |
| `g:molten_save_path`                          | (`stdpath("data").."/molten"`) \| any path to a folder      | Where to save/load data with `:MoltenSave` and `:MoltenLoad` |
| `g:molten_tick_rate`                          | (`500`) \| `int`                                            | How often (in ms) we poll the kernel for updates. Determines how quickly the ui will update, if you want a snappier experience, you can set this to 150 or 200 |
| `g:molten_use_border_highlights`              | `true` \| (`false`)                                         | When true, uses different highlights for output border depending on the state of the cell (running, done, error). see [highlights](#highlights) |
| `g:molten_limit_output_chars`                 | (`1000000`) \| int                                          | Limit on the number of chars in an output. If you're lagging your editor with too much output text, decrease it |
| `g:molten_virt_lines_off_by_1`                | `true` \| (`false`)                                         | Allows the output window to cover exactly one line of the regular buffer when `output_virt_lines` is true, also effects where `virt_text_output` is displayed. (useful for running code in a markdown file where that covered line will just be \`\`\`) |
| `g:molten_virt_text_output`                   | `true` \| (`false`)                                         | When true, show output as virtual text below the cell, virtual text stays after leaving the cell. When true, output window doesn't open automatically on run. Effected by `virt_lines_off_by_1` |
| `g:molten_virt_text_max_lines`                | (`12`) \| `int`                                             | Max height of the virtual text |
| `g:molten_wrap_output`                        | `true` \| (`false`)                                         | Wrap output text |
| [DEBUG] `g:molten_show_mimetype_debug`        | `true` \| (`false`)                                         | Before any non-iostream output chunk, the mime-type for that output chunk is shown. Meant for debugging/plugin devlopment |

### Status Line

Molten provides a few functions that you can use to see information in your status line. These are
listed below:

```lua
require('molten.status').initialized() -- "Molten" or "" based on initialization information
require('molten.status').kernels() -- "kernel1 kernel2" list of kernels attached to buffer or ""
require('molten.status').all_kernels() -- same as kernels, but will show all kernels
```

The way these are used will vary based on status line plugin. So please refer to your status line
plugin to figure out how to use them.

### Highlights

You can change highlights like so:

```lua
-- see :h nvim_set_hl for what to put in place of ...
-- I would recommend using the `link` option to link the values to colors from your color scheme
vim.api.nvim_set_hl(0, "MoltenOutputBorder", { ... })
```

Here is a complete list of the highlight groups that Molten uses, and their default values

- `MoltenOutputBorder` = `FloatBorder`: default output window border
- `MoltenOutputBorderFail` = `MoltenOutputBorder`: border of a failed output window
- `MoltenOutputBorderSuccess` = `MoltenOutputBorder`: border of a successfully run output window
- `MoltenOutputWin` = `NormalFloat`: the innards of the output window
- `MoltenOutputWinNC` = `MoltenOutputWin`: a "Non-Current" output window
- `MoltenOutputFooter` = `FloatFooter`: the "x more lines" text
- `MoltenCell` = `CursorLine`: applied to code that makes up a cell
- `MoltenVirtualText` = `Comment`: output that is rendered as virtual text

## Autocommands

We provide some `User` autocommands (see `:help User`) for further customization. They are:

- `MoltenInitPre`: runs right before `MoltenInit` initialization happens for a buffer
- `MoltenInitPost`: runs right after `MoltenInit` initialization happens for a buffer
- `MoltenDeinitPre`: runs right before `MoltenDeinit` de-initialization happens for a buffer
- `MoltenDeinitPost`: runs right after `MoltenDeinit` de-initialization happens for a buffer
- `MoltenKernelReady`: runs when a kernel is ready for the first time. `data` field has the `kernel_id`

<details>
  <summary>Lua Usage</summary>

Here is an example of attaching molten specific mappings to the buffer after initialization:

```lua
vim.api.nvim_create_autocmd("User", {
  pattern = "MoltenInitPost",
  callback = function()
    vim.keymap.set("v", "<localleader>r", ":<C-u>MoltenEvaluateVisual<CR>gv",
      { desc = "execute visual selection", buffer = true, silent = true })
    -- ... more mappings
  end,
})
```

Similarly, you could remove these mappings on `MoltenDeinitPost`

---

For `MoltenKernelReady` you can get the kernel id like this:

```lua
-- ...
  callback = function(e)
    print("Kernel id: " .. e.data.kernel_id)
  end
-- ...
```

</details>

## Functions

Molten exposes some functionality through vim functions. These are mostly for plugin authors and
people who want some custom behavior.

<details>
  <summary>MoltenEvaluateRange</summary>

`MoltenEvaluateRange(start_line, end_line, [start_col, end_col])` - evaluates the code between the
given line numbers and column numbers.

- ranges are inclusive and the indexing 1 based
- columns are optional, when omitted the entire line is captured
- passing `-1` for `end_col` will use the last col on the line
- passing `0` for all other positions will use the last line/col
- The values are used to create extmarks, and the `strict` option is set to false. See `:h
nvim_buf_set_extmark()` and then `options > strict`. This means passing `10` when there are only `5`
  lines in the buffer does result in an error.

```lua
-- run lines 1 through 23 (inclusive):
vim.fn.MoltenEvaluateRange(1, 23)

-- run code starting with col 4 on line 1, and ending with the last col on line 3
vim.fn.MoltenEvaluateRange(1, 3, 4, -1)
```

Additionally, this function can take a `kernel_id` as the first argument. When a string is given as
the first argument, it's assumed to be a `kernel_id`.

```lua
-- run lines 1 through 23 (inclusive) with the python3 kernel
vim.fn.MoltenEvaluateRange("python3", 1, 23)

-- run code starting with col 4 on line 1, and ending with col 20 on line 3 with the R kernel
vim.fn.MoltenEvaluateRange("ir", 1, 3, 4, 20)
```

_When there are multiple kernels attached to the buffer, and this function is called without
a `kernel_id`, the user will be prompted for a kernel with vim.ui.select_

</details>

<details>
  <summary>MoltenUpdateOption</summary>

Because Molten is a remote plugin, options are loaded and cached at initialization. This avoids
making an unnecessary number of RPC calls if we were to fetch configuration values every time we
needed to use them. This comes with the trade-off of not being able to update config values on the
fly... can you see where this is going.

This function lets you update a configuration value after initialization, and the new value will
take effect immediately.

You can specify option names with or without the "molten" prefix.

```lua
-- these are the same!
vim.fn.MoltenUpdateOption("auto_open_output", true)
vim.fn.MoltenUpdateOption("molten_auto_open_output", true)
```

</details>

<details>
  <summary>MoltenRunningKernels</summary>

Return a list of the currently running kernels' IDs. Takes one argument, when true,
returns only kernels running in the current buffer. Otherwise, returns all running kernel_ids.

```lua
vim.fn.MoltenRunningKernels(true) -- list buf local kernel ids
vim.fn.MoltenRunningKernels(false) -- list all kernel ids
```

</details>

<details>
  <summary>MoltenAvailableKernels</summary>

Returns a list of kernel names that molten is aware of.

```lua
vim.fn.MoltenAvailableKernels()
```

</details>

<details>
  <summary>MoltenDefineCell</summary>

Takes in a start line, and end line, and a kernel and creates a code cell in the current buffer
associated with that kernel. Does not run the code or create/open an output window.

_for compatibility reasons, if there is only one active kernel, you do not need to pass the kernel
argument_

```lua
-- Creates a cell from line 5 to line 10 associated with the python3 kernel
vim.fn.MoltenDefineCell(5, 10, 'python3')
```

</details>

## Output Chunks

In the Jupyter protocol, most output-related messages provide a dictionary of mime-types which can
be used to display the data. Theoretically, a `text/plain` field (i.e., plain text) is always
present, so we (theoretically) always have that fallback.

Here is a list of the currently handled mime-types:

- `text/plain`: Plain text. Shown as text in the output window's buffer.
- `image/*`: Molten attempts to render any `image` mimetype by sending it to `image.nvim`. In theory,
  this means that Molten can handle any image format that `image.nvim` supports, though I've only
  tested common formats
- `application/vnd.plotly.v1+json`: A Plotly figure. Rendered into a PNG with
  [Plotly](https://plotly.com/python/) + [Kaleido](https://github.com/plotly/Kaleido)
- `text/latex`: A LaTeX formula. Rendered into a PNG with
  [pnglatex](https://pypi.org/project/pnglatex/)
- `text/html`: via the `:MoltenOpenInBrowser` command.

This already provides quite a bit of basic functionality, but if you find a use case for a mime-type
that isn't currently supported, feel free to open an issue and/or PR!

## Thanks

- @dccsillag and everyone who has contributed to [magma-nvim](https://github.com/dccsillag/magma-nvim)
- @3rd and everyone who has contributed to [image.nvim](https://github.com/3rd/image.nvim)

