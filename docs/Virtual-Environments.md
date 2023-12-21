# Virtual Environments

Installing python packages globally isn't recommended. Instead, you should install Molten python
dependencies in a virtual environment using [venv](https://docs.python.org/3/library/venv.html).

The main reason is that working without a virtual environment gets really messy really quickly, and
can just be impossible if you work on multiple python projects that have different dependency
version requirements. If you want to use this plugin with venv, you shouldn't have to add all of
Molten's dependencies to your project's virtual environment, that's what this guide is for.

To facilitate the creation and activation of 'global' virtual environments, I use a [venv
wrapper](https://gist.github.com/benlubas/5b5e38ae27d9bb8b5c756d8371e238e6). I would definitely
recommend a wrapper script of some kind if you are a python dev. If you're just installing these
deps to use Molten with a non-python kernel, you can skip the wrapper without much worry.

## Create a Virtual Environment

We'll create a virtual environment called `neovim` that will contain all of our Molten (and other
remote plugin dependencies).

Using the wrapper:
```bash
mkvenv neovim # create a new venv called neovim
venv neovim # activate the virtual environment
```

Not using the wrapper
```bash
mkdir ~/.virtualenvs
python -m venv ~/.virtualenvs/neovim # create a new venv
# note, activate is a bash/zsh script, use activate.fish for fish shell
source ~/.virtualenvs/neovim/bin/activate # activate the venv
```

## Install Dependencies

Make sure your venv is active (you can test with `echo $VIRTUAL_ENV`) then you can install the
python packages that relate to the types of output you want to render. Remember, `pynvim` and
`jupyter_client` are 100% necessary, everything else is optional. You can see what each package does
in the readme.

```bash
pip install pynvim jupyter_client cairosvg plotly kaleido pnglatex pyperclip
```

## Point Neovim at this Virtual Environment

add this to your neovim configuration
```lua
vim.g.python3_host_prog=vim.fn.expand("~/.virtualenvs/neovim/bin/python3")
```

## Install The Kernel In a Project Virtual Environment

In your project virtual environment (here named "project_name"), we need to run:

```bash
venv project_name # activate the project venv
pip install ipykernel
python -m ipykernel install --user --name project_name
```

Now, launch Neovim with the project venv active. You should be able to run `:MoltenInit
project_name` to start a Kernel for your project virtual environment.

### Automatically launch the correct Kernel

Assuming you followed the steps above, you may now have multiple python kernels all with names that
match their corresponding virtual environment. Calling `:MoltenInit` and selecting an option all the
time is kinda annoying, instead, we can add this mapping, which allows you to automatically
initialize the correct kernel.

```lua
vim.keymap.set("n", "<localleader>ip", function()
  local venv = os.getenv("VIRTUAL_ENV")
  if venv ~= nil then
    -- in the form of /home/benlubas/.virtualenvs/VENV_NAME
    venv = string.match(venv, "/.+/(.+)")
    vim.cmd(("MoltenInit %s"):format(venv))
  else
    vim.cmd("MoltenInit python3")
  end
end, { desc = "Initialize Molten for python3", silent = true })
```
