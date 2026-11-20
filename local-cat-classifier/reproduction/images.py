"""Preprocessing shared by training and CPU inference."""
import numpy as np
from PIL import Image, ImageOps


LABELS = ["Eli", "Empty", "Pixel"]
MEAN = np.array([.485, .456, .406], np.float32)
STD = np.array([.229, .224, .225], np.float32)


def image_tensor(image, size):
    padded = ImageOps.pad(image.convert("RGB"), (size, size), method=Image.Resampling.BICUBIC,
                          color=(124, 116, 104))
    return ((np.asarray(padded, np.float32) / 255 - MEAN) / STD).transpose(2, 0, 1).copy()
