from pathlib import Path

from setuptools import find_packages, setup


ROOT = Path(__file__).resolve().parent


setup(
  name="launch-pro",
  version="0.1.4",
  description="CLI for opening local Positron or RStudio projects, Shiny apps, and GitHub pages.",
  long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
  long_description_content_type="text/markdown",
  python_requires=">=3.9",
  license="Apache-2.0",
  packages=find_packages(where="src"),
  package_dir={"": "src"},
  entry_points={"console_scripts": ["launch=launch_pro.cli:main"]},
)
