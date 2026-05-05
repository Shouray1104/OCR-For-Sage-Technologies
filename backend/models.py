from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class InvoiceMetadata(Base):
    """Model for invoice metadata"""
    __tablename__ = "invoice_metadata"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    total_amount = Column(Float, nullable=True)
    item_count = Column(Integer, nullable=True)
    raw_response = Column(Text, nullable=True)  # Stores JSON string of Textract response
    status = Column(String, default="completed")  # completed, failed, processing
    error_message = Column(String, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to bill items
    bill_items = relationship("BillItem", back_populates="invoice")


class BillItem(Base):
    """Model for extracted bill line items"""
    __tablename__ = "bill_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoice_metadata.id"), nullable=False, index=True)
    job_id = Column(String, index=True, nullable=False)
    item_name = Column(String, nullable=True)
    category = Column(String, nullable=True)
    hsn_code = Column(String, nullable=True)
    quantity = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    unit_rate = Column(Float, nullable=True)
    gst_percent = Column(Float, nullable=True)
    total_amount = Column(Float, nullable=True)
    confidence_score = Column(Float, default=0.95, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship back to invoice
    invoice = relationship("InvoiceMetadata", back_populates="bill_items")
