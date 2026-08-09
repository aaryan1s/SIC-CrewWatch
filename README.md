# CrewWatch | AI-Powered Workforce Safety Monitoring

> 🎓 **Capstone Project**: Developed as a capstone project for the **Samsung Innovation Campus — AI & Machine Learning Course**.

CrewWatch is an enterprise-grade, computer-vision safety monitoring platform engineered for industrial and construction environments. Utilizing custom-trained YOLOv8 object detection, CrewWatch provides real-time Personal Protective Equipment (PPE) compliance evaluation across static image audits, video telemetry, live webcams, and network RTSP/IP CCTV camera feeds.

---

## 🌟 Key Features

- **Static Image Inspection**: Detect workers and evaluate individual PPE compliance (Helmets/Hardhats, High-Vis Vests, Gloves, Steel-Toe Boots).
- **Video Telemetry Analysis**: Frame-by-frame video processing with browser-compatible H.264 MP4 export and aggregated safety scoring.
- **Live Stream Monitoring**: Real-time MJPEG streaming supporting local USB webcams, wireless cameras, and network RTSP CCTV endpoints.
- **Automated PDF Inspection Reports**: On-demand generation of audit reports featuring site scorecards, violation breakdown tables, evidence snapshots, and OSHA safety recommendations.
- **Safety Analytics Dashboard**: Dynamic Plotly.js charts displaying site compliance rates and worker compliance ratios.
- **Cross-Platform Compatibility**: Fully compatible with macOS, Windows, and Linux using unified `pathlib.Path` resolution.
- **Production-Ready Core**: Built with pathlib path management, structured logging, automatic directory creation, and strict input security.

---

## 🛠️ Technology Stack

- **Backend Framework**: Python 3.10+, Flask, Werkzeug
- **AI & Computer Vision**: Ultralytics YOLOv8 (`models/best.pt`), OpenCV (`opencv-python`), NumPy
- **Video Processing**: `imageio-ffmpeg` (H.264/AAC browser conversion)
- **PDF Generation**: ReportLab
- **Analytics & Visualization**: Plotly.js, HTML5, CSS3, JavaScript (ES6)

---

## 📁 Folder Structure

```
SIC Capstone Project/
├── app.py                  # Main Flask Application & REST API Endpoints
├── config.py               # Centralized Path & Environment Configuration
├── logger.py               # Structured Logging Setup (logs/crewwatch.log)
├── health_check.py         # Automatic System Startup Validation & Health Check
├── detector.py             # YOLOv8 Model Loader & Inference Engine
├── compliance.py           # Worker Spatial Association & PPE Compliance Math
├── video_detector.py      # Video Telemetry Processing & H.264 Transcoding
├── camera_detector.py     # Live Webcam & RTSP Streaming Engine
├── dashboard.py            # Plotly Chart Generators for Dashboard
├── report.py               # ReportLab PDF Report Generator
├── alerts.py              # Safety Violation Alert Generator
├── utils.py                # File Utilities, Bounding Boxes, & Overlay Renderer
├── requirements.txt        # Pinned Python Dependencies
├── VERSION                 # Version & Platform Metadata
├── models/
│   └── best.pt             # Trained YOLOv8 PPE Model Weights
├── static/
│   ├── css/style.css       # Platform Styling
│   ├── js/main.js          # Interactive Frontend Controller
│   └── img/                # UI Graphical Assets
├── templates/
│   ├── index.html          # Inspection Studio View
│   └── dashboard.html      # Safety Dashboard View
├── uploads/                # Storage for Uploaded Media
├── outputs/                # Storage for Annotated Outputs & Captured Snapshots
├── reports/                # Storage for Generated PDF Audit Reports
├── temp/                   # Temporary File Buffer
└── logs/                   # System Logs Directory (crewwatch.log)
```

---

## 💻 Cross-Platform Setup & Installation Guide

CrewWatch is fully cross-platform and runs natively on **Windows**, **macOS**, and **Linux** using strict `pathlib.Path` resolutions.

---

### 1. Prerequisites

