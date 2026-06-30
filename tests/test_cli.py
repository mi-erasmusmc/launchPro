import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
  sys.path.insert(0, str(SRC))

from launch_pro import cli


class CliApplicationTests(unittest.TestCase):
  def test_parse_args_defaults_to_no_override(self) -> None:
    args = cli.parse_args(["Demo"])

    self.assertIsNone(args.project_application)

  def test_register_args_accept_default_app(self) -> None:
    args = cli.parse_args([
      "register",
      "Demo",
      "~/demo",
      "-",
      "https://example.com/demo",
      "--app",
      "rstudio",
    ])

    self.assertEqual(args.default_app, "rstudio")

  def test_run_uses_positron_by_default(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      project_dir = Path(tmpdir) / "DemoProject"
      project_dir.mkdir()
      projects_path = Path(tmpdir) / "projects.json"
      projects_path.write_text(
        json.dumps(
          {
            "Demo": {
              "base_folder": str(project_dir),
              "shiny_folder": None,
              "github_url": "https://example.com/demo",
              "default_app": None,
            }
          }
        ),
        encoding="utf-8",
      )
      commands = []

      def fake_run(command, check=True, **kwargs):
        commands.append(command)
        return None

      with patch.object(cli, "projects_file", return_value=projects_path):
        with patch.object(cli.subprocess, "run", side_effect=fake_run):
          with patch.object(cli.shutil, "which", side_effect=lambda value: f"/mock/{value}"):
            status = cli.run(["Demo", "-p"])

      self.assertEqual(status, 0)
      self.assertEqual(commands[0], self.expected_command("positron", project_dir.resolve()))

  def test_run_uses_rstudio_when_requested(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      project_dir = Path(tmpdir) / "DemoProject"
      project_dir.mkdir()
      rproj_path = project_dir / "demo.Rproj"
      rproj_path.touch()
      projects_path = Path(tmpdir) / "projects.json"
      projects_path.write_text(
        json.dumps(
          {
            "Demo": {
              "base_folder": str(project_dir),
              "shiny_folder": None,
              "github_url": "https://example.com/demo",
              "default_app": None,
            }
          }
        ),
        encoding="utf-8",
      )
      commands = []

      def fake_run(command, check=True, **kwargs):
        commands.append(command)
        return None

      with patch.object(cli, "projects_file", return_value=projects_path):
        with patch.object(cli.subprocess, "run", side_effect=fake_run):
          with patch.object(cli.shutil, "which", side_effect=lambda value: f"/mock/{value}"):
            status = cli.run(["Demo", "-p", "--app", "rstudio"])

      self.assertEqual(status, 0)
      self.assertEqual(commands[0], self.expected_command("rstudio", rproj_path.resolve()))

  def test_run_uses_registered_default_app(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      project_dir = Path(tmpdir) / "DemoProject"
      project_dir.mkdir()
      rproj_path = project_dir / "demo.Rproj"
      rproj_path.touch()
      projects_path = Path(tmpdir) / "projects.json"
      projects_path.write_text(
        json.dumps(
          {
            "Demo": {
              "base_folder": str(project_dir),
              "shiny_folder": None,
              "github_url": "https://example.com/demo",
              "default_app": "rstudio",
            }
          }
        ),
        encoding="utf-8",
      )
      commands = []

      def fake_run(command, check=True, **kwargs):
        commands.append(command)
        return None

      with patch.object(cli, "projects_file", return_value=projects_path):
        with patch.object(cli.subprocess, "run", side_effect=fake_run):
          with patch.object(cli.shutil, "which", side_effect=lambda value: f"/mock/{value}"):
            status = cli.run(["Demo", "-p"])

      self.assertEqual(status, 0)
      self.assertEqual(commands[0], self.expected_command("rstudio", rproj_path.resolve()))

  def test_run_uses_positron_without_rproj(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      project_dir = Path(tmpdir) / "DemoProject"
      project_dir.mkdir()
      projects_path = Path(tmpdir) / "projects.json"
      projects_path.write_text(
        json.dumps(
          {
            "Demo": {
              "base_folder": str(project_dir),
              "shiny_folder": None,
              "github_url": "https://example.com/demo",
              "default_app": None,
            }
          }
        ),
        encoding="utf-8",
      )
      commands = []

      def fake_run(command, check=True, **kwargs):
        commands.append(command)
        return None

      with patch.object(cli, "projects_file", return_value=projects_path):
        with patch.object(cli.subprocess, "run", side_effect=fake_run):
          with patch.object(cli.shutil, "which", side_effect=lambda value: f"/mock/{value}"):
            status = cli.run(["Demo", "-p"])

      self.assertEqual(status, 0)
      self.assertEqual(commands[0], self.expected_command("positron", project_dir.resolve()))

  def test_run_uses_positron_shiny_folder(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      project_dir = Path(tmpdir) / "DemoProject"
      project_dir.mkdir()
      shiny_dir = project_dir / "inst" / "shiny" / "App"
      shiny_dir.mkdir(parents=True)
      projects_path = Path(tmpdir) / "projects.json"
      projects_path.write_text(
        json.dumps(
          {
            "Demo": {
              "base_folder": str(project_dir),
              "shiny_folder": str(shiny_dir),
              "github_url": "https://example.com/demo",
              "default_app": None,
            }
          }
        ),
        encoding="utf-8",
      )
      commands = []

      def fake_run(command, check=True, **kwargs):
        commands.append(command)
        return None

      with patch.object(cli, "projects_file", return_value=projects_path):
        with patch.object(cli.subprocess, "run", side_effect=fake_run):
          with patch.object(cli.shutil, "which", side_effect=lambda value: f"/mock/{value}"):
            status = cli.run(["Demo", "-s"])

      self.assertEqual(status, 0)
      self.assertEqual(commands[0], self.expected_command("positron", shiny_dir.resolve()))

  def test_run_uses_rstudio_shiny_rproj(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      project_dir = Path(tmpdir) / "DemoProject"
      project_dir.mkdir()
      shiny_dir = project_dir / "inst" / "shiny" / "App"
      shiny_dir.mkdir(parents=True)
      shiny_rproj = shiny_dir / "demo-shiny.Rproj"
      shiny_rproj.touch()
      projects_path = Path(tmpdir) / "projects.json"
      projects_path.write_text(
        json.dumps(
          {
            "Demo": {
              "base_folder": str(project_dir),
              "shiny_folder": str(shiny_dir),
              "github_url": "https://example.com/demo",
              "default_app": "rstudio",
            }
          }
        ),
        encoding="utf-8",
      )
      commands = []

      def fake_run(command, check=True, **kwargs):
        commands.append(command)
        return None

      with patch.object(cli, "projects_file", return_value=projects_path):
        with patch.object(cli.subprocess, "run", side_effect=fake_run):
          with patch.object(cli.shutil, "which", side_effect=lambda value: f"/mock/{value}"):
            status = cli.run(["Demo", "-s"])

      self.assertEqual(status, 0)
      self.assertEqual(commands[0], self.expected_command("rstudio", shiny_rproj.resolve()))

  def test_open_terminal_uses_frontmost_terminal_on_macos(self) -> None:
    target = Path("/tmp/demo project")
    scripts = []

    def fake_run(command, check=True, capture_output=False, text=False, **kwargs):
      scripts.append(command)
      if len(scripts) == 1:
        return subprocess.CompletedProcess(command, 0, stdout="Terminal\n")
      return subprocess.CompletedProcess(command, 0, stdout="")

    with patch.object(cli.sys, "platform", "darwin"):
      with patch.object(cli.subprocess, "run", side_effect=fake_run):
        cli.open_terminal(target)

    expected_cd = cli.apple_script_string(cli.shell_cd_command(target))
    self.assertEqual(
      scripts,
      [
        [
          "osascript",
          "-e",
          'tell application "System Events" to get name of first application process whose frontmost is true',
        ],
        [
          "osascript",
          "-e",
          'tell application "Terminal"\n'
          "activate\n"
          "if not (exists front window) then reopen\n"
          f'do script "{expected_cd}" in selected tab of front window\n'
          "end tell",
        ],
      ],
    )

  def test_open_terminal_uses_alacritty_fallback_without_terminal_app(self) -> None:
    target = Path("/tmp/demo project")
    commands = []

    def fake_run(command, check=True, capture_output=False, text=False, **kwargs):
      commands.append(command)
      if len(commands) == 1:
        return subprocess.CompletedProcess(command, 0, stdout="Alacritty\n")
      if len(commands) == 2:
        raise subprocess.CalledProcessError(1, command)
      return subprocess.CompletedProcess(command, 0, stdout="")

    with patch.object(cli.sys, "platform", "darwin"):
      with patch.object(cli.subprocess, "run", side_effect=fake_run):
        cli.open_terminal(target)

    expected_cd = cli.apple_script_string(cli.shell_cd_command(target))
    self.assertEqual(
      commands,
      [
        [
          "osascript",
          "-e",
          'tell application "System Events" to get name of first application process whose frontmost is true',
        ],
        [
          "osascript",
          "-e",
          'tell application "Alacritty" to activate\n'
          'tell application "System Events"\n'
          f'keystroke "{expected_cd}"\n'
          "key code 36\n"
          "end tell",
        ],
        [
          "alacritty",
          "msg",
          "create-window",
          "--working-directory",
          str(target.resolve()),
        ],
      ],
    )

  def test_open_terminal_accepts_lowercase_alacritty_on_macos(self) -> None:
    target = Path("/tmp/demo project")
    commands = []

    def fake_run(command, check=True, capture_output=False, text=False, **kwargs):
      commands.append(command)
      if len(commands) == 1:
        return subprocess.CompletedProcess(command, 0, stdout="alacritty\n")
      return subprocess.CompletedProcess(command, 0, stdout="")

    with patch.object(cli.sys, "platform", "darwin"):
      with patch.object(cli.subprocess, "run", side_effect=fake_run):
        cli.open_terminal(target)

    expected_cd = cli.apple_script_string(cli.shell_cd_command(target))
    self.assertEqual(
      commands,
      [
        [
          "osascript",
          "-e",
          'tell application "System Events" to get name of first application process whose frontmost is true',
        ],
        [
          "osascript",
          "-e",
          'tell application "Alacritty" to activate\n'
          'tell application "System Events"\n'
          f'keystroke "{expected_cd}"\n'
          "key code 36\n"
          "end tell",
        ],
      ],
    )

  def test_open_terminal_rejects_unsupported_macos_terminal(self) -> None:
    target = Path("/tmp/demo")

    def fake_run(command, check=True, capture_output=False, text=False, **kwargs):
      return subprocess.CompletedProcess(command, 0, stdout="Warp\n")

    with patch.object(cli.sys, "platform", "darwin"):
      with patch.object(cli.subprocess, "run", side_effect=fake_run):
        with self.assertRaisesRegex(ValueError, "Warp"):
          cli.open_terminal(target)

  def expected_command(self, application: str, rproj_path: Path) -> list[str]:
    if cli.sys.platform == "darwin":
      app_name = "Positron" if application == "positron" else "RStudio"
      return ["open", "-a", app_name, str(rproj_path)]
    return [f"/mock/{application}", str(rproj_path)]


if __name__ == "__main__":
  unittest.main()
