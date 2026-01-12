"""Layer Depth Order Task Prompts."""

import random

PROMPTS = {
    "default": [
        "Identify the layer order of these overlapping shapes from front to back, then show them separated.",
        "Determine which shape is in front and which is in back. Separate them to show the depth order.",
        "These shapes overlap. Figure out the layer order based on occlusion and display them front to back.",
    ],
}

def get_prompt(task_type: str = "default") -> str:
    prompts = PROMPTS.get(task_type, PROMPTS["default"])
    return random.choice(prompts)

def get_all_prompts(task_type: str = "default") -> list[str]:
    return PROMPTS.get(task_type, PROMPTS["default"])
