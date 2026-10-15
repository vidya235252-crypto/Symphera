from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from schemas import AnalyzeRequest, AnalyzeResponse  # noqa: E402
import pipeline  # noqa: E402

app = FastAPI(title="Women's health guide")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    return pipeline.run(req.text, req.language_hint)
