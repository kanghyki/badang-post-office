from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

app = FastAPI(
    title="Jeju Translation API",
    description="제주 방언 번역 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정 (모든 origin 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 글로벌 변수로 모델 저장
model = None
tokenizer = None
device = None

class TranslateRequest(BaseModel):
    text: str

class TranslateResponse(BaseModel):
    original: str
    translated: str

@app.on_event("startup")
async def load_model():
    """앱 시작 시 모델 로드"""
    global model, tokenizer, device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained("Junhoee/Kobart-Jeju-translation")
    model = AutoModelForSeq2SeqLM.from_pretrained("Junhoee/Kobart-Jeju-translation").to(device)
    model.eval()

@app.post("/translate", summary="제주어 번역", tags=["Translation"])
async def translate(req: TranslateRequest):
    """표준어를 제주어로 번역"""
    try:
        input_text = "[표준] " + req.text
        input_ids = tokenizer(
            input_text,
            return_tensors="pt",
            padding=True,
            truncation=True
        ).input_ids.to(device)

        with torch.no_grad():
            outputs = model.generate(input_ids, max_length=64)

        translated = tokenizer.decode(outputs[0], skip_special_tokens=True)

        return TranslateResponse(original=req.text, translated=translated)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
