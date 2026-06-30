# News

## 0.1.4

- Changed `-t` on macOS to target the active terminal app instead of falling back to `Terminal.app`.
- Added explicit macOS support for `Alacritty` terminal launches, including an `alacritty msg create-window` fallback when direct window control is unavailable.
- Documented terminal behavior updates and added CLI coverage for the macOS terminal dispatch logic.

## 0.1.3

- Added `--app` to choose `positron` or `rstudio` for project and Shiny launches.
- Added project registration support for saving a per-project default app, with `positron` as the fallback when none is configured.

## 0.1.2

- Fixed an issue where the `launch` command failed when installed from `main` due to a missing return statement in the parser builder.

## 0.1.1

- Updated `-t` flag to attempt opening the project in the current/active terminal window on macOS and Windows, and added a robust terminal fallback for Linux.
- Fixed a bug where the terminal flag caused a `TypeError`.
- Updated installation instructions to recommend `pipx` for a cleaner global installation.
- Improved documentation for developers and agents.

## 0.1.0

- Initial public release of `launch_pro`.
- Package the project as an installable Python CLI with the `launch` command.
- Store the user project registry in the standard per-user app-data directory.
- Support project launch, Shiny launch, GitHub launch, and `launch register`.
