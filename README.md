<div align="center">

# 🤟 ISL Recognition System

### Real-time Indian Sign Language Recognition powered by Deep Learning

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15-FF6F00?style=flat-square&logo=tensorflow&logoColor=white)](https://tensorflow.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10-0097A7?style=flat-square&logo=google&logoColor=white)](https://mediapipe.dev)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

A full-stack, production-grade system for recognizing **296 Indian Sign Language words** in real-time via webcam. Built with a BiLSTM + Attention neural network trained on the INCLUDE dataset, achieving **92.2% validation accuracy**. Features a live landmark overlay, sentence building, and an interactive **"Teach"** mode so users can train the AI on new signs — no retraining required.

</div>

---

## ✨ Features

| Feature | Description |
|---|---|
| **Real-time Recognition** | Live webcam stream processed at ~10fps via WebSocket |
| **296 ISL Words** | Trained on the INCLUDE dataset covering everyday vocabulary |
| **BiLSTM + Attention** | Temporal sequence model with self-attention over 45-frame windows |
| **Landmark Overlay** | Cyan left-hand / violet right-hand skeleton drawn live on video |
| **Teach Mode** | Record 4 samples of any new sign — AI learns it instantly, no retraining |
| **Sentence Builder** | Accumulates recognized words into full sentences |
| **Hindi Labels** | Every recognized sign shown in both English and Hindi |
| **Multi-mode** | Word mode (BiLSTM), Alphabet mode (static CNN), Sentence mode |
| **Glassmorphism UI** | Dark futuristic interface with animated gradients and spring animations |
| **REST + WebSocket API** | Full FastAPI backend with Swagger docs at `/api/docs` |
| **Async Job Queue** | Long video uploads processed via Celery + Redis |
| **Docker Support** | One-command spin-up with `docker compose up` |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Browser (React 18)                      │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │  Camera  │  │ Output   │  │Confidence│  │   Teach   │  │
│  │  Panel   │  │  Panel   │  │  Meter   │  │   Page    │  │
│  └────┬─────┘  └──────────┘  └──────────┘  └─────┬─────┘  │
│       │  JPEG frames (binary WebSocket)            │        │
└───────┼────────────────────────────────────────────┼────────┘
        │ ws://localhost:8000/ws/recognize/live       │ ws://.../ws/teach
┌───────▼────────────────────────────────────────────▼────────┐
│                    FastAPI Backend (Python)                   │
│                                                              │
│  ┌──────────────────┐   ┌──────────────────────────────────┐│
│  │  live_recognition│   │        teach_ws.py               ││
│  │  _endpoint       │   │  config → ready → begin_sample   ││
│  │  SlidingWindow   │   │  → recording → sample_captured   ││
│  │  Buffer(45,22)   │   │  → teaching_complete             ││
│  └────────┬─────────┘   └──────────────┬───────────────────┘│
│           └──────────────┬─────────────┘                     │
│  ┌────────────────────────▼────────────────────────────────┐ │
│  │                   ISLRecognizer                         │ │
│  │  1. FeatureExtractor  (MediaPipe Holistic → 258-dim)   │ │
│  │  2. CustomSignStore   (cosine sim, threshold = 0.88)   │ │
│  │  3. BiLSTM+Attention  (TF SavedModel, 296 classes)     │ │
│  │  4. Temperature Scale (T=3.0, calibrated confidence)   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  REST: /api/recognize  /api/vocab  /api/teach/signs         │
│  Celery Worker ← Redis ← video upload async processing      │
└──────────────────────────────────────────────────────────────┘
```

---

## 🧠 Model Details

### Dynamic Sign Classifier — BiLSTM + Attention

| Property | Value |
|---|---|
| **Architecture** | BiLSTM (256 × 2 layers) + Attention + Dense head |
| **Input** | 45 frames × 258 features |
| **Output** | 296 ISL word classes (softmax) |
| **Dataset** | INCLUDE (Indian Sign Language, IIT Madras) |
| **Val Accuracy** | **92.2%** |
| **Test Accuracy** | **89.9%** |
| **Loss** | `CategoricalCrossentropy(label_smoothing=0.1)` |
| **Optimizer** | Adam + Cosine Decay with 10-epoch warmup |
| **Training Time** | ~25 min on RTX 4060 Laptop GPU (WSL2 + TF 2.15) |
| **Calibration** | Temperature scaling T=3.0 at inference |

#### Architecture (code summary)

```python
Input(shape=(45, 258))
  → LayerNormalization()
  → Bidirectional(LSTM(256, return_sequences=True, dropout=0.3))
  → Bidirectional(LSTM(256, return_sequences=True, dropout=0.3))
  → Attention(256)            # weighted sum over time steps
  → Dense(512, activation='relu') + Dropout(0.4)
  → Dense(256, activation='relu') + Dropout(0.3)
  → Dense(296, activation='softmax')
```

### Feature Extraction — MediaPipe Holistic

Each video frame produces a 258-dimensional feature vector:

| Source | Landmarks | Dimensions | Description |
|---|---|---|---|
| Left hand | 21 | 63 | Wrist + 5 fingers × 4 joints (x, y, z) |
| Right hand | 21 | 63 | Wrist + 5 fingers × 4 joints (x, y, z) |
| Pose | 33 | 132 | Full body skeleton (x, y, z, visibility) |
| **Total** | **75** | **258** | Concatenated per frame |

Missing hands are **zero-padded** (not skipped) to preserve temporal alignment.

### Data Augmentation

Four augmentations are applied on-the-fly during training:

| Augmentation | Probability | Effect |
|---|---|---|
| Gaussian noise | 50% | `σ=0.008` additive noise on all features |
| Feature dropout | 40% | Random landmark coordinates zeroed (4% rate) |
| Time masking | 30% | Consecutive 3–8 frame segment zeroed |
| Temporal scaling | 20% | Resample sequence at 0.8–1.2× speed |

### Inference Pipeline

```
JPEG Frame
    ↓  OpenCV decode
MediaPipe Holistic
    ↓  258-dim vector per frame
Sliding Window Buffer (45 frames, 22 overlap)
    ↓  fires every 22 frames
Motion Gate: std(hand_features) ≥ 0.04  →  skip if below threshold
    ↓
CustomSignStore.match()  →  cosine similarity ≥ 0.88  →  return custom sign
    ↓  (if no match)
BiLSTM forward pass (TF SavedModel)
    ↓
Temperature Scaling (T=3.0)
    ↓
Top-1 + 2 alternatives → WebSocket JSON response
```

---

## 🎓 Teach Mode — Zero-Shot Custom Signs

Users can teach the AI **any new sign** — no model retraining needed:

1. Navigate to the **Teach** page and enter the word (English + optional Hindi)
2. Record the sign **4 times** (each recording is ~4.5 seconds / 45 frames)
3. Backend computes the **mean feature template** across all 4 recordings
4. Template stored in `backend/custom_signs/signs.json`
5. At inference time, **cosine similarity** is computed between the incoming 45×258 sequence and every stored template
6. If similarity ≥ **0.88**, the custom sign takes priority over the BiLSTM model

```
similarity = dot(seq_flat, template_flat) / (‖seq_flat‖ × ‖template_flat‖)
```

Custom signs persist across server restarts and are reflected **immediately** on the Home recognition page.

---

## 📁 Project Structure

```
isl-recognition/
├── backend/                         # FastAPI application
│   ├── app/
│   │   ├── main.py                  # App entrypoint, lifespan, routers
│   │   ├── config.py                # Pydantic settings (loaded from .env)
│   │   ├── api/
│   │   │   ├── health.py            # GET /api/health
│   │   │   ├── recognize.py         # POST /api/recognize (image upload)
│   │   │   ├── vocab.py             # GET /api/vocab
│   │   │   └── jobs.py              # Async job status
│   │   ├── routers/
│   │   │   └── teach.py             # GET/DELETE /api/teach/signs
│   │   ├── services/
│   │   │   ├── recognizer.py        # ISLRecognizer singleton + inference logic
│   │   │   ├── feature_extractor.py # MediaPipe Holistic wrapper
│   │   │   ├── custom_sign_store.py # Cosine-sim custom sign store (JSON-backed)
│   │   │   └── translator.py        # English → Hindi label translation
│   │   ├── ws/
│   │   │   ├── live_recognition.py  # /ws/recognize/live WebSocket handler
│   │   │   └── teach_ws.py          # /ws/teach WebSocket (teaching protocol)
│   │   └── workers/
│   │       ├── celery_app.py        # Celery configuration
│   │       └── tasks.py             # Async video processing tasks
│   ├── custom_signs/
│   │   └── signs.json               # Persisted user-taught signs
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                        # React 18 + Vite SPA
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx             # Live recognition (main page)
│   │   │   ├── Teach.jsx            # Interactive teaching page
│   │   │   ├── Vocab.jsx            # Browse all 296 signs
│   │   │   ├── Upload.jsx           # Video file upload + async processing
│   │   │   ├── Learn.jsx            # Learning / practice mode
│   │   │   └── About.jsx            # Project information
│   │   ├── components/
│   │   │   ├── CameraPanel.jsx      # Webcam feed with detecting badge
│   │   │   ├── LandmarkOverlay.jsx  # Canvas skeleton (cyan/violet hands)
│   │   │   ├── OutputPanel.jsx      # Animated sign prediction display
│   │   │   ├── ConfidenceMeter.jsx  # Gradient confidence bar
│   │   │   ├── ModeSelector.jsx     # Word / Alphabet / Sentence tabs
│   │   │   ├── RecognitionHistory.jsx # Color-coded sign history chips
│   │   │   ├── Navbar.jsx           # Frosted-glass navigation bar
│   │   │   └── SentenceBuilder.jsx  # Accumulated sentence display
│   │   ├── hooks/
│   │   │   ├── useWebSocket.js      # Live recognition WebSocket hook
│   │   │   ├── useTeachSession.js   # Teaching session state machine
│   │   │   └── useCamera.js         # getUserMedia + captureFrame helpers
│   │   ├── store/
│   │   │   └── recognitionStore.js  # Zustand global state
│   │   └── index.css                # Glassmorphism design system
│   ├── package.json
│   └── vite.config.js
│
├── ml/                              # Machine learning pipeline
│   ├── data/
│   │   ├── preprocess_dynamic.py    # Extract features from INCLUDE dataset
│   │   ├── preprocess_static.py     # Static alphabet preprocessing
│   │   └── preprocess_sentence.py  # Sentence-level preprocessing
│   ├── training/
│   │   ├── train_dynamic.py         # BiLSTM training script (GPU-ready)
│   │   ├── train_static.py          # Static CNN training
│   │   ├── train_sentence.py        # Sentence model training
│   │   └── evaluate.py              # Evaluation + confusion matrix
│   ├── models/                      # Trained SavedModel files (not in repo)
│   │   ├── dynamic_classifier/
│   │   └── sentence_model/
│   └── notebooks/                   # Jupyter exploration notebooks
│
├── nginx/
│   └── nginx.conf                   # Reverse proxy config
├── docker-compose.yml
├── docker-compose.dev.yml
└── .env.example
```

---

## 🚀 Quick Start

### Prerequisites

- Python **3.11+**
- Node.js **18+** and [pnpm](https://pnpm.io)
- **Redis** (Docker or WSL2: `sudo service redis-server start`)
- *(GPU training only)* CUDA 12.3+ driver, WSL2

### Option A — Docker Compose (Recommended)

```bash
git clone https://github.com/YOUR_USERNAME/isl-recognition.git
cd isl-recognition

cp .env.example .env

docker compose up --build
```

Open **http://localhost:5173**.

> **Note:** Trained model files are not included due to size. See [Downloading / Training Models](#-downloading--training-models).

---

### Option B — Local Development (4 terminals)

#### Terminal 1 — Redis

```bash
# Docker:
docker run -d -p 6379:6379 redis:7-alpine

# OR WSL2:
sudo service redis-server start
```

#### Terminal 2 — Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp ../.env.example ../.env    # configure model paths

uvicorn app.main:app --reload --port 8000
```

#### Terminal 3 — Celery Worker

```bash
# Same venv as backend
cd backend
source venv/bin/activate

# Windows (prefork unsupported):
celery -A app.workers.celery_app worker --loglevel=info --pool=solo

# Linux / macOS:
celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
```

#### Terminal 4 — Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Open **http://localhost:5173**.

---

## 📥 Downloading / Training Models

Trained model weights are not included in this repository. Train them from scratch:

### 1. Download the INCLUDE Dataset

```bash
# Requires a Kaggle API key (~/.kaggle/kaggle.json)
cd ml/data
python download_datasets.py
```

Or download manually from [Kaggle — INCLUDE Dataset](https://www.kaggle.com/datasets/sridharstreaks/include-dataset-for-indian-sign-language).

### 2. Preprocess

```bash
cd ml/data
python preprocess_dynamic.py
# → writes ml/data/processed/dynamic_X_train.npy etc.
```

### 3. Train (GPU recommended)

**On Linux / WSL2 with GPU:**
```bash
# WSL2 setup (Windows users — TF drops GPU support after 2.10 on native Windows)
sudo apt install python3.11 python3.11-venv
python3.11 -m venv ~/tf-gpu-env
source ~/tf-gpu-env/bin/activate
pip install tensorflow==2.15.1 "numpy<2.0.0" mediapipe scikit-learn matplotlib

# Verify GPU
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"

cd /mnt/k/AI\ project/isl-recognition/ml/training
python train_dynamic.py
```

**On CPU (slower):**
```bash
cd ml/training
python train_dynamic.py
```

Training output: `ml/models/dynamic_classifier/saved_model.pb` + `label_map.json`

Expected directory after training:
```
ml/models/
├── dynamic_classifier/
│   ├── saved_model.pb
│   ├── variables/
│   │   ├── variables.data-00000-of-00001
│   │   └── variables.index
│   └── label_map.json
└── sentence_model/
    ├── saved_model.pb
    ├── variables/
    └── vocab.json
```

---

## 🎯 API Reference

### WebSocket — Live Recognition

**Endpoint:** `ws://localhost:8000/ws/recognize/live`

```jsonc
// 1. Client sends mode config
{"mode": "word"}

// 2. Server acknowledges
{"type": "config_ack", "mode": "word"}

// 3. Client streams raw JPEG bytes (binary messages, ~10fps)

// 4. Server sends landmark data for skeleton overlay
{"type": "landmark", "data": {"left_hand": [...], "right_hand": [...], "pose": [...]}}

// 5. Server sends prediction
{
  "type": "prediction",
  "label": "HELLO",
  "label_hindi": "नमस्ते",
  "confidence": 0.87,
  "mode": "word",
  "model_used": "dynamic_lstm",
  "landmarks_detected": true,
  "alternatives": [
    {"label": "WAVE", "confidence": 0.06},
    {"label": "HI",   "confidence": 0.03}
  ]
}
```

### WebSocket — Teaching Session

**Endpoint:** `ws://localhost:8000/ws/teach`

```jsonc
// Protocol phases: config → teach_ready → [begin_sample → recording → sample_captured] × N → teaching_complete

// Client: configure
{"type": "config", "label": "NAMASTE", "label_hindi": "नमस्ते", "total_samples": 4}

// Server: ready
{"type": "teach_ready", "total_samples": 4}

// Client: start a sample
{"type": "begin_sample"}

// Server: recording started
{"type": "recording", "sample": 1, "total": 4}

// Client: stream 45 JPEG frames as binary messages (10fps × 4.5s)

// Server: streams landmarks during recording
{"type": "landmark", "data": {...}}

// Server: sample done
{"type": "sample_captured", "sample": 1, "landmark_frames": 38}

// ... repeat begin_sample → sample_captured for each sample ...

// Server: all done — sign is saved
{"type": "teaching_complete", "label": "NAMASTE", "label_hindi": "नमस्ते", "samples_recorded": 4}
```

### REST API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health + model load status |
| `POST` | `/api/recognize` | Single-frame sign recognition (multipart image) |
| `GET` | `/api/vocab` | List all 296 recognizable signs |
| `GET` | `/api/teach/signs` | List user-taught custom signs |
| `DELETE` | `/api/teach/signs/{label}` | Delete a custom sign |
| `POST` | `/api/jobs/upload` | Submit video for async processing |
| `GET` | `/api/jobs/{job_id}` | Poll async job status |

Full interactive docs: **http://localhost:8000/api/docs**

---

## 🖥️ Tech Stack

### Backend
| Technology | Version | Role |
|---|---|---|
| **FastAPI** | 0.115 | Async REST API + WebSocket server |
| **TensorFlow** | 2.15.1 | Model inference (SavedModel format) |
| **MediaPipe** | 0.10.9 | Real-time pose + hand landmark extraction |
| **Celery** | 5.4 | Async task queue for video processing |
| **Redis** | 7 | Celery broker + result backend |
| **SQLAlchemy** | 2.0 | Async ORM (SQLite dev, PostgreSQL-ready) |
| **Uvicorn** | 0.32 | ASGI server |
| **OpenCV** | 4.10 | Frame decoding |
| **Loguru** | 0.7 | Structured logging |
| **SlowAPI** | 0.1 | Rate limiting |

### Frontend
| Technology | Version | Role |
|---|---|---|
| **React** | 18.3 | UI framework |
| **Vite** | 5 | Build tool + HMR dev server |
| **TailwindCSS** | 3.4 | Utility-first styling |
| **Framer Motion** | 11 | Spring animations |
| **Zustand** | 5 | Global state (landmarks, predictions) |
| **TanStack Query** | 5 | Server state + query caching |
| **Lucide React** | 0.468 | Icon library |
| **Recharts** | 2.14 | Confidence visualization |
| **React Router** | 6.28 | Client-side routing |

### ML / Training
| Technology | Role |
|---|---|
| **TensorFlow 2.15 + CUDA** | GPU-accelerated training (WSL2) |
| **NumPy / Pandas** | Data loading and preprocessing |
| **scikit-learn** | Evaluation metrics, class weights |
| **Matplotlib / Seaborn** | Training curves, confusion matrix |
| **Kaggle API** | INCLUDE dataset download |

---

## 🔧 Environment Variables

Copy `.env.example` to `.env`:

```env
# App
APP_NAME=ISL Recognition System
APP_VERSION=1.0.0
DEBUG=true
SECRET_KEY=change-this-in-production

# Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Database (SQLite for dev, swap to postgres:// for prod)
DATABASE_URL=sqlite+aiosqlite:///./isl_dev.db

# Redis / Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Model paths (relative to backend/)
MODELS_DIR=../ml/models
DYNAMIC_MODEL_PATH=../ml/models/dynamic_classifier
SENTENCE_MODEL_PATH=../ml/models/sentence_model

# MediaPipe thresholds
MEDIAPIPE_MIN_DETECTION_CONFIDENCE=0.7
MEDIAPIPE_MIN_TRACKING_CONFIDENCE=0.5

# Frontend (Vite injects these at build time)
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

---

## 🔬 Deep Dive

### Sliding Window Inference

The `SlidingWindowBuffer` maintains a rolling deque of 45 feature vectors. Inference fires every **22 new frames** (50% overlap), providing near-continuous predictions without redundant computation:

```
frames: 0──────────44
                 22──────────66
                          44──────────88  ...
```

### Motion Gate

Before every BiLSTM call, a gate rejects frames with insufficient hand motion to prevent false positives when hands are still:

```python
hand_seq = feature_seq[:, :126]            # left + right hand only
active   = hand_seq[np.any(hand_seq != 0, axis=1)]
if len(active) < 5 or np.std(active) < 0.04:
    return "—"   # no prediction
```

### Custom Sign Priority

User-taught signs are checked **before** the neural network using cosine similarity on the full 11,610-dimensional vector (45 × 258 = 11,610):

```python
sim = dot(seq.flatten(), template.flatten()) / (‖seq‖ × ‖template‖)
# → custom sign returned if sim ≥ 0.88
```

This gives O(K) lookup where K = number of custom signs — effectively zero latency.

### Landmark Rendering

Skeleton is drawn on a transparent `<canvas>` overlay in the browser:

```javascript
// Left hand — cyan glow
ctx.strokeStyle = '#00d4ff'
ctx.shadowColor = '#00d4ff'
ctx.shadowBlur   = 14

// Right hand — violet glow
ctx.strokeStyle = '#a78bfa'

// Fingertips (indices 4,8,12,16,20) — larger dots
ctx.arc(x, y, 5, 0, 2 * Math.PI)
```

---

## 📊 Results

| Metric | Value |
|---|---|
| Validation accuracy (best checkpoint) | **92.2%** |
| Test accuracy | **89.9%** |
| Number of classes | 296 ISL words |
| BiLSTM inference latency | ~15ms (RTX 4060) |
| MediaPipe landmark extraction | ~30ms per frame (CPU) |
| End-to-end recognition latency | ~120ms (capture → UI update) |

---

## 🐛 Known Issues & Workarounds

| Issue | Cause | Fix |
|---|---|---|
| Celery `PermissionError` on Windows | Prefork uses Windows shared memory | `celery ... worker --pool=solo` |
| TF GPU not detected on native Windows | TF drops Windows GPU after 2.10 | Train in WSL2 with TF 2.15 |
| Redis Docker `name already in use` | Old container not removed | `docker rm redis-isl` then re-run |
| `numpy` 2.x conflict with TF 2.15 | mediapipe pulls numpy 2.x | `pip install "numpy<2.0.0"` |
| Static model (A-Z alphabet) missing | Not trained by default | Run `ml/training/train_static.py` |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

### Running Tests

```bash
# Backend unit tests
cd backend
pytest tests/ -v

# Frontend lint
cd frontend
pnpm lint
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- **INCLUDE Dataset** — Indian Sign Language benchmark by IIT Madras ([Kaggle](https://www.kaggle.com/datasets/sridharstreaks/include-dataset-for-indian-sign-language))
- **Google MediaPipe** — Real-time ML framework for hand and pose landmark extraction
- **TensorFlow / Keras** — Deep learning framework for training and inference
- **FastAPI** — Modern async Python web framework

---

<div align="center">

Built with ❤️ for accessibility and inclusive technology

</div>
