# NixOS Installation

There are several ways to get Molten working on NixOS. If you would like to install Molten with nix,
the Home Manager instructions provide an example of how to do that. It's also possible to manage
your neovim plugins with lazy.

These setups include setup for `image.nvim`. If you don't need image rendering, you can exclude the
lines marked `# for image rendering`.

## NixOS Home Manager Installation

If you use home manager and have configure Neovim through it, you can set up the dependencies like
so:

```nix
  # home.nix or wherever you configure neovim
  { pkgs, ... }:
  let
    # the vimPlugins.molten-nvim package has not been merged into nixpkgs yet but for now you can use this
    molten-nvim = pkgs.callPackage pkgs.vimUtils.buildVimPlugin {
      pname = "molten-nvim";
      version = "2023-10-21";
      src = fetchFromGitHub {
        owner = "benlubas";
        repo = "molten-nvim";
        rev = "f9c28efc13f7a262e27669b984f3839ff5c50c32";
        sha256 = "1r8xf3jphgml0pax34p50d67rglnq5mazdlmma1jnfkm67acxaac";
      };
      meta.homepage = "https://github.com/benlubas/molten-nvim/";
    };
  in {
    # ... other config
    programs.neovim = {
      # whatever other neovim configuration you have
      plugins = with pkgs.vimPlugins; [
        # ... other plugins
        image-nvim # for image rendering
        molten-nvim
      ];
      extraPackages = with pkgs; [
        # ... other packages
        imagemagick # for image rendering
      ];
      extraLuaPackages = ps: [
        # ... other lua packages
        magick # for image rendering
      ];
      extraPython3Packages = ps: with ps; [
        # ... other python packages
        pynvim
        jupyter-client
        cairosvg # for image rendering
        pnglatex # for image rendering
        plotly # for image rendering
        pyperclip
      ];
    };
  }
```

There are multiple ways to manage your Lua configuration so follow the instructions for setting up
`Image.nvim` and `molten-nvim` for your specific setup.

## Vanilla NixOS + lazy.nvim

This is an example setup with no home manager, and installing neovim plugins with lazy nvim. You
might want to do this if you want to keep a neovim configuration that works on systems that don't
have nix installed.

Just create a file and import it into `configuration.nix`.

```nix
{ lib, pkgs, neovimUtils, wrapNeovimUnstable, ... }:

let
  config = pkgs.neovimUtils.makeNeovimConfig {
    extraLuaPackages = p: with p; [
      # ... other lua packages
      p.magick # for image rendering
    ];
    extraPython3Packages = p: with p; [
      pynvim
      jupyter-client
      cairosvg # for image rendering
      ipython
      nbformat
      # ... other python packages
    ];
    extraPackages = p: with p; [
      imageMagick # for image rendering
      # ... other packages
    ];
    withNodeJs = true;
    withRuby = true;
    withPython3 = true;
    # https://github.com/NixOS/nixpkgs/issues/211998
    customRC = "luafile ~/.config/nvim/init.lua";
  };
in {
  nixpkgs.overlays = [
    (_: super: {
      neovim-custom = pkgs.wrapNeovimUnstable
        (super.neovim-unwrapped.overrideAttrs (oldAttrs: {
          buildInputs = oldAttrs.buildInputs ++ [ super.tree-sitter ];
        })) config;
    })
  ];

  environment.systemPackages = with pkgs; [
    neovim-custom

    # Can't install this with the rest of the python packages b/c this needs to be in path
    python3Packages.jupytext # if you want to use vim-jupytext or similar

    # ... other system packages
  ];
}
```
