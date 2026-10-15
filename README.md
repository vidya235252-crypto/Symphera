# Symphera

**Your health, your language.**  
🌐 **Live demo:** https://symphera.onrender.com/

Symphera is a multilingual women's-health guidance tool that helps users describe symptoms in English, Hindi, or Kannada and understand possible next steps. It focuses on PCOS-related concerns and helps users prepare questions for a healthcare professional.

> **Note:** Symphera provides general information, not a diagnosis or a replacement for professional medical care.

## Features

- Multilingual symptom input: English, Hindi, and Kannada
- Voice input where supported by the browser
- Plain-language summaries and possible symptom patterns
- Urgency guidance and suggested specialist
- Questions to ask a doctor and symptom-tracking suggestions
- Responsive interface for desktop and mobile

## Tech stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** FastAPI
- **AI:** Groq API
- **Deployment:** Render

## Run Locally

### Prerequisites
- Python 3.10 or newer
- Git

### 1. Clone the repository

git clone https://github.com/vidya235252-crypto/Sympher.git
cd Sympher

### 2. Create and activate a virtual environment

**Windows:**

python -m venv .venv
.venv\Scripts\activate

**macOS/Linux:**

python3 -m venv .venv
source .venv/bin/activate

### 3. Install backend dependencies

cd backend
pip install -r requirements.txt

### 4. Configure environment variables

Create a '.env' file inside the `backend/` directory using `.env.example` as a reference. Add your LLM API key and the required model configuration.

Never commit your `.env` file or expose API keys in frontend code.

### 5. Start the application

From the `backend/` directory, run:

uvicorn main:app --reload

Open `http://127.0.0.1:8000` in your browser.

### API endpoints
- `GET /health` — health check
- `POST /analyze` — symptom analysis

For the demo interface, try `http://127.0.0.1:8000/?demo`.


## Responsible use

Symphera does not diagnose PCOS or any other condition. AI-generated information can be incomplete or inaccurate. Consult a qualified healthcare professional, and seek urgent care for severe or rapidly worsening symptoms.

