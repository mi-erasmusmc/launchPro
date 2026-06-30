import json
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
            status = cli.run(["Demo", "-p"])

      self.assertEqual(status, 0)
      self.assertEqual(commands[0], self.expected_command("positron", rproj_path.resolve()))

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

  def expected_command(self, application: str, rproj_path: Path) -> list[str]:
    if cli.sys.platform == "darwin":
      app_name = "Positron" if application == "positron" else "RStudio"
      return ["open", "-a", app_name, str(rproj_path)]
    return [f"/mock/{application}", str(rproj_path)]


if __name__ == "__main__":
  unittest.main()
