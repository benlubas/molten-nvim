local M = {}


---remove comments from the given string of code using treesitter
---@param str string code to remove comments from
---@param lang string language of the code
---@return string
M.remove_comments = function(str, lang)
  local parser = vim.treesitter.get_string_parser(str, lang)
  local tree = parser:parse()
  local root = tree[1]:root()
  -- create comment query
  local query = vim.treesitter.query.parse(lang, [[((comment) @c (#offset! @c 0 0 0 -1))]])
  -- split content lines
  local lines = vim.split(str, '\n')
  -- iterate over query match metadata
  for _, _, metadata in query:iter_matches(root, str, root:start(), root:end_(), {}) do
    local region = metadata[1].range
    local line = region[1] + 1
    local col_start = region[2]
    -- remove comment by extracting the text before
    lines[line] = string.sub(lines[line], 1, col_start)
  end
  -- remove blank lines
  lines = vim.tbl_filter(function(line) return line ~= '' end, lines)
  -- join lines
  local result = vim.fn.join(lines, '\n')
  return result
end

return M
