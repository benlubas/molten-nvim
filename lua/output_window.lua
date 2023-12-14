
local M = {}

---Calculate the y position of the output window
---@param buf_line number
---@return number
M.calculate_window_position = function(buf_line)
  local win = vim.api.nvim_get_current_win()
  local pos = vim.fn.screenpos(win, buf_line, 0)
  local topline = vim.fn.line('w0')
  local win_origin = vim.fn.screenpos(win, topline, 0)

  return pos.row - (win_origin.row - 1)
end

return M
