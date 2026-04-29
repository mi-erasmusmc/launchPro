# Plan for Issue #5: Improve -t flag to open directory in current terminal window

## Objective
Modify the `-t` flag to attempt to send the `cd` command to the currently active/frontmost terminal window on macOS and Windows, and improve the fallback chain on Linux.

## Steps

### 1. macOS "Hijack" Implementation
- **Terminal.app**: Update AppleScript to use `do script "cd '...' in front window"`.
- **iTerm2**: Add support for `iTerm2` by attempting to send a command to the `current session` of the `frontmost window`.

### 2. Windows "Windows Terminal" Support
- Check if `wt.exe` is available.
- If available, use `wt.exe -d <path>` to open the directory in the existing terminal environment.
- Fallback to `start cmd` for legacy environments.

### 3. Linux Robustness
- Implement a prioritized fallback chain of terminals: `gnome-terminal`, `konsole`, `xfce4-terminal`, `alacritty`, `kitty`.
- Iterate through the list and attempt to run the command with the `--working-directory` flag until one succeeds.

### 4. Verification
- **Syntax Check**: `python3 -m py_compile src/launch_pro/cli.py`.
- **Functional Tests**: 
    - macOS: Verify it targets the front-most window.
    - Windows: Verify `wt.exe` usage if present.
    - Linux: Verify the fallback chain works.
