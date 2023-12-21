-- Example for configuring Neovim to load user-installed installed Lua rocks:
package.path = package.path .. ";" .. vim.fn.expand("$HOME") .. "/.luarocks/share/lua/5.1/?/init.lua"
package.path = package.path .. ";" .. vim.fn.expand("$HOME") .. "/.luarocks/share/lua/5.1/?.lua"

-- You should specify your python3 path here.
vim.g.python3_host_prog = vim.fn.expand("$HOME") .. "YOUR PATH"

local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({
    "git",
    "clone",
    "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    "--branch=stable", -- latest stable release
    lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

-- install plugins
local plugins = {
  { "bluz71/vim-moonfly-colors" }, -- don't change the color scheme
  {
    "benlubas/molten-nvim",
    dependencies = { "3rd/image.nvim" },
    build = ":UpdateRemotePlugins",
    init = function()
      -- Comment/uncomment config as you need to. Change as few defaults as possible to reproduce
      -- the issue.
      vim.g.molten_image_provider = "image.nvim"
      -- vim.g.molten_output_win_max_height = 12 -- these all have their default values currently
      -- vim.g.molten_virt_text_output = false
      -- vim.g.molten_output_win_border = { "", "━", "", "" }
      -- vim.g.molten_wrap_output = false

      -- don't change the mappings
      vim.keymap.set("n", "<localleader>e", ":MoltenEvaluateOperator<CR>")
      vim.keymap.set("n", "<localleader>rr", ":MoltenReevaluateCell<CR>")
      vim.keymap.set("v", "<localleader>r", ":<C-u>MoltenEvaluateVisual<CR>gv")
      vim.keymap.set("n", "<localleader>os", ":noautocmd MoltenEnterOutput<CR>")
      vim.keymap.set("n", "<localleader>oh", ":MoltenHideOutput<CR>")
      vim.keymap.set("n", "<localleader>md", ":MoltenDelete<CR>")
    end,
  },
  {
    "3rd/image.nvim",
    opts = {
      backend = "kitty",
      integrations = {},
      max_width = 100,
      max_height = 12,
      max_height_window_percentage = math.huge,
      max_width_window_percentage = math.huge,
      window_overlap_clear_enabled = true,
      window_overlap_clear_ft_ignore = { "cmp_menu", "cmp_docs", "" },
    },
    version = "1.1.0", -- or comment out for latest
  },
  {
    "nvim-treesitter/nvim-treesitter",
    build = ":TSUpdate",
    config = function()
      require("nvim-treesitter.configs").setup({
        ensure_installed = {
          "markdown",
          "markdown_inline",
        },
      })
    end,
  },
}

require("lazy").setup(plugins)

vim.cmd.colorscheme("moonfly")

vim.api.nvim_set_hl(0, "MoltenOutputBorder", { link = "Normal" })
vim.api.nvim_set_hl(0, "MoltenOutputBorderFail", { link = "MoonflyCrimson" })
vim.api.nvim_set_hl(0, "MoltenOutputBorderSuccess", { link = "MoonflyBlue" })
