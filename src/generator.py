"""
Layer Depth Order Task Generator.

Generates overlapping semi-transparent shapes where the task is to
identify the layer order from front to back.
"""

import random
import tempfile
import math
from pathlib import Path
from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig
from .prompts import get_prompt


class TaskGenerator(BaseGenerator):
    """Layer depth order task generator."""
    
    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.renderer = ImageRenderer(image_size=config.image_size)
        
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")
    
    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one task pair."""
        task_data = self._generate_task_data()
        
        first_image = self._render_initial_state(task_data)
        final_image = self._render_final_state(task_data)
        
        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(first_image, final_image, task_id, task_data)
        
        prompt = get_prompt(task_data.get("type", "default"))
        
        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            ground_truth_video=video_path
        )
    
    def _generate_task_data(self) -> dict:
        """Generate overlapping shapes with depth order."""
        num_shapes = random.randint(self.config.min_shapes, self.config.max_shapes)
        width, height = self.config.image_size
        
        # Center area for overlapping shapes
        center_x = width // 2
        center_y = height // 2
        spread = 60
        
        shapes = []
        available_colors = list(self.config.shape_colors)
        random.shuffle(available_colors)
        
        shape_types = ["circle", "square", "triangle"]
        
        for i in range(num_shapes):
            # Position near center with some offset
            x = center_x + random.randint(-spread, spread)
            y = center_y + random.randint(-spread, spread)
            
            size = random.randint(self.config.min_shape_size, self.config.max_shape_size)
            shape_type = random.choice(shape_types)
            color = available_colors[i % len(available_colors)]
            
            shapes.append({
                "x": x,
                "y": y,
                "size": size,
                "type": shape_type,
                "color": color,
                "layer": i,  # 0 = back, higher = front
            })
        
        return {
            "shapes": shapes,
            "num_shapes": num_shapes,
            "type": "default",
        }
    
    def _draw_shape(self, img: Image.Image, shape: dict, offset_x: int = 0, offset_y: int = 0):
        """Draw a semi-transparent shape on the image."""
        x = shape["x"] + offset_x
        y = shape["y"] + offset_y
        size = shape["size"]
        color = shape["color"]
        shape_type = shape["type"]
        
        # Create a temporary image for the shape with alpha
        temp = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(temp)
        
        half = size // 2
        
        if shape_type == "circle":
            draw.ellipse([x - half, y - half, x + half, y + half], 
                        fill=color, outline=(0, 0, 0, 255), width=2)
        elif shape_type == "square":
            draw.rectangle([x - half, y - half, x + half, y + half],
                          fill=color, outline=(0, 0, 0, 255), width=2)
        elif shape_type == "triangle":
            points = [
                (x, y - half),
                (x - half, y + half),
                (x + half, y + half),
            ]
            draw.polygon(points, fill=color, outline=(0, 0, 0, 255), width=2)
        
        # Composite onto main image
        img.paste(temp, (0, 0), temp)
    
    def _render_overlapping(self, task_data: dict) -> Image.Image:
        """Render shapes overlapping at center."""
        width, height = self.config.image_size
        img = Image.new('RGBA', (width, height), (*self.config.bg_color, 255))
        
        # Draw shapes from back to front
        shapes = sorted(task_data["shapes"], key=lambda s: s["layer"])
        for shape in shapes:
            self._draw_shape(img, shape)
        
        return img.convert('RGB')
    
    def _render_separated(self, task_data: dict) -> Image.Image:
        """Render shapes separated, showing layer order left to right."""
        width, height = self.config.image_size
        img = Image.new('RGBA', (width, height), (*self.config.bg_color, 255))
        draw = ImageDraw.Draw(img)
        
        shapes = sorted(task_data["shapes"], key=lambda s: s["layer"], reverse=True)  # Front to back
        num_shapes = len(shapes)
        
        # Calculate positions for separated shapes
        margin = 40
        available_width = width - 2 * margin
        spacing = available_width // (num_shapes + 1)
        
        # Draw labels
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font = ImageFont.load_default()
            small_font = font
        
        # Draw "Front" and "Back" labels
        draw.text((margin, 30), "FRONT", fill=self.config.label_color, font=font)
        draw.text((width - margin - 40, 30), "BACK", fill=self.config.label_color, font=font)
        
        # Draw arrow
        arrow_y = 45
        draw.line([(margin + 50, arrow_y), (width - margin - 50, arrow_y)], 
                 fill=(150, 150, 150), width=2)
        draw.polygon([
            (width - margin - 50, arrow_y),
            (width - margin - 60, arrow_y - 5),
            (width - margin - 60, arrow_y + 5)
        ], fill=(150, 150, 150))
        
        # Draw shapes in order
        for i, shape in enumerate(shapes):
            new_x = margin + spacing * (i + 1)
            new_y = height // 2
            
            # Create modified shape at new position
            temp_shape = shape.copy()
            temp_shape["x"] = new_x
            temp_shape["y"] = new_y
            
            self._draw_shape(img, temp_shape)
            
            # Draw layer number
            draw.text((new_x - 5, new_y + shape["size"] // 2 + 10), 
                     str(i + 1), fill=self.config.label_color, font=small_font)
        
        return img.convert('RGB')
    
    def _render_initial_state(self, task_data: dict) -> Image.Image:
        """Render initial state with overlapping shapes."""
        return self._render_overlapping(task_data)
    
    def _render_final_state(self, task_data: dict) -> Image.Image:
        """Render final state with shapes separated showing layer order."""
        return self._render_separated(task_data)
    
    def _generate_video(self, first_image: Image.Image, final_image: Image.Image,
                        task_id: str, task_data: dict) -> str:
        """Generate video showing shapes separating."""
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"
        
        frames = []
        hold_frames = 5
        animation_frames = 25
        
        width, height = self.config.image_size
        shapes = sorted(task_data["shapes"], key=lambda s: s["layer"], reverse=True)
        num_shapes = len(shapes)
        
        # Calculate final positions
        margin = 40
        available_width = width - 2 * margin
        spacing = available_width // (num_shapes + 1)
        
        final_positions = []
        for i in range(num_shapes):
            final_x = margin + spacing * (i + 1)
            final_y = height // 2
            final_positions.append((final_x, final_y))
        
        # Hold initial
        for _ in range(hold_frames):
            frames.append(first_image.copy())
        
        # Animate separation
        for frame_idx in range(animation_frames):
            progress = frame_idx / (animation_frames - 1)
            # Ease out
            progress = 1 - (1 - progress) ** 2
            
            img = Image.new('RGBA', (width, height), (*self.config.bg_color, 255))
            draw = ImageDraw.Draw(img)
            
            for i, shape in enumerate(shapes):
                # Interpolate position
                start_x, start_y = shape["x"], shape["y"]
                end_x, end_y = final_positions[i]
                
                curr_x = start_x + (end_x - start_x) * progress
                curr_y = start_y + (end_y - start_y) * progress
                
                temp_shape = shape.copy()
                temp_shape["x"] = int(curr_x)
                temp_shape["y"] = int(curr_y)
                
                self._draw_shape(img, temp_shape)
            
            frames.append(img.convert('RGB'))
        
        # Hold final
        for _ in range(hold_frames * 2):
            frames.append(final_image.copy())
        
        result = self.video_generator.create_video_from_frames(frames, video_path)
        return str(result) if result else None
