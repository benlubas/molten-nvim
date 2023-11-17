# Notebook Setup

There are a few different ways to use this plugin. This file will focus on the main way that I use
it: To edit Jupyter Notebook Files...kind of.

I don't need to edit and share `ipynb` file very often. I only have to submit a homework assignment
once in a while. So I pull down a notebook file, convert it to markdown, work on it for a week or
two, and then convert it back right before submitting.

## Quarto

[Quarto](https://quarto.org/) is, at its core, a tool for writing and publishing literate
programming documents, or just any markdown document really. It's built on top of Pandoc, and so can
render markdown to pdf, html, or any format that Pandoc supports.

`quarto convert some_notebook.ipynb --to my_notebook.qmd` will convert a notebook into a "quarto
markdown" file, which is a nice plain-text format that you can work with in neovim.

Quarto also has its own neovim plugin: [quarto-nvim](https://github.com/quarto-dev/quarto-nvim).
I use this plugin primarily for its integration with
[otter.nvim](https://github.com/jmbuhr/otter.nvim), which enables LSP features in the markdown
document, but this is also a very easy way to render markdown files that you're working on in
neovim.

### Alternatives

_I've never used these tools, and cannot provide the best support for using them with Molten. That
said, always happy to try and help if you have issues._

There are other ways to edit Jupyter notebook files in Neovim. Most notably
[Jupytext](https://github.com/mwouts/jupytext) with
[jupytext.vim](https://github.com/goerz/jupytext.vim). This will let you open a normal `.ipynb`
file, convert it automatically to plain-text and display it in a temporary buffer, and then convert
it back again when you write.


There is also the [NotebookNavigator](https://github.com/GCBallesteros/NotebookNavigator.nvim)
plugin, which allows you to turn python files into notebooks with comment delimiters. The plugin
comes with a few qol features, and while molten support isn't officially part of the plugin at the
time of writing, it's being worked on, and there's nothing stopping you from just using molten's
builtin run methods.

## Code Running

Obviously we're going to use Molten for this, but there is some extra setup we can do to get more of
a Notebook experience. The concept of "Code Cell" still exists in Markdown documents, and often
you'll want to run an entire cell or all the cells above the current one. The easiest way to do this
is with a little bit of lua scripting.

### Quarto Code Runner

[quarto_code_runner.lua](https://github.com/benlubas/.dotfiles/blob/d6c540b6c9fe740c18876b2e43cbfcc6aa70fcf9/nvim/lua/benlubas/quarto_code_runner.lua)
is a small script that I've written to help easily run code in a `qmd` document.

It uses Molten to send code from a quarto buffer to a running kernel.


For now, this is just a very quick script that I threw together, I plan to improve it in the
future. Anyone is welcome to take and modify this code for their own purposes, so if you would like
to have a similar setup, just grab the file above, and throw it into your config.

#### Run mappings

Using the functions from the file above, we can setup mappings like this:

```lua
vim.keymap.set("n", "<localleader>rc", M.run_cell,
    { desc = "run code cell", buffer = true })
vim.keymap.set("n", "<localleader>ra", M.run_all_above,
    { desc = "run all code cells above the cursor", buffer = true })
vim.keymap.set("n", "<localleader>rl", M.run_line,
    { desc = "run line", buffer = true })
```

_These mappings only work inside of code blocks in quarto documents_

We get two mappings for running code by the cell, and another mapping for running code by line. Note
that Molten ships with a command `:MoltenEvaluateLine` which also runs a line of code. The
difference here is that `quarto_code_runner.run_line` is aware of code cells, and will not try to
run lines outside of a code cell.
