local M = {}

local has_py_mod = function(mod)
  vim.cmd("python3 import importlib")
  return vim.fn.py3eval("importlib.util.find_spec(vim.eval('" .. mod .. "')) is not None")
end

local py_mod_check = function(mod, pip)
  if has_py_mod(mod) then
    vim.health.ok("Python package " .. pip .. " found")
  else
    vim.health.error("Python package " .. pip .. " not found", "pip install " .. pip)
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
  if vim.fn.py3eval("sys.version_info.major == 3 and sys.version_info.minor >= 10") == 1 then
    vim.health.ok("Python >=3.10")
  else
    vim.health.error("molten-nvim requires Python >=3.10")
  end

  py_mod_check("pynvim", "pynvim")
  py_mod_check("jupyter_client", "jupyter-client")
  py_mod_check("cairosvg", "cairosvg")
  py_mod_check("pnglatex", "pnglatex")
  py_mod_check("plotly", "plotly")
  py_mod_check("kaleido", "kaleido")
  py_mod_check("pyperclip", "pyperclip")
end

return M
