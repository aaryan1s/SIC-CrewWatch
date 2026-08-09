import os
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO

from config import MODEL_PATH
from utils import CLASS_COLORS, draw_bounding_box
from logger import logger

# Default class mapping as present in models/best.pt
DEFAULT_CLASS_MAP = {
    0: 'boots',
    1: 'glove',
    2: 'helmet',
    3: 'person',
    4: 'vest'
}

_MODEL_CACHE = {}

def load_yolo_model(model_path=None):
    """
    Loads and caches the YOLOv8 PPE detection model in memory using pathlib.Path relative resolution.
    """
    if model_path is None:
        target_path = MODEL_PATH
    else:
        target_path = Path(model_path)
        
    resolved_path = target_path.resolve()
    path_str = str(resolved_path)
    
    if not resolved_path.exists():
        logger.error(f"YOLO Model file not found at resolved path: {resolved_path}")
        raise FileNotFoundError(f"Model file not found at path: {resolved_path}")
        
    if path_str not in _MODEL_CACHE:
        logger.info(f"Loading YOLO PPE Detection model into memory from: {resolved_path}")
        _MODEL_CACHE[path_str] = YOLO(path_str)
        logger.info("YOLO Model loaded successfully into memory cache.")
        
    return _MODEL_CACHE[path_str]

class PPEDetector:
    def __init__(self, model_path=None):
        self.model_path = Path(model_path) if model_path else MODEL_PATH
        self.model = load_yolo_model(self.model_path)
        # Verify model classes or use default mapping
        self.names = self.model.names if hasattr(self.model, 'names') else DEFAULT_CLASS_MAP

    def detect(self, img, conf_threshold=0.25, iou_threshold=0.45):
        """
        Runs object detection on an image (numpy array BGR or file path/Path).
        Returns a dict containing detected objects list, raw result, and custom annotated image.
        """
        if isinstance(img, (str, Path)):
            img_path_str = str(Path(img).resolve())
            img_bgr = cv2.imread(img_path_str)
        else:
            img_bgr = img.copy()

        if img_bgr is None:
            logger.error("Input image for PPE detection could not be loaded or is None.")
            raise ValueError("Input image could not be loaded.")

        # Run inference
        results = self.model(img_bgr, conf=conf_threshold, iou=iou_threshold, verbose=False)
        result = results[0]
        
        detections = []
        annotated_bgr = img_bgr.copy()
        
        if result.boxes is not None and len(result.boxes) > 0:
            boxes = result.boxes.xyxy.cpu().numpy()
            confs = result.boxes.conf.cpu().numpy()
            clss = result.boxes.cls.cpu().numpy().astype(int)
            
            for box, conf, cls_id in zip(boxes, confs, clss):
                class_name = self.names.get(cls_id, f"class_{cls_id}").lower()
                detection_item = {
                    'class_id': int(cls_id),
                    'class_name': class_name,
                    'confidence': float(conf),
                    'box': box.tolist()  # [x1, y1, x2, y2]
                }
                detections.append(detection_item)
                
                # Draw box
                color = CLASS_COLORS.get(class_name, (200, 200, 200))
                draw_bounding_box(annotated_bgr, box, class_name, conf, color=color)

        return {
            'detections': detections,
            'annotated_image': annotated_bgr,
            'raw_result': result,
            'counts': self._count_classes(detections)
        }

    def _count_classes(self, detections):
        """Helper to count detections per class."""
        counts = {'person': 0, 'helmet': 0, 'vest': 0, 'glove': 0, 'boots': 0}
        for d in detections:
            c = d['class_name']
            if c in counts:
                counts[c] += 1
            else:
                counts[c] = 1
        return counts
