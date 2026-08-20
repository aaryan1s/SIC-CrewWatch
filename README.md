# CrewWatch

CrewWatch is a computer vision application that detects Personal Protective Equipment (PPE) compliance in industrial and construction environments. Powered by custom-trained YOLOv8, it analyzes images, video files, and live camera feeds to identify safety violations. The system provides automated compliance scoring, safety analytics, and downloadable PDF inspection reports.

## About

This project was developed as a capstone project for the Samsung Innovation Campus (SIC) AI & Machine Learning Course. Industrial sites often face challenges in manually monitoring whether workers are wearing required safety gear such as helmets, vests, gloves, and boots. CrewWatch automates safety compliance checking using deep learning object detection to help improve workplace safety and simplify inspection logging.

## Features

- PPE detection from images
- Video analysis
- Live webcam/CCTV monitoring
- PPE compliance checking
- Safety analytics/dashboard
- PDF inspection reports

## Tech Stack

- Python 3.10+
- Flask & Werkzeug
- Ultralytics YOLOv8 & OpenCV
- NumPy & imageio-ffmpeg
- ReportLab
- HTML, CSS, JavaScript & Plotly.js

## Project Structure

```
CrewWatch/
├── app.py                  # Main Flask application entry point
├── detector.py             # YOLOv8 inference engine
├── compliance.py           # PPE compliance calculation logic
├── video_detector.py       # Video processing module
├── camera_detector.py      # Live camera streaming module
├── dashboard.py            # Dashboard charts generator
├── report.py               # PDF inspection report generator
├── config.py               # Application configuration and paths
├── requirements.txt        # Python dependencies
├── models/
│   └── best.pt             # Trained YOLOv8 model weights
├── static/                 # CSS, JavaScript, and image assets
├── templates/              # HTML templates
├── uploads/                # Directory for uploaded input files
├── outputs/                # Directory for annotated output files
└── reports/                # Directory for generated PDF reports
```

## Setup

### Prerequisites

- Python 3.10 or higher
- Git (optional)

### Installation

1. Clone or download the repository:
```bash
git clone https://github.com/your-username/CrewWatch.git
cd CrewWatch
```

2. Create and activate a virtual environment:

Windows:
```cmd
python -m venv venv
venv\Scripts\activate
```

macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the Flask application:
```bash
python app.py
```

5. Open your web browser and navigate to `http://localhost:5001`.

## Model

The project uses a trained YOLOv8 PPE detection model stored in `models/best.pt`. The model identifies workers and detects safety equipment to calculate overall site and worker compliance scores.

## Demo / Presentation

[YouTube Video Link]

https://youtu.be/jHLDcshnuwg?si=5-qn32G-KhEJh7Hd 

## Academic Context

Developed as a capstone project for the Samsung Innovation Campus (SIC) AI & Machine Learning Course.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
