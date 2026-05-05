# ERP OCR Portal - Full Stack Application

A modern full-stack application for intelligent invoice processing and data extraction using AWS Textract and OCR technology. The system extracts structured data from PDF invoices including line items, HSN codes, GST information, and quantities.

## Features

-  **PDF Upload** - Drag-and-drop PDF invoice upload interface
-  **AWS Textract Integration** - Enterprise-grade OCR using AWS Textract AnalyzeExpense API
-  **Data Extraction** - Extracts structured line items with fields:
  - Item name and category
  - HSN Code (Indian tax classification)
  - Quantity and unit
  - Unit rate and total amount
  - GST percentage
-  **SQLite Database** - Persistent storage of extracted data
-  **Real-time Progress** - Step-by-step processing status tracking
-  **Responsive UI** - Beautiful, responsive React + Vite frontend
-  **CORS Enabled** - Secure cross-origin requests

## Project Structure

```
erp-ocr-portal/
├── frontend/                 # React + Vite application
│   ├── src/
│   │   ├── components/
│   │   │   ├── UploadZone.jsx       # Drag-drop upload component
│   │   │   ├── ProcessingStatus.jsx # Progress tracking component
│   │   │   └── ExtractedTable.jsx   # Results display component
│   │   ├── App.jsx                  # Main app component
│   │   ├── App.css                  # Styling
│   │   ├── main.jsx                 # React entry point
│   │   └── index.css                # Global styles
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── .gitignore
│
├── backend/                  # FastAPI server
│   ├── main.py              # FastAPI application & endpoints
│   ├── ocr_service.py       # AWS Textract integration
│   ├── parser.py            # Data parsing logic
│   ├── database.py          # SQLAlchemy database setup
│   ├── models.py            # Database models
│   ├── job_manager.py       # Job tracking system
│   ├── uploads/             # Temporary PDF storage
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Environment variables (template)
│   └── erp_ocr.db          # SQLite database (created on first run)
│
├── README.md               # This file
└── .gitignore             # Git ignore rules
```

## Prerequisites

- **Node.js** (v16+) and **npm** for frontend
- **Python** (v3.8+) and **pip** for backend
- **AWS Account** with Textract API access
- AWS credentials (Access Key ID and Secret Access Key)

## Installation & Setup

### 1. Clone/Setup the Project

```bash
cd d:\FULL_STACK\erp-ocr-portal
```

### 2. Backend Setup

#### Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### Configure AWS Credentials

Edit `backend/.env` with your AWS credentials:

```env
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1
```

