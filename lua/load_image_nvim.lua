-- loads the image.nvim plugin and exposes methods to the python remote plugin
local ok, image = pcall(require, "image")

if not ok then
  vim.api.nvim_err_writeln("[Molten] `image.nvim` not found")
  return
end

local utils = require("image.utils")

local image_api = {}
local images = {}

image_api.from_file = function(path, opts)
  if opts.window and opts.window == vim.NIL then
    opts.window = nil
  end
  images[path] = image.from_file(path, opts or {})
  return path
end

image_api.render = function(identifier, geometry)
  geometry = geometry or {}
  local img = images[identifier]

  -- a way to render images in windows when only their buffer is set
  if img.buffer and not img.window then
    local buf_win = vim.fn.getbufinfo(img.buffer)[1].windows
    if #buf_win > 0 then
      img.window = buf_win[1]
    end
  end

  -- only render when the window is visible
  if not img.window or not vim.api.nvim_win_is_valid(img.window) then
    img.window = nil
  end

  if img.window then
    img:render(geometry)
  end
end

image_api.clear = function(identifier)
  images[identifier]:clear()
end

image_api.clear_all = function()
  for _, img in pairs(images) do
    img:clear()
  end
end

image_api.move = function(identifier, x, y)
  images[identifier]:move(x, y)
end

---returns the max height this image can be displayed at considering the image size and user's max
---width/height settings. Does not consider max width/height percent values.
image_api.image_size = function(identifier)
  local img = images[identifier]
  local term_size = require("image.utils.term").get_size()
  local gopts = img.global_state.options
  local true_size = {
    width = math.min(img.image_width / term_size.cell_width, gopts.max_width or math.huge),
    height = math.min(img.image_height / term_size.cell_height, gopts.max_height or math.huge),
  }
  local width, height = utils.math.adjust_to_aspect_ratio(
    term_size,
    img.image_width,
    img.image_height,
    true_size.width,
    true_size.height
  )
  return { width = math.ceil(width), height = math.ceil(height) }
end

return { image_api = image_api }
