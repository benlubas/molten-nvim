# Changelog

## [1.1.6](https://github.com/benlubas/molten-nvim/compare/v1.1.5...v1.1.6) (2023-12-10)


### Bug Fixes

* don't delete running cells ([#75](https://github.com/benlubas/molten-nvim/issues/75)) ([6b2660d](https://github.com/benlubas/molten-nvim/commit/6b2660d790696dc41238b3bca19541e347e27bf2))
* progress bars in virtual text ([#77](https://github.com/benlubas/molten-nvim/issues/77)) ([3b886c1](https://github.com/benlubas/molten-nvim/commit/3b886c1e987ee9d2654e31f9d0a1234fce8bcb92))
* remove orphaned cells ([#73](https://github.com/benlubas/molten-nvim/issues/73)) ([b500515](https://github.com/benlubas/molten-nvim/commit/b5005158ddb16fd9c864de957eef92eca9ab1d72))

## [1.1.5](https://github.com/benlubas/molten-nvim/compare/v1.1.4...v1.1.5) (2023-11-30)


### Bug Fixes

* duplicate virt text/virt text wrap ([#70](https://github.com/benlubas/molten-nvim/issues/70)) ([71faa0d](https://github.com/benlubas/molten-nvim/commit/71faa0d98ee6aea2167f69d9c6c67ccab1571c14))
* healthcheck on python 3.11+ ([#65](https://github.com/benlubas/molten-nvim/issues/65)) ([523d0ec](https://github.com/benlubas/molten-nvim/commit/523d0eceb3349c8deb798f52c2d827fbfdd44668))
* truncate output text ([#67](https://github.com/benlubas/molten-nvim/issues/67)) ([3141b93](https://github.com/benlubas/molten-nvim/commit/3141b936ee69f15f3a926b122d110b0940e152e0))

## [1.1.4](https://github.com/benlubas/molten-nvim/compare/v1.1.3...v1.1.4) (2023-11-26)


### Bug Fixes

* images in output windows with virt text ([#55](https://github.com/benlubas/molten-nvim/issues/55)) ([18b6b9a](https://github.com/benlubas/molten-nvim/commit/18b6b9a680cbce2b037409df79e81e7fdc10c155))

## [1.1.3](https://github.com/benlubas/molten-nvim/compare/v1.1.2...v1.1.3) (2023-11-22)


### Bug Fixes

* images being pushed down doubly by virt text ([#53](https://github.com/benlubas/molten-nvim/issues/53)) ([909f6f8](https://github.com/benlubas/molten-nvim/commit/909f6f890b6c607ee802ff8662892880dd78baec))

## [1.1.2](https://github.com/benlubas/molten-nvim/compare/v1.1.1...v1.1.2) (2023-11-18)


### Bug Fixes

* enter float destroying virt output ([#46](https://github.com/benlubas/molten-nvim/issues/46)) ([49ac223](https://github.com/benlubas/molten-nvim/commit/49ac223b5486eb751fadfd627c7618c3b65ad8c4))

## [1.1.1](https://github.com/benlubas/molten-nvim/compare/v1.1.0...v1.1.1) (2023-11-18)


### Bug Fixes

* hide images when appropriate ([#44](https://github.com/benlubas/molten-nvim/issues/44)) ([f431035](https://github.com/benlubas/molten-nvim/commit/f4310356c6028b29da596888e0804655243f5db8))

## [1.1.0](https://github.com/benlubas/molten-nvim/compare/v1.0.0...v1.1.0) (2023-11-18)


### Features

* export cell output to ipynb file ([#40](https://github.com/benlubas/molten-nvim/issues/40)) ([ef9cb41](https://github.com/benlubas/molten-nvim/commit/ef9cb41381926878ee832b9c96d74accbb4fabdf))
* Output as Virtual Text ([#33](https://github.com/benlubas/molten-nvim/issues/33)) ([820463d](https://github.com/benlubas/molten-nvim/commit/820463df259d2c77d080e8106f1ad48ed4e8c7b7))

## 1.0.0 (2023-11-17)

### Features From Magma

- Start a kernel from a list of kernels
- Attach to already running jupyter kernel
- Send code to the Jupyter Kernel to run asynchronously
- View output in a floating window below the `cell` that you ran, including image outputs
- Cells are saved, and you can rerun them, they expand when you type, and you can pull up their
output again, and rerun them. Interact with the output in a vim buffer

### New Features (pre 1.0.0)

- Completely custom borders
- Border colors per run status
- "Cropped" window borders
- Window footer to display the number of extra lines that don't fit in the window
- configurable max window size
- Can specify no border without minimal style
- Buffers can be shared across kernels `:MoltenInit shared [kernal]`
- You can have multiple kernels running in one buffer, including the same kernel running more than
once
- Update configuration values on the fly
- Enter output can also open the output so you have one key to do both
- You can hide the output without leaving the cell
- Quitting an output window hides the output window (configurable)
- A function for running a range of lines, enabling user created code runners
- 
- Image rendering
    - Images are rendered with Image.nvim which has support for kitty and uberzug++. Much more
    consistent image rendering.
    - Configurable max image height
    - Allows for cropped images
    - CairoSVG is no longer required for rendering svg. The ImageMagic dependency of Image.nvim
    handles that for us
    - more image formats supported
- More graceful LaTeX image rendering errors
- `:MoltenInfo` command to see information about kernels
- Status line functions to see running kernels and/or initialization status


### Bug Fixes

- Kernel prompt actually works when used from the command line
- Close output command works from inside an output window
- Folding text above an output window is correctly accounted for
    - Similarly, virtual lines are correctly accounted for
- Window rendering performance: No longer redraw an open window ever, it's just updated
- Cell rendering performance: Don't redraw the cell highlights every time the window scrolls or the
cursor moves
- Run status is working again
- Save/load is working again
