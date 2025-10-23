# Credit Card Statement Parser

A comprehensive web application for parsing credit card statements from PDF files. The application extracts key information such as due dates, credit limits, available credit, and statement dates from various bank statements using both regex pattern matching and OCR (Optical Character Recognition).

## 🏦 Supported Banks

- **HDFC Bank** - India
- **ICICI Bank** - India  
- **Kotak Bank** - India
- **American Express (AMEX)** - International
- **Capital One** - International

## ✨ Features

### Core Functionality
- **Multi-bank Support**: Automatically detects and parses statements from 5 major banks
- **Dual Parsing Methods**: Uses both PyPDF2 text extraction and Tesseract OCR for maximum accuracy
- **Batch Processing**: Upload and parse multiple statements simultaneously (up to 10 files)
- **Smart Field Extraction**: Extracts due dates, credit limits, available credit, statement dates, and last 4 digits of card numbers

### Web Interface
- **Modern React Frontend**: Clean, responsive UI with drag-and-drop file upload
- **Real-time Processing**: Live progress updates and status notifications
- **Statement History**: View and manage previously parsed statements
- **Edit Capabilities**: Update parsed data manually if needed
- **Export Functionality**: Download results as CSV files

### Backend API
- **FastAPI Backend**: High-performance REST API with automatic documentation
- **SQLite Database**: Persistent storage with full CRUD operations
- **CORS Support**: Cross-origin requests enabled for frontend integration
- **Error Handling**: Comprehensive error handling and logging
- **Health Checks**: Built-in health monitoring endpoints

## 🛠️ Technology Stack

### Backend
- **Python 3.8+**
- **FastAPI** - Modern, fast web framework
- **PyPDF2** - PDF text extraction
- **Tesseract OCR** - Optical character recognition
- **SQLite** - Lightweight database
- **Pydantic** - Data validation

### Frontend
- **React 18** - Modern UI library
- **Axios** - HTTP client
- **React Dropzone** - File upload component
- **Lucide React** - Icon library

### Dependencies
- **pdf2image** - PDF to image conversion
- **Pillow** - Image processing
- **python-dateutil** - Date parsing utilities

## 📋 Prerequisites

### System Requirements
- **Python 3.8+**
- **Node.js 16+** and npm
- **Tesseract OCR** (for OCR functionality)
- **Poppler** (for PDF to image conversion)

### Installation Commands

#### macOS
```bash
# Install Tesseract OCR
brew install tesseract

# Install Poppler
brew install poppler
```

#### Ubuntu/Debian
```bash
# Install Tesseract OCR
sudo apt-get install tesseract-ocr

# Install Poppler
sudo apt-get install poppler-utils
```

#### Windows
- Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
- Download Poppler from: https://github.com/oschwartz10612/poppler-windows/releases/

## 🚀 Quick Start

### Option 1: Using Startup Scripts (Recommended)

1. **Start the Backend**
   ```bash
   chmod +x start_backend.sh
   ./start_backend.sh
   ```

2. **Start the Frontend** (in a new terminal)
   ```bash
   chmod +x start_frontend.sh
   ./start_frontend.sh
   ```

3. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Option 2: Manual Setup

#### Backend Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## 📁 Project Structure

```
creditcard_parser/
├── main.py                 # FastAPI backend server
├── parser.py              # Core parsing logic 
├── database.py            # SQLite database operations
├── requirements.txt       # Python dependencies
├── start_backend.sh       # Backend startup script
├── start_frontend.sh      # Frontend startup script            
├── venv/                  # Python virtual environment
├── credit_card_statements.db  # SQLite database
└── frontend/              # React frontend application
    ├── package.json       # Node.js dependencies
    ├── public/            # Static assets
    └── src/               # React source code
        ├── App.js         # Main React component
        ├── App.css        # Styling
        └── index.js       # React entry point
```

## 🔧 API Endpoints

### Core Endpoints
- `POST /parse-single` - Parse a single PDF statement
- `POST /parse-multiple` - Parse multiple PDF statements
- `GET /supported-banks` - List supported banks and fields

### Database Endpoints
- `GET /statements` - Get all parsed statements
- `GET /statements/{id}` - Get specific statement
- `PUT /statements/{id}` - Update statement fields
- `DELETE /statements/{id}` - Delete statement
- `GET /statements/search?q={query}` - Search statements
- `GET /statistics` - Get database statistics

### Utility Endpoints
- `GET /` - Root endpoint
- `GET /health` - Health check

## 💡 Usage Examples

### Parse Single Statement
```bash
curl -X POST "http://localhost:8000/parse-single" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@statement.pdf"
```

### Get All Statements
```bash
curl -X GET "http://localhost:8000/statements"
```

### Search Statements
```bash
curl -X GET "http://localhost:8000/statements/search?q=HDFC"
```

## 🔍 How It Works

### Parsing Process
1. **File Upload**: PDF files are uploaded via the web interface or API
2. **Bank Detection**: The system analyzes the PDF content to identify the bank
3. **Dual Extraction**: 
   - **PyPDF2**: Extracts text directly from PDF structure
   - **OCR**: Converts PDF to images and uses Tesseract for text recognition
4. **Pattern Matching**: Bank-specific regex patterns extract key fields
5. **Result Combination**: Smart logic combines results from both methods
6. **Database Storage**: Parsed data is saved to SQLite database


## 🎯 Extracted Fields

For each statement, the parser extracts:
- **Due Date** - Payment due date
- **Last 4 Digits** - Last 4 digits of credit card number
- **Credit Limit** - Total credit limit
- **Available Credit** - Remaining available credit
- **Statement Date** - Statement generation date
- **Bank** - Detected bank name

## 🛡️ Error Handling

- **File Validation**: Only PDF files are accepted
- **Size Limits**: Maximum 10 files per batch upload
- **Duplicate Detection**: Prevents processing the same file twice
- **Graceful Degradation**: Continues processing even if some files fail
- **Comprehensive Logging**: Detailed logs for debugging

## 📊 Database Schema

```sql
CREATE TABLE statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    bank TEXT,
    due_date TEXT,
    last_4_digits TEXT,
    credit_limit TEXT,
    available_credit TEXT,
    statement_date TEXT,
    parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_hash TEXT UNIQUE,
    raw_data TEXT
);
```

## 🔧 Configuration

### Environment Variables
- No environment variables required for basic operation
- Tesseract path can be configured in `parser.py` if needed

### Database
- SQLite database is created automatically
- Database file: `credit_card_statements.db`
- No additional configuration required

## 🐛 Troubleshooting

### Common Issues

1. **Tesseract not found**
   ```bash
   # Install Tesseract
   brew install tesseract  # macOS
   sudo apt-get install tesseract-ocr  # Ubuntu
   ```

2. **Poppler not found**
   ```bash
   # Install Poppler
   brew install poppler  # macOS
   sudo apt-get install poppler-utils  # Ubuntu
   ```

3. **Port already in use**
   - Backend: Change port in `start_backend.sh` or `main.py`
   - Frontend: Change port in `start_frontend.sh` or use `PORT=3001 npm start`

4. **CORS errors**
   - Ensure backend is running on port 8000
   - Check CORS configuration in `main.py`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation at http://localhost:8000/docs
3. Check the application logs for detailed error messages

## 🔮 Future Enhancements

- Support for additional banks
- Enhanced OCR accuracy with machine learning
- Batch processing improvements
- Data visualization and analytics
- Mobile app development
- Cloud deployment options
