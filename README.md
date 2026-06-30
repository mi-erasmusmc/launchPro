# launchPro

`launchPro` is a small Python CLI for opening local Positron or RStudio projects, optional Shiny project folders, and project GitHub pages from a single command.

Current version: `0.1.5`

## Requirements

- Python 3.9 or newer
- A local project folder
- An `.Rproj` file only when opening the project in RStudio
- Windows, macOS or Linux

## Setup

The recommended way to install `launchPro` is using `pipx`, which installs the package in an isolated environment and automatically manages your `PATH`.

### Using pipx (Recommended)

```bash
git clone https://github.com/mi-erasmusmc/launchPro
cd launchPro
pipx install .
```

### Using pip (Alternative)

If you prefer using `pip`, you can install it directly, but you may need to manually add the Python scripts directory to your `PATH`.

```bash
python3 -m pip install .
```

If your terminal cannot find `launch`, add the Python scripts directory to `PATH`:

- Windows:
  Run `py -m site --user-base`, append `\Python39\Scripts` to the returned path, add that folder to your user `Path`, then open a new terminal.
- macOS:
  Add `~/Library/Python/3.x/bin` to your shell `PATH`, restart the terminal, and verify with `launch --help`.
- Linux:
  Add `~/.local/bin` to your shell `PATH`, restart the terminal, and verify with `launch --help`.

The CLI creates its runtime `projects.json` on first use in the standard per-user app-data location:

- Windows: `%LOCALAPPDATA%\\launch_pro\\projects.json`
- macOS: `~/Library/Application Support/launch_pro/projects.json`
- Linux: `${XDG_DATA_HOME:-~/.local/share}/launch_pro/projects.json`


## Run the CLI

Show help:

```bash
launch --help
```

Register a project first:

```bash
launch register MyProject ~/Documents/my-project - https://github.com/your-org/my-project
launch register MyStudy ~/Documents/my-study ~/Documents/my-study/inst/shiny/App https://github.com/your-org/my-study --app rstudio
```

Then open the main project folder:

```bash
launch MyProject -p
```

Open the same project in RStudio:

```bash
launch MyProject -p --app rstudio
```

Open the Shiny project and GitHub page:

```bash
launch MyStudy -s -g
```

Open the project folder in a terminal:

```bash
launch MyProject -t
```

If no flag is provided, `launch` uses the registered app for that project, or Positron when no project default was saved:

```bash
launch MyProject
```

Choose the project application explicitly with `--app positron` or `--app rstudio`.

## Register a New Project

Add or update a project entry in the app-data `projects.json`:

```bash
launch register MyProject ~/Documents/my-project - https://github.com/your-org/my-project
```

Save a default project application while registering:

```bash
launch register MyProject ~/Documents/my-project - https://github.com/your-org/my-project --app rstudio
```

Use `-` when the project does not have a Shiny folder. If it does, pass the Shiny directory instead:

```bash
launch register MyStudy ~/Documents/my-study ~/Documents/my-study/inst/shiny/App https://github.com/your-org/my-study
```

## Notes

- Paths may use `~` and environment variables.
- Positron opens the project or Shiny folder as a workspace target, even when that folder does not contain an `.Rproj` file.
- RStudio still requires the target folder to contain exactly one `.Rproj` file.
- On macOS, `-t` targets the active terminal app instead of falling back to `Terminal.app`. `Terminal`, `iTerm2`, and `Alacritty` are supported.
- On macOS, the `Alacritty` path uses Accessibility-driven keystrokes for the active window and falls back to `alacritty msg create-window --working-directory ...` if needed.
- On macOS it opens project files in the selected app with `open -a`.
- On Linux and Windows it looks for the selected `positron` or `rstudio` executable in `PATH`.
- On Linux, terminal detection includes `gnome-terminal`, `konsole`, `xfce4-terminal`, `alacritty`, and `kitty`.
- For local development without installing, run `./launch ...` from the repository root.

## License

This project is licensed under the Apache License 2.0. See `LICENSE` for the full text.
