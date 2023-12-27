# Notebook Setup

_TL;DR at the bottom_

How to edit Jupyter Notebooks (`.ipynb` files) in neovim, using molten to run code.

This is how _I_ edit notebooks, there are other plugins that will do similar things you can see
a list of them at the bottom of the README.

## The promise:

\> your friend sends you a jupyter notebook file  
\> `nvim friends_file.ipynb`  
\> you see a markdown representation of the notebook  
\> `:MoltenImportOutput` - you see the cell outputs from the notebook
\> you edit the notebook, with LSP autocomplete, and format the code cells before running your new
code, and all the cells below it, watching the cells run as they run  
\> You admire the new chart, _in neovim_  
\> You write the file  
\> You send the `.ipynb` file, complete with your changes and the output of the code you ran, back
to your friend  

## The Setup:

There are three main things required for a good notebook experience in neovim:
- Code running
- LSP/autocomplete in a plaintext/markdown file
- File format conversion

### Code Running

We'll be using molten, a few configuration options will improve the experience.

```lua
-- I find auto open annoying, keep in mind setting this option will require setting
-- a keybind for `:noautocmd MoltenEnterOutput` to open the output again
vim.g.molten_auto_open_output = false

-- this guide will be using image.nvim, you can leave it out if you want want it
vim.g.molten_image_provider = "image.nvim"


-- optional, I like wrapping. works for virt text and the output window
vim.g.molten_wrap_output = true

-- Output as virtual text. Allows outputs to always be shown, works with images, but can be buggy
-- with longer images
vim.g.molten_virt_text_output = true
-- this will make it so the output shows up below the \`\`\` cell delimiter
vim.g.molten_virt_lines_off_by_1 = true
```

### LSP Features with quarto-nvim

One of the issues with plaintext notebooks is that you end up essentially editing a markdown file,
and the pyright language server (for example) can't read a markdown file and give you information
about the python code cells in it. Enter Quarto, and specifically quarto-nvim.

[Quarto](https://quarto.org/) is a lot of things. One of those is tool for writing and publishing
literate programming documents, or just any markdown document really. It's built on top of Pandoc,
and so can render markdown to pdf, html, or any format that Pandoc supports.

The neovim plugin [quarto-nvim](https://github.com/quarto-dev/quarto-nvim) provides:
- LSP Autocomplete, formatting, diagnostics, go to definition, and other LSP features for code cells
in markdown documents
- A code running integration with molten to easily run code cells
- A convenient way to render the file you're working on

All of that works out of the box in a `qmd` document, _and_ in a normal markdown document too! (Just
run `:QuartoActivate` in the markdown doc, or setup a filetype plugin to do it for you)

### Notebook Conversion

The tool `Quarto` (not the plugin) can convert jupyter notebooks to `qmd` files with the `quarto
convert` command manually or you can automatically do this conversion with
[GCBallesteros/jupytext.nvim](https://github.com/GCBallesteros/jupytext.nvim), but it is slow.
Currently jupytext.nvim is a little buggy and unreliable, but it supports more conversion formats
than the alternative&mdash;[goerz/jupytext.vim](https://github.com/goerz/jupytext.vim). Which does
the same thing, but will only work for markdown conversion more or less.

**Most people should use `goerz/jupytext.vim` at the time of writing, but the alternative is
maintained, and improving, so I will eventually switch this recommendation.**

If you use Jupytext to produce a markdown output (recommended), you can use this in conjunction with
the quarto-nvim plugin mentioned above to get get LSP features and convenient code running binds.

> [!NOTE] Quarto doesn't activate automatically in markdown files. You have to run `:QuartoActivate`
> manually or setup an auto command or ft plugin for markdown files to do this for you.

### Extras

#### Treesitter Text Objects

Other than the quarto-nvim x molten integration, the best way to run code is with the
`:MoltenEvaluateOperator` command (bound to some convenient mapping of course). I use
`<localleader>e` for evaluate.

When combined with treesitter text objects, you can easily run code cells without the quarto
integration.

To define a new capture group, you need to add this:

#### Output Chunks

Saving output chunks has historically not been possible (afaik) with plaintext notebooks. You will
lose output chunks in a round trip from `ipynb` to `qmd` to `ipynb`. And that is still true, but,
the pain can be lessened a little.

Jupytext _updates_ notebooks and doesn't destroy outputs that already exist, and **Molten has a way
to export outputs from code that you ran to a matching jupyter notebook file**. More details in the
molten [docs](https://github.com/benlubas/molten-nvim/blob/main/docs/Advanced-Functionality.md#exporting-outputs).

While this feature is still considered 'experimental' and is likely buggy, it _works_. Especially
for basic things like text, image, and error outputs, I've had only one issue, and it relates to
progress bars, and it's totally fixable I'm just lazy and it's not that big an issue imo.

#### Navigation

The reason that we're doing any of this in the first place is b/c we love using neovim, otherwise
we'd just use jupyter lab or vs code. One of the large advantages of editing a notebook in neovim is
the ability to quickly navigate notebooks.

The way I do this is with a combination of nvim-treesitter text objects and the
[Hydra](https://github.com/anuvyklack/hydra.nvim) plugin, and it's detailed
[here](https://github.com/quarto-dev/quarto-nvim/wiki/Integrating-with-Hydra).



## Compromises

Compared to Jupyter-lab:
- output formats. Molten can't render everything that jupyter-lab can, notably HTML is currently
unsupported.
- loading outputs from `.ipynb`. This is on the roadmap for molten for sure
- jank. the UI is definitely worse, and sometimes images will move somewhere weird or just not show
up. Molten is still new, and I'm sure people will break it... bring it on lol
- setup is a lot of work. I've mentioned 4 different plugins that are required to get this working
and all 4 of those plugins have external dependencies.

But it's worth it, for me anyway

**TL;DR:** molten-nvim + image.nvim + quarto-nvim + jupytext.vim = great notebook experience,
unfortunately, it does take some time to setup.
