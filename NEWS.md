# News

## 0.1.2

- Fixed an issue where the `launch` command failed when installed from `main` due to a missing return statement in the parser builder.
## 0.1.1

- Updated `-t` flag to attempt opening the project in the current/active terminal window on macOS and Windows, and added a robust terminal fallback for Linux.
- Fixed a bug where the terminal flag caused a `TypeError`.
- Updated installation instructions to recommend `pipx` for a cleaner global installation.
- Improved documentation for developers and agents.
## 0.1.0

- Initial public and public release of `launch_pro`.
- Package the project as an installable Python CLI with the `launch` command.
- Store the user project registry in the standard per-user app-data directory.
- Support project launch, Shiny launch, GitHub launch, and `launch register`.
