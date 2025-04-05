-- loads the snacks.nvim plugin and exposes methods to the python remote plugin
local ok, snacks = pcall(require, "snacks")

if not ok then
  vim.api.nvim_echo({ { "[Molten] `snacks.nvim` not found" } }, true, { err = true })
  return
end

local snacks_api = {}
local images = {}

snacks_api.from_file = function(path, opts)
  opts.opts = {
    inline = true,
    pos = { opts.y, opts.x },
    max_height = opts.max_height,
    max_width = opts.max_width,
  }
  opts.placement = nil

  images[path] = opts
  return path
end

snacks_api.render = function(identifier)
  local img = images[identifier]

  if img.placement == nil then
    img.placement = Snacks.image.placement.new(img.buffer, identifier, img.opts)
  end
end

snacks_api.clear = function(identifier)
  local img = images[identifier]
  if img and img.placeement then
    img.placement:close()
    img.placement = nil
  end
end

snacks_api.clear_all = function()
  for _, img in pairs(images) do
    snacks_api.clear(img)
  end
end

--- try to estimate actual size based on raw image and snack opts. Actual rendered size is somewhat random but we cannot get it due to it not being available until after render()
snacks_api.image_size = function(identifier)
  local img = images[identifier]
  local size =
    snacks.image.util.fit(identifier, { width = img.opts.max_width, height = img.opts.max_height })
  return size
end

return { snacks_api = snacks_api }
