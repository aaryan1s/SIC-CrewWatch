import os
import io
import time
import cv2
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, Response
from werkzeug.utils import secure_filename

# Import central configuration, logging, & health check
from config import (
    Config, UPLOADS_DIR, OUTPUTS_DIR, REPORTS_DIR, MODELS_DIR,
    TEMP_DIR, LOGS_DIR, ensure_directories
)
from logger import logger
from health_check import run_system_health_check

# Import custom application backend modules
from utils import discover_files, save_uploaded_file, render_worker_overlay, is_port_in_use, find_available_port
from detector import PPEDetector
from compliance import evaluate_compliance
from alerts import generate_alerts
from video_detector import process_video_file
from camera_detector import generate_camera_frames, get_latest_stream_snapshot
from dashboard import get_compliance_breakdown_chart_json, get_worker_ratio_chart_json
from report import generate_pdf_report, save_pdf_report_to_disk

# 1. Ensure all system storage folders exist
ensure_directories()

# 2. Initialize Flask App & Load Config
app = Flask(__name__)
app.config.from_object(Config)

# 3. Perform Startup System Health Check
run_system_health_check()

# Global State Container for last evaluated data
app_state = {
    'detector': None,
    'last_compliance_result': {
        'total_workers': 0,
        'compliant_workers': 0,
        'non_compliant_workers': 0,
        'helmet_compliance_pct': 0.0,
        'vest_compliance_pct': 0.0,
        'glove_compliance_pct': 0.0,
        'boot_compliance_pct': 0.0,
        'overall_safety_score': 0.0,
        'workers': []
    },
    'last_alerts': [],
    'last_annotated_image_path': None,
    'last_original_image_path': None,
    'last_inspection_type': 'Static Image Audit',
    'last_pdf_filename': None,
    'last_video_filename': None
}

def get_detector():
    if app_state['detector'] is None:
        logger.info("Initializing PPEDetector instance in app_state...")
        app_state['detector'] = PPEDetector()
    return app_state['detector']


# ==========================================
# ERROR HANDLERS (No Raw Tracebacks Exposed)
# ==========================================

