local M = {}

M.set_default_highlight = function(group, value)
  -- if vim.api.nvim_get_hl(0, { name = group, create = false }) then
  if vim.fn.hlexists(group) == 0 then
    vim.api.nvim_set_hl(0, group, { default = false, link = value })
  end
end

return M
