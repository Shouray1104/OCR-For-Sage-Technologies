import os
import uuid
import shutil
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from ocr_service import OCRService
from parser import Parser
from database import init_db, get_db, create_bill, save_bill_items, get_bill_items, get_all_bills, get_db_stats

app = FastAPI(
    title="ERP OCR Portal API",
    description="Invoice OCR processing and data extraction API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://ocr-for-sage-technologies.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_MIMETYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}


@app.on_event("startup")
async def startup_event():
    init_db()
    print("✓ Database initialized")
    print("✓ OCR Portal API started")


def get_ocr_service():
    aws_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION", "ap-south-1")
    return OCRService(aws_key, aws_secret, aws_region)


def validate_file(file: UploadFile) -> str:
    if file.content_type not in ALLOWED_MIMETYPES:
        raise HTTPException(
            status_code=400,
            detail="File type not allowed. Supported types: PDF, JPG, PNG"
        )
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File extension not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    return file_ext


def save_uploaded_file(file: UploadFile, file_ext: str, job_id: str) -> str:
    file_path = UPLOAD_DIR / f"{job_id}{file_ext}"
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return str(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    file_ext = validate_file(file)
    job_id = str(uuid.uuid4())
    file_path = None

    try:
        # Step 1 - Save file
        file_path = save_uploaded_file(file, file_ext, job_id)

        # Step 2 - Run OCR
        ocr_service = get_ocr_service()
        ocr_result = ocr_service.process_document(file_path)

        # Step 3 - Parse line items
        parsed_items = Parser.parse_textract_response(ocr_result)

        # Step 4 - Get header info
        header_info = ocr_result.get("header", {})

        # Step 5 - Save bill to database
        bill = create_bill(job_id, file.filename, header_info)
        if not bill:
            raise Exception("Failed to create bill record in database")

        # Step 6 - Save line items to database
        if parsed_items:
            success = save_bill_items(job_id, parsed_items)
            if not success:
                raise Exception("Failed to save bill items to database")

        # Step 7 - Clean up uploaded file
        try:
            os.remove(file_path)
        except:
            pass

        return {
            "job_id": job_id,
            "filename": file.filename,
            "status": "completed",
            "item_count": len(parsed_items),
            "total_amount": header_info.get("total_amount", 0),
            "vendor_name": header_info.get("vendor_name", ""),
            "invoice_number": header_info.get("invoice_number", ""),
        }

    except HTTPException:
        raise
    except Exception as e:
        try:
            if file_path and Path(file_path).exists():
                os.remove(file_path)
        except:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"File processing failed: {str(e)}"
        )


@app.get("/results/{job_id}")
async def get_results(job_id: str, db: Session = Depends(get_db)):
    try:
        items_data = get_bill_items(job_id)

        if not items_data:
            raise HTTPException(
                status_code=404,
                detail=f"No results found for job_id: {job_id}"
            )

        total_amount = sum(
            float(item.get("total_amount", 0) or 0)
            for item in items_data
        )

        return {
            "job_id": job_id,
            "status": "success",
            "total_amount": total_amount,
            "item_count": len(items_data),
            "items": items_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving results: {str(e)}"
        )


@app.get("/jobs")
async def get_all_jobs(db: Session = Depends(get_db)):
    try:
        jobs = get_all_bills()
        return {
            "status": "success",
            "total_jobs": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving jobs: {str(e)}"
        )


@app.get("/health")
async def health_check():
    try:
        stats = get_db_stats()
        return {
            "status": "healthy",
            "service": "ERP OCR Portal API",
            "version": "1.0.0",
            "database": stats
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "ERP OCR Portal API",
            "error": str(e)
        }


@app.get("/")
async def root():
    return {
        "service": "ERP OCR Portal API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /upload - Upload PDF or image for OCR",
            "results": "GET /results/{job_id} - Get extracted line items",
            "jobs": "GET /jobs - Get all past uploaded bills",
            "health": "GET /health - Health check"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
