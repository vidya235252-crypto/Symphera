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

## Run locally

```bash
git clone https://github.com/vidya235252-crypto/Symphera.git
cd Symphera
```

Create and activate a virtual environment, then install the dependencies listed in the repository.

**Windows PowerShell**
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS/Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configure the environment variables required by the backend (including your Groq API key). Never commit secrets to GitHub. Start the FastAPI app using the entry point and command defined in the repository, then open http://localhost:8000.

## API

| Endpoint | Purpose |
|---|---|
| `GET /health` | Service health check |
| `POST /analyze` | Analyze a symptom description and return guidance |

## Responsible use

Symphera does not diagnose PCOS or any other condition. AI-generated information can be incomplete or inaccurate. Consult a qualified healthcare professional, and seek urgent care for severe or rapidly worsening symptoms.

