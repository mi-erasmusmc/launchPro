# launchPro

`launchPro` is a small Python CLI for opening local RStudio projects, optional Shiny project folders, and project GitHub pages from a single command.

Current version: `0.1.0`

## Requirements

- Python 3.9 or newer
- A local project folder containing exactly one `.Rproj` file
- macOS, Linux, or Windows

## Setup

Install it with `pip` from the repository root:

```bash
git clone https://github.com/mi-erasmusmc/launchPro
cd launchPro
python3 -m pip install .
```

This installs a terminal command named `launch`. After installation, run `launch` from any directory in the same Python environment.

If your terminal cannot find `launch`, add the Python scripts directory to `PATH`.

- macOS:

```bash
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
rehash
```

- Linux:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
hash -r
```

- Windows:

Add `%APPDATA%\Python\Python39\Scripts` to your user `Path`, then open a new terminal.

Then verify:

```bash
command -v launch
launch --help
```

The CLI creates its runtime `projects.json` on first use in the standard per-user app-data location:

- macOS: `~/Library/Application Support/launch_pro/projects.json`
- Linux: `${XDG_DATA_HOME:-~/.local/share}/launch_pro/projects.json`
- Windows: `%LOCALAPPDATA%\\launch_pro\\projects.json`

## Run the CLI

Show help:

```bash
launch --help
```

Register a project first:

```bash
launch register MyProject ~/Documents/my-project - https://github.com/your-org/my-project
launch register MyStudy ~/Documents/my-study ~/Documents/my-study/inst/shiny/App https://github.com/your-org/my-study
```

Then open the main project folder:

```bash
launch MyProject -p
```

Open the Shiny project and GitHub page:

```bash
launch MyStudy -s -g
```

If no flag is provided, `launch` opens the main project by default:

```bash
launch MyProject
```

## Register a New Project

Add or update a project entry in the app-data `projects.json`:

```bash
launch register MyProject ~/Documents/my-project - https://github.com/your-org/my-project
```

Use `-` when the project does not have a Shiny folder. If it does, pass the Shiny directory instead:

```bash
launch register MyStudy ~/Documents/my-study ~/Documents/my-study/inst/shiny/App https://github.com/your-org/my-study
```

## Notes

- Paths may use `~` and environment variables.
- The CLI fails if a target folder does not exist or contains zero or multiple `.Rproj` files.
- On macOS it uses `open`, on Linux `xdg-open`, and on Windows the system default file opener.
- For local development without installing, run `./launch ...` from the repository root.

## License

This project is licensed under the Apache License 2.0. See `LICENSE` for the full text.
