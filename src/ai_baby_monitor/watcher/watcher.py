import base64
import os
from enum import Enum

import structlog
from openai import OpenAI
from pydantic import BaseModel

from ai_baby_monitor.stream import Frame
from ai_baby_monitor.watcher import get_cat_monitoring_prompt,get_instructions_prompt

logger = structlog.get_logger()


class AwarenessLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class WatcherResponse(BaseModel):
    should_alert: bool
    reasoning: str
    recommended_awareness_level: AwarenessLevel


class Watcher:
    def __init__(
        self,
        instructions: list[str],
        api_key: str | None = None,
        model_name: str = "gpt-4o-mini",
    ):
        """
        Initialize the Watcher with instructions and OpenAI API details.

        Args:
            instructions: List of monitoring instructions to check against frames
            api_key: OpenAI API key (if None, will use OPENAI_API_KEY environment variable)
            model_name: OpenAI model name to use for inference
        """
        self.instructions_prompt = get_instructions_prompt(instructions)
        self.cat_monitoring_prompt = get_cat_monitoring_prompt()

        self.json_schema = WatcherResponse.model_json_schema()
        self.model_name = model_name

        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
        )

        logger.info(
            "Initialized Watcher",
            model_name=model_name,
            instructions=instructions,
        )

    def _frames_to_base64(self, frames: list[Frame]) -> list[str]:
        """Convert JPEG-encoded frame data to base64 encoded strings."""
        base64_frames = []
        for frame in frames:
            jpeg_bytes = bytes(frame.frame_data)
            base64_str = base64.b64encode(jpeg_bytes).decode("utf-8")
            base64_frames.append(base64_str)

        return base64_frames

    def _calculate_fps(self, frames: list[Frame], default_fps: int = 2) -> int:
        """Calculate FPS from frame timestamps, defaulting to 2 if calculation fails."""
        if len(frames) < 2:
            logger.warning("Too few frames to calculate FPS, using default of 2")
            return default_fps

        try:
            time_diff = (frames[-1].timestamp - frames[0].timestamp).total_seconds()
            if time_diff <= 0:
                return default_fps

            fps = round((len(frames) - 1) / time_diff)

            # Return default if calculated FPS is unreasonable
            return default_fps if fps < 0.02 or fps > 60 else fps

        except Exception as e:
            logger.warning("FPS calculation error", error=e)
            return default_fps

    def process_frames(
        self, frames: list[Frame], fps: int | None = None
    ) -> dict[str, str | bool]:
        """Process frames to detect instruction violations.

        Returns:
            dict containing:
                - success (bool): Whether processing completed successfully
                - should_alert (bool): If an alert should be triggered
                - reasoning (str): Explanation for the decision
                - recommended_awareness_level (str): Suggested monitoring level. Should be one of: LOW, MEDIUM, HIGH
                - raw_response (str): Original model response
                - error (str, optional): Error message if processing failed
        """
        if not frames:
            logger.warning("No frames provided for processing")
            return {
                "success": False,
                "error": "No frames provided",
            }

        try:
            # Convert frames to base64
            base64_frames = self._frames_to_base64(frames)

            # Create content with multiple images for OpenAI
            content = [
                {"type": "text", "text": self.cat_monitoring_prompt}
            ]
            
            # Add each frame as a separate image
            for base64_frame in base64_frames:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_frame}"
                    }
                })

            # Create message with instructions
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant and animal sitter.",
                },
                {
                    "role": "user",
                    "content": content,
                },
            ]

            # Send to OpenAI API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=512,
                response_format={"type": "json_object"},
            )
            logger.info("OpenAI response", response=response)
            
            parsed_response = WatcherResponse.model_validate_json(
                response.choices[0].message.content
            )

            return {
                "success": True,
                "should_alert": parsed_response.should_alert,
                "reasoning": parsed_response.reasoning,
                "recommended_awareness_level": parsed_response.recommended_awareness_level,
                "raw_response": response.choices[0].message.content,
            }

        except Exception as e:
            logger.error("Error processing frames", error=e)
            return {
                "success": False,
                "error": str(e),
            }
