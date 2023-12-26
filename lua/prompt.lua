local M = {}

local format_shared = function(item)
  if item[2] then
    return "(shared) " .. item[1]
  else
    return item[1]
  end
end

---show the MoltenInit prompt with the given kernels
---started as shared kernels.
---@param kernels table<table> list of tuples of (str, bool)
---@param prompt string
M.prompt_init = function(kernels, prompt)
  vim.schedule_wrap(function()
    vim.ui.select(kernels, {
      prompt = prompt,
      format_item = format_shared,
    }, function(choice)
      if choice == nil then
        return
      end
      vim.schedule_wrap(function()
        if choice[2] then
          vim.cmd("MoltenInit shared " .. choice[1])
        else
          vim.cmd("MoltenInit " .. choice[1])
        end
      end)()
    end)
  end)()
end

---show the MoltenInit prompt with the given kernels
---started as shared kernels.
---@param kernels table<table> list of tuples of (str, bool)
---@param prompt string
---@param command string command, with %k substituted for the selected kernel name
M.prompt_init_and_run = function(kernels, prompt, command)
  vim.schedule_wrap(function()
    vim.ui.select(kernels, {
      prompt = prompt,
      format_item = format_shared,
    }, function(choice)
      if choice == nil then
        return
      end
      if choice[2] then
        vim.schedule_wrap(function()
          vim.cmd("MoltenInit shared " .. choice[1])
          vim.cmd(command:gsub("%%k", choice[1]))
        end)()
      else
        vim.api.nvim_create_autocmd("User", {
          pattern = "MoltenKernelReady",
          once = true,
          callback = function(e)
            vim.cmd(command:gsub("%%k", e.data.kernel_id))
          end,
        })
        vim.schedule_wrap(function()
          vim.cmd("MoltenInit " .. choice[1])
        end)()
      end
    end) -- ui select
  end)() -- vim.schedule_wrap
end

---prompt the user for a kernel, and then run the command with that kernel. %k in the command means
---the kernel name will be substituted in.
---@param kernels table<string> list of kernels
---@param prompt string
---@param command string command, with %k substituted for the selected kernel name
M.select_and_run = function(kernels, prompt, command)
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
