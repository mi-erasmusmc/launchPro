from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


APP_NAME = "launch_pro"
PROJECTS_FILENAME = "projects.json"
ENV_PROJECTS_FILE = "LAUNCH_PROJECTS_FILE"
DEFAULT_PROJECT_APPLICATION = "positron"
PROJECT_APPLICATION_COMMANDS = {
  "positron": ("positron", "Positron"),
  "rstudio": ("rstudio", "RStudio"),
}
LINUX_TERMINALS = ("gnome-terminal", "konsole", "xfce4-terminal", "alacritty", "kitty")
MACOS_TERMINALS = ("Terminal", "iTerm2", "Alacritty")

DEFAULT_PROJECTS: Dict[str, Dict[str, Optional[str]]] = {}


def user_data_dir() -> Path:
  override = os.environ.get(ENV_PROJECTS_FILE)
  if override:
    return expand_path(override).parent
  if sys.platform == "darwin":
    return Path.home() / "Library" / "Application Support" / APP_NAME
  if os.name == "nt":
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / APP_NAME
  base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
  return Path(base) / APP_NAME


def projects_file() -> Path:
  override = os.environ.get(ENV_PROJECTS_FILE)
  if override:
    return expand_path(override)
  return user_data_dir() / PROJECTS_FILENAME


def expand_path(value: str) -> Path:
  return Path(os.path.expandvars(os.path.expanduser(value))).resolve()


@dataclass
class Project:
  name: str
  base_folder: Path
  shiny_folder: Optional[Path]
  github_url: str
  default_app: Optional[str]

  @classmethod
  def from_dict(cls, name: str, payload: Dict[str, Any]) -> "Project":
    shiny_folder = payload.get("shiny_folder")
    return cls(
      name=name,
      base_folder=expand_path(payload["base_folder"]),
      shiny_folder=expand_path(shiny_folder) if shiny_folder else None,
      github_url=payload["github_url"],
      default_app=payload.get("default_app"),
    )

  def to_dict(self) -> Dict[str, Optional[str]]:
    return {
      "base_folder": str(self.base_folder),
      "shiny_folder": str(self.shiny_folder) if self.shiny_folder else None,
      "github_url": self.github_url,
      "default_app": self.default_app,
    }


class ProjectRegistry:
  def __init__(self, path: Path) -> None:
    self.path = path

  def load(self) -> Dict[str, Project]:
    self.ensure_exists()
    with self.path.open("r", encoding="utf-8") as handle:
      raw = json.load(handle)
    return {name: Project.from_dict(name, payload) for name, payload in raw.items()}

  def save(self, projects: Dict[str, Project]) -> None:
    raw = {name: project.to_dict() for name, project in sorted(projects.items())}
    self.save_raw(raw)

  def ensure_exists(self) -> None:
    if self.path.exists():
      return
    self.path.parent.mkdir(parents=True, exist_ok=True)
    self.save_raw(DEFAULT_PROJECTS)

  def save_raw(self, payload: Dict[str, Dict[str, Optional[str]]]) -> None:
    self.path.parent.mkdir(parents=True, exist_ok=True)
    with self.path.open("w", encoding="utf-8") as handle:
      json.dump(payload, handle, indent=2)
      handle.write("\n")


def open_target(target: str) -> None:
  if sys.platform == "darwin":
    subprocess.run(["open", target], check=True)
    return
  if os.name == "nt":
    os.startfile(target)  # type: ignore[attr-defined]
    return
  subprocess.run(["xdg-open", target], check=True)


def project_application_command(application: str) -> list[str]:
  candidates = PROJECT_APPLICATION_COMMANDS.get(application)
  if not candidates:
    raise ValueError(f"Unsupported project application: {application}")
  if sys.platform == "darwin":
    return ["open", "-a", candidates[-1]]
  for candidate in candidates:
    executable = shutil.which(candidate)
    if executable:
      return [executable]
  raise ValueError(f"Could not find the {application} executable in PATH")


def open_project_target(target: Path, application: str) -> None:
  subprocess.run([*project_application_command(application), str(target)], check=True)


def resolve_project_application(project: Project, requested_app: Optional[str]) -> str:
  return requested_app or project.default_app or DEFAULT_PROJECT_APPLICATION


