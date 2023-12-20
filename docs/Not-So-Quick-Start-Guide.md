# Not So Quick Start Guide

This will walk you through the install, light configuration, and basic usage! It's a little less
than quick in the interest of explaining what's necessary and what's not.

## Installation

### Dependencies

This plugin has many dependencies if you would like the full experience. Most of these dependencies
are optional and are only necessary if you would like image support.

#### Image.nvim

[Image.nvim](https://github.com/3rd/image.nvim) is a neovim plugin that provides an api for
rendering images. Rending images in the terminal is not the most straight forward thing in the
world. As such, I'd recommend clicking that link, configuring image.nvim, making sure it works
with their builtin markdown integration, and then coming back here to finish setting up Molten.

##### After Image.nvim is working

There are a few image.nvim config options that will dramatically improve your experience. Here is
a sample configuration that leaves out the document integrations (note if you want to disable these,
please see the [image.nvim](https://github.com/3rd/image.nvim) readme.

```lua
-- image nvim options table. Pass to `require('image').setup`
{
  backend = "kitty", -- Kitty will provide the best experience, but you need a compatible terminal
  integrations = {}, -- do whatever you want with image.nvim's integrations
  max_width = 100, -- tweak to preference
  max_height = 12, -- ^
  max_height_window_percentage = math.huge, -- this is necessary for a good experience
  max_width_window_percentage = math.huge,
  window_overlap_clear_enabled = true,
  window_overlap_clear_ft_ignore = { "cmp_menu", "cmp_docs", "" },
},
```

**Important**: `max_width` and `max_height` _must_ be set, or large images can cause your terminal
to crash. I recommend the values 100 and 12, that feels natural to me, but feel free to increase or
decrease as you see fit (font size will make a large difference here).

Less important but still important: Setting `max_height_window_percentage` to `math.huge` is
necessary for Molten to render output windows at the correct dimensions. This value defaults to
50 or 60%, and for a plugin like Molten, which tries to display a window that's only as tall as it
needs to be, window percentage caps are problematic. Note that even setting this value to 100% is not
enough, as this can cause images to be resized instead of cropped when the molten output window is
partially off-screen, and the image is (until you scroll) taller than the window.


##### Pinning Image.nvim version

Image.nvim is still in it's early stages, and as such, breaks more often than other plugins. For the
most reliable experience with Molten, you should pin the version of image.nvim that you use.

Different package managers allow for pinning versions differently, so please refer to your package
manager's documentation if you don't use Lazy.

> [!NOTE]
> Note that I will always use the latest version of image.nvim, and will try to keep this doc up to
> date with the last working version. But if you're having issues with the version listed here,
> please first try the latest image.nvim version, and then open an issue or pr.

```lua
version = "1.1.0",
```

#### Python Deps

**Note**: It's recommended that you install python packages in a virtual environment as outlined in
the [venv guide](./Virtual-Environments.md)

**Absolutely necessary python packages:**
- [`pynvim`](https://github.com/neovim/pynvim) (for the Remote Plugin API)
- [`jupyter_client`](https://github.com/jupyter/jupyter_client) (for interacting with Jupyter)

**Packages only required for their specific image support:**
- [`cairosvg`](https://cairosvg.org/) (for displaying transparent SVG images)
    - If you don't have cariosvg installed, we fallback to image.nvim's svg support, which uses the
    ImageMagic library. From what I've gathered, this library has differing levels of support for
    SVGs with transparent backgrounds. So I'd recommend trying to get away without cairo, and only
    installing it if you notice an issue.
- [`pnglatex`](https://pypi.org/project/pnglatex/) (for displaying TeX formulas)
    - Note that this has additional, non-pip, dependencies. You need a TeX distribution installed on
    your machine as well as the following executables: `pdftopnm`, `pnmtopng`, `pdfcrop` which you
    can find through your system package manager.
- `plotly` and `kaleido` (for displaying Plotly figures)
    - In order to render plotly figures you might also needed `nbformat` installed in the project
    venv, unfortunately installing it in the neovim venv did not work (see [venv
    guide](./Virtual-Environments.md))
- `pyperclip` if you want to use `molten_copy_output`

#### .NET Deps
- `dotnet tool install -g Microsoft.dotnet-interactive`
- `dotnet interactive jupyter install`

> [!NOTE]
> I personally do not use .NET (nor have I ever), all the tooling for .NET is working in theory, but
> hasn't been tested by myself. This is something Magma supported, and there's no reason that it
> shouldn't still work, but I'll be able to provide limited help here.

### Sample Lazy.nvim Config

```lua
return {
    {
        "benlubas/molten-nvim",
        version = "^1.0.0", -- use version <2.0.0 to avoid breaking changes
        dependencies = { "3rd/image.nvim" },
        build = ":UpdateRemotePlugins",
        init = function()
            -- these are examples, not defaults. Please see the readme
            vim.g.molten_image_provider = "image.nvim"
            vim.g.molten_output_win_max_height = 20
        end,
    },
    {
        -- see the image.nvim readme for more information about configuring this plugin
        "3rd/image.nvim",
        opts = {
            backend = "kitty", -- whatever backend you would like to use
            max_width = 100,
            max_height = 12,
            max_height_window_percentage = math.huge,
            max_width_window_percentage = math.huge,
            window_overlap_clear_enabled = true, -- toggles images when windows are overlapped
            window_overlap_clear_ft_ignore = { "cmp_menu", "cmp_docs", "" },
        },
    }
},
```

### A Note on Remote Plugins

Molten is a remote plugin. This means that the first time you install, and after you update Molten
you need to run the `:UpdateRemotePlugins` command in Neovim. This can be done with some package
mangers (like Lazy for example) automatically.

But if things aren't working, make sure that you run that command and then restart your editor.

> [!WARNING]
> Windows users see [the windows page](./Windows.md)

### Customize

The README is the best resource for customization info. Additionally, you'll want to setup some
keybinds for common commands like `:MoltenEvaluateVisual`, more information about doing this is also
in the README!
