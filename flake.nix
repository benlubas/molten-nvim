# I'm very new to nix, so this is probably really ugly. If you want to contribute to improve this,
# please do
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    { nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        molten-nvim = pkgs.callPackage pkgs.vimUtils.buildVimPlugin {
          pname = "molten-nvim";
          version = "unstable";
          # Will use current branch / source, hence marked as "unstable"
          src = ./.;
          # Might be a bit of a bug in buildVimPlugin, but nulling this out with
          # a space seems to reliably work, the offending call is here:
          path = " ";
          meta.homepage = "https://github.com/benlubas/molten-nvim/";
        };
        config = pkgs.neovimUtils.makeNeovimConfig {
          # TODO: Break these out for more modularity. Good for dev env, but not
          # really needed.
          extraPython3Packages = p:
            with p; [
              # Required
              pynvim
              jupyter_client

              # Optional Extensions
              ipykernel
              pyperclip
              pnglatex
              cairosvg # for image rendering

              # Common
              numpy
              black
              plotly
              matplotlib
              nbformat
              svgwrite
              sympy
              tqdm
            ];
          extraLuaPackages = p:
            with p; [
              p.magick # for image rendering
            ];
          extraPackages = p:
            with p; [
              imageMagick # for image rendering
            ];
          plugins = [
            { plugin = molten-nvim; }
            # for image rendering
            { plugin = pkgs.vimPlugins.image-nvim; }
          ];
          withNodeJs = true;
          withRuby = true;
          withPython3 = true;
        };

        neovim-custom =
          pkgs.wrapNeovimUnstable
            (pkgs.neovim-unwrapped.overrideAttrs (oldAttrs: {
              buildInputs = oldAttrs.buildInputs ++ [ pkgs.tree-sitter ];
            }))
            config;
      in
      rec {
        checks = {
          # Example of how to run unit tests using flakes.
          check = pkgs.stdenv.mkDerivation {
            name = "kernel-check";
            src = ./.;
            doCheck = true;
            checkPhase = ''
              # Start up nvim and start kernel
              # Note: Fails if can't start kernel in 1 second
              ${packages.molten}/bin/molten --headless \
                   -c ':MoltenInit python3' \
                   -c 'sleep 1' \
                   +q \
                   2>&1 | grep "\[Molten\] Kernel 'python3' (id: python3) is ready." || exit 1
              echo OK > $out
            '';
          };
        };

        packages = rec {
          molten = pkgs.writeShellScriptBin "molten" ''
            PATH=$PATH:${pkgs.python3Packages.jupytext}/bin ${neovim-custom}/bin/nvim \
                -c "set runtimepath+=${./.}" "$@"
          '';
          default = molten;
        };
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            config.python3Env
            pkgs.python3Packages.jupytext
            nodePackages.pyright
          ];
        };
      }
    );
}
