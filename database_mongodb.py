"""
MongoDB Database Manager for Credit Card Statement Parser
Compatible with Vercel serverless deployment
"""

import os
from datetime import datetime
from typing import List, Dict, Optional
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import asyncio

logger = logging.getLogger(__name__)

class MongoDBManager:
    """MongoDB database manager for parsed statements"""
    
    def __init__(self):
        # Get MongoDB connection string from environment or config
        self.connection_string = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
        self.database_name = os.getenv('MONGODB_DATABASE', 'credit_card_parser')
        self.collection_name = 'statements'
        
        # Configuration is now handled entirely through environment variables
        
        # Initialize MongoDB client
        self.client = None
        self.db = None
        self.collection = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            if self.connection_string.startswith('mongodb+srv://'):
                # MongoDB Atlas connection
                self.client = AsyncIOMotorClient(self.connection_string)
            else:
                # Local MongoDB connection
                self.client = AsyncIOMotorClient(self.connection_string)
            
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            
            # Create indexes for better performance
            await self.collection.create_index("filename")
            await self.collection.create_index("bank")
            await self.collection.create_index("parsed_at")
            await self.collection.create_index("file_hash", unique=True)
            
            logger.info("Connected to MongoDB successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def save_statement(self, statement_data: Dict) -> Optional[str]:
        """Save parsed statement to MongoDB"""
        try:
            if self.collection is None:
                await self.connect()
            
            # Generate file hash for duplicate detection
            import hashlib
            file_content = statement_data.get('filename', '') + str(datetime.now())
            file_hash = hashlib.md5(file_content.encode()).hexdigest()
            
            # Check if statement already exists
            existing = await self.collection.find_one({"file_hash": file_hash})
            if existing:
                logger.info(f"Statement already exists: {statement_data.get('filename')}")
                return str(existing['_id'])
            
            # Prepare document for insertion
            document = {
                'filename': statement_data.get('filename', ''),
                'bank': statement_data.get('bank', ''),
                'due_date': statement_data.get('due_date', ''),
                'last_4_digits': statement_data.get('last_4_digits', ''),
                'credit_limit': statement_data.get('credit_limit', ''),
                'available_credit': statement_data.get('available_credit', ''),
                'statement_date': statement_data.get('statement_date', ''),
                'parsed_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'file_hash': file_hash,
                'raw_data': statement_data
            }
            
            # Insert document
            result = await self.collection.insert_one(document)
            statement_id = str(result.inserted_id)
            
            logger.info(f"Statement saved with ID: {statement_id}")
            return statement_id
            
        except Exception as e:
            logger.error(f"Error saving statement: {e}")
            return None
    
    async def get_all_statements(self) -> List[Dict]:
        """Get all parsed statements"""
        try:
            if self.collection is None:
                await self.connect()
            
            cursor = self.collection.find({}).sort("parsed_at", -1)
            statements = []
            
            async for doc in cursor:
                # Convert ObjectId to string
                doc['id'] = str(doc['_id'])
                del doc['_id']  # Remove ObjectId from response
                
                # Convert datetime objects to ISO format strings
                if 'parsed_at' in doc and isinstance(doc['parsed_at'], datetime):
                    doc['parsed_at'] = doc['parsed_at'].isoformat()
                if 'updated_at' in doc and isinstance(doc['updated_at'], datetime):
                    doc['updated_at'] = doc['updated_at'].isoformat()
                
                statements.append(doc)
            
            return statements
            
        except Exception as e:
            logger.error(f"Error fetching statements: {e}")
            return []
    
    async def get_statement_by_id(self, statement_id: str) -> Optional[Dict]:
        """Get statement by ID"""
        try:
            if self.collection is None:
                await self.connect()
            
            from bson import ObjectId
            doc = await self.collection.find_one({"_id": ObjectId(statement_id)})
            
            if doc:
                doc['id'] = str(doc['_id'])
                del doc['_id']
                
                # Convert datetime objects to ISO format strings
                if 'parsed_at' in doc and isinstance(doc['parsed_at'], datetime):
                    doc['parsed_at'] = doc['parsed_at'].isoformat()
                if 'updated_at' in doc and isinstance(doc['updated_at'], datetime):
                    doc['updated_at'] = doc['updated_at'].isoformat()
                
                return doc
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching statement {statement_id}: {e}")
            return None
    
    async def update_statement(self, statement_id: str, updates: Dict) -> bool:
        """Update statement fields"""
        try:
            if self.collection is None:
                await self.connect()
            
            from bson import ObjectId
            
            # Prepare update document
            update_doc = {}
            for field, value in updates.items():
                if field in ['bank', 'due_date', 'last_4_digits', 'credit_limit', 
                            'available_credit', 'statement_date']:
                    update_doc[field] = value
            
            if not update_doc:
                return False
            
            # Add updated_at timestamp
            update_doc['updated_at'] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(statement_id)},
                {"$set": update_doc}
            )
            
            if result.modified_count > 0:
                logger.info(f"Statement {statement_id} updated successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating statement {statement_id}: {e}")
            return False
    
    async def delete_statement(self, statement_id: str) -> bool:
        """Delete statement by ID"""
        try:
            if self.collection is None:
                await self.connect()
            
            from bson import ObjectId
            result = await self.collection.delete_one({"_id": ObjectId(statement_id)})
            
            if result.deleted_count > 0:
                logger.info(f"Statement {statement_id} deleted successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting statement {statement_id}: {e}")
            return False
    
    async def search_statements(self, query: str) -> List[Dict]:
        """Search statements by filename or bank"""
        try:
            if self.collection is None:
                await self.connect()
            
            # Create search filter
            search_filter = {
                "$or": [
                    {"filename": {"$regex": query, "$options": "i"}},
                    {"bank": {"$regex": query, "$options": "i"}}
                ]
            }
            
            cursor = self.collection.find(search_filter).sort("parsed_at", -1)
            statements = []
            
            async for doc in cursor:
                doc['id'] = str(doc['_id'])
                del doc['_id']
                
                # Convert datetime objects to ISO format strings
                if 'parsed_at' in doc and isinstance(doc['parsed_at'], datetime):
                    doc['parsed_at'] = doc['parsed_at'].isoformat()
                if 'updated_at' in doc and isinstance(doc['updated_at'], datetime):
                    doc['updated_at'] = doc['updated_at'].isoformat()
                
                statements.append(doc)
            
            return statements
            
        except Exception as e:
            logger.error(f"Error searching statements: {e}")
            return []
    
    async def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            if self.collection is None:
                await self.connect()
            
            # Total statements
            total_statements = await self.collection.count_documents({})
            
            # Statements by bank
            pipeline = [
                {"$group": {"_id": "$bank", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            bank_stats = {}
            async for doc in self.collection.aggregate(pipeline):
                bank_stats[doc['_id']] = doc['count']
            
            # Recent activity (last 7 days)
            from datetime import timedelta
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_week = await self.collection.count_documents({
                "parsed_at": {"$gte": week_ago}
            })
            
            return {
                'total_statements': total_statements,
                'bank_distribution': bank_stats,
                'recent_week': recent_week
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}


# Global database manager instance
db_manager = MongoDBManager()

# Initialize connection on import
async def init_db():
    """Initialize database connection"""
    await db_manager.connect()

# Sync wrapper for non-async usage
class SyncMongoDBManager:
    """Synchronous wrapper for MongoDB operations"""
    
    def __init__(self):
        self.async_manager = MongoDBManager()
    
    def save_statement(self, statement_data: Dict) -> Optional[str]:
        """Sync wrapper for save_statement"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.async_manager.save_statement(statement_data))
        finally:
            loop.close()
    
    def get_all_statements(self) -> List[Dict]:
        """Sync wrapper for get_all_statements"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.async_manager.get_all_statements())
        finally:
            loop.close()
    
    def get_statement_by_id(self, statement_id: str) -> Optional[Dict]:
        """Sync wrapper for get_statement_by_id"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.async_manager.get_statement_by_id(statement_id))
        finally:
            loop.close()
    
    def update_statement(self, statement_id: str, updates: Dict) -> bool:
        """Sync wrapper for update_statement"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.async_manager.update_statement(statement_id, updates))
        finally:
            loop.close()
    
    def delete_statement(self, statement_id: str) -> bool:
        """Sync wrapper for delete_statement"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.async_manager.delete_statement(statement_id))
        finally:
            loop.close()
    
    def search_statements(self, query: str) -> List[Dict]:
        """Sync wrapper for search_statements"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.async_manager.search_statements(query))
        finally:
            loop.close()
    
    def get_statistics(self) -> Dict:
        """Sync wrapper for get_statistics"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.async_manager.get_statistics())
        finally:
            loop.close()
