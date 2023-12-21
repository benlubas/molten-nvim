local M = {}

local has_py_mod = function(mod)
  vim.cmd("python3 import pkgutil")
  vim.cmd("python3 import importlib")
  return vim.fn.py3eval("importlib.util.find_spec('" .. mod .. "') is not None")
end

local py_mod_check = function(mod, pip, required)
  if has_py_mod(mod) then
    vim.health.ok("Python module " .. pip .. " found")
  elseif required then
    vim.health.error("Required python module " .. pip .. " not found", "pip install " .. pip)
  else
    vim.health.warn("Optional python module " .. pip .. " not found", "pip install " .. pip)
  end
end

M.check = function()
  vim.health.start("molten-nvim")

  if vim.fn.has("nvim-0.9") == 1 then
    vim.health.ok("NeoVim >=0.9")
  else
    vim.health.error("molten-nvim requires NeoVim >=0.9")
  end

  if vim.fn.has("python3") == 0 then
    vim.health.error("molten-nvim requires a Python provider to be configured!")
    return
  end

  vim.cmd("python3 import sys")
  if vim.fn.py3eval("sys.version_info.major == 3 and sys.version_info.minor >= 10") then
    vim.health.ok("Python >=3.10")
  else
    vim.health.error("molten-nvim requires Python >=3.10")
  end

  py_mod_check("pynvim", "pynvim", true)
  py_mod_check("jupyter_client", "jupyter-client", true)
  py_mod_check("cairosvg", "cairosvg", false)
  py_mod_check("pnglatex", "pnglatex", false)
  py_mod_check("plotly", "plotly", false)
  py_mod_check("kaleido", "kaleido", false)
  py_mod_check("pyperclip", "pyperclip", false)
  py_mod_check("nbformat", "nbformat", false)
end

return M
