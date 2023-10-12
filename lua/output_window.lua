
local M = {}

---Calculate the y position of the output window, accounting for folds, extmarks, and scroll.
---@param buf number
---@param buf_line number
---@return number
M.calculate_window_position = function(buf, buf_line)
  -- code modified from image.nvim https://github.com/3rd/image.nvim/blob/16f54077ca91fa8c4d1239cc3c1b6663dd169092/lua/image/renderer.lua#L254
  local win_top = vim.fn.line("w0")
  if win_top == nil then return buf_line end
  local offset = 0

  if vim.wo.foldenable then
    local i = win_top
    while i <= buf_line do
      local fold_start, fold_end = vim.fn.foldclosed(i), vim.fn.foldclosedend(i)

      if fold_start ~= -1 and fold_end ~= -1 then
        offset = offset + (fold_end - fold_start)
        i = fold_end + 1
      else
        i = i + 1
      end
    end
  end

  local extmarks = vim.tbl_map(
    function(mark)
      local mark_id, mark_row, mark_col, mark_opts = unpack(mark)
      local virt_height = #(mark_opts.virt_lines or {})
      return { id = mark_id, row = mark_row, col = mark_col, height = virt_height }
    end,
    vim.api.nvim_buf_get_extmarks(
      buf,
      -1,
      { win_top - 1, 0 },
      { buf_line - 1, 0 },
      { details = true }
    )
  )
  for _, mark in ipairs(extmarks) do
    if mark.row + 1 ~= buf_line then offset = offset - mark.height end
  end

  return buf_line - win_top + 1 - offset
end

return M
