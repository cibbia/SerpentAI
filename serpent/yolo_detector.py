"""YOLOv8-Nano Sprite Detector

This helper wraps the `ultralytics` package to perform real-time object
(or sprite) detection on game frames. It is **optional**: if the
`ultralytics` package or model files are not present the detector falls
back to a no-op implementation that returns an empty list so that the rest
of the framework continues to operate.

Model
-----
A default `yolov8n.pt` model will be downloaded automatically the first
run (≈ 3 MB). You can supply your own fine-tuned model by setting the
``SERPENT_YOLO_MODEL`` environment variable to a local path.

Returned boxes are in *(x1, y1, x2, y2, conf, class_id)* format.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Tuple

import numpy as np

try:
    from ultralytics import YOLO  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – lightweight installs
    YOLO = None  # type: ignore

Box = Tuple[int, int, int, int, float, int]


class YoloDetector:
    """Thin wrapper around ultralytics YOLOv8-Nano model."""

    _singleton: "YoloDetector | None" = None

    def __new__(cls):
        # Singleton so we only load weights once per process.
        if cls._singleton is None:
            cls._singleton = super().__new__(cls)
        return cls._singleton

    def __init__(self):
        if getattr(self, "_initialised", False):
            return
        self._initialised = True

        if YOLO is None:
            self.model = None
            return

        model_path = os.getenv("SERPENT_YOLO_MODEL", "yolov8n.pt")
        self.model = YOLO(model_path)  # will auto-download if not present

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, frame: np.ndarray) -> List[Box]:
        """Run detection on a single RGB frame (H×W×3 uint8)."""
        if self.model is None:
            return []

        # ultralytics expects BGR order; convert once using numpy.
        bgr = frame[..., ::-1]
        results = self.model.predict(bgr, verbose=False, imgsz=max(frame.shape[:2]), device="cpu")  # type: ignore
        boxes: List[Box] = []
        for r in results:  # batch=1 => single result
            for xyxy, conf, cls_id in zip(r.boxes.xyxy.cpu().numpy(), r.boxes.conf.cpu().numpy(), r.boxes.cls.cpu().numpy()):  # type: ignore
                x1, y1, x2, y2 = map(int, xyxy)
                boxes.append((x1, y1, x2, y2, float(conf), int(cls_id)))
        return boxes

# Convenience function ----------------------------------------------------

def detect_sprites(frame: np.ndarray) -> List[Box]:
    """Module-level helper using the singleton detector."""
    return YoloDetector().detect(frame)