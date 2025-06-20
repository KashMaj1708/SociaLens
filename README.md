# SociaLens

A Full-Stack Platform to Clean, Analyze, and Export Multimodal Social Media Data

## 🚀 Features

- **Data Ingestion**: Upload JSON, CSV, or ZIP files with images/videos from social platforms
- **Data Cleaning**: Automated text cleaning, emoji removal, URL cleanup, language detection
- **Multimodal Processing**: NLP (sentiment analysis, NER) + Computer Vision (image tagging, captions)
- **Interactive Dashboard**: Filter, visualize, and explore your social media data
- **Export Capabilities**: Download cleaned data in CSV/JSON formats
- **Annotation Mode**: Manual tagging and sentiment editing

## 🛠 Tech Stack

### Frontend
- React (with Vite)
- Tailwind CSS
- Axios
- Recharts (for visualizations)

### Backend
- FastAPI (Python)
- Pydantic (schema validation)
- Celery + Redis (background processing)
- MongoDB (NoSQL database)
- GridFS (media file storage)

### AI/ML
- spaCy + HuggingFace Transformers (NLP)
- CLIP/BLIP (image-to-text)
- OpenCV (image preprocessing)
- langdetect (language detection)

## 📁 Project Structure

```
/socialens
├── /frontend         (React app)
├── /backend          (FastAPI app)
│   ├── /routes
│   ├── /services     (NLP, CV, cleaning modules)
│   ├── /workers      (Celery tasks)
│   ├── /schemas
│   └── main.py
├── /scripts          (sample data loaders, converters)
├── /models           (pretrained models or wrappers)
└── docker-compose.yml
```

## 🚀 Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed

### Production Setup
```bash
# Clone the repository
git clone <repository-url>
cd SociaLens

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Documentation: http://localhost:8000/docs
```

### Development Setup
```bash
# Start development environment with hot reloading
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- MongoDB
- Redis

### Installation

1. **Clone and setup backend:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Setup frontend:**
```bash
cd frontend
npm install
```

3. **Start services:**
```bash
# Start MongoDB and Redis
docker-compose up -d

# Start backend
cd backend
uvicorn main:app --reload

# Start frontend
cd frontend
npm run dev
```

4. **Access the application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📊 Sample Data

The platform includes sample datasets for testing:
- 10 tweets with images
- 5 Instagram posts with multiple images
- 3 YouTube-style metadata records

## 🔧 Configuration

Environment variables are configured in `.env` files for both frontend and backend.

## 📝 License

MIT License