# Notebook Setup

_TL;DR at the bottom_

> [!NOTE]
> Although I include sample configuration, this is **not** a replacement for reading the
> readme for each plugin that I mention. Please setup each of these plugins individually
> to ensure they're working before trying to use them all together.

How to edit Jupyter Notebooks (`.ipynb` files) in neovim, using molten to run code, and
load/save code cell output.

This is how _I_ edit notebooks, and it's tailored to python notebooks. It's the best
experience you can get (in my opinion), but there are some extra features you can get with
other plugins that I don't use but will mention at the bottom.

## The promise:

\> your friend sends you a jupyter notebook file  
\> `nvim friends_file.ipynb`  
\> you see a markdown representation of the notebook, including code outputs and images  
\> you edit the notebook, with LSP autocomplete, and format the code cells before running
your new code, and all the cells below it, watching each cell output update as they run  
\> `:wq`  
\> You send the `.ipynb` file, complete with your changes and the output of the code you
ran, back to your friend

## The Setup:

There are four big things required for a good notebook experience in neovim:

- Code running
- Output viewing
- LSP features (autocomplete, go to definition/references, rename, format, etc.) in
  a plaintext/markdown file
- File format conversion

### Code Running And Output Viewing

Shocker we'll be using molten. A few configuration options will dramatically improve the
notebook experience of this plugin.

```lua
-- I find auto open annoying, keep in mind setting this option will require setting
-- a keybind for `:noautocmd MoltenEnterOutput` to open the output again
vim.g.molten_auto_open_output = false

-- this guide will be using image.nvim
-- Don't forget to setup and install the plugin if you want to view image outputs
vim.g.molten_image_provider = "image.nvim"

-- optional, I like wrapping. works for virt text and the output window
vim.g.molten_wrap_output = true

-- Output as virtual text. Allows outputs to always be shown, works with images, but can
-- be buggy with longer images
vim.g.molten_virt_text_output = true

-- this will make it so the output shows up below the \`\`\` cell delimiter
vim.g.molten_virt_lines_off_by_1 = true
```

Additionally, you will want to setup some keybinds (as always, change the lhs to suit your
needs) to run code and interact with the plugin. **At a minimum you should setup:**

```lua
vim.keymap.set("n", "<localleader>e", ":MoltenEvaluateOperator<CR>", { desc = "evaluate operator", silent = true })
vim.keymap.set("n", "<localleader>os", ":noautocmd MoltenEnterOutput<CR>", { desc = "open output window", silent = true })
```

But I'd also recommend these ones:

```lua
vim.keymap.set("n", "<localleader>rr", ":MoltenReevaluateCell<CR>", { desc = "re-eval cell", silent = true })
vim.keymap.set("v", "<localleader>r", ":<C-u>MoltenEvaluateVisual<CR>gv", { desc = "execute visual selection", silent = true })
vim.keymap.set("n", "<localleader>oh", ":MoltenHideOutput<CR>", { desc = "close output window", silent = true })
vim.keymap.set("n", "<localleader>md", ":MoltenDelete<CR>", { desc = "delete Molten cell", silent = true })

-- if you work with html outputs:
vim.keymap.set("n", "<localleader>mx", ":MoltenOpenInBrowser<CR>", { desc = "open output in browser", silent = true })
```

### LSP Features with quarto-nvim

One of the issues with plaintext notebooks is that you end up essentially editing
a markdown file, and the pyright language server (for example) can't read a markdown file
and give you information about the python code cells in it. Enter Quarto, and specifically
quarto-nvim.

