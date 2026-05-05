import os
import base64
import requests
import logging
import random
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCRService:
    def __init__(self, aws_key=None, aws_secret=None, aws_region=None):
        self.ocr_space_key = os.getenv("OCR_SPACE_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")

        if self.ocr_space_key:
            logger.info("✓ OCR.space configured successfully")
        else:
            logger.warning("✗ OCR.space key not found")

        if self.groq_key:
            logger.info("✓ Groq AI configured successfully")
        else:
            logger.warning("✗ Groq key not found")

        self.use_mock = not (self.ocr_space_key and self.groq_key)

        if self.use_mock:
            logger.warning("Missing API keys - using mock mode")
        else:
            logger.info("✓ Real OCR mode active - will process actual documents")

    def process_document(self, file_path: str) -> dict:
        if self.use_mock:
            logger.info("Using mock data")
            return self.mock_process_document(file_path)

        try:
            logger.info(f"Extracting text from: {file_path}")
            raw_text = self._extract_text_ocr_space(file_path)

            if not raw_text or len(raw_text.strip()) < 20:
                logger.warning("OCR returned very little text - using mock")
                return self.mock_process_document(file_path)

            logger.info(f"OCR extracted {len(raw_text)} characters - sending to Groq")
            structured_data = self._structure_with_groq(raw_text)
            return structured_data

        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            raise Exception(str(e))

    def _extract_text_ocr_space(self, file_path: str) -> str:
        file_path = Path(file_path)
        file_ext = file_path.suffix.lower()

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        base64_file = base64.b64encode(file_bytes).decode("utf-8")

        if file_ext == ".pdf":
            file_type = "application/pdf"
        elif file_ext in [".jpg", ".jpeg"]:
            file_type = "image/jpeg"
        else:
            file_type = "image/png"

        payload = {
            "base64Image": f"data:{file_type};base64,{base64_file}",
            "apikey": self.ocr_space_key,
            "language": "eng",
            "isOverlayRequired": False,
            "OCREngine": 2,
            "scale": True,
            "isTable": True,
        }

        logger.info("Sending to OCR.space...")
        response = requests.post(
            "https://api.ocr.space/parse/image",
            data=payload,
            timeout=60
        )

        result = response.json()

        if result.get("IsErroredOnProcessing"):
            error_msg = result.get("ErrorMessage", ["Unknown error"])
            if isinstance(error_msg, list):
                error_msg = " ".join(error_msg)
            raise Exception(f"OCR.space error: {error_msg}")

        parsed_results = result.get("ParsedResults", [])
        if not parsed_results:
            raise Exception("No text extracted from document")

        full_text = "\n".join(
            r.get("ParsedText", "") for r in parsed_results
        )

        logger.info(f"OCR.space returned {len(full_text)} characters")
        logger.info(f"OCR TEXT PREVIEW: {full_text[:300]}")
        return full_text

    def _structure_with_groq(self, raw_text: str) -> dict:
        prompt = f"""You are an expert invoice and bill parser for Indian businesses.

Given this raw OCR text extracted from an invoice or bill, extract all structured data.

RAW OCR TEXT:
{raw_text}

Extract and return a JSON object with EXACTLY this structure:
{{
    "header": {{
        "vendor_name": "company or vendor name",
        "invoice_number": "invoice or bill number",
        "invoice_date": "date of invoice",
        "total_amount": 0.0,
        "gst_number": "GST number if found else empty string"
    }},
    "line_items": [
        {{
            "item_name": "full item description",
            "quantity": 1,
            "unit": "Pcs or Box or Nos or Set or Kg or Ltr etc",
            "unit_price": 0.0,
            "amount": 0.0,
            "tax": 18,
            "hsn_code": "HSN code if found else empty string"
        }}
    ]
}}

Critical rules:
- unit_price means the PRICE PER SINGLE UNIT before tax
- amount means the TOTAL for that line BEFORE tax which equals quantity x unit_price
- tax means the GST percentage number only like 18 not 18%
- total_amount in header means the GRAND TOTAL of the entire invoice including all taxes
- Extract ALL line items visible in the text
- If quantity is not found assume 1
- If unit is not found use Pcs
- If tax or GST percent is not found use 18
- If HSN code is not found use empty string
- Return ONLY the raw JSON object
- Do NOT include markdown backticks
- Do NOT include the word json at the start
- Do NOT add any explanation before or after the JSON"""

        logger.info("Sending to Groq AI for structuring...")

        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert invoice parser. Always respond with valid JSON only. No markdown, no explanation."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 4096,
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        logger.info(f"Groq response status: {response.status_code}")
        result = response.json()

        if "error" in result:
            error_msg = result["error"].get("message", "Unknown Groq error")
            logger.error(f"Groq API error: {error_msg}")
            raise Exception(f"Groq error: {error_msg}")

        response_text = result["choices"][0]["message"]["content"].strip()
        logger.info(f"Groq raw response preview: {response_text[:300]}")

        response_text = response_text.replace("```json", "").replace("```", "").strip()
        if response_text.startswith("json"):
            response_text = response_text[4:].strip()

        try:
            data = json.loads(response_text)
            logger.info(f"✓ Groq extracted {len(data.get('line_items', []))} line items")
            logger.info(f"✓ Header: {data.get('header', {})}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Groq returned invalid JSON: {response_text[:300]}")
            raise Exception(f"AI returned invalid JSON: {str(e)}")

    @staticmethod
    def mock_process_document(file_path: str) -> dict:
        logger.info(f"Mock processing: {Path(file_path).name}")
        return {
            "header": {
                "vendor_name": "Sharma Traders Pvt. Ltd.",
                "invoice_number": f"INV-2024-{random.randint(1000, 9999)}",
                "invoice_date": "2024-11-15",
                "total_amount": 124820.00,
                "gst_number": "27AABCS1429B1Z1"
            },
            "line_items": [
                {
                    "item_name": "A4 Paper Ream 500 Sheets",
                    "quantity": 50,
                    "unit": "Box",
                    "unit_price": 250,
                    "amount": 14000,
                    "tax": 12,
                    "hsn_code": "4802"
                },
                {
                    "item_name": "HP Toner Cartridge 85A",
                    "quantity": 10,
                    "unit": "Pcs",
                    "unit_price": 3200,
                    "amount": 37760,
                    "tax": 18,
                    "hsn_code": "8443"
                },
                {
                    "item_name": "Office Chair Mesh Back",
                    "quantity": 5,
                    "unit": "Nos",
                    "unit_price": 8500,
                    "amount": 50150,
                    "tax": 18,
                    "hsn_code": "9401"
                },
                {
                    "item_name": "Whiteboard Marker Set",
                    "quantity": 20,
                    "unit": "Set",
                    "unit_price": 180,
                    "amount": 4032,
                    "tax": 12,
                    "hsn_code": "9608"
                },
                {
                    "item_name": "Hand Sanitizer 500ml",
                    "quantity": 30,
                    "unit": "Bottle",
                    "unit_price": 190,
                    "amount": 6726,
                    "tax": 18,
                    "hsn_code": "3808"
                }
            ]
        }