@app.errorhandler(404)
def handle_404_error(e):
    logger.warning(f"404 Not Found requested: {request.path}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Requested API endpoint or resource was not found.'}), 404
    return render_template('index.html'), 404

@app.errorhandler(413)
def handle_413_error(e):
    logger.warning("413 Request Entity Too Large: Uploaded file exceeds max content limit.")
    return jsonify({'error': 'File payload exceeds maximum allowable upload size limit (500 MB).'}), 413

@app.errorhandler(500)
def handle_500_error(e):
    logger.exception("500 Internal Server Error encountered during request execution:")
    return jsonify({'error': 'An internal server error occurred while processing your request.'}), 500


# ==========================================
# VIEW ROUTES
# ==========================================

@app.route('/')
def index():
    """Main Industrial PPE Inspection Studio page."""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Safety Analytics Dashboard page."""
    return render_template('dashboard.html')


# ==========================================
# FILE SERVING & DOWNLOAD ROUTES (Secure Path Handling)
# ==========================================

@app.route('/outputs/<path:filename>')
def serve_output_file(filename):
    ensure_directories()
    clean_name = secure_filename(Path(filename).name)
    mimetype = 'video/mp4' if clean_name.lower().endswith('.mp4') else None
    return send_from_directory(str(OUTPUTS_DIR.resolve()), clean_name, mimetype=mimetype)

@app.route('/uploads/<path:filename>')
def serve_upload_file(filename):
    ensure_directories()
    clean_name = secure_filename(Path(filename).name)
    mimetype = 'video/mp4' if clean_name.lower().endswith('.mp4') else None
    return send_from_directory(str(UPLOADS_DIR.resolve()), clean_name, mimetype=mimetype)

@app.route('/reports/<path:filename>')
def serve_report_file(filename):
    ensure_directories()
    clean_name = secure_filename(Path(filename).name)
    return send_from_directory(str(REPORTS_DIR.resolve()), clean_name)

@app.route('/download/output/<path:filename>')
def download_output_file(filename):
    """Triggers attachment download for output assets (images, videos)."""
    ensure_directories()
    clean_name = secure_filename(Path(filename).name)
    return send_from_directory(str(OUTPUTS_DIR.resolve()), clean_name, as_attachment=True)

@app.route('/download/report/<path:filename>')
def download_report_file(filename):
    """Triggers attachment download for PDF audit reports."""
    ensure_directories()
    clean_name = secure_filename(Path(filename).name)
    return send_from_directory(str(REPORTS_DIR.resolve()), clean_name, as_attachment=True)


# ==========================================
# REST API ENDPOINTS
# ==========================================

@app.route('/api/inspect-image', methods=['POST'])
def api_inspect_image():
    """Handles static image PPE inspection with 100% production fault tolerance."""
    ensure_directories()
    try:
        if 'image' not in request.files or request.files['image'].filename == '':
            logger.warning("No image file provided in upload request.")
            return jsonify({'error': 'Please select an image file to upload.'}), 400

        uploaded = request.files['image']
        ext = Path(uploaded.filename).suffix.lower()
        if ext not in Config.ALLOWED_IMAGE_EXTENSIONS:
            logger.warning(f"Unsupported image file extension: {ext}")
            return jsonify({'error': f'Unsupported image file extension: {ext}'}), 400

        try:
            image_path_str = save_uploaded_file(uploaded)
            image_path = Path(image_path_str)
        except Exception as e:
            logger.exception("Failed to save uploaded image file:")
            return jsonify({'error': f'Failed to save uploaded image: {str(e)}'}), 500

        if not image_path.exists():
            logger.error(f"Saved uploaded image file not found: {image_path_str}")
            return jsonify({'error': 'Uploaded image file could not be saved.'}), 400

        logger.info(f"Processing static image inspection for: {image_path.name}")

        # Step 1: Image loaded
        logger.info("--> [1/8] Loading image from disk...")
        try:
            image_bgr = cv2.imread(str(image_path.resolve()))
            if image_bgr is None:
                raise ValueError(f"cv2.imread returned None for path '{image_path}'")
            logger.info("✔ Image loaded successfully.")
        except Exception as e:
            logger.exception(f"Error loading image '{image_path.name}':")
            return jsonify({'error': f'Failed to decode image file: {str(e)}'}), 400

        # Step 2: YOLO inference complete
        logger.info("--> [2/8] Running YOLO model inference...")
        try:
            detector = get_detector()
            det_result = detector.detect(image_bgr)
            logger.info("✔ YOLO inference complete.")
        except Exception as e:
            logger.exception("Error executing YOLO model inference:")
            return jsonify({'error': f'AI detection inference failed: {str(e)}'}), 500

        # Step 3: Compliance computed
        logger.info("--> [3/8] Computing compliance rules...")
        try:
            comp_result = evaluate_compliance(det_result['detections'])
            logger.info("✔ Compliance computed.")
        except Exception as e:
            logger.exception("Error evaluating compliance rules:")
            return jsonify({'error': f'Compliance evaluation failed: {str(e)}'}), 500

        # Step 4: Overlay rendered
        logger.info("--> [4/8] Rendering worker overlay...")
        try:
            annotated_bgr = render_worker_overlay(det_result['annotated_image'], comp_result['workers'])
            logger.info("✔ Overlay rendered.")
        except Exception as e:
            logger.exception("Error rendering worker overlay badges (falling back to detector output):")
            annotated_bgr = det_result.get('annotated_image', image_bgr)

        # Step 5: Annotated image saved
        logger.info("--> [5/8] Saving annotated image output...")
        base_name = image_path.name
        ann_filename = f"annotated_{base_name}"
        ann_path = OUTPUTS_DIR / ann_filename
        try:
            cv2.imwrite(str(ann_path.resolve()), annotated_bgr)
            logger.info(f"✔ Annotated image saved to: {ann_path.name}")
        except Exception as e:
            logger.exception("Error saving annotated image to disk:")

        # Alerts generation
        try:
            alerts = generate_alerts(comp_result)
        except Exception as e:
            logger.exception("Error generating compliance alerts:")
            alerts = []

        # Step 6: Generating PDF
        logger.info("--> [6/8] Generating PDF safety inspection report...")
        pdf_filename = None
        download_pdf_url = None
        try:
            pdf_bytes = generate_pdf_report(
                compliance_data=comp_result,
                alerts_list=alerts,
                image_path=str(ann_path.resolve()) if ann_path.exists() else None,
                original_image_path=str(image_path.resolve()),
                title="CrewWatch Safety Inspection Report",
                inspection_type="Static Image Audit"
            )
            if pdf_bytes:
                pdf_filename = f"ppe_image_report_{int(time.time())}.pdf"
                saved_pdf = save_pdf_report_to_disk(pdf_bytes, filename=pdf_filename)
                if saved_pdf:
                    download_pdf_url = f"/download/report/{pdf_filename}"
                    # Step 7: PDF generated successfully
                    logger.info("✔ PDF generated successfully.")
                else:
                    logger.warning("PDF generated but disk save returned None. Setting download_pdf_url to None.")
            else:
                logger.warning("PDF generation returned empty bytes. Setting download_pdf_url to None.")
        except Exception as e:
            logger.exception("PDF generation failed during image inspection (bypassing PDF, returning JSON with download_pdf_url=null):")
            download_pdf_url = None

        # Update App State safely
        try:
            app_state['last_compliance_result'] = comp_result
            app_state['last_alerts'] = alerts
            app_state['last_annotated_image_path'] = str(ann_path.resolve()) if ann_path.exists() else None
            app_state['last_original_image_path'] = str(image_path.resolve())
            app_state['last_inspection_type'] = "Static Image Audit"
            app_state['last_pdf_filename'] = pdf_filename
        except Exception as e:
            logger.exception("Error updating app_state container:")

        # Step 8: Returning API response
        logger.info("--> [8/8] Returning API response successfully.")
        return jsonify({
            'success': True,
            'original_url': f"/uploads/{base_name}",
            'annotated_url': f"/outputs/{ann_filename}",
            'download_annotated_url': f"/download/output/{ann_filename}",
            'download_pdf_url': download_pdf_url,
            'compliance': comp_result,
            'alerts': alerts
        })
    except Exception as e:
        logger.exception("Unhandled error in /api/inspect-image endpoint:")
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-video', methods=['POST'])
def api_process_video():
    """Handles video file frame-by-frame PPE processing."""
    ensure_directories()
    try:
        if 'video' not in request.files or request.files['video'].filename == '':
            return jsonify({'error': 'Please select a video file to upload.'}), 400

        uploaded = request.files['video']
        ext = Path(uploaded.filename).suffix.lower()
        if ext not in Config.ALLOWED_VIDEO_EXTENSIONS:
            return jsonify({'error': f'Unsupported video file extension: {ext}'}), 400

        video_path_str = save_uploaded_file(uploaded)
        video_path = Path(video_path_str)

        if not video_path.exists():
            return jsonify({'error': 'Uploaded video file could not be saved.'}), 400

        logger.info(f"Processing video telemetry analysis for: {video_path.name}")

        detector = get_detector()
        res = process_video_file(str(video_path.resolve()), detector=detector)

        comp_data = {
            'total_workers': res['max_workers'],
            'compliant_workers': int(res['max_workers'] * (res['overall_safety_score'] / 100.0)),
            'non_compliant_workers': res['max_workers'] - int(res['max_workers'] * (res['overall_safety_score'] / 100.0)),
            'helmet_compliance_pct': res['helmet_compliance_pct'],
            'vest_compliance_pct': res['vest_compliance_pct'],
            'glove_compliance_pct': res['glove_compliance_pct'],
            'boot_compliance_pct': res['boot_compliance_pct'],
            'overall_safety_score': res['overall_safety_score'],
            'workers': res['last_compliance']['workers'] if res['last_compliance'] else []
        }

        # Fault Tolerant Video PDF Report
        download_pdf_url = None
        pdf_filename = None
        try:
            pdf_bytes = generate_pdf_report(
                compliance_data=comp_data,
                alerts_list=res['alerts'],
                image_path=None,
                title="CrewWatch Safety Inspection Report",
                inspection_type="Video Recording Analysis"
            )
            if pdf_bytes:
                pdf_filename = f"ppe_video_report_{int(time.time())}.pdf"
                saved_pdf = save_pdf_report_to_disk(pdf_bytes, filename=pdf_filename)
                if saved_pdf:
                    download_pdf_url = f"/download/report/{pdf_filename}"
        except Exception as e:
            logger.exception("PDF generation failed during video analysis (setting download_pdf_url=None):")
            download_pdf_url = None

        # Update App State
        app_state['last_compliance_result'] = comp_data
        app_state['last_alerts'] = res['alerts']
        app_state['last_inspection_type'] = "Video Recording Analysis"
        app_state['last_pdf_filename'] = pdf_filename
        app_state['last_video_filename'] = res['output_video_filename']

        orig_filename = video_path.name

        return jsonify({
            'success': True,
            'original_video_url': f"/uploads/{orig_filename}",
            'annotated_video_url': f"/outputs/{res['output_video_filename']}",
            'download_video_url': f"/download/output/{res['output_video_filename']}",
            'download_pdf_url': download_pdf_url,
            'stats': comp_data,
            'alerts': res['alerts']
        })
    except Exception as e:
        logger.exception("Error in /api/process-video endpoint:")
        return jsonify({'error': str(e)}), 500

@app.route('/api/video-feed')
def api_video_feed():
    """Streams live webcam or RTSP MJPEG video feed."""
    source_param = request.args.get('source', '0')
    logger.info(f"Video feed requested for source: '{source_param}'")
    detector = get_detector()
    return Response(
        generate_camera_frames(source_param, detector=detector),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/api/capture-frame', methods=['POST'])
def api_capture_frame():
    """
    Captures current live stream snapshot (Webcam or RTSP), saves annotated image,
    generates immediate ReportLab PDF, and returns download URLs.
    """
    ensure_directories()
    try:
        data = request.get_json() or {}
        stream_type = data.get('stream_type', 'Webcam')

        snapshot = get_latest_stream_snapshot()
        if snapshot is None:
            return jsonify({'error': 'No active stream frame buffer found. Please start live feed first.'}), 400

        raw_frame = snapshot['raw_frame']
        annotated_frame = snapshot['annotated_frame']
        comp_result = snapshot['compliance']

        timestamp_str = int(time.time())
        raw_filename = f"captured_raw_{stream_type.lower()}_{timestamp_str}.jpg"
        ann_filename = f"captured_ann_{stream_type.lower()}_{timestamp_str}.jpg"

        raw_path = OUTPUTS_DIR / raw_filename
        ann_path = OUTPUTS_DIR / ann_filename

        try:
            cv2.imwrite(str(raw_path.resolve()), raw_frame)
            cv2.imwrite(str(ann_path.resolve()), annotated_frame)
        except Exception as e:
            logger.exception("Error saving captured stream frames to disk:")

        alerts = generate_alerts(comp_result)

        # Fault Tolerant PDF Report for Captured Frame
        inspection_label = f"Live {stream_type} Stream Capture"
        download_pdf_url = None
        pdf_filename = None
        try:
            pdf_bytes = generate_pdf_report(
                compliance_data=comp_result,
                alerts_list=alerts,
                image_path=str(ann_path.resolve()) if ann_path.exists() else None,
                original_image_path=str(raw_path.resolve()) if raw_path.exists() else None,
                title="CrewWatch Safety Inspection Report",
                inspection_type=inspection_label
            )
            if pdf_bytes:
                pdf_filename = f"ppe_stream_report_{timestamp_str}.pdf"
                saved_pdf = save_pdf_report_to_disk(pdf_bytes, filename=pdf_filename)
                if saved_pdf:
                    download_pdf_url = f"/download/report/{pdf_filename}"
        except Exception as e:
            logger.exception("PDF generation failed during frame capture (setting download_pdf_url=None):")
            download_pdf_url = None

        # Update App State
        app_state['last_compliance_result'] = comp_result
        app_state['last_alerts'] = alerts
        app_state['last_annotated_image_path'] = str(ann_path.resolve()) if ann_path.exists() else None
        app_state['last_original_image_path'] = str(raw_path.resolve()) if raw_path.exists() else None
        app_state['last_inspection_type'] = inspection_label
        app_state['last_pdf_filename'] = pdf_filename

        return jsonify({
            'success': True,
            'captured_image_url': f"/outputs/{ann_filename}",
            'download_image_url': f"/download/output/{ann_filename}",
            'download_pdf_url': download_pdf_url,
            'compliance': comp_result,
            'alerts': alerts
        })
    except Exception as e:
        logger.exception("Error in /api/capture-frame endpoint:")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard-data')
def api_dashboard_data():
    """Returns analytics data, Plotly JSON charts, and worker matrix."""
    try:
        comp = app_state['last_compliance_result']
        bar_chart_json = get_compliance_breakdown_chart_json(comp)
        pie_chart_json = get_worker_ratio_chart_json(comp)

        return jsonify({
            'compliance': comp,
            'alerts': app_state['last_alerts'],
            'bar_chart': bar_chart_json,
            'pie_chart': pie_chart_json
        })
    except Exception as e:
        logger.exception("Error in /api/dashboard-data endpoint:")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-pdf', methods=['POST'])
def api_generate_pdf():
    """Generates and downloads PDF safety report on demand."""
    try:
        data = request.get_json() or {}
        title = data.get('title', 'CrewWatch Safety Inspection Report')

        comp = app_state['last_compliance_result']
        alerts = app_state['last_alerts']
        ann_path = app_state['last_annotated_image_path']
        raw_path = app_state['last_original_image_path']
        insp_type = app_state['last_inspection_type']

        pdf_bytes = generate_pdf_report(
            compliance_data=comp,
            alerts_list=alerts,
            image_path=ann_path,
            original_image_path=raw_path,
            title=title,
            inspection_type=insp_type
        )
        saved_pdf = save_pdf_report_to_disk(pdf_bytes)
        download_name = Path(saved_pdf).name if saved_pdf else "ppe_safety_report.pdf"

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=download_name
        )
    except Exception as e:
        logger.exception("Error in /api/generate-pdf endpoint:")
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )

