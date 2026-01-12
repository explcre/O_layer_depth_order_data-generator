"""
Layer Depth Order Task Configuration.
"""

from pydantic import Field
from core import GenerationConfig


class TaskConfig(GenerationConfig):
    """
    Layer Depth Order task configuration.
    
    Task: Given overlapping shapes, identify the layer order (front to back)
    and show them separated.
    """
    
    domain: str = Field(default="layer_depth")
    image_size: tuple[int, int] = Field(default=(512, 512))
    
    generate_videos: bool = Field(default=True)
    video_fps: int = Field(default=10)
    
    # Shape settings
    min_shapes: int = Field(default=3, description="Minimum number of overlapping shapes")
    max_shapes: int = Field(default=5, description="Maximum number of overlapping shapes")
    min_shape_size: int = Field(default=80, description="Minimum shape size")
    max_shape_size: int = Field(default=150, description="Maximum shape size")
    
    # Colors with alpha
    shape_colors: list = Field(default=[
        (255, 100, 100, 180),  # Red
        (100, 255, 100, 180),  # Green
        (100, 100, 255, 180),  # Blue
        (255, 255, 100, 180),  # Yellow
        (255, 100, 255, 180),  # Magenta
        (100, 255, 255, 180),  # Cyan
    ])
    
    bg_color: tuple[int, int, int] = Field(default=(255, 255, 255))
    label_color: tuple[int, int, int] = Field(default=(50, 50, 50))