def resolve_rproj(target_folder: Path, label: str) -> Path:
  if not target_folder.is_dir():
    raise ValueError(f"Could not find {label} folder at {target_folder}")
  project_files = sorted(target_folder.glob("*.Rproj"))
  if not project_files:
    raise ValueError(f"Could not find an .Rproj file in {target_folder}")
  if len(project_files) > 1:
    raise ValueError(f"Found multiple .Rproj files in {target_folder}")
  return project_files[0]


def shell_cd_command(target_folder: Path) -> str:
  return f"cd {shlex.quote(str(target_folder.resolve()))}"


def apple_script_string(value: str) -> str:
  return value.replace("\\", "\\\\").replace('"', '\\"')


def run_osascript(script: str, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    ["osascript", "-e", script],
    check=True,
    capture_output=capture_output,
    text=capture_output,
  )


def frontmost_macos_application() -> str:
  script = 'tell application "System Events" to get name of first application process whose frontmost is true'
  result = run_osascript(script, capture_output=True)
  app_name = result.stdout.strip()
  if not app_name:
    raise ValueError("Could not determine the active macOS application")
  return app_name


def normalize_macos_application_name(app_name: str) -> str:
  return app_name.strip().casefold()


def open_terminal_macos_terminal(target_folder: Path) -> None:
  command = apple_script_string(shell_cd_command(target_folder))
  script = (
    'tell application "Terminal"\n'
    "activate\n"
    "if not (exists front window) then reopen\n"
    f'do script "{command}" in selected tab of front window\n'
    "end tell"
  )
  run_osascript(script)


def open_terminal_macos_iterm2(target_folder: Path) -> None:
  command = apple_script_string(shell_cd_command(target_folder))
  script = (
    'tell application "iTerm2"\n'
    "activate\n"
    "if not (exists current window) then create window with default profile\n"
    f'tell current session of current window to write text "{command}"\n'
    "end tell"
  )
  run_osascript(script)


def open_terminal_macos_alacritty(target_folder: Path) -> None:
  command = apple_script_string(shell_cd_command(target_folder))
  script = (
    'tell application "Alacritty" to activate\n'
    'tell application "System Events"\n'
    f'keystroke "{command}"\n'
    "key code 36\n"
    "end tell"
  )
  try:
    run_osascript(script)
  except subprocess.CalledProcessError:
    subprocess.run(
      ["alacritty", "msg", "create-window", "--working-directory", str(target_folder.resolve())],
      check=True,
    )


def open_terminal_macos(target_folder: Path) -> None:
  app_name = frontmost_macos_application()
  normalized_name = normalize_macos_application_name(app_name)
  if normalized_name == "terminal":
    open_terminal_macos_terminal(target_folder)
    return
  if normalized_name == "iterm2":
    open_terminal_macos_iterm2(target_folder)
    return
  if normalized_name == "alacritty":
    open_terminal_macos_alacritty(target_folder)
    return
  supported = ", ".join(MACOS_TERMINALS)
  raise ValueError(
    f"Active macOS application '{app_name}' is not a supported terminal for -t. "
    f"Supported terminals: {supported}"
  )


def open_terminal_windows(target_folder: Path) -> None:
  target_str = str(target_folder.resolve())
  wt_path = subprocess.run(["where", "wt.exe"], capture_output=True, text=True).stdout.strip()
  if wt_path:
    subprocess.run(["wt.exe", "-d", target_str], check=True)
    return
  subprocess.run(["cmd", "/c", "start", "cmd", "/K", f'cd /d "{target_str}"'], check=True)


def open_terminal_linux(target_folder: Path) -> None:
  target_str = str(target_folder.resolve())
  for term in LINUX_TERMINALS:
    try:
      subprocess.run([term, "--working-directory", target_str], check=True)
      return
    except (FileNotFoundError, subprocess.CalledProcessError):
      continue
  print(
    f"Warning: Could not find a compatible terminal from {list(LINUX_TERMINALS)}.",
    file=sys.stderr,
  )


def open_terminal(target_folder: Path) -> None:
  """Open the target folder in the current terminal app when possible."""
  if sys.platform == "darwin":
    open_terminal_macos(target_folder)
    return
  if os.name == "nt":
    open_terminal_windows(target_folder)
    return
  open_terminal_linux(target_folder)



