"""
Image Preprocessing Pipeline for Optical Character Recognition (OCR).

Implements six key preprocessing techniques:
1. Original (unprocessed pass-through)
2. Grayscale conversion
3. Image resizing (upscaling for low-resolution text)
4. Noise removal (median / smoothing filter)
5. Binarization / thresholding (Otsu's global thresholding)
6. Deskewing (orientation alignment via projection profile)

Supports PIL/OpenCV when available, with pure-Python image matrix fallback
for guaranteed deterministic execution across all environments.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Optional imaging libraries
try:
    from PIL import Image, ImageFilter, ImageOps
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


class SimpleGrayscaleImage:
    """Lightweight 2D grayscale image representation (0-255 pixels)."""

    def __init__(self, width: int, height: int, pixels: Optional[List[List[int]]] = None):
        self.width = width
        self.height = height
        if pixels is not None:
            self.pixels = pixels
        else:
            self.pixels = [[255 for _ in range(width)] for _ in range(height)]

    def get_pixel(self, x: int, y: int) -> int:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.pixels[y][x]
        return 255  # default white background

    def set_pixel(self, x: int, y: int, val: int) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y][x] = max(0, min(255, val))

    def clone(self) -> SimpleGrayscaleImage:
        new_pixels = [row[:] for row in self.pixels]
        return SimpleGrayscaleImage(self.width, self.height, new_pixels)


class ImagePreprocessor:
    """Configurable preprocessing suite for optimizing images for OCR."""

    @staticmethod
    def to_grayscale(image: SimpleGrayscaleImage) -> SimpleGrayscaleImage:
        """Grayscale conversion: Returns image in 8-bit luminance space."""
        # SimpleGrayscaleImage is already grayscale
        return image.clone()

    @staticmethod
    def resize(image: SimpleGrayscaleImage, scale_factor: float = 2.0) -> SimpleGrayscaleImage:
        """Image resizing: Scales dimensions using bilinear interpolation."""
        new_w = max(1, int(image.width * scale_factor))
        new_h = max(1, int(image.height * scale_factor))
        resized = SimpleGrayscaleImage(new_w, new_h)

        for y in range(new_h):
            orig_y = y / scale_factor
            y0 = int(math.floor(orig_y))
            y1 = min(y0 + 1, image.height - 1)
            dy = orig_y - y0

            for x in range(new_w):
                orig_x = x / scale_factor
                x0 = int(math.floor(orig_x))
                x1 = min(x0 + 1, image.width - 1)
                dx = orig_x - x0

                p00 = image.get_pixel(x0, y0)
                p10 = image.get_pixel(x1, y0)
                p01 = image.get_pixel(x0, y1)
                p11 = image.get_pixel(x1, y1)

                val = (
                    p00 * (1 - dx) * (1 - dy)
                    + p10 * dx * (1 - dy)
                    + p01 * (1 - dx) * dy
                    + p11 * dx * dy
                )
                resized.set_pixel(x, y, int(round(val)))

        return resized

    @staticmethod
    def remove_noise(image: SimpleGrayscaleImage, window_size: int = 3) -> SimpleGrayscaleImage:
        """Noise removal: Applies a 3x3 median filter to eliminate salt-and-pepper noise."""
        denoised = SimpleGrayscaleImage(image.width, image.height)
        offset = window_size // 2

        for y in range(image.height):
            for x in range(image.width):
                neighborhood = []
                for dy in range(-offset, offset + 1):
                    for dx in range(-offset, offset + 1):
                        neighborhood.append(image.get_pixel(x + dx, y + dy))
                neighborhood.sort()
                median_val = neighborhood[len(neighborhood) // 2]
                denoised.set_pixel(x, y, median_val)

        return denoised

    @staticmethod
    def compute_otsu_threshold(image: SimpleGrayscaleImage) -> int:
        """Compute Otsu's optimal global binarization threshold."""
        # Compute histogram
        hist = [0] * 256
        total_pixels = image.width * image.height
        for y in range(image.height):
            for x in range(image.width):
                hist[image.get_pixel(x, y)] += 1

        sum_all = sum(i * hist[i] for i in range(256))
        sum_b = 0
        weight_b = 0
        max_variance = 0.0
        best_threshold = 128

        for t in range(256):
            weight_b += hist[t]
            if weight_b == 0:
                continue
            weight_f = total_pixels - weight_b
            if weight_f == 0:
                break

            sum_b += t * hist[t]
            mean_b = sum_b / weight_b
            mean_f = (sum_all - sum_b) / weight_f

            between_variance = weight_b * weight_f * ((mean_b - mean_f) ** 2)
            if between_variance > max_variance:
                max_variance = between_variance
                best_threshold = t

        return best_threshold

    @classmethod
    def binarize(
        cls, image: SimpleGrayscaleImage, threshold: Optional[int] = None
    ) -> SimpleGrayscaleImage:
        """Binarization / Thresholding: Maps pixels to pure black (0) or white (255)."""
        if threshold is None:
            threshold = cls.compute_otsu_threshold(image)

        binary = SimpleGrayscaleImage(image.width, image.height)
        for y in range(image.height):
            for x in range(image.width):
                val = 255 if image.get_pixel(x, y) >= threshold else 0
                binary.set_pixel(x, y, val)

        return binary

    @staticmethod
    def rotate(image: SimpleGrayscaleImage, angle_degrees: float) -> SimpleGrayscaleImage:
        """Rotate image by given angle in degrees about its center."""
        if abs(angle_degrees) < 0.1:
            return image.clone()

        rad = math.radians(angle_degrees)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        cx = image.width / 2.0
        cy = image.height / 2.0

        rotated = SimpleGrayscaleImage(image.width, image.height)
        for y in range(image.height):
            for x in range(image.width):
                # Reverse mapping
                nx = cos_a * (x - cx) + sin_a * (y - cy) + cx
                ny = -sin_a * (x - cx) + cos_a * (y - cy) + cy

                val = image.get_pixel(int(round(nx)), int(round(ny)))
                rotated.set_pixel(x, y, val)

        return rotated

    @classmethod
    def detect_skew_angle(cls, image: SimpleGrayscaleImage) -> float:
        """Estimate skew angle in degrees using horizontal projection profile variance."""
        best_angle = 0.0
        max_variance = -1.0

        # Scan angles from -10 to +10 degrees in 1-degree steps
        for angle in [float(a) for a in range(-10, 11)]:
            rotated = cls.rotate(image, angle)
            # Calculate horizontal projection (sum of dark pixels per row)
            row_sums = [
                sum(1 for x in range(rotated.width) if rotated.get_pixel(x, y) < 128)
                for y in range(rotated.height)
            ]
            mean_sum = sum(row_sums) / max(1, len(row_sums))
            variance = sum((s - mean_sum) ** 2 for s in row_sums) / max(1, len(row_sums))

            if variance > max_variance:
                max_variance = variance
                best_angle = angle

        return best_angle

    @classmethod
    def deskew(cls, image: SimpleGrayscaleImage) -> Tuple[SimpleGrayscaleImage, float]:
        """Deskewing: Detects angle and rotates image back to horizontal orientation."""
        angle = cls.detect_skew_angle(image)
        if abs(angle) >= 0.5:
            return cls.rotate(image, -angle), -angle
        return image.clone(), 0.0

    @classmethod
    def apply_pipeline(
        cls,
        image: SimpleGrayscaleImage,
        techniques: List[str],
    ) -> Tuple[SimpleGrayscaleImage, Dict[str, Any]]:
        """Apply a sequence of named preprocessing techniques."""
        current = image.clone()
        info: Dict[str, Any] = {"applied": []}

        for tech in techniques:
            tech_lower = tech.lower().strip()
            if tech_lower in ("original", "none"):
                info["applied"].append("original")
            elif tech_lower in ("grayscale", "gray"):
                current = cls.to_grayscale(current)
                info["applied"].append("grayscale")
            elif tech_lower in ("resize", "rescale"):
                current = cls.resize(current, scale_factor=2.0)
                info["applied"].append("resize_2x")
            elif tech_lower in ("noise_removal", "denoise"):
                current = cls.remove_noise(current, window_size=3)
                info["applied"].append("denoise_median3x3")
            elif tech_lower in ("binarize", "threshold", "otsu"):
                t_val = cls.compute_otsu_threshold(current)
                current = cls.binarize(current, threshold=t_val)
                info["applied"].append(f"binarize_otsu_t{t_val}")
            elif tech_lower in ("deskew", "straighten"):
                current, detected_angle = cls.deskew(current)
                info["applied"].append(f"deskew_{detected_angle:+.1f}deg")

        return current, info
