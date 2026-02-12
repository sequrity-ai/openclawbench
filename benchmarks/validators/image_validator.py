"""Validation utilities for image generation skill tasks."""

from pathlib import Path
from typing import Any

from benchmarks.base import TaskResult


class ImageValidator:
    """Validates image generation skill task results."""

    @staticmethod
    def validate_image_generation(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: Image generation.

        Expected: Image file exists at the specified path and is >1KB.
        """
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        workspace_dir = Path(setup_data.get("workspace_dir", "/tmp/openclaw_benchmark"))
        expected_file = workspace_dir / "fox.png"

        # Also check for common alternative filenames
        candidates = [
            expected_file,
            workspace_dir / "fox.jpg",
            workspace_dir / "fox.jpeg",
            workspace_dir / "fox.webp",
        ]

        found_file = None
        for candidate in candidates:
            if candidate.exists():
                found_file = candidate
                break

        if not found_file:
            # Check for any image file in the workspace
            for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
                matches = list(workspace_dir.glob(ext))
                if matches:
                    found_file = matches[0]
                    break

        if found_file:
            validation_details["file_path"] = str(found_file)
            file_size = found_file.stat().st_size
            validation_details["file_size_bytes"] = file_size

            if file_size > 1024:
                accuracy_score += 80.0
                validation_details["size_ok"] = True
            else:
                accuracy_score += 20.0
                validation_details["size_ok"] = False
                error_message = f"Image file too small ({file_size} bytes)"

            # Bonus: correct filename
            if found_file.name == "fox.png":
                accuracy_score += 20.0
                validation_details["correct_name"] = True
            else:
                validation_details["correct_name"] = False

            if accuracy_score >= 80.0:
                success = True
            if accuracy_score >= 100.0:
                accuracy_score = 100.0
        else:
            error_message = "No image file found in workspace"
            validation_details["file_path"] = None

        return TaskResult(
            task_name="Image Generation",
            prompt="Generate an image of a red fox in a snowy forest",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
