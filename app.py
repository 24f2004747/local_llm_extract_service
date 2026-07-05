from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re

app = FastAPI()


class ExtractRequest(BaseModel):
    text: str


class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


CURRENCIES = ["USD", "EUR", "GBP"]


def extract_vendor(text: str):
    patterns = [
        r"Invoice\s+from\s+(.+?)(?:\.|,|\n)",
        r"Vendor\s*[:\-]\s*(.+?)(?:\n|$)",
        r"Supplier\s*[:\-]\s*(.+?)(?:\n|$)",
        r"Bill\s+From\s*[:\-]?\s*(.+?)(?:\n|$)",
    ]

    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return m.group(1).strip()

    m = re.search(r"([A-Za-z0-9&.,' -]+?(?:Ltd\.?|LLC|Inc\.?|Industries|Corporation|Company))", text, re.I)
    if m:
        return m.group(1).strip()

    return ""


def extract_currency(text: str):
    for c in CURRENCIES:
        if c in text.upper():
            return c
    return ""


def extract_amount(text: str):
    patterns = [
        r"(?:Total\s+Due|Amount\s+Due|Total|Balance\s+Due)\D*([0-9]+(?:\.[0-9]{1,2})?)",
        r"(USD|EUR|GBP)\s*([0-9]+(?:\.[0-9]{1,2})?)",
        r"([0-9]+(?:\.[0-9]{1,2})?)\s*(USD|EUR|GBP)",
    ]

    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            nums = re.findall(r"[0-9]+(?:\.[0-9]{1,2})?", m.group(0))
            if nums:
                return float(nums[-1])

    nums = re.findall(r"[0-9]+(?:\.[0-9]{1,2})?", text)
    if nums:
        return float(max(nums, key=float))

    return 0.0


def extract_date(text: str):
    m = re.search(r"(2026-\d{2}-\d{2})", text)
    if m:
        return m.group(1)

    m = re.search(r"Due\s*(?:Date)?[: ]*(\d{4}-\d{2}-\d{2})", text, re.I)
    if m:
        return m.group(1)

    return ""


@app.post("/extract", response_model=InvoiceResponse)
def extract(req: ExtractRequest):
    if not req.text.strip():
        raise HTTPException(status_code=422, detail="Empty input")

    text = req.text

    return InvoiceResponse(
        vendor=extract_vendor(text),
        amount=extract_amount(text),
        currency=extract_currency(text),
        date=extract_date(text),
    )
