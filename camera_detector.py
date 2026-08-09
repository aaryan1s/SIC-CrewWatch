import cv2
import time
import os
import sys
import threading
import numpy as np
from detector import PPEDetector
from compliance import evaluate_compliance
from utils import render_worker_overlay
from logger import logger

# Global Thread-Safe Latest Frame Storage
LATEST_FRAME_LOCK = threading.Lock()
LATEST_STREAM_FRAME = {
    'raw_frame': None,
    'annotated_frame': None,
    'compliance': None,
    'timestamp': None
}

def get_latest_stream_snapshot():
    """
    Returns a copy of the latest stream frame (raw & annotated) and compliance data.
    """
    with LATEST_FRAME_LOCK:
        if LATEST_STREAM_FRAME['raw_frame'] is None:
            return None
        return {
            'raw_frame': LATEST_STREAM_FRAME['raw_frame'].copy(),
            'annotated_frame': LATEST_STREAM_FRAME['annotated_frame'].copy(),
            'compliance': LATEST_STREAM_FRAME['compliance'],
            'timestamp': LATEST_STREAM_FRAME['timestamp']
        }

def make_error_frame(attempted_source, error_details=""):
    """
    Generates a dark styled error frame image displaying the exact attempted source/index and OpenCV error message.
    """
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(img, "Camera Connection Failed", (25, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
    cv2.putText(img, f"Attempted Device Index / Source: {attempted_source}", (25, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    
    if error_details:
        words = error_details.split(' ')
        line1 = " ".join(words[:7])
        line2 = " ".join(words[7:14])
        line3 = " ".join(words[14:])
        
        cv2.putText(img, f"OpenCV Error: {line1}", (25, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1, cv2.LINE_AA)
        if line2:
            cv2.putText(img, line2, (25, 265), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1, cv2.LINE_AA)
        if line3:
            cv2.putText(img, line3, (25, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1, cv2.LINE_AA)
            
    cv2.putText(img, "Support: Local Webcams / Continuity Camera / RTSP Streams", (25, 345), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (160, 160, 160), 1, cv2.LINE_AA)
    ret, buffer = cv2.imencode('.jpg', img)
    return buffer.tobytes()

def generate_camera_frames(
    source,
    detector=None,
    conf_threshold=0.35,
    iou_threshold=0.45,
    required_ppe=None
):
    """
    Robust generator function for Flask real-time MJPEG video streaming across platforms.
    Attempts default OpenCV backend first for maximum cross-platform compatibility (Windows, Linux, macOS).
    Falls back to platform-specific backends (e.g. AVFoundation on macOS) if needed.
    """
    if detector is None:
        detector = PPEDetector()

    # Convert numeric string to integer for local webcam index
    if isinstance(source, str) and source.isdigit():
        source_val = int(source)
    else:
        source_val = source

    logger.info(f"[Webcam/Stream] Requested camera source: {source_val} (Raw: '{source}')")

    cap = None
    open_error_msg = ""

    # Check if RTSP/HTTP Stream URL or local camera index
    if isinstance(source_val, str) and source_val.startswith(('rtsp://', 'http://', 'https://')):
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;5000000"
        logger.info(f"[RTSP Stream] Opening network CCTV stream: {source_val}")
        cap = cv2.VideoCapture(source_val, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            open_error_msg = f"Failed to connect to RTSP endpoint: {source_val}"
    else:
        # Local Webcam Index
        device_index = int(source_val) if isinstance(source_val, (int, str)) and str(source_val).isdigit() else 0
        logger.info(f"[Webcam] Initializing local camera index: {device_index}")

        max_attempts = 5
        for attempt in range(1, max_attempts + 1):
            # Attempt 1: Default OpenCV backend (Cross-platform standard: Linux V4L2, Windows DirectShow/MSMF, macOS)
            logger.info(f"[Webcam] Attempt {attempt}/{max_attempts}: Opening cv2.VideoCapture({device_index})...")
            cap = cv2.VideoCapture(device_index)
            
            if cap.isOpened():
                ret_test, frame_test = cap.read()
                if ret_test and frame_test is not None:
                    logger.info(f"[Webcam] Successfully opened camera index {device_index} via default backend on attempt {attempt}")
                    break
                else:
                    logger.warning(f"[Webcam] Camera index {device_index} opened with default backend but initial read failed.")
                    cap.release()
            else:
                cap.release()

            # Attempt 2: Platform-specific fallback (AVFoundation on macOS for Continuity Camera / external webcams)
            if sys.platform == 'darwin':
                logger.info(f"[Webcam] Attempt {attempt}/{max_attempts} (macOS Fallback): Trying cv2.CAP_AVFOUNDATION...")
                cap = cv2.VideoCapture(device_index, cv2.CAP_AVFOUNDATION)
                if cap.isOpened():
                    ret_test, frame_test = cap.read()
                    if ret_test and frame_test is not None:
                        logger.info(f"[Webcam] Successfully opened camera index {device_index} via AVFoundation on attempt {attempt}")
                        break
                    else:
                        cap.release()
                else:
                    cap.release()

            time.sleep(0.5)

        if not cap or not cap.isOpened():
            open_error_msg = f"cv2.VideoCapture({device_index}) failed after {max_attempts} attempts. Unable to access device index {device_index}."
            logger.error(f"[Webcam Error] {open_error_msg}")

    if not cap or not cap.isOpened():
        error_bytes = make_error_frame(source_val, open_error_msg)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + error_bytes + b'\r\n')
        return

    consecutive_failures = 0
    max_grace_failures = 30  # Grace period for camera frame initialization

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or frame is None:
                consecutive_failures += 1
                logger.warning(f"[Webcam] Frame read failed for source {source_val} (Consecutive failures: {consecutive_failures})")
                if consecutive_failures > max_grace_failures:
                    error_msg = f"Stream interrupted from device {source_val} after {consecutive_failures} read failures."
                    logger.error(f"[Webcam Error] {error_msg}")
                    error_bytes = make_error_frame(source_val, error_msg)
                    yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + error_bytes + b'\r\n')
                    break
                time.sleep(0.08)
                continue

            consecutive_failures = 0

            # Run detection
            det_result = detector.detect(frame, conf_threshold=conf_threshold, iou_threshold=iou_threshold)
            
            # Evaluate compliance
            comp_result = evaluate_compliance(det_result['detections'], required_ppe=required_ppe)
            
            # Render worker overlays
            annotated_frame = render_worker_overlay(det_result['annotated_image'], comp_result['workers'])
            
            # Store in global thread-safe snapshot buffer
            with LATEST_FRAME_LOCK:
                LATEST_STREAM_FRAME['raw_frame'] = frame.copy()
                LATEST_STREAM_FRAME['annotated_frame'] = annotated_frame.copy()
                LATEST_STREAM_FRAME['compliance'] = comp_result
                LATEST_STREAM_FRAME['timestamp'] = time.strftime("%H:%M:%S")

            # Encode frame as JPEG
            ret_enc, buffer = cv2.imencode('.jpg', annotated_frame)
            if not ret_enc:
                continue

            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Pause to cap frame rate (~25 FPS max)
            time.sleep(0.04)

    finally:
        if cap:
            cap.release()
            logger.info(f"[Webcam] Released video capture capture for camera source: {source_val}")