[Quarto](https://quarto.org/) is a lot of things. One of those is tool for writing and
publishing literate programming documents, or just any markdown document really. It's
built on top of Pandoc, and so can render markdown to pdf, html, or any format that Pandoc
supports.

The neovim plugin [quarto-nvim](https://github.com/quarto-dev/quarto-nvim) provides:

- LSP Autocomplete, formatting, diagnostics, go to definition, and other LSP features for
  code cells in markdown documents via [otter.nvim](https://github.com/jmbuhr/otter.nvim)
- A code running integration with molten (written by me, so I'll provide support if there
  are problems/bugs) to easily run code cells (including run above, run below, run all)
- A convenient way to render the file you're working on

<details>
  <summary>Sample configuration for quarto-nvim</summary>
  
```lua
local quarto = require("quarto")
quarto.setup({
    lspFeatures = {
        -- NOTE: put whatever languages you want here:
        languages = { "r", "python", "rust" },
        chunks = "all",
        diagnostics = {
            enabled = true,
            triggers = { "BufWritePost" },
        },
        completion = {
            enabled = true,
        },
    },
    keymap = {
        -- NOTE: setup your own keymaps:
        hover = "H",
        definition = "gd",
        rename = "<leader>rn",
        references = "gr",
        format = "<leader>gf",
    },
    codeRunner = {
        enabled = true,
        default_method = "molten",
    },
})
```

</details>

When you configure quarto, you gain access to these functions which should be mapped to
commands:

```lua
local runner = require("quarto.runner")
vim.keymap.set("n", "<localleader>rc", runner.run_cell,  { desc = "run cell", silent = true })
vim.keymap.set("n", "<localleader>ra", runner.run_above, { desc = "run cell and above", silent = true })
vim.keymap.set("n", "<localleader>rA", runner.run_all,   { desc = "run all cells", silent = true })
vim.keymap.set("n", "<localleader>rl", runner.run_line,  { desc = "run line", silent = true })
vim.keymap.set("v", "<localleader>r",  runner.run_range, { desc = "run visual range", silent = true })
vim.keymap.set("n", "<localleader>RA", function()
  runner.run_all(true)
end, { desc = "run all cells of all languages", silent = true })
```

#### Activate Quarto-nvim in markdown buffers

By default, quarto only activates in `quarto` buffers.

We will do this with an ftplugin.

> [!NOTE]
> In order to do this, you must make sure that quarto is loaded for markdown filetypes
> (ie. if you're using lazy.nvim, use `ft = {"quarto", "markdown"}`)

```lua
-- file: nvim/ftplugin/markdown.lua

require("quarto").activate()
```

### Notebook Conversion

[GCBallesteros/jupytext.nvim](https://github.com/GCBallesteros/jupytext.nvim) is a plugin
that will automatically convert from `ipynb` files to plaintext (markdown) files, and then
back again when you save. By default, it converts to python files, but we will configure
the plugin to produce a markdown representation.

```lua
require("jupytext").setup({
    style = "markdown",
    output_extension = "md",
    force_ft = "markdown",
})
```

> [!NOTE]
> Jupytext can convert to the Quarto format, but it's slow enough to notice, on open _and_
> on save, so I prefer markdown

Because Jupytext generates markdown files, we get the full benefits of quarto-nvim when
using Jupytext.

### Extras

#### Treesitter Text Objects

[Treesitter text objects](importingexporting-outputs-tofrom-ipynb-files) help quickly
navigate cells, copy their contents, delete them, move them around, and run code with
`:MoltenEvaluateOperator`.

We'll first want to define a new capture group `@code_cell` for the filetype we want to
run code in. Here's a very simple example for markdown, but you can do this with any
filetype you want to have a code cell in:

```scm
;; located in: nvim/after/queries/markdown/textobjects.scm

;extends

(fenced_code_block (code_fence_content) @code_cell.inner) @code_cell.outer
```

We can now use `@code_cell.inner` and `@code_cell.outer` in the treesitter-text-objects
plugin like so, I use b, you can use whatever mappings you like:

```lua
require("nvim-treesitter.configs").setup({
    -- ... other ts config
    textobjects = {
        move = {
            enable = true,
            set_jumps = false, -- you can change this if you want.
            goto_next_start = {
                --- ... other keymaps
                ["]b"] = { query = "@code_cell.inner", desc = "next code block" },
            },
            goto_previous_start = {
                --- ... other keymaps
                ["[b"] = { query = "@code_cell.inner", desc = "previous code block" },
            },
        },
        select = {
            enable = true,
            lookahead = true, -- you can change this if you want
            keymaps = {
                --- ... other keymaps
                ["ib"] = { query = "@code_cell.inner", desc = "in block" },
                ["ab"] = { query = "@code_cell.outer", desc = "around block" },
            },
        },
        swap = { -- Swap only works with code blocks that are under the same
                 -- markdown header
            enable = true,
            swap_next = {
                --- ... other keymap
                ["<leader>sbl"] = "@code_cell.outer",
            },
            swap_previous = {
                --- ... other keymap
                ["<leader>sbh"] = "@code_cell.outer",
            },
        },
    }
})
```

Test it by selecting the insides of a code cell with `vib`, or run them with
`:MoltenEvaluateOperator<CR>ib`.

#### Output Chunks

Saving output chunks has historically not been possible (afaik) with plaintext notebooks.
You will lose output chunks in a round trip from `ipynb` to `qmd` to `ipynb`. And while
that's still true, we can work around it.

Jupytext _updates_ notebooks and doesn't destroy outputs that already exist, and Molten
can both **import outputs** from a notebook AND **export outputs from code you run** to a jupyter
notebook file. More details about how and when this works on the [advanced
functionality](./Advanced-Functionality.md#importingexporting-outputs-tofrom-ipynb-files)
page.

We can make importing/exporting outputs seamless with a few autocommands:

```lua
-- automatically import output chunks from a jupyter notebook
-- tries to find a kernel that matches the kernel in the jupyter notebook
-- falls back to a kernel that matches the name of the active venv (if any)
vim.api.nvim_create_autocmd("BufWinEnter", {
    pattern = { "*.ipynb" },
    callback = function(e)
        local kernels = vim.fn.MoltenAvailableKernels()

        local try_kernel_name = function()
            local metadata = vim.json.decode(io.open(e.file, "r"):read("a"))["metadata"]
            return metadata.kernelspec.name
        end
        local ok, kernel_name = pcall(try_kernel_name)

        if not ok or not vim.tbl_contains(kernels, kernel_name) then
            kernel_name = nil
            local venv = os.getenv("VIRTUAL_ENV")
            if venv ~= nil then
                kernel_name = string.match(venv, "/.+/(.+)")
            end
        end

        if kernel_name ~= nil and vim.tbl_contains(kernels, kernel_name) then
            vim.cmd(("MoltenInit %s"):format(kernel_name))
        end
        vim.cmd("MoltenImportOutput")
    end,
})
```

> [!NOTE]
> If no matching kernel is found, this will prompt you for a kernel to start

```lua
-- automatically export output chunks to a jupyter notebook on write
vim.api.nvim_create_autocmd("BufWritePost", {
    pattern = { "*.ipynb" },
    callback = function()
        if require("molten.status").initialized() == "Molten" then
            vim.cmd("MoltenExportOutput!")
        end
    end,
})
```

> [!WARNING]
> This export, in conjunction with the jupytext conversion, can make saving lag the editor
> for ~500ms, so autosave plugins can cause a bad experience.

> [!NOTE]
> If you have more than one kernel active this will prompt you for a kernel to choose
> from

#### Hydra

The [Hydra](https://github.com/nvimtools/hydra.nvim) plugin allows very quick navigation
and code running.

I have a detailed explanation of how to set this up
[on the quarto-nvim wiki](https://github.com/quarto-dev/quarto-nvim/wiki/Integrating-with-Hydra).
Recommend setting up treesitter-text-objects before following that.

#### Disable Annoying Pyright Diagnostic

It's very common to leave an unused expression at the bottom of a cell as a way of
printing the value. Pyright will yell at you for this. Fortunately we can configure it to
not do that. Just add this option to whatever existing configuration you have:

```lua
require("lspconfig")["pyright"].setup({
    on_attach = on_attach,
    capabilities = capabilities,
    settings = {
        python = {
            analysis = {
                diagnosticSeverityOverrides = {
                    reportUnusedExpression = "none",
                },
            },
        },
    },
})
```

#### Change Molten settings based on filetype

Molten is a multi purpose code runner, I use it in regular python files to quickly test
out a line of code. In those situations, creating virtual text is obnoxious, and I'd
rather have output shown in a float that disappears when I move away.

Autocommands to the rescue:

```lua
-- change the configuration when editing a python file
vim.api.nvim_create_autocmd("BufEnter", {
  pattern = "*.py",
  callback = function(e)
    if string.match(e.file, ".otter.") then
      return
    end
    if require("molten.status").initialized() == "Molten" then -- this is kinda a hack...
      vim.fn.MoltenUpdateOption("virt_lines_off_by_1", false)
      vim.fn.MoltenUpdateOption("virt_text_output", false)
    else
      vim.g.molten_virt_lines_off_by_1 = false
      vim.g.molten_virt_text_output = false
    end
  end,
})

-- Undo those config changes when we go back to a markdown or quarto file
vim.api.nvim_create_autocmd("BufEnter", {
  pattern = { "*.qmd", "*.md", "*.ipynb" },
  callback = function(e)
    if string.match(e.file, ".otter.") then
      return
    end
    if require("molten.status").initialized() == "Molten" then
      vim.fn.MoltenUpdateOption("virt_lines_off_by_1", true)
      vim.fn.MoltenUpdateOption("virt_text_output", true)
    else
      vim.g.molten_virt_lines_off_by_1 = true
      vim.g.molten_virt_text_output = true
    end
  end,
})
```

## Compromises

Compared to Jupyter-lab:

- output formats. Molten can't render everything that jupyter-lab can, specifically
  in-editor HTML is just not going to happen
- Markdown and latex-in-markdown rendering. Currently you can render latex, but you have
  to send it to the kernel. It doesn't happen automatically.
- jank. the UI is definitely worse, and sometimes images will move somewhere weird until
  you scroll. Molten is still relatively new, and bugs are still being ironed out.
- setup is a lot of work. I've mentioned ~4~ 5 different plugins that are required to get
this working and all 4 of those plugins have external dependencies.

## Honorable Mentions

Plugins that didn't quite make it into my workflow, but which are still really good and
worth looking at.

- [jupyter-kernel.nvim](https://github.com/lkhphuc/jupyter-kernel.nvim) - this plugin adds
  autocomplete from the jupyter kernel, as well as hover inspections from the jupyter
  kernel. Me personally, I'd rather just use pyright via quarto-nvim/otter.nvim. This
  plugin could co-exist with the current setup, but might lead to double completions, and so
  you might want to disable quarto's lsp features if you choose to use this plugin
- [NotebookNavigator.nvim](https://github.com/GCBallesteros/NotebookNavigator.nvim) -
  a plugin for editing notebooks as a different plaintext format which defines cells using
  comments in the native language of the notebook. This plugin would be used in place of
  quarto-nvim, as language servers just work in a `.py` file. I prefer to edit markdown
  notebooks, and the point of notebooks to me is the markdown component, and having markdown
  shown as comments without syntax highlighting is a deal breaker.

## TL;DR

molten-nvim + image.nvim + quarto-nvim (+ otter.nvim) + jupytext.nvim = great notebook experience,
unfortunately, it does take some time to setup.

<!-- vim: set tw=90: -->
