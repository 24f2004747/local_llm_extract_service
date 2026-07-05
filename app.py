from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import requests, json

app = FastAPI()

class ExtractRequest(BaseModel):
    text: str

class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

PROMPT = """
Extract invoice information.

Return ONLY valid JSON.

Schema:
{
  "vendor":"string",
  "amount":number,
  "currency":"USD",
  "date":"YYYY-MM-DD"
}
Rules:
- vendor = company issuing invoice
- amount = total amount due
- currency = ISO 4217 3-letter uppercase code
- date = payment due date
"""

@app.post("/extract", response_model=InvoiceResponse)
def extract(req: ExtractRequest):
    if not req.text.strip():
        raise HTTPException(status_code=422, detail="Empty input")

    payload = {
        "model": MODEL,
        "prompt": PROMPT + "\n\nInvoice:\n" + req.text,
        "stream": False,
        "format": "json"
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
        r.raise_for_status()
        result = r.json()
        data = json.loads(result["response"])
        return InvoiceResponse(
            vendor=str(data["vendor"]),
            amount=float(data["amount"]),
            currency=str(data["currency"]).upper(),
            date=str(data["date"])
        )
    except HTTPException:
        raise
    except Exception:
        return JSONResponse(
            status_code=422,
            content={
                "vendor":"",
                "amount":0.0,
                "currency":"",
                "date":""
            }
        )
