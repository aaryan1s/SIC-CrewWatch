import os
import socket
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from werkzeug.utils import secure_filename

from config import (
    BASE_DIR, UPLOADS_DIR, OUTPUTS_DIR, REPORTS_DIR, MODELS_DIR,
    TEMP_DIR, LOGS_DIR, ALLOWED_IMAGE_EXTENSIONS, ALLOWED_VIDEO_EXTENSIONS, ensure_directories
)
from logger import logger

# Ensure directories exist on module load
ensure_directories()

# Class colors in BGR format
CLASS_COLORS = {
    'person': (255, 191, 0),    # Deep Cyan/Amber
    'helmet': (0, 230, 115),    # Vibrant Green
    'vest': (0, 165, 255),      # Bright Orange
    'glove': (230, 216, 0),     # Bright Cyan/Yellow
    'boots': (230, 100, 255),   # Soft Purple
    'missing': (50, 50, 230)    # High-contrast Red for missing PPE
}

_FONT_CACHE = {}

def get_unicode_font(font_size=12):
    """
    Loads a system TrueType font capable of rendering Unicode checkmarks (✓, ✗).
    Caches font objects per size for optimal performance.
    """
    if font_size in _FONT_CACHE:
        return _FONT_CACHE[font_size]

    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Verdana.ttf",
        "/System/Library/Fonts/Supplemental/Tahoma.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
    ]

    for p in font_paths:
        if not os.path.exists(p) and not p.endswith(".ttf"):
            continue
        try:
            font = ImageFont.truetype(p, font_size)
            mask_v = font.getmask("✓")
            mask_x = font.getmask("✗")
            if mask_v.size[0] > 0 and mask_v.size[1] > 0 and mask_x.size[0] > 0 and mask_x.size[1] > 0:
                _FONT_CACHE[font_size] = font
                return font
        except Exception:
            continue

    fallback = ImageFont.load_default()
    _FONT_CACHE[font_size] = fallback
    return fallback

def draw_unicode_text_on_cv2(img_bgr, text, org, font_size=12, color=(200, 255, 200)):
    """
    Renders text (including Unicode ✓ and ✗) onto a cv2 BGR image at org=(x, y).
    Replaces cv2.putText for Unicode string rendering.
    """
    try:
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        draw = ImageDraw.Draw(pil_img)
        font = get_unicode_font(font_size)

        rgb_color = (color[2], color[1], color[0])
        draw.text(org, text, font=font, fill=rgb_color)

        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        logger.error(f"Error rendering Unicode text overlay via PIL: {e}")
        return img_bgr

def discover_files(directory=UPLOADS_DIR, image_exts=ALLOWED_IMAGE_EXTENSIONS, video_exts=ALLOWED_VIDEO_EXTENSIONS):
    """
    Automatically discovers image and video files in the specified directory using pathlib.Path.
    Returns a dict with 'images' and 'videos' lists containing file metadata.
    """
    ensure_directories()
    target_dir = Path(directory)
    images = []
    videos = []
    
    if not target_dir.exists():
        return {'images': [], 'videos': []}
        
    try:
        for entry in target_dir.iterdir():
            if entry.is_file() and not entry.name.startswith('.'):
                ext = entry.suffix.lower()
                stat = entry.stat()
                mod_time = stat.st_mtime
                size_mb = stat.st_size / (1024 * 1024)
                file_info = {
                    'name': entry.name,
                    'path': str(entry.resolve()),
                    'ext': ext,
                    'mtime': mod_time,
                    'size_mb': round(size_mb, 2)
                }
                if ext in image_exts:
                    images.append(file_info)
                elif ext in video_exts:
                    videos.append(file_info)
    except Exception as e:
        logger.error(f"Error discovering files in directory '{target_dir}': {e}")
                
    # Sort files newest first
    images.sort(key=lambda x: x['mtime'], reverse=True)
    videos.sort(key=lambda x: x['mtime'], reverse=True)
    
    return {'images': images, 'videos': videos}

