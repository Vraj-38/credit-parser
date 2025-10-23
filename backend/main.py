"""
FastAPI Backend for Credit Card Statement Parser
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import shutil
import tempfile
from typing import List, Dict, Optional
import logging
from dotenv import load_dotenv
from parser import CreditCardParser
from database_mongodb import MongoDBManager
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Credit Card Statement Parser",
    description="Upload and parse credit card statements to extract key information",
    version="1.0.0"
)

# Ensure DB connection on startup
@app.on_event("startup")
async def startup_event():
    try:
        await db_manager.connect()
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB on startup: {e}")

# Add CORS middleware - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize parser and database
parser = CreditCardParser()
db_manager = MongoDBManager()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Pydantic models for request/response
class StatementUpdate(BaseModel):
    bank: Optional[str] = None
    due_date: Optional[str] = None
    last_4_digits: Optional[str] = None
    credit_limit: Optional[str] = None
    available_credit: Optional[str] = None
    statement_date: Optional[str] = None

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Credit Card Statement Parser API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running"}

@app.post("/parse-single")
async def parse_single_statement(file: UploadFile = File(...)):
    """
    Parse a single credit card statement PDF
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Create temporary file
    temp_path = None
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
        
        # Parse the statement
        logger.info(f"Parsing file: {file.filename}")
        result = parser.parse_statement(temp_path)
        
        # Add filename to result
        result['filename'] = file.filename
        
        # Save to database
        try:
            statement_id = await db_manager.save_statement(result)
            result['id'] = statement_id
            logger.info(f"Statement saved to database with ID: {statement_id}")
        except Exception as e:
            logger.warning(f"Failed to save to database: {e}")
            result['id'] = None
        
        return JSONResponse(content={
            "success": True,
            "data": result,
            "message": "Statement parsed successfully"
        })
        
    except Exception as e:
        logger.error(f"Error parsing statement: {e}")
        raise HTTPException(status_code=500, detail=f"Error parsing statement: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

@app.post("/parse-multiple")
async def parse_multiple_statements(files: List[UploadFile] = File(...)):
    """
    Parse multiple credit card statement PDFs
    """
    if len(files) > 10:  # Limit to 10 files
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed")
    
    results = []
    temp_paths = []
    
    try:
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                continue  # Skip non-PDF files
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                shutil.copyfileobj(file.file, temp_file)
                temp_path = temp_file.name
                temp_paths.append(temp_path)
            
            try:
                # Parse the statement
                logger.info(f"Parsing file: {file.filename}")
                result = parser.parse_statement(temp_path)
                result['filename'] = file.filename
                result['success'] = True
                
                # Save to database
                try:
                    statement_id = await db_manager.save_statement(result)
                    result['id'] = statement_id
                    logger.info(f"Statement saved to database with ID: {statement_id}")
                except Exception as e:
                    logger.warning(f"Failed to save to database: {e}")
                    result['id'] = None
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error parsing {file.filename}: {e}")
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'error': str(e),
                    'bank': 'UNKNOWN',
                    'due_date': None,
                    'last_4_digits': None,
                    'credit_limit': None,
                    'available_credit': None,
                    'statement_date': None
                })
        
        return JSONResponse(content={
            "success": True,
            "data": results,
            "message": f"Processed {len(results)} files"
        })
        
    finally:
        # Clean up temporary files
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

@app.get("/supported-banks")
async def get_supported_banks():
    """Get list of supported banks"""
    return {
        "supported_banks": [
            "HDFC",
            "ICICI", 
            "KOTAK",
            "AMEX",
            "CAPITAL_ONE"
        ],
        "extracted_fields": [
            "Due Date",
            "Last 4 Digits",
            "Credit Limit", 
            "Available Credit",
            "Statement Date"
        ]
    }

# Database endpoints
@app.get("/statements")
async def get_all_statements():
    """Get all previously parsed statements"""
    try:
        statements = await db_manager.get_all_statements()
        return JSONResponse(content={
            "success": True,
            "data": statements,
            "count": len(statements)
        })
    except Exception as e:
        logger.error(f"Error fetching statements: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching statements: {str(e)}")

@app.get("/statements/{statement_id}")
async def get_statement(statement_id: str):
    """Get specific statement by ID"""
    try:
        statement = await db_manager.get_statement_by_id(statement_id)
        if not statement:
            raise HTTPException(status_code=404, detail="Statement not found")
        
        return JSONResponse(content={
            "success": True,
            "data": statement
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching statement {statement_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching statement: {str(e)}")

@app.put("/statements/{statement_id}")
async def update_statement(statement_id: str, updates: StatementUpdate):
    """Update statement fields"""
    try:
        # Convert Pydantic model to dict, excluding None values
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        success = await db_manager.update_statement(statement_id, update_dict)
        if not success:
            raise HTTPException(status_code=404, detail="Statement not found or no changes made")
        
        # Return updated statement
        updated_statement = await db_manager.get_statement_by_id(statement_id)
        return JSONResponse(content={
            "success": True,
            "data": updated_statement,
            "message": "Statement updated successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating statement {statement_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating statement: {str(e)}")

@app.delete("/statements/{statement_id}")
async def delete_statement(statement_id: str):
    """Delete statement by ID"""
    try:
        success = await db_manager.delete_statement(statement_id)
        if not success:
            raise HTTPException(status_code=404, detail="Statement not found")
        
        return JSONResponse(content={
            "success": True,
            "message": "Statement deleted successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting statement {statement_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting statement: {str(e)}")

@app.get("/statements/search")
async def search_statements(q: str = Query(..., description="Search query")):
    """Search statements by filename or bank"""
    try:
        statements = await db_manager.search_statements(q)
        return JSONResponse(content={
            "success": True,
            "data": statements,
            "count": len(statements),
            "query": q
        })
    except Exception as e:
        logger.error(f"Error searching statements: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching statements: {str(e)}")

@app.get("/statistics")
async def get_statistics():
    """Get database statistics"""
    try:
        stats = await db_manager.get_statistics()
        return JSONResponse(content={
            "success": True,
            "data": stats
        })
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
