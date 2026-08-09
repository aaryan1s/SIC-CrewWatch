import sys
import cv2
from pathlib import Path
from config import (
    UPLOADS_DIR, OUTPUTS_DIR, REPORTS_DIR, MODELS_DIR,
    TEMP_DIR, LOGS_DIR, STATIC_DIR, TEMPLATES_DIR, MODEL_PATH, ensure_directories
)
from logger import logger

def run_system_health_check():
    """
    Performs startup system health checks and verifies core application readiness.
    Logs status for each component and creates any missing required directories automatically.
    """
    logger.info("==================================================")
    logger.info("  CrewWatch Industrial PPE Safety System Startup  ")
    logger.info("==================================================")
    
    # 1. Ensure Directories
    ensure_directories()
    
    health_status = {
        'config_loaded': True,
        'uploads_ready': UPLOADS_DIR.exists(),
        'outputs_ready': OUTPUTS_DIR.exists(),
        'reports_ready': REPORTS_DIR.exists(),
        'logs_ready': LOGS_DIR.exists(),
        'temp_ready': TEMP_DIR.exists(),
        'static_ready': STATIC_DIR.exists(),
        'templates_ready': TEMPLATES_DIR.exists(),
        'opencv_ready': False,
        'model_file_exists': MODEL_PATH.exists(),
        'model_loaded': False
    }

    logger.info("✔ [Health Check] Configuration Loaded successfully.")
    logger.info(f"✔ [Health Check] Uploads Directory: {UPLOADS_DIR} (Ready)")
    logger.info(f"✔ [Health Check] Outputs Directory: {OUTPUTS_DIR} (Ready)")
    logger.info(f"✔ [Health Check] Reports Directory: {REPORTS_DIR} (Ready)")
    logger.info(f"✔ [Health Check] Logs Directory:    {LOGS_DIR} (Ready)")
    logger.info(f"✔ [Health Check] Temp Directory:    {TEMP_DIR} (Ready)")
    
    if health_status['static_ready']:
        logger.info(f"✔ [Health Check] Static Folder:     {STATIC_DIR} (Ready)")
    else:
        logger.warning(f"⚠ [Health Check] Static Folder missing at: {STATIC_DIR}")
        
    if health_status['templates_ready']:
        logger.info(f"✔ [Health Check] Templates Folder:  {TEMPLATES_DIR} (Ready)")
    else:
        logger.warning(f"⚠ [Health Check] Templates Folder missing at: {TEMPLATES_DIR}")

    # 2. Check OpenCV
    try:
        cv_version = cv2.__version__
        health_status['opencv_ready'] = True
        logger.info(f"✔ [Health Check] OpenCV Ready (Version: {cv_version})")
    except Exception as e:
        logger.error(f"❌ [Health Check] OpenCV initialization failed: {e}")

    # 3. Check Model File
    if health_status['model_file_exists']:
        logger.info(f"✔ [Health Check] YOLO Model File found at: {MODEL_PATH}")
    else:
        logger.error(f"❌ [Health Check] YOLO Model File MISSING at: {MODEL_PATH}")

    # 4. Verify Model Load Readiness
    try:
        from detector import load_yolo_model
        model = load_yolo_model(MODEL_PATH)
        if model is not None:
            health_status['model_loaded'] = True
            health_status['yolo_ready'] = True
            logger.info("✔ [Health Check] YOLO Model Loaded successfully into memory.")
    except Exception as e:
        logger.error(f"❌ [Health Check] YOLO Model loading failed: {e}")

    all_critical_passed = (
        health_status['config_loaded'] and
        health_status['uploads_ready'] and
        health_status['outputs_ready'] and
        health_status['reports_ready'] and
        health_status['opencv_ready'] and
        health_status['model_file_exists'] and
        health_status['model_loaded']
    )

    if all_critical_passed:
        logger.info("🚀 [Health Check] All System Checks PASSED. System is ready for requests.")
    else:
        logger.warning("⚠ [Health Check] Startup completed with non-fatal warnings or errors.")

    return health_status
