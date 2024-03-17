-- loads the wezterm.nvim plugin and exposes methods to the python remote plugin
local ok, wezterm = pcall(require, "wezterm")
if not ok then
  vim.api.nvim_err_writeln("[Molten] `wezterm.nvim` not found")
  return
end

local wezterm_api = {}

wezterm_api.get_pane_id = function()
  local current_pane_id = wezterm.get_current_pane()
  return current_pane_id
end

-- Split the current pane and return the new pane id
--- type function
--- @param initial_pane_id number, the pane id to split
--- @param direction string, direction to split the pane
--- @param size string, size of the new pane
--- @return image_pane_id number the new pane id
wezterm_api.wezterm_molten_init = function(initial_pane_id, direction, size)
  direction = "--" .. (direction or "bottom")
  size = (size or "35")

  wezterm.exec_sync({ "cli", "split-pane", direction, "--percent", size })
  wezterm.exec_sync({ "cli", "activate-pane", "--pane-id", tostring(initial_pane_id) })
  local _, image_pane_id = wezterm.exec_sync({ "cli", "get-pane-direction", "Prev" })
  return image_pane_id
end

-- Send an image to the image pane (terminal split)
--- type function
--- @param path string, path to the image
--- @param image_pane_id number, the pane id of the image pane
--- @param initial_pane_id number, the pane id of the initial pane
--- @return nil
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

-- Close the image pane
--- type function
--- @param image_pane_id number, the pane id of the image pane
--- @return nil
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
