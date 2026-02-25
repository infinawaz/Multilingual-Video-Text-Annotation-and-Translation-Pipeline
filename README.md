# 🎬 Multilingual Video Text Annotation & Translation Pipeline

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/infinawaz/Multilingual-Video-Text-Annotation-and-Translation-Pipeline)

An automated pipeline to **extract**, **annotate**, and **translate** textual regions from video frames using **Tesseract OCR** and **LibreTranslate**. Supports multilingual content detection across **English**, **Hindi**, **Bengali**, and **Tamil**.

---

## ✨ Features

- 🔍 **Frame-by-frame OCR** — Extract text from video frames using Tesseract
- 🌐 **Multilingual Detection** — Supports English, Hindi, Bengali & Tamil scripts
- 🔄 **Real-time Translation** — Translate detected text via LibreTranslate API
- 🎨 **Visual Annotations** — Bounding boxes with color-coded language labels
- 📊 **Confidence Scoring** — Filter results by OCR confidence levels
- 🖼️ **Image & Video Support** — Process both individual images and video files
- 📤 **JSON Export** — Download structured annotation results
- 🚀 **One-click Deploy** — Ready for Render deployment with Docker

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│                  Frontend UI                 │
│         (HTML / CSS / JavaScript)            │
└──────────────────┬──────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────┐
│              FastAPI Server                   │
│                 (app.py)                      │
├──────────────────────────────────────────────┤
│  ┌────────────┐ ┌──────────┐ ┌────────────┐ │
│  │ Preprocess │→│   OCR    │→│ Translate   │ │
│  │ (OpenCV)   │ │(Tesseract)│ │(LibreTrans.)│ │
│  └────────────┘ └──────────┘ └────────────┘ │
│                      │                       │
│              ┌───────▼───────┐               │
│              │   Overlay     │               │
│              │ (Annotations) │               │
│              └───────────────┘               │
└──────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Tesseract OCR installed on your system

### Local Setup

```bash
# Clone the repository
git clone https://github.com/infinawaz/Multilingual-Video-Text-Annotation-and-Translation-Pipeline.git
cd Multilingual-Video-Text-Annotation-and-Translation-Pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m uvicorn app:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### Docker

```bash
docker build -t video-text-pipeline .
docker run -p 8000:10000 video-text-pipeline
```

---

## ☁️ Deploy to Render

1. Push this repository to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **New → Blueprint** and connect this repo
4. Render will auto-detect `render.yaml` and deploy

**Or** use the Deploy button at the top of this README!

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LIBRETRANSLATE_URL` | `https://libretranslate.com` | LibreTranslate API URL |
| `LIBRETRANSLATE_API_KEY` | _(empty)_ | API key (if required) |
| `PORT` | `10000` | Server port |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Frontend UI |
| `GET` | `/api/health` | Health check |
| `POST` | `/api/process` | Process video/image file |
| `GET` | `/api/languages` | List supported languages |

### Process Endpoint

```bash
curl -X POST "http://localhost:8000/api/process?target_lang=en&max_frames=8" \
  -F "file=@video.mp4"
```

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, Uvicorn
- **OCR**: Tesseract (pytesseract)
- **Translation**: LibreTranslate API
- **Image Processing**: OpenCV, Pillow, NumPy
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Deployment**: Docker, Render

---

## 📂 Project Structure

```
├── app.py                  # FastAPI application
├── pipeline/
│   ├── __init__.py
│   ├── preprocess.py       # Image preprocessing (thresholding, denoising)
│   ├── ocr.py              # Tesseract OCR text detection
│   ├── translate.py        # LibreTranslate API integration
│   └── overlay.py          # Bounding box & text annotation overlay
├── static/
│   ├── index.html          # Frontend UI
│   ├── style.css           # Dark glassmorphism theme
│   └── app.js              # Frontend logic
├── Dockerfile              # Docker configuration
├── render.yaml             # Render Blueprint
├── requirements.txt        # Python dependencies
└── README.md
```

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ using FastAPI · Tesseract OCR · LibreTranslate · OpenCV
</p>
