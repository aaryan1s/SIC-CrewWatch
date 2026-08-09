import os
from pathlib import Path

# Base Directory of the Project
BASE_DIR = Path(__file__).parent.resolve()

# Core Application Storage Directories
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"
REPORTS_DIR = BASE_DIR / "reports"
MODELS_DIR = BASE_DIR / "models"
TEMP_DIR = BASE_DIR / "temp"
LOGS_DIR = BASE_DIR / "logs"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Model & Log File Paths
MODEL_PATH = MODELS_DIR / "best.pt"
LOG_FILE_PATH = LOGS_DIR / "crewwatch.log"

# Allowed File Extensions
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}

class Config:
    """Production & Local Environment Configuration Class."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'crewwatch-safety-secret-key-prod-2026')
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5001))
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024))  # 500 MB max upload
    
    # Allowed File Extensions
    ALLOWED_IMAGE_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS
    ALLOWED_VIDEO_EXTENSIONS = ALLOWED_VIDEO_EXTENSIONS
    
    # Directory Mapping
    BASE_DIR = BASE_DIR
    UPLOADS_DIR = UPLOADS_DIR
    OUTPUTS_DIR = OUTPUTS_DIR
    REPORTS_DIR = REPORTS_DIR
    MODELS_DIR = MODELS_DIR
    TEMP_DIR = TEMP_DIR
    LOGS_DIR = LOGS_DIR
    MODEL_PATH = MODEL_PATH

def ensure_directories():
    """Automatically ensures all required runtime directories exist."""
    required_dirs = [UPLOADS_DIR, OUTPUTS_DIR, REPORTS_DIR, MODELS_DIR, TEMP_DIR, LOGS_DIR]
    for directory in required_dirs:
        directory.mkdir(parents=True, exist_ok=True)

# Run ensure_directories on module import
ensure_directories()