- **Python 3.10, 3.11, or 3.12** installed on your system.
  - [Download Python](https://www.python.org/downloads/) (Make sure to check *"Add Python to PATH"* during Windows installation).
- **Git** (optional, for cloning the repository).
- **pip** (Python package installer, included with standard Python distributions).

---

### 2. Clone or Download the Project

```bash
# Clone the repository
git clone https://github.com/your-username/CrewWatch.git

# Navigate into the project directory
cd CrewWatch
```
*(If downloaded as a ZIP, extract the archive and open your terminal / command prompt inside the extracted folder).*

---

### 3. Create & Activate a Virtual Environment

It is recommended to use a virtual environment to manage dependencies cleanly.

#### 🪟 Windows

**Option A: Command Prompt (cmd.exe)**
```cmd
# 1. Create the virtual environment
python -m venv venv

# 2. Activate the virtual environment
venv\Scripts\activate.bat
```

**Option B: PowerShell**
```powershell
# 1. Create the virtual environment
python -m venv venv

# 2. If script execution is disabled, enable it for this session:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 3. Activate the virtual environment
.\venv\Scripts\Activate.ps1
```

#### 🍎 macOS

```bash
# 1. Ensure command line tools are installed (if first time using Python on Mac)
# xcode-select --install

# 2. Create the virtual environment
python3 -m venv venv

# 3. Activate the virtual environment
source venv/bin/activate
```

#### 🐧 Linux (Ubuntu / Debian / Fedora / Arch)

```bash
# 1. Install system prerequisites (required for OpenCV & venv on Debian/Ubuntu)
sudo apt update
sudo apt install -y python3-venv python3-pip libgl1 libglib2.0-0

# For Fedora / RHEL:
# sudo dnf install -y python3-pip mesa-libGL glib2

# For Arch Linux:
# sudo pacman -S python-pip libglvnd

# 2. Create the virtual environment
python3 -m venv venv

# 3. Activate the virtual environment
source venv/bin/activate
```

---

### 4. Install Dependencies

Once your virtual environment is active (indicated by `(venv)` in your terminal prompt):

```bash
# Upgrade pip to latest version
pip install --upgrade pip

# Install all required dependencies
pip install -r requirements.txt
```

> **Optional: NVIDIA GPU Acceleration (Windows / Linux with CUDA)**
> If you have a compatible NVIDIA GPU and want maximum real-time FPS with CUDA acceleration:
> ```bash
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
> ```

---

### 5. Launch the Application

```bash
# On Windows / macOS / Linux:
python app.py
# (or 'python3 app.py' if 'python' points to Python 2 on some Linux distros)
```

1. Upon startup, CrewWatch executes an automated **System Health Check** to verify directories, OpenCV bindings, and the YOLOv8 model weights.
2. Open your web browser and navigate to:
   👉 **`http://localhost:5001`** (or the port displayed in the terminal)

---

### 6. Troubleshooting & OS-Specific Notes

| Operating System | Common Issue | Solution |
| :--- | :--- | :--- |
| **Windows** | `Activate.ps1 cannot be loaded because running scripts is disabled` | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in PowerShell before activating `venv`. |
| **Linux (Ubuntu/Debian)** | `ImportError: libGL.so.1: cannot open shared object file` | Run `sudo apt install -y libgl1 libglib2.0-0` to install missing OpenCV system dependencies. |
| **macOS** | `Camera access denied in live webcam mode` | Go to **System Settings > Privacy & Security > Camera** and ensure your terminal / IDE has camera permissions enabled. |
| **All Platforms** | `Port 5001 already in use` | CrewWatch will automatically locate the next available port (e.g., `5002`), or you can specify `PORT=5002` in `config.py`. |

---

## 🛡️ Security & Path Management

- **Path Security**: All file paths are constructed using `pathlib.Path`. Hardcoded slashes and working-directory dependencies are removed.
- **Filename Sanitization**: Uploaded files are sanitized via `werkzeug.utils.secure_filename` and stripped of leading paths (`Path(filename).name`) to prevent directory traversal attacks.
- **Error Shielding**: Production error handlers capture detailed stack traces in `logs/crewwatch.log` while presenting friendly JSON error messages to users.

---

## 🩺 System Health Check & Logging

On every application startup, CrewWatch executes `run_system_health_check()` which automatically validates:
1. Configuration loading
2. Directory existence (`uploads/`, `outputs/`, `reports/`, `models/`, `temp/`, `logs/`)
3. OpenCV library readiness
4. Model file presence (`models/best.pt`) and memory loading

Logs are saved to `logs/crewwatch.log` and printed to console stdout.

---

## 📜 Version

Refer to the `VERSION` file for build metadata, release notes, and supported platforms.

---

## 🎓 Academic Attribution & Acknowledgments

This project was conceived and built as the final Capstone Project for the **Samsung Innovation Campus (SIC) — AI & Machine Learning Course**. Special thanks to the mentors, instructors, and coordinators for their guidance on deep learning, computer vision architectures, and practical AI deployment.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.