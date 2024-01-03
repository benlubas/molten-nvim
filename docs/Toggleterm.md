# Toggleterm Guide: Integrating Python with Quarto & Molten in Neovim

https://github.com/benlubas/molten-nvim/assets/14924440/34b66959-0f10-4d74-a15a-e38dfd6aaa0d

For developers accustomed to using toggleterm with Python3 during development, extending this convenience to a notebook buffer offers enhanced functionality for specific use-cases. This guide demonstrates how to configure a toggleterm in Neovim to interact with a Quarto notebook using the Molten plugin. While the example focuses on a specific setup using Quarto & Molten with the Lazy plugin manager, the principles can be adapted to various setups.

## Setting Up a Python3 Toggle Term

First, let's look at how to set up a standard Python3 toggle term:

```lua
local python_term = require("toggleterm.terminal").Terminal:new({ cmd = 'python3', hidden = true, direction = 'float'})
vim.keymap.set('n', '<C-p>', function() python_term:toggle() end, { noremap = true, silent = true })
```

## Configuring a Neovim Buffer for Quarto Notebooks

To enable a similar setup for a nvim buffer, a few additional steps are required. We need to launch a new neovim instance, create an empty virtual buffer, insert template code, and initialize Quarto and Molten.

```lua
local function markdown_codeblock(language, content)
    return '\\`\\`\\`{' .. language .. '}\n' .. content .. '\n\\`\\`\\`'
end

local quarto_notebook_cmd = 'nvim -c enew -c "set filetype=quarto"' ..
' -c "norm GO## IPython\nThis is Quarto IPython notebook. Syntax is the same as in markdown\n\n' .. markdown_codeblock('python', '# enter code here\n') .. '"' ..
' -c "norm Gkk"' ..
-- This line needed because QuartoActivate and MoltenInit commands must be accessible; should be adjusted depending on plugin manager
" -c \"lua require('lazy.core.loader').load({'molten-nvim', 'quarto-nvim'}, {cmd = 'Lazy load'})\"" ..
' -c "MoltenInit python3" -c QuartoActivate -c startinsert'
```

Breakdown of Commands (passed with `-c`):

1. Open a new empty virtual buffer.
2. Set filetype to quarto
3. Insert a template code snippet
4. Adjust the cursor position within the newly created cell.
5. Ensure Molten and Quarto plugins are loaded
6. Initialize Molten and Quarto for the current buffer
7. Switch to insert mode

Last step slightly optimizes the workflow, allowing you to start typing code in the terminal immediately, similar to a regular IPython instance.

During the initial launch, there may be a slight delay due to steps 5 and 6. Subsequent uses will be much quicker.

## Keymapping for Nested Neovim Instances

To prevent nested terminals and ensure proper toggling functionality, modify the key mapping for terminal mode:

```lua
local molten_term = require("toggleterm.terminal").Terminal:new({ cmd = quarto_notebook_cmd, hidden = true, direction = 'float'})
vim.keymap.set('n', '<C-p>', function () molten_term:toggle() end, { noremap = true, silent = true })
vim.keymap.set('t', '<C-p>', function ()
    vim.cmd 'stopinsert'
    molten_term:toggle()
end, { noremap = true, silent = true })
```

With this setup, Ctrl+P will toggle terminal with quarto notebook & molten, preloaded with following template:

````markdown
## IPython
This is Quarto IPython notebook. Syntax is the same as in markdown

```{python}
# enter code here

```
````
