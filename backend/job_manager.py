import uuid
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

# Job storage (in production, use a proper database)
processing_jobs = {}

class ProcessingJob:
    def __init__(self, upload_id: str, filename: str, filepath: str):
        self.upload_id = upload_id
        self.filename = filename
        self.filepath = filepath
        self.status = "processing"  # processing, completed, failed
        self.data = None
        self.error = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

def create_job(filename: str, filepath: str) -> str:
    """Create a new processing job and return its ID"""
    upload_id = str(uuid.uuid4())
    job = ProcessingJob(upload_id, filename, filepath)
    processing_jobs[upload_id] = job
    return upload_id

def get_job(upload_id: str) -> Optional[ProcessingJob]:
    """Retrieve a job by ID"""
    return processing_jobs.get(upload_id)

def update_job_completed(upload_id: str, data: dict):
    """Mark job as completed with data"""
    if upload_id in processing_jobs:
        job = processing_jobs[upload_id]
        job.status = "completed"
        job.data = data
        job.updated_at = datetime.utcnow()

def update_job_failed(upload_id: str, error: str):
    """Mark job as failed with error message"""
    if upload_id in processing_jobs:
        job = processing_jobs[upload_id]
        job.status = "failed"
        job.error = error
        job.updated_at = datetime.utcnow()
