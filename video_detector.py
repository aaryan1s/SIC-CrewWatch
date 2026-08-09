import os
from pathlib import Path
import cv2
import time
import subprocess
import numpy as np
import imageio_ffmpeg

from detector import PPEDetector
from compliance import evaluate_compliance
from alerts import generate_alerts
from utils import render_worker_overlay
from config import OUTPUTS_DIR, TEMP_DIR, ensure_directories
from logger import logger

def process_video_file(
    video_path,
    detector=None,
    conf_threshold=0.25,
    iou_threshold=0.45,
    required_ppe=None
):
    """
    Processes a video file frame-by-frame, performs PPE detection & compliance evaluation,
    and exports a browser-playable H.264 MP4 video output using imageio-ffmpeg.
    Uses pathlib.Path for all file path operations.
    """
    ensure_directories()
    
    if detector is None:
        detector = PPEDetector()
        
    input_path = Path(video_path).resolve()
    if not input_path.exists():
        logger.error(f"Video file not found at: {input_path}")
        raise ValueError(f"Could not open video file at: {input_path}")

    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        logger.error(f"cv2.VideoCapture failed to open video file at: {input_path}")
        raise ValueError(f"Could not open video file at: {input_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    filename = input_path.name
    base_name = input_path.stem
    
    temp_raw_filename = f"temp_raw_{base_name}_{int(time.time())}.mp4"
    temp_raw_path = TEMP_DIR / temp_raw_filename
    
    final_h264_filename = f"annotated_{base_name}.mp4"
    final_h264_path = OUTPUTS_DIR / final_h264_filename
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(temp_raw_path), fourcc, fps, (width, height))

    logger.info(f"Started video telemetry processing for file: '{filename}' ({width}x{height} @ {fps:.1f} FPS)")

    frame_count = 0
    worker_counts = []
    helmet_pcts = []
    vest_pcts = []
    glove_pcts = []
    boot_pcts = []
    scores = []
    all_alerts = []

    last_compliance = None

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            
            # Run detection
            det_result = detector.detect(frame, conf_threshold=conf_threshold, iou_threshold=iou_threshold)
            detections = det_result['detections']
            
            # Evaluate compliance
            comp_result = evaluate_compliance(detections, required_ppe=required_ppe)
            last_compliance = comp_result
            
            # Render worker overlays
            annotated_frame = render_worker_overlay(det_result['annotated_image'], comp_result['workers'])
            
            # Write to temp raw video file
            writer.write(annotated_frame)
            
            # Record frame stats
            worker_counts.append(comp_result['total_workers'])
            helmet_pcts.append(comp_result['helmet_compliance_pct'])
            vest_pcts.append(comp_result['vest_compliance_pct'])
            glove_pcts.append(comp_result['glove_compliance_pct'])
            boot_pcts.append(comp_result['boot_compliance_pct'])
            scores.append(comp_result['overall_safety_score'])
            
            frame_alerts = generate_alerts(comp_result)
            all_alerts.extend([a for a in frame_alerts if a['severity'] != 'SUCCESS'])

    finally:
        cap.release()
        writer.release()

    logger.info(f"Completed frame-by-frame detection for '{filename}'. Total frames processed: {frame_count}")

    # Re-encode video into browser-standard H.264/AAC MP4 using imageio-ffmpeg static binary
    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [
            ffmpeg_exe, '-y',
            '-i', str(temp_raw_path),
            '-vcodec', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
            str(final_h264_path)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"H.264 video conversion successful: '{final_h264_filename}'")
        if temp_raw_path.exists():
            temp_raw_path.unlink()
    except Exception as e:
        logger.warning(f"H.264 conversion warning: {e}. Falling back to raw file rename.")
        if temp_raw_path.exists():
            if final_h264_path.exists():
                final_h264_path.unlink()
            temp_raw_path.rename(final_h264_path)

    # Aggregate global video stats
    avg_workers = round(float(np.mean(worker_counts)), 1) if worker_counts else 0
    max_workers = int(np.max(worker_counts)) if worker_counts else 0
    avg_helmet = round(float(np.mean(helmet_pcts)), 1) if helmet_pcts else 0.0
    avg_vest = round(float(np.mean(vest_pcts)), 1) if vest_pcts else 0.0
    avg_glove = round(float(np.mean(glove_pcts)), 1) if glove_pcts else 0.0
    avg_boot = round(float(np.mean(boot_pcts)), 1) if boot_pcts else 0.0
    avg_score = round(float(np.mean(scores)), 1) if scores else 0.0

    return {
        'output_video_filename': final_h264_filename,
        'output_video_path': str(final_h264_path.resolve()),
        'total_frames': frame_count,
        'avg_workers': avg_workers,
        'max_workers': max_workers,
        'helmet_compliance_pct': avg_helmet,
        'vest_compliance_pct': avg_vest,
        'glove_compliance_pct': avg_glove,
        'boot_compliance_pct': avg_boot,
        'overall_safety_score': avg_score,
        'last_compliance': last_compliance,
        'alerts': all_alerts[:15],
        'frame_scores': scores
    }
