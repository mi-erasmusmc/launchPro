from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


APP_NAME = "launch_pro"
PROJECTS_FILENAME = "projects.json"
ENV_PROJECTS_FILE = "LAUNCH_PROJECTS_FILE"

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

  @classmethod
  def from_dict(cls, name: str, payload: Dict[str, Any]) -> "Project":
    shiny_folder = payload.get("shiny_folder")
    return cls(
      name=name,
      base_folder=expand_path(payload["base_folder"]),
      shiny_folder=expand_path(shiny_folder) if shiny_folder else None,
      github_url=payload["github_url"],
    )

  def to_dict(self) -> Dict[str, Optional[str]]:
    return {
      "base_folder": str(self.base_folder),
      "shiny_folder": str(self.shiny_folder) if self.shiny_folder else None,
      "github_url": self.github_url,
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


def resolve_rproj(target_folder: Path, label: str) -> Path:
  if not target_folder.is_dir():
    raise ValueError(f"Could not find {label} folder at {target_folder}")
  project_files = sorted(target_folder.glob("*.Rproj"))
  if not project_files:
    raise ValueError(f"Could not find an .Rproj file in {target_folder}")
  if len(project_files) > 1:
    raise ValueError(f"Found multiple .Rproj files in {target_folder}")
  return project_files[0]


def open_terminal(target_folder: Path) -> None:
  """Opens the target folder in a terminal window (attempting to use the current one)."""
  target_str = str(target_folder.resolve())
  if sys.platform == "darwin":
    # macOS: Try to hijack the frontmost window in Terminal or iTerm2
    # 1. Try Terminal.app
    try:
      script = f'tell application "Terminal" to do script "cd \'{target_str}\'" in front window'
      subprocess.run(["osascript", "-e", script], check=True)
      return
    except (subprocess.CalledProcessError, FileNotFoundError):
      pass

    # 2. Try iTerm2
    try:
      script = f'tell application "iTerm2" to tell current session of front window to write text "cd \'{target_str}\'"'
      subprocess.run(["osascript", "-e", script], check=True)
      return
    except (subprocess.CalledProcessError, FileNotFoundError):
      pass

    # 3. Fallback to new window
    script = f'tell application "Terminal" to do script "cd \'{target_str}\'"'
    subprocess.run(["osascript", "-e", script], check=True)

  elif os.name == "nt":
    # Windows: Try Windows Terminal (wt.exe) if available, else fallback to cmd
    wt_path = subprocess.run(["where", "wt.exe"], capture_output=True, text=True).stdout.strip()
    if wt_path:
      subprocess.run(["wt.exe", "-d", target_str], check=True)
    else:
      # Fallback to default cmd window
      subprocess.run(["cmd", "/c", "start", "cmd", "/K", f"cd /d \"{target_str}\""],
                     check=True)
  else:
    # Linux: Iterate through a list of common terminals
    terminals = ["gnome-terminal", "konsole", "xfce4-terminal", "alacritty", "kitty"]
    success = False
    for term in terminals:
      try:
        subprocess.run([term, "--working-directory", target_str], check=True)
        success = True
        break
      except (FileNotFoundError, subprocess.CalledProcessError):
        continue

    if not success:
      print(f"Warning: Could not find a compatible terminal from {terminals}.",
            file=sys.stderr)



def launch_project(project: Project, open_project: bool, open_shiny: bool, open_github: bool, should_open_terminal: bool) -> int:
  status = 0
  if not any([open_project, open_shiny, open_github, should_open_terminal]):
    open_project = True

  if open_project:
    try:
      rproj = resolve_rproj(project.base_folder, "project")
      print(f"Launching {project.name} project")
      open_target(str(rproj))
    except Exception as exc:
      print(f"Error: {exc}", file=sys.stderr)
      status = 1

  if open_shiny:
    try:
      if not project.shiny_folder:
        raise ValueError(f"No shiny project configured for {project.name}")
      rproj = resolve_rproj(project.shiny_folder, "shiny project")
      print(f"Launching {project.name} shiny project")
      open_target(str(rproj))
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
  return launch_project(project, args.open_project, args.open_shiny, args.open_github, args.open_terminal)


def main() -> None:
  raise SystemExit(run())

if __name__ == "__main__":
  main()
