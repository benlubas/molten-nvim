local M = {}

---show the MoltenInit prompt with the given kernels
---started as shared kernels.
---@param kernels table<table> list of tuples of (str, bool)
---@param prompt string
M.prompt_init = function(kernels, prompt)
  vim.schedule_wrap(function()
    vim.ui.select(kernels, {
      prompt = prompt,
      format_item = function(item)
        if item[2] then
          return "(shared) " .. item[1]
        else
          return item[1]
        end
      end,
    }, function(choice)
      if choice ~= nil then
        vim.schedule_wrap(function()
          if choice[2] then
            vim.cmd("MoltenInit shared " .. choice[1])
          else
            vim.cmd("MoltenInit " .. choice[1])
          end
        end)()
      end
    end)
  end)()
end

---prompt the user for a kernel, and then run the command with that kernel. %k in the command means
---the kernel name will be substituted in.
---@param kernels table<string> list of kernels
---@param prompt string
---@param command string command, with %k substituted for the selected kernel name
M.select_and_run = function (kernels, prompt, command)
  vim.schedule_wrap(function()
    vim.ui.select(kernels, {
      prompt = prompt,
    }, function(choice)
      if choice ~= nil then
        vim.schedule_wrap(function()
            vim.cmd(command:gsub("%%k", choice))
        end)()
      end
    end)
  end)()
end

return M