def save_uploaded_file(uploaded_file, destination_dir=UPLOADS_DIR):
    """
    Saves a Flask FileStorage object or buffer to the destination directory securely.
    Sanitizes filenames using secure_filename and Path.name to prevent path traversal.
    Returns the string representation of the saved file path.
    """
    ensure_directories()
    dest = Path(destination_dir)
    
    if hasattr(uploaded_file, 'filename') and uploaded_file.filename:
        raw_name = uploaded_file.filename
    elif hasattr(uploaded_file, 'name') and uploaded_file.name:
        raw_name = uploaded_file.name
    else:
        raw_name = "uploaded_file"

    # Strict path traversal defense: secure_filename + Path.name
    clean_name = secure_filename(Path(raw_name).name)
    if not clean_name:
        clean_name = "uploaded_file"
        
    target_path = dest / clean_name
    
    try:
        if hasattr(uploaded_file, 'save'):
            uploaded_file.save(str(target_path))
        elif hasattr(uploaded_file, 'read'):
            with open(target_path, "wb") as f:
                f.write(uploaded_file.read())
        else:
            raise ValueError("Unsupported uploaded_file object type.")
        
        logger.info(f"File uploaded & saved securely to: {target_path}")
        return str(target_path.resolve())
    except Exception as e:
        logger.error(f"Failed to save uploaded file '{clean_name}': {e}")
        raise

def draw_bounding_box(img, box, label, confidence, color=(0, 255, 0), thickness=2):
    """
    Draws a styled bounding box with semi-transparent label background banner.
    """
    x1, y1, x2, y2 = map(int, box)
    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
    
    caption = f"{label} {confidence:.2f}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_thick = 1
    
    (w, h), baseline = cv2.getTextSize(caption, font, font_scale, font_thick)
    
    # Draw label box background
    cv2.rectangle(img, (x1, max(0, y1 - h - 10)), (x1 + w + 10, y1), color, -1)
    # Text in white/dark contrast
    text_color = (255, 255, 255) if sum(color) < 400 else (0, 0, 0)
    cv2.putText(img, caption, (x1 + 5, max(12, y1 - 5)), font, font_scale, text_color, font_thick, cv2.LINE_AA)

def render_worker_overlay(img, worker_compliance_list):
    """
    Overlays worker compliance summary badges directly on worker bounding boxes.
    Renders ✓ and ✗ unicode checkmarks using PIL ImageDraw with original layout.
    """
    annotated_img = img.copy()
    
    for idx, worker in enumerate(worker_compliance_list, 1):
        x1, y1, x2, y2 = map(int, worker['box'])
        is_compliant = worker['is_fully_compliant']
        box_color = (0, 220, 0) if is_compliant else (0, 0, 235)
        
        # Worker main bounding box
        cv2.rectangle(annotated_img, (x1, y1), (x2, y2), box_color, 3)
        
        # Worker Header badge
        status_str = "COMPLIANT" if is_compliant else f"NON-COMPLIANT ({len(worker['missing_items'])} missing)"
        header_text = f"Worker #{idx}: {status_str}"
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.55
        font_thick = 2
        (w, h), _ = cv2.getTextSize(header_text, font, font_scale, font_thick)
        
        badge_y1 = max(0, y1 - h - 14)
        cv2.rectangle(annotated_img, (x1, badge_y1), (x1 + w + 16, y1), box_color, -1)
        cv2.putText(annotated_img, header_text, (x1 + 8, y1 - 6), font, font_scale, (255, 255, 255), font_thick, cv2.LINE_AA)
        
        # Draw PPE presence checklist pill on bottom of worker box
        checklist_items = []
        for gear in ['helmet', 'vest', 'glove', 'boots']:
            status_symbol = "✓" if worker['detected_items'].get(gear, False) else "✗"
            checklist_items.append(f"{gear[0].upper()}:{status_symbol}")
        
        checklist_str = " | ".join(checklist_items)
        (cw, ch), _ = cv2.getTextSize(checklist_str, font, 0.45, 1)
        
        pill_y1 = y2
        pill_y2 = min(annotated_img.shape[0], y2 + ch + 10)
        cv2.rectangle(annotated_img, (x1, pill_y1), (x1 + cw + 14, pill_y2), (30, 30, 30), -1)

        # Replace ONLY cv2.putText with Pillow draw_unicode_text_on_cv2 for full Unicode rendering
        text_color = (200, 255, 200) if is_compliant else (150, 150, 255)
        annotated_img = draw_unicode_text_on_cv2(
            annotated_img,
            checklist_str,
            (x1 + 7, pill_y1 + 2),
            font_size=12,
            color=text_color
        )
        
    return annotated_img

def is_port_in_use(port: int, host: str = '0.0.0.0') -> bool:
    """Checks whether a TCP port is currently bound or in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True

def find_available_port(host: str = '0.0.0.0', start_port: int = 5001, max_tries: int = 50) -> int:
    """
    Checks if start_port is available. If taken, finds and returns the next free port.
    """
    for port in range(start_port, start_port + max_tries):
        if not is_port_in_use(port, host):
            return port
    return start_port
