from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Get the backend directory path
BACKEND_DIR = Path(__file__).parent
DATABASE_PATH = BACKEND_DIR / "erp_ocr.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


class Bill(Base):
    """Model for bills/invoices"""
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)
    filename = Column(String, nullable=False)
    vendor_name = Column(String, nullable=True)
    invoice_number = Column(String, nullable=True, index=True)
    invoice_date = Column(String, nullable=True)
    total_amount = Column(Float, nullable=True)
    status = Column(String, default="completed")  # completed, failed, processing
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship to bill items
    bill_items = relationship("BillItem", back_populates="bill", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Bill(job_id={self.job_id}, filename={self.filename}, total={self.total_amount})>"


class BillItem(Base):
    """Model for line items in bills"""
    __tablename__ = "bill_items"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("bills.job_id"), nullable=False, index=True)
    item_name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    hsn_code = Column(String, nullable=True)
    quantity = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    unit_rate = Column(Float, nullable=True)
    gst_percent = Column(Float, nullable=True)
    total_amount = Column(Float, nullable=True)
    confidence_score = Column(Float, default=0.95, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to bill
    bill = relationship("Bill", back_populates="bill_items")

    def __repr__(self):
        return f"<BillItem(item_name={self.item_name}, quantity={self.quantity}, total={self.total_amount})>"


def init_db():
    """
    Initialize database by creating all tables.
    This is called on application startup.
    """
    try:
        logger.info(f"Initializing database at {DATABASE_PATH}")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return False


def get_db() -> Session:
    """
    Dependency to get database session.
    Use in FastAPI endpoints with Depends(get_db).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_bill(job_id: str, filename: str, header_info: Dict[str, Any]) -> Optional[Bill]:
    """
    Create and save a new bill record.

    Args:
        job_id: Unique job identifier
        filename: Original filename of the invoice
        header_info: Dictionary with header information:
            - vendor_name: Name of vendor/supplier
            - invoice_number: Invoice/reference number
            - invoice_date: Date of invoice
            - total_amount: Total invoice amount

    Returns:
        Bill object if successful, None otherwise
    """
    db = SessionLocal()
    try:
        bill = Bill(
            job_id=job_id,
            filename=filename,
            vendor_name=header_info.get('vendor_name'),
            invoice_number=header_info.get('invoice_number'),
            invoice_date=header_info.get('invoice_date'),
            total_amount=header_info.get('total_amount'),
            status="completed"
        )
        db.add(bill)
        db.commit()
        db.refresh(bill)
        logger.info(f"Created bill with job_id={job_id}, invoice_number={header_info.get('invoice_number')}")
        return bill
    except Exception as e:
        logger.error(f"Error creating bill: {str(e)}")
        db.rollback()
        return None
    finally:
        db.close()


def save_bill_items(job_id: str, items_list: List[Dict[str, Any]]) -> bool:
    """
    Save all line items for a bill.

    Args:
        job_id: Job identifier matching the bill
        items_list: List of item dictionaries with fields:
            - item_name: Item description
            - category: Product category
            - hsn_code: HSN code for tax
            - quantity: Quantity
            - unit: Unit of measurement
            - unit_rate: Price per unit
            - gst_percent: GST percentage
            - total_amount: Total for line item
            - confidence_score: OCR confidence (0.85-1.0)

    Returns:
        True if successful, False otherwise
    """
    db = SessionLocal()
    try:
        if not items_list:
            logger.warning(f"No items to save for job_id={job_id}")
            return True

        # Create BillItem objects
        bill_items = [
            BillItem(
                job_id=job_id,
                item_name=item.get('item_name'),
                category=item.get('category'),
                hsn_code=item.get('hsn_code'),
                quantity=item.get('quantity'),
                unit=item.get('unit'),
                unit_rate=item.get('unit_rate'),
                gst_percent=item.get('gst_percent'),
                total_amount=item.get('total_amount'),
                confidence_score=item.get('confidence_score', 0.95)
            )
            for item in items_list
        ]

        db.add_all(bill_items)
        db.commit()
        logger.info(f"Saved {len(bill_items)} line items for job_id={job_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving bill items: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


def get_bill_items(job_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all line items for a specific bill.

    Args:
        job_id: Job identifier

    Returns:
        List of dictionaries containing item details
    """
    db = SessionLocal()
    try:
        items = db.query(BillItem).filter(BillItem.job_id == job_id).all()

        items_list = [
            {
                'id': item.id,
                'item_name': item.item_name,
                'category': item.category,
                'hsn_code': item.hsn_code,
                'quantity': item.quantity,
                'unit': item.unit,
                'unit_rate': item.unit_rate,
                'gst_percent': item.gst_percent,
                'total_amount': item.total_amount,
                'confidence_score': item.confidence_score
            }
            for item in items
        ]

        logger.info(f"Retrieved {len(items_list)} items for job_id={job_id}")
        return items_list
    except Exception as e:
        logger.error(f"Error retrieving bill items: {str(e)}")
        return []
    finally:
        db.close()


def get_all_bills() -> List[Dict[str, Any]]:
    """
    Retrieve list of all bills.

    Returns:
        List of dictionaries containing bill summary information
    """
    db = SessionLocal()
    try:
        bills = db.query(Bill).order_by(Bill.created_at.desc()).all()

        bills_list = [
            {
                'id': bill.id,
                'job_id': bill.job_id,
                'filename': bill.filename,
                'vendor_name': bill.vendor_name,
                'invoice_number': bill.invoice_number,
                'invoice_date': bill.invoice_date,
                'total_amount': bill.total_amount,
                'status': bill.status,
                'created_at': bill.created_at.isoformat() if bill.created_at else None,
                'item_count': len(bill.bill_items)
            }
            for bill in bills
        ]

        logger.info(f"Retrieved {len(bills_list)} bills from database")
        return bills_list
    except Exception as e:
        logger.error(f"Error retrieving bills: {str(e)}")
        return []
    finally:
        db.close()


def get_bill_by_job_id(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a specific bill by job ID.

    Args:
        job_id: Job identifier

    Returns:
        Bill dictionary or None if not found
    """
    db = SessionLocal()
    try:
        bill = db.query(Bill).filter(Bill.job_id == job_id).first()

        if not bill:
            logger.warning(f"Bill not found for job_id={job_id}")
            return None

        bill_dict = {
            'id': bill.id,
            'job_id': bill.job_id,
            'filename': bill.filename,
            'vendor_name': bill.vendor_name,
            'invoice_number': bill.invoice_number,
            'invoice_date': bill.invoice_date,
            'total_amount': bill.total_amount,
            'status': bill.status,
            'created_at': bill.created_at.isoformat() if bill.created_at else None,
            'item_count': len(bill.bill_items)
        }

        return bill_dict
    except Exception as e:
        logger.error(f"Error retrieving bill: {str(e)}")
        return None
    finally:
        db.close()


def delete_bill(job_id: str) -> bool:
    """
    Delete a bill and all its line items.

    Args:
        job_id: Job identifier

    Returns:
        True if successful, False otherwise
    """
    db = SessionLocal()
    try:
        # Delete bill (cascades to bill_items due to relationship)
        result = db.query(Bill).filter(Bill.job_id == job_id).delete()
        db.commit()

        if result > 0:
            logger.info(f"Deleted bill with job_id={job_id}")
            return True
        else:
            logger.warning(f"No bill found to delete for job_id={job_id}")
            return False
    except Exception as e:
        logger.error(f"Error deleting bill: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


def get_db_stats() -> Dict[str, Any]:
    """
    Get database statistics.

    Returns:
        Dictionary with database stats
    """
    db = SessionLocal()
    try:
        bill_count = db.query(Bill).count()
        item_count = db.query(BillItem).count()
        total_amount = db.query(Bill).with_entities(
            db.func.sum(Bill.total_amount)
        ).scalar() or 0

        return {
            'bills': bill_count,
            'items': item_count,
            'total_amount': total_amount,
            'database_path': str(DATABASE_PATH)
        }
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        return {}
    finally:
        db.close()