**Getting AWS Credentials:**
1. Go to [AWS Console](https://console.aws.amazon.com/)
2. Navigate to IAM → Users → Create user or use existing
3. Create access keys or use existing keys
4. Ensure the user has permissions for:
   - `textract:AnalyzeExpense`
   - `textract:AnalyzeDocument`

#### Run Backend Server

```bash
cd backend
python main.py
```

The backend will start at `http://localhost:8000`

**API Endpoints:**
- `POST /upload` - Upload PDF file
- `GET /results/{upload_id}` - Get processing results
- `GET /health` - Health check
- `GET /` - API documentation

### 3. Frontend Setup

#### Install Node Dependencies

```bash
cd frontend
npm install
```

#### Run Development Server

```bash
npm run dev
```

The frontend will start at `http://localhost:5173`

## Usage

1. **Start Backend**: Ensure the FastAPI server is running on port 8000
2. **Start Frontend**: Run the React development server on port 5173
3. **Upload Invoice**: 
   - Drag and drop a PDF invoice file or click to select
   - The file will be processed with AWS Textract
4. **View Results**: 
   - Progress tracker shows processing steps
   - Once complete, extracted line items display in a table
   - Download or further process the extracted data

## API Workflow

### Upload File
```bash
POST /upload
Content-Type: multipart/form-data

Body:
file: <PDF_FILE>

Response:
{
  "upload_id": "uuid",
  "filename": "invoice.pdf",
  "status": "processing"
}
```

### Get Results
```bash
GET /results/{upload_id}

Response (processing):
{
  "upload_id": "uuid",
  "status": "processing",
  "data": null
}

Response (completed):
{
  "upload_id": "uuid",
  "status": "completed",
  "data": {
    "items": [
      {
        "item_name": "Item Description",
        "category": "Category",
        "hsn_code": "9999",
        "quantity": 10,
        "unit": "pcs",
        "unit_rate": 100.0,
        "gst_percent": 18.0,
        "total_amount": 1000.0
      }
    ],
    "total_amount": 1000.0,
    "item_count": 1
  }
}
```

## Database Schema

### BillItem Table
Stores extracted line items from invoices:
- `id` - Primary key
- `upload_id` - Reference to upload
- `item_name` - Product/service name
- `category` - Item category
- `hsn_code` - HSN tax code
- `quantity` - Quantity ordered
- `unit` - Unit of measurement
- `unit_rate` - Price per unit
- `gst_percent` - GST tax percentage
- `total_amount` - Line item total
- `created_at` - Timestamp

### InvoiceMetadata Table
Stores invoice processing metadata:
- `id` - Primary key
- `upload_id` - Unique upload identifier
- `filename` - Original filename
- `total_amount` - Invoice total
- `item_count` - Number of line items
- `raw_response` - Full Textract response (JSON)
- `status` - Processing status
- `error_message` - Error details if failed
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

## Technology Stack

### Frontend
- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Axios** - HTTP client
- **React Dropzone** - File upload handling
- **CSS3** - Modern styling with gradients and animations

### Backend
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI web server
- **SQLAlchemy** - ORM for database
- **SQLite** - Lightweight database
- **Boto3** - AWS SDK for Python
- **Python-dotenv** - Environment variable management

### AWS Services
- **AWS Textract** - Document analysis and OCR
- **Textract AnalyzeExpense API** - Invoice-specific processing

## Configuration

### Environment Variables

**Backend (.env)**
```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Frontend Configuration
FRONTEND_URL=http://localhost:5173
```

### CORS Settings
Currently configured to allow requests from `http://localhost:5173`. To add more origins, modify `main.py`:

```python
allow_origins=["http://localhost:5173", "http://your-domain.com"]
```

## Development

### Running Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Build for Production

**Frontend:**
```bash
cd frontend
npm run build
# Creates dist/ folder with optimized build
```

**Backend:**
No build needed - runs directly from Python files or can be containerized with Docker.

## Troubleshooting

### AWS Credentials Error
- Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set in .env
- Check AWS account permissions for Textract
- Ensure AWS_REGION is valid (e.g., us-east-1)

### CORS Error
- Ensure backend is running on port 8000
- Check frontend is accessing http://localhost:8000
- Verify CORS middleware is configured correctly

### PDF Processing Failure
- Ensure PDF is a valid invoice document
- AWS Textract AnalyzeExpense works best with structured invoices
- Check CloudWatch logs in AWS Console for detailed errors

### Database Error
- Ensure write permissions in the backend directory
- Delete erp_ocr.db to reset database
- Check SQLite version compatibility

### Port Already in Use
- Change port in vite.config.js (frontend) or main.py (backend)
- Or kill existing process using the port

## Performance Optimization

- **Frontend**: Vite provides optimized production builds with code splitting
- **Backend**: Async processing handles multiple uploads concurrently
- **Database**: SQLite adequate for development; use PostgreSQL for production
- **AWS**: Textract bills per page; optimize with batch processing for large volumes

## Security Considerations

1. **AWS Credentials**: Never commit .env file with real credentials
2. **File Upload**: Validate file types and size limits
3. **CORS**: Restrict to known frontend domains in production
4. **Database**: Use PostgreSQL in production with encrypted connections
5. **API Rate Limiting**: Implement in production environment

## Future Enhancements

- [ ] Batch processing for multiple invoices
- [ ] Custom OCR model training
- [ ] Real-time editing of extracted data
- [ ] Export to Excel/CSV formats
- [ ] Invoice comparison and deduplication
- [ ] Integration with accounting software (Tally, QuickBooks)
- [ ] Multi-language support
- [ ] Docker containerization
- [ ] CI/CD pipeline setup

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review AWS Textract documentation
3. Check application logs in backend console
4. Review browser console for frontend errors

## Authors

- Full Stack ERP OCR Portal Team

---

**Last Updated**: May 2024
**Version**: 1.0.0

# OCR-For-Sage-Technologies
2026 ERP OCR Portal. Design and Developed by Shouray Soni.
