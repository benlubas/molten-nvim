
# Features

A more complete list of features, and a list of some of the things that have been added to Magma to
make Molten

## Features From Magma

- Start a kernel from a list of kernels
- Attach to already running jupyter kernel
- Send code to the Jupyter Kernel to run asynchronously
- View output in a floating window below the `cell` that you ran, including image outputs
- Cells are saved, and you can rerun them, they expand when you type, and you can pull up their
output again, and rerun them. Interact with the output in a vim buffer

## Additions/Changes to Magma

- Completely custom borders
- Border colors per run status
- "Cropped" window borders
- Window footer to display the number of extra lines that don't fit in the window
- configurable max window size
- Can specify no border without minimal style
- Buffers can be shared across kernels `:MoltenInit shared [kernal]`
- You can have multiple kernels running in one buffer, including the same kernel running more than
once
- Kernel prompt actually works when used from the command line
- Update configuration values on the fly
- Enter output can also open the output so you have one key to do both
- You can hide the output without leaving the cell
- Close output command works from inside an output window
- Quitting an output window hides the output window (configurable)
- Fold support. Folding text above an output window is correctly accounted for
    - Similarly, virtual lines are correctly accounted for
- A function for running a range of lines, enabling user created code runners
- Window rendering. No longer redraw an open window ever, it's just updated
- Cell rendering. We don't redraw the cell highlights every time the window scrolls or the cursor
moves
- Image rendering
    - Images are rendered with Image.nvim which has support for kitty and uberzug++. The image
    rendering is much more consistent than it used to be
    - Configurable max image height
    - Allows for cropped images
    - CairoSVG is no longer required for rendering svg. The ImageMagic dependency of Image.nvim
    handles that for us
    - Arbitrary image support
- More graceful LaTeX image rendering errors
- Many bug fixes, notably:
    - Run status is working again
    - Save/load is working again
- `:MoltenInfo` command to see information about kernels
- Status line functions to see running kernels and/or initialization status

There are probably more than I'm forgetting. a lot has changed
