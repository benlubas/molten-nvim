-- loads the wezterm.nvim plugin and exposes methods to the python remote plugin
local ok, wezterm = pcall(require, "wezterm")
if not ok then
  vim.api.nvim_echo({ { "[Molten] `wezterm.nvim` not found" } }, true, { err = true })
  return
end

local wezterm_api = {}

wezterm_api.get_pane_id = function()
  local current_pane_id = wezterm.get_current_pane()
  return current_pane_id
end

--- Validate the split direction
--- type function
--- @param direction string the direction to validate
--- @return string validated direction if valid
local validate_split_dir = function(direction)
  local accepted_dirs = { "top", "bottom", "left", "right" }
  --if direction not in accepted_dirs, return "bottom" else return direction
  if not vim.tbl_contains(accepted_dirs, direction) then
    vim.notify(
      "[Molten] 'molten_split_dir' must be one of 'top', 'bottom', 'left', or 'right', defaulting to 'right'",
      vim.log.levels.WARN
    )
    return "right"
  end
  return direction
end

--- Validate the split size
--- type function
--- @param size number the size to validate
--- @return number validated size if valid
local validate_split_size = function(size)
  if size == nil or size < 0 or size > 100 then
    vim.notify(
      "[Molten] 'molten_split_size' must be a number between 0 and 100, defaulting to a 40% split.",
      vim.log.levels.WARN
    )
    return 40
  end
  return size
end

-- Split the current pane and return the new pane id
--- type function
--- @param initial_pane_id number, the pane id to split
--- @param direction string, direction to split the pane
--- @param size number, size of the new pane
--- @return number image_pane_id the new pane id
wezterm_api.wezterm_molten_init = function(initial_pane_id, direction, size)
  direction = "--" .. validate_split_dir(direction)
  size = validate_split_size(size)

  wezterm.exec_sync({ "cli", "split-pane", direction, "--percent", tostring(size) })
  wezterm.exec_sync({ "cli", "activate-pane", "--pane-id", tostring(initial_pane_id) })
  local _, image_pane_id = wezterm.exec_sync({ "cli", "get-pane-direction", "Prev" })
  return tonumber(image_pane_id, 10)
end

-- Send an image to the image pane (terminal split)
--- type function
--- @param path string, path to the image
--- @param image_pane_id number, the pane id of the image pane
--- @param initial_pane_id number, the pane id of the initial pane
--- @return nil
wezterm_api.send_image = function(path, image_pane_id, initial_pane_id)
  local placeholder = "wezterm imgcat --tmux-passthru detect %s \r"
  local image = string.format(placeholder, path)
  wezterm.exec_sync({ "cli", "activate-pane", "--pane-id", tostring(image_pane_id) })
  wezterm.exec_sync({
    "cli",
    "send-text",
    "--pane-id",
    tostring(image_pane_id),
    "--no-paste",
    image,
  })
  wezterm.exec_sync({ "cli", "activate-pane", "--pane-id", tostring(initial_pane_id) })
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
    tostring(image_pane_id),
    "--no-paste",
    "wezterm cli kill-pane --pane-id " .. image_pane_id .. "\r",
  })
end

return { wezterm_api = wezterm_api }
