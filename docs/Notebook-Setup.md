# Notebook Setup

There are many ways to use Molten, but I'd guess the most common will be to edit "notebooks" in
neovim. When I say notebooks I mean Jupyter notebooks (`ipynb` files), as well as other formats,
like simple markdown notebooks, or Quarto notebooks.

This file will go over some common setups that involve molten. Personally, I use quarto for my own
notebooks, and jupytext (with it's plugin) when I need to quickly edit an `ipynb` file.

Note that these plugins are not mutually exclusive. You could use none or all of them depending on
your needs.

## Quarto

[Quarto](https://quarto.org/) is, at its core, a tool for writing and publishing literate
programming documents, or just any markdown document really. It's built on top of Pandoc, and so can
render markdown to pdf, html, or any format that Pandoc supports.

`quarto convert some_notebook.ipynb --to my_notebook.qmd` will convert a notebook into a "quarto
markdown" file, which is a nice plain-text format that you can work with in neovim.

Quarto also has its own neovim plugin: [quarto-nvim](https://github.com/quarto-dev/quarto-nvim).
The quarto-nvim plugin provides:
- LSP Autocomplete, formatting, diagnostics, go to definition, and others
- A code running integration with molten to easy run code cells
- A convenient way to render the file you're working on

All of that in a normal markdown document too! (Just run `:QuartoActivate` in the markdown doc)

## Jupytext

This is the most convenient way to open an `ipynb` file, make a change to a code cell, run it, and
save both the file and the output (with `:MoltenExportOutput`).

[Jupytext](https://github.com/mwouts/jupytext) with
[jupytext.vim](https://github.com/goerz/jupytext.vim) will let you open a normal `.ipynb`
file with neovim. It's automatically converted to plain-text where you can edit it like normal. On
save, it converts back to `ipynb` and writes the file.

If you use Jupytext to produce a markdown output (recommended), you can use this in conjunction with
the quarto-nvim plugin mentioned above to get get LSP features and convenient code running binds.

If you don't want to use the quarto plugin, running a code cell is made easier with a treesitter
text object that selects text inside a code block. Then you cane use `:MoltenEvaluateOperator` with
a keybinding to easily run the code.

``` lua
--- other treesitter text objects config ...
select = {
    enable = true,
    lookahead = true,
    keymaps = {
        -- refers to the code inside a markdown code block (as well as other things)
        ["ib"] = { query = "@block.inner", desc = "in block" },
        --- other mappings ...
    },
},
--- other config ...
```

## NotebookNavigator

The [NotebookNavigator](https://github.com/GCBallesteros/NotebookNavigator.nvim) plugin, which
allows you to turn python files into notebooks with comment delimiters. The plugin comes with a few
quality of life features, and while molten support isn't officially part of the plugin at the time
of writing, it's being worked on, and there's nothing stopping you from just using molten's builtin
run methods.
