"""Image generation skill benchmark scenario."""

import logging
import shutil
from pathlib import Path

from benchmarks.base import (
    BenchmarkTask,
    CheckStatus,
    HealthCheckResult,
    ScenarioBase,
    SetupResult,
)
from benchmarks.skill_checker import check_skills, get_ready_skills
from benchmarks.validators.image_validator import ImageValidator

logger = logging.getLogger(__name__)

WORKSPACE_DIR = "/tmp/openclaw_benchmark"


class ImageScenario(ScenarioBase):
    """Benchmark scenario for image generation skills."""

    def __init__(self):
        # Pick whichever image skill is installed
        ready = get_ready_skills()
        if "openai-image-gen" in ready:
            skill_name = "openai-image-gen"
        elif "nano-banana-pro" in ready:
            skill_name = "nano-banana-pro"
        else:
            skill_name = "openai-image-gen"  # default, will fail pre_check

        super().__init__(
            name="Image Generation",
            description=f"Tests the {skill_name} skill: generate an image from a text prompt",
            required_skills=[skill_name],
        )

        self.workspace_dir = Path(WORKSPACE_DIR)
        self.validator = ImageValidator()
        self._define_tasks()

    def _define_tasks(self) -> None:
        self.add_task(
            BenchmarkTask(
                name="Image Generation",
                prompt=(
                    f"Generate an image of a red fox sitting in a snowy forest. "
                    f"Save it to {self.workspace_dir}/fox.png"
                ),
                expected_output_description="PNG image file at /tmp/openclaw_benchmark/fox.png",
                validation_fn=self.validator.validate_image_generation,
                timeout=120.0,
            )
        )

    def pre_check(self) -> list[HealthCheckResult]:
        checks = check_skills(self.required_skills)

        # Verify workspace is writable
        try:
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
            test_file = self.workspace_dir / ".img_test"
            test_file.write_text("test")
            test_file.unlink()
            checks.append(
                HealthCheckResult(
                    check_name="Workspace Access",
                    status=CheckStatus.PASS,
                    message=f"Can write to {self.workspace_dir}",
                )
            )
        except Exception as e:
            checks.append(
                HealthCheckResult(
                    check_name="Workspace Access",
                    status=CheckStatus.FAIL,
                    message=f"Cannot write to {self.workspace_dir}: {e}",
                )
            )

        return checks

    def setup(self) -> SetupResult:
        try:
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
            return SetupResult(
                status=CheckStatus.PASS,
                message="Workspace ready for image generation",
                setup_data={"workspace_dir": str(self.workspace_dir)},
            )
        except Exception as e:
            return SetupResult(
                status=CheckStatus.FAIL,
                message=f"Failed to create workspace: {e}",
                error=str(e),
            )

    def cleanup(self) -> bool:
        try:
            # Only remove generated images, not the whole workspace
            for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
                for f in self.workspace_dir.glob(ext):
                    f.unlink()
            return True
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return False
