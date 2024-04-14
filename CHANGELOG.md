# Changelog

## [1.8.1](https://github.com/benlubas/molten-nvim/compare/v1.8.0...v1.8.1) (2024-04-14)


### Bug Fixes

* supply empty opts table to iter_matches ([#183](https://github.com/benlubas/molten-nvim/issues/183)) ([fb59bea](https://github.com/benlubas/molten-nvim/commit/fb59bea5b64e7259dc9bd7c5f54a0ca14c7005c6))
* surface error when failing to start kernel ([#182](https://github.com/benlubas/molten-nvim/issues/182)) ([7d97cab](https://github.com/benlubas/molten-nvim/commit/7d97cab8d6f26e0ec1ab56004221ee25d3c6daeb))

## [1.8.0](https://github.com/benlubas/molten-nvim/compare/v1.7.0...v1.8.0) (2024-03-30)


### Features

* execution time ([#153](https://github.com/benlubas/molten-nvim/issues/153)) ([12fc198](https://github.com/benlubas/molten-nvim/commit/12fc198e1dac89cde3e9512b2999972da01dc625))
* wezterm image provider ([#162](https://github.com/benlubas/molten-nvim/issues/162)) ([4ef66a1](https://github.com/benlubas/molten-nvim/commit/4ef66a162222065f278a5ea92f19eaa9e8b7301c))
* write connection file ([#176](https://github.com/benlubas/molten-nvim/issues/176)) ([5bc04c9](https://github.com/benlubas/molten-nvim/commit/5bc04c9b985ea7b9d13358b17d82f578021b332e))


### Bug Fixes

* catch error on nonexistant kernel init ([#172](https://github.com/benlubas/molten-nvim/issues/172)) ([2fffc76](https://github.com/benlubas/molten-nvim/commit/2fffc76616b645f8e0fff65a3acb89e5f38bd2a9))
* don't require pillow unless it's used ([#164](https://github.com/benlubas/molten-nvim/issues/164)) ([ca725ae](https://github.com/benlubas/molten-nvim/commit/ca725ae7928b292bbda1fc90eeeae701026c6e83))
* make sure there is a visual selection ([#159](https://github.com/benlubas/molten-nvim/issues/159)) ([7d8bd23](https://github.com/benlubas/molten-nvim/commit/7d8bd23e3b36bfc911f7af361f3e1c311c61e8e7))
* make UpdateInterface sync ([#166](https://github.com/benlubas/molten-nvim/issues/166)) ([8d31d04](https://github.com/benlubas/molten-nvim/commit/8d31d04e18acc419f147452861ad5eb34b998276))

## [1.7.0](https://github.com/benlubas/molten-nvim/compare/v1.6.0...v1.7.0) (2024-02-23)


### Features

* Cover Empty Lines ([#129](https://github.com/benlubas/molten-nvim/issues/129)) ([2f50650](https://github.com/benlubas/molten-nvim/commit/2f50650d2712229c2008c65490ea0915b9e88879))
* open images externally ([#150](https://github.com/benlubas/molten-nvim/issues/150)) ([3ca888e](https://github.com/benlubas/molten-nvim/commit/3ca888e5a3e554ce7fcda815a79e6eb4d018a35a))


### Bug Fixes

* small bugs ([65da69e](https://github.com/benlubas/molten-nvim/commit/65da69e669953d9d2bc89bc400ef5595779d8062))

## [1.6.0](https://github.com/benlubas/molten-nvim/compare/v1.5.2...v1.6.0) (2024-01-20)


### Features

* handle input_request messages ([#136](https://github.com/benlubas/molten-nvim/issues/136)) ([4a3980f](https://github.com/benlubas/molten-nvim/commit/4a3980f74742ac6f151cc00e444e74fc02b799a2))


### Bug Fixes

* error io ([#135](https://github.com/benlubas/molten-nvim/issues/135)) ([3883374](https://github.com/benlubas/molten-nvim/commit/38833744d5cdffc5cfc84b2be0c5449b5b132495))

## [1.5.2](https://github.com/benlubas/molten-nvim/compare/v1.5.1...v1.5.2) (2024-01-18)


### Bug Fixes

* none check on import loading ([#130](https://github.com/benlubas/molten-nvim/issues/130)) ([921e6e9](https://github.com/benlubas/molten-nvim/commit/921e6e9021dccd48f2d4a43be234ca9c118ef065))

## [1.5.1](https://github.com/benlubas/molten-nvim/compare/v1.5.0...v1.5.1) (2024-01-07)


### Bug Fixes

* forgot the virtual lines ([#127](https://github.com/benlubas/molten-nvim/issues/127)) ([3733aa8](https://github.com/benlubas/molten-nvim/commit/3733aa8d9dfb433dcf570d413e3da7c0a3b1a60b))

## [1.5.0](https://github.com/benlubas/molten-nvim/compare/v1.4.0...v1.5.0) (2024-01-06)


### Features

* MoltenAvailableKernels ([#124](https://github.com/benlubas/molten-nvim/issues/124)) ([36a4e9e](https://github.com/benlubas/molten-nvim/commit/36a4e9eb435ff890127c7cb45c50d3efe0819f00))

## [1.4.0](https://github.com/benlubas/molten-nvim/compare/v1.3.1...v1.4.0) (2024-01-06)


### Features

* configurable tick_rate ([#123](https://github.com/benlubas/molten-nvim/issues/123)) ([d79f48c](https://github.com/benlubas/molten-nvim/commit/d79f48c010639d7bc59fb695a1e94ccf96040cab))


### Bug Fixes

* mark imported cells DONE so no re-render ([#119](https://github.com/benlubas/molten-nvim/issues/119)) ([2adcc7f](https://github.com/benlubas/molten-nvim/commit/2adcc7f8b99ade56eac8f7250e4e8cbfb68a151d))
* progress bar exports and similar ([#122](https://github.com/benlubas/molten-nvim/issues/122)) ([bee4bb5](https://github.com/benlubas/molten-nvim/commit/bee4bb5b43d20d2cdd88f1555af92d362f3aa362))

## [1.3.1](https://github.com/benlubas/molten-nvim/compare/v1.3.0...v1.3.1) (2023-12-31)


### Bug Fixes

* account for stream jupter outputs ([#113](https://github.com/benlubas/molten-nvim/issues/113)) ([54e7450](https://github.com/benlubas/molten-nvim/commit/54e7450479cb9883a30bea6881965686da79e629))
* **docs:** image nvim provider config option ([#114](https://github.com/benlubas/molten-nvim/issues/114)) ([02561e0](https://github.com/benlubas/molten-nvim/commit/02561e0301910eaae1ba70ba247dc85e0ea3d517))
* don't add image height twice ([#107](https://github.com/benlubas/molten-nvim/issues/107)) ([8a661e7](https://github.com/benlubas/molten-nvim/commit/8a661e714c9761302f7e63d21c1396e2e25c7ddc))
* dont clear img on win changed ([#110](https://github.com/benlubas/molten-nvim/issues/110)) ([ab0eec9](https://github.com/benlubas/molten-nvim/commit/ab0eec985cc16549518453e2cfe5a770b560998d))

## [1.3.0](https://github.com/benlubas/molten-nvim/compare/v1.2.0...v1.3.0) (2023-12-26)


### Features

* auto init ([#104](https://github.com/benlubas/molten-nvim/issues/104)) ([744be0d](https://github.com/benlubas/molten-nvim/commit/744be0df2d31fb007d0a05ddbe84e3c73024c86b))
* import outputs from ipynb files ([#94](https://github.com/benlubas/molten-nvim/issues/94)) ([427ecea](https://github.com/benlubas/molten-nvim/commit/427eceac033544fbf1dc50db15918510a837536c))
* MoltenInit revamp + bug fixes ([#103](https://github.com/benlubas/molten-nvim/issues/103)) ([b626f8d](https://github.com/benlubas/molten-nvim/commit/b626f8d848ed01d648357f5b3d223fddcc732dcf))


### Bug Fixes

* import nb format when needed ([#100](https://github.com/benlubas/molten-nvim/issues/100)) ([75ce8fe](https://github.com/benlubas/molten-nvim/commit/75ce8fe3cc8206f8fd3ecdc315e16c47f0ddb75c))
* status methods in unfamiliar buffer ([#91](https://github.com/benlubas/molten-nvim/issues/91)) ([23e0c79](https://github.com/benlubas/molten-nvim/commit/23e0c79d190d861348733c526a40e7b8ce141c98))
* trailing comments are removed for comparison ([#99](https://github.com/benlubas/molten-nvim/issues/99)) ([af86259](https://github.com/benlubas/molten-nvim/commit/af86259f22a2286c3ff4334acf5a6858c687418d))

## [1.2.0](https://github.com/benlubas/molten-nvim/compare/v1.1.6...v1.2.0) (2023-12-16)


### Features

* :ReevaluateAllCells command ([#85](https://github.com/benlubas/molten-nvim/issues/85)) ([6da3d19](https://github.com/benlubas/molten-nvim/commit/6da3d1934922bfde5ba6ccf27b465a23e6190115))
* cache output text for floats ([#84](https://github.com/benlubas/molten-nvim/issues/84)) ([1ba4023](https://github.com/benlubas/molten-nvim/commit/1ba4023319c23a49f575d5b6a6d37239a4d3312f))
* MoltenEvaluateRange non-strict indexing ([#81](https://github.com/benlubas/molten-nvim/issues/81)) ([955b0e8](https://github.com/benlubas/molten-nvim/commit/955b0e8d1beecce0e78b4a7b5b70037a16daa94d))
* MoltenOpenInBrowser command ([#87](https://github.com/benlubas/molten-nvim/issues/87)) ([ebf2bda](https://github.com/benlubas/molten-nvim/commit/ebf2bda74e8b903222ad0378ffda57c9afb5cc84))


### Bug Fixes

* account for windows not at the top of screen ([#82](https://github.com/benlubas/molten-nvim/issues/82)) ([900441a](https://github.com/benlubas/molten-nvim/commit/900441aa5d39e1847d180b7aead7b538c4678176))
* window positioning logic (again) ([#89](https://github.com/benlubas/molten-nvim/issues/89)) ([aa45835](https://github.com/benlubas/molten-nvim/commit/aa45835f2830b1040568f32060e4b5ecb2e003f6))

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
