local M = {}

M.set_default_highlights = function(values)
  for group, value in pairs(values) do
    if vim.fn.hlexists(group) == 0 then
      vim.api.nvim_set_hl(0, group, { default = false, link = value })
    end
  end
end

return M
