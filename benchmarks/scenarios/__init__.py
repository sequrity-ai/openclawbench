"""Benchmark scenarios for OpenClaw capabilities."""

from .file_scenario import FileScenario
from .github_scenario import GitHubScenario
from .image_scenario import ImageScenario
from .weather_scenario import WeatherScenario
from .web_scenario import WebScenario

__all__ = ["FileScenario", "WebScenario", "WeatherScenario", "GitHubScenario", "ImageScenario"]

# Map of scenario name -> class for CLI lookup
SCENARIO_MAP = {
    "file": FileScenario,
    "web": WebScenario,
    "weather": WeatherScenario,
    "github": GitHubScenario,
    "image": ImageScenario,
}
