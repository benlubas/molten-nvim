# I'm very new to nix, so this is probably really ugly. If you want to contribute to improve this,
# please do
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {nixpkgs, flake-utils, ...}:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python310;
      in {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            (python.withPackages (ps: with ps; [
              numpy
              pynvim
              jupyter_client
              ipykernel
              black
              pyperclip
              pnglatex
              cairosvg
              plotly
              matplotlib
              nbformat
              svgwrite
              sympy
              tqdm
            ]))

            nodePackages.pyright
          ];
        };
      }
    );
}
