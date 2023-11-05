# Contributing

Contributions are more than welcome. Please keep the following in mind:

- If your contribution is large, please open an issue to discuss it *before* doing the work.
- Nothing breaking (unless it's necessary)
- The code is old and rather messy in some places
- This is a remote plugin. So it's written mostly in python using `pynvim` (which is not the best
documented thing out there), if you have questions about how to do something, I've probably done it
in this plugin, so just poke around, grep around, and you'll probably find it, or open an issue here
if you still have trouble.

## Dev Environment

This project is configured for the pyright language server and black code formatter.

### With nix

You can make use of the flake.nix in conjunction with direnv to easily build an environment with all
the dependencies. You will need the flakes experimental feature enabled.

### Without nix

You're kinda on your own. I've listed all the python requirements here. you can install them with
pip into a venv.

```bash
pip install plotly pnglatex pynvim pyperclip svgwrite sympy tqdm cairosvg ipykernel jupyter_client kaleido matplotlib
```

## Code Style

- `snake_case` names everywhere (except for user commands and vim functions)
- Black code formatting, please format your code
- try to avoid introducing new really long functions, there are already too many of those that
I need to refactor
- If you're going to notify the user via the notify api, there are utility functions for that

## Testing

There are no automated tests. Instead, when you've made a change, please test that you haven't
broken any of the examples in the
[test file](https://gist.github.com/benlubas/f145b6fe91a9eed5ee6bee9d3e100466) before you open a PR.