def launch_project(project: Project,
                   open_project: bool,
                   open_shiny: bool,
                   open_github: bool,
                   should_open_terminal: bool,
                   project_application: str) -> int:
  status = 0
  if not any([open_project, open_shiny, open_github, should_open_terminal]):
    open_project = True

  if open_project:
    try:
      rproj = resolve_rproj(project.base_folder, "project")
      print(f"Launching {project.name} project in {project_application}")
      open_project_target(rproj, project_application)
    except Exception as exc:
      print(f"Error: {exc}", file=sys.stderr)
      status = 1

  if open_shiny:
    try:
      if not project.shiny_folder:
        raise ValueError(f"No shiny project configured for {project.name}")
      rproj = resolve_rproj(project.shiny_folder, "shiny project")
      print(f"Launching {project.name} shiny project in {project_application}")
      open_project_target(rproj, project_application)
    except Exception as exc:
      print(f"Error: {exc}", file=sys.stderr)
      status = 1

  if open_github:
    try:
      print(f"Launching {project.name} GitHub URL")
      open_target(project.github_url)
    except Exception as exc:
      print(f"Error: {exc}", file=sys.stderr)
      status = 1

  if should_open_terminal:
    try:
      print(f"Opening terminal for {project.name}")
      open_terminal(project.base_folder)
    except Exception as exc:
      print(f"Error: {exc}", file=sys.stderr)
      status = 1

  return status


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
    prog="launch",
    description="Open configured project folders, Shiny apps, and GitHub URLs.",
  )
  parser.add_argument("project", nargs="?", help="Project name to launch")
  parser.add_argument("-p", "--project-folder", action="store_true", dest="open_project")
  parser.add_argument("-s", "--shiny", action="store_true", dest="open_shiny")
  parser.add_argument("-g", "--github", action="store_true", dest="open_github")
  parser.add_argument("-t", "--terminal", action="store_true", dest="open_terminal")
  parser.add_argument("-f", "--folder-in-terminal", action="store_true", dest="open_terminal")
  parser.add_argument(
    "-a",
    "--app",
    choices=sorted(PROJECT_APPLICATION_COMMANDS),
    default=None,
    dest="project_application",
    help="Application used to open project files. Defaults to the registered app or positron.",
  )
  return parser


def parse_args(argv: list[str]) -> argparse.Namespace:
  if argv and argv[0] == "register":
    parser = argparse.ArgumentParser(
      prog="launch register",
      description="Register or update a project mapping.",
    )
    parser.add_argument("project_name")
    parser.add_argument("base_folder")
    parser.add_argument("shiny_folder", help="Use '-' when the project has no Shiny folder.")
    parser.add_argument("github_url")
    parser.add_argument(
      "--app",
      choices=sorted(PROJECT_APPLICATION_COMMANDS),
      dest="default_app",
      help="Default application for this project.",
    )
    namespace = parser.parse_args(argv[1:])
    namespace.command = "register"
    return namespace

  parser = build_parser()
  namespace = parser.parse_args(argv)
  namespace.command = "launch"
  if not namespace.project:
    parser.error("the following arguments are required: project")
  return namespace


def register_project(registry: ProjectRegistry, args: argparse.Namespace) -> int:
  projects = registry.load()
  shiny_folder = None if args.shiny_folder == "-" else expand_path(args.shiny_folder)
  project = Project(
    name=args.project_name,
    base_folder=expand_path(args.base_folder),
    shiny_folder=shiny_folder,
    github_url=args.github_url,
    default_app=args.default_app,
  )
  projects[project.name] = project
  registry.save(projects)
  print(f"Registered project {project.name} in {registry.path}")
  return 0


def run(argv: Optional[list[str]] = None) -> int:
  registry = ProjectRegistry(projects_file())
  args = parse_args(argv or sys.argv[1:])

  if args.command == "register":
    return register_project(registry, args)

  projects = registry.load()
  project = projects.get(args.project)
  if not project:
    print(f"Error: Not a valid project: {args.project}", file=sys.stderr)
    if projects:
      print(f"Available projects: {', '.join(sorted(projects))}", file=sys.stderr)
    else:
      print("No projects are registered yet. Use 'launch register ...' first.", file=sys.stderr)
    return 1
  project_application = resolve_project_application(project, args.project_application)
  return launch_project(
    project,
    args.open_project,
    args.open_shiny,
    args.open_github,
    args.open_terminal,
    project_application,
  )


def main() -> None:
  raise SystemExit(run())

if __name__ == "__main__":
  main()
