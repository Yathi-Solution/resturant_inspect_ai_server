# 🍽️ Restaurant Inspector

AI-powered restaurant review analyzer that scores reviews across 5 key aspects: Food, Service, Hygiene, Parking, and Cleanliness.

## 🚀 Features

- **Multi-Aspect Analysis**: Scores 5 different aspects from a single review
- **Fast**: CPU-optimized DistilBERT model (67MB)
- **Production-Ready**: FastAPI with proper validation and error handling
- **Easy Deployment**: One-click deploy to Render

## 🧠 Technology Stack

- **Model**: DistilBERT (fine-tuned on Yelp reviews)
- **Framework**: FastAPI + Uvicorn
- **ML Libraries**: Transformers, PyTorch, Datasets
- **Python**: 3.11+

## 📦 Installation

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd resturant-inspector-server
```

### 2. Create Virtual Environment

```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
# OR
source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -e .
```

### 4. Install Dev Tools (Optional)

```bash
pip install -e ".[dev]"  # Includes ruff for formatting/linting
```

## 🎯 Training the Model

Train the model on Yelp restaurant reviews (~45 minutes):

```bash
python train.py
```

This will:
1. Download 1,500 Yelp reviews
2. Create aspect labels using keyword rules
3. Fine-tune DistilBERT (2 epochs)
4. Save model to `./model/`

## 🏃 Running Locally

### Start the API Server

```bash
uvicorn main:app --reload
```

Server runs at: http://localhost:8000

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing the API

### Using curl

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "Amazing biryani but terrible parking and dirty bathrooms"}'
```

### Expected Response

```json
{
  "review": "Amazing biryani but terrible parking and dirty bathrooms",
  "scores": {
    "FOOD": 0.892,
    "SERVICE": 0.654,
    "HYGIENE": 0.234,
    "PARKING": 0.189,
    "CLEANLINESS": 0.276
  },
  "timestamp": "2026-03-23T14:30:00.000Z"
}
```

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/analyze` | POST | Analyze review |
| `/docs` | GET | Swagger UI |

## 🚀 Deploying to Render

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 2. Create Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:

**Settings:**
- **Name**: `restaurant-inspector`
- **Environment**: `Python 3`
- **Build Command**: 
  ```bash
  pip install -e . && python train.py
  ```
- **Start Command**:
  ```bash
  uvicorn main:app --host 0.0.0.0 --port $PORT
  ```
- **Instance Type**: Free (512MB RAM)

5. Click **"Create Web Service"**
6. Wait ~45 minutes for initial build (includes training)

### 3. Test Deployed API

```bash
curl -X POST "https://your-app.onrender.com/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "Great food but slow service"}'
```

## 🛠️ Development

### Format Code

```bash
ruff format .
```

### Lint Code

```bash
ruff check .
```

### Fix Linting Issues

```bash
ruff check --fix .
```

## 📊 Model Details

- **Base Model**: distilbert-base-uncased
- **Training Data**: Yelp Polarity Reviews (1,500 samples)
- **Labeling**: Rule-based keyword extraction
- **Aspects**: 5 (Food, Service, Hygiene, Parking, Cleanliness)
- **Training Time**: ~45 minutes (CPU)
- **Model Size**: 67MB

## 🎭 Aspect Scoring

The model analyzes text for keywords and patterns:

- **FOOD**: delicious, tasty, bland, terrible
- **SERVICE**: friendly, rude, attentive, slow
- **HYGIENE**: dirty, clean, filthy, spotless
- **PARKING**: parking, no space
- **CLEANLINESS**: clean, messy, well-maintained

## 📝 Project Structure

```
resturant-inspector-server/
├── pyproject.toml          # Dependencies
├── train.py                # Training script
├── main.py                 # FastAPI application
├── README.md               # This file
├── .gitignore             # Git ignore rules
├── venv/                  # Virtual environment (not committed)
└── model/                 # Trained model (generated, not committed)
    ├── config.json
    ├── model.safetensors
    └── tokenizer files
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run linting: `ruff check --fix .`
5. Format code: `ruff format .`
6. Submit a pull request

## 📄 License

MIT License

## 🙏 Acknowledgments

- Hugging Face for Transformers library
- Yelp for the dataset
- FastAPI team for the framework

## 📞 Support

For issues or questions, please open a GitHub issue.

---

**Built with ❤️ using Python, FastAPI, and DistilBERT**
