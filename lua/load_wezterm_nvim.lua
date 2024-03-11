-- loads the wezterm.nvim plugin and exposes methods to the python remote plugin
local ok, wezterm = pcall(require, "wezterm")
if not ok then
  vim.api.nvim_err_writeln("[Molten] `wezterm.nvim` not found")
  return
end

local wezterm_api = {}

wezterm_api.get_pane_id = function()
  local current_pane_id = wezterm.get_pane_id()
  return current_pane_id
end

wezterm_api.wezterm_molten_init = function(initial_pane_id)
  local direction = "bottom"
  local size = "35"

  direction = "--" .. (direction or "bottom")
  size = tostring(size or "35")

  wezterm.exec_sync({ "cli", "split-pane", direction, "--percent", size })
  wezterm.exec_sync({ "cli", "activate-pane", "--pane-id", tostring(initial_pane_id) })
  local _, image_pane_id = wezterm.exec_sync({ "cli", "get-pane-direction", "Prev" })
  return image_pane_id
end

wezterm_api.send_image = function(path, image_pane_id, initial_pane_id)
  local placeholder = "wezterm imgcat %s \r"
  local image = string.format(placeholder, path)
  wezterm.exec_sync({ "cli", "activate-pane", "--pane-id", image_pane_id })
  wezterm.exec_sync({
    "cli",
    "send-text",
    "--pane-id",
    image_pane_id,
    "--no-paste",
    image,
  })
  wezterm.exec_sync({ "cli", "activate-pane", "--pane-id", initial_pane_id })
end

wezterm_api.close_image_pane = function(image_pane_id)
  wezterm.exec_sync({
    "cli",
    "send-text",
    "--pane-id",
    image_pane_id,
    "--no-paste",
    "wezterm cli kill-pane --pane-id " .. image_pane_id .. "\r",
  })
end

return { wezterm_api = wezterm_api }
