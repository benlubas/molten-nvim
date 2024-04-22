
local M = {}

---Calculate the y position of the output window
---@param buf_line number
---@return number
M.calculate_window_position = function(buf_line)
  local win = vim.api.nvim_get_current_win()
  local num_lines = vim.fn.line("$")
  local pos = vim.fn.screenpos(win, math.min(num_lines, buf_line), 0)
  local win_off = vim.fn.getwininfo(win)[1].winrow

  return pos.row - (win_off - 1)
end

return M
