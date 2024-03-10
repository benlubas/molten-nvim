-- loads the wezterm.nvim plugin and exposes methods to the python remote plugin
local ok, wezterm = pcall(require, "wezterm")

if not ok then
  vim.api.nvim_err_writeln("[Molten] `wezterm.nvim` not found")
  return
end

local wezterm_api = {}

wezterm_api.get_current_pane = function()
  local current_pane_id = wezterm.get_pane_id()
  return current_pane_id
end

wezterm_api.split_pane = function(direction, opts)
  if direction == "horizontal" then
    wezterm.exec_sync({ "cli", "split-pane" })
  elseif direction == "vertical" then
    wezterm.exec_sync({ "cli", "split-pane" })
  end
end

wezterm_api.wezterm_molten_init = function()
  local direction = "horizontal"
  local opts = {}
  wezterm.exec_sync({ "cli", "split-pane" })
end

return { wezterm = wezterm_api }
