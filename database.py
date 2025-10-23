"""
SQLite Database Models for Credit Card Statement Parser
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database operations for parsed statements"""
    
    def __init__(self, db_path: str = "credit_card_statements.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create statements table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS statements (
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
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_filename ON statements(filename)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_bank ON statements(bank)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_parsed_at ON statements(parsed_at)')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def save_statement(self, statement_data: Dict) -> int:
        """Save parsed statement to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Generate file hash for duplicate detection
                import hashlib
                file_content = statement_data.get('filename', '') + str(datetime.now())
                file_hash = hashlib.md5(file_content.encode()).hexdigest()
                
                # Check if statement already exists
                cursor.execute('SELECT id FROM statements WHERE file_hash = ?', (file_hash,))
                existing = cursor.fetchone()
                
                if existing:
                    logger.info(f"Statement already exists: {statement_data.get('filename')}")
                    return existing[0]
                
                # Insert new statement
                cursor.execute('''
                    INSERT INTO statements (
                        filename, bank, due_date, last_4_digits, 
                        credit_limit, available_credit, statement_date, 
                        file_hash, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    statement_data.get('filename', ''),
                    statement_data.get('bank', ''),
                    statement_data.get('due_date', ''),
                    statement_data.get('last_4_digits', ''),
                    statement_data.get('credit_limit', ''),
                    statement_data.get('available_credit', ''),
                    statement_data.get('statement_date', ''),
                    file_hash,
                    json.dumps(statement_data)
                ))
                
                statement_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Statement saved with ID: {statement_id}")
                return statement_id
                
        except Exception as e:
            logger.error(f"Error saving statement: {e}")
            raise
    
    def get_all_statements(self) -> List[Dict]:
        """Get all parsed statements"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, filename, bank, due_date, last_4_digits, 
                           credit_limit, available_credit, statement_date, 
                           parsed_at, updated_at
                    FROM statements 
                    ORDER BY parsed_at DESC
                ''')
                
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                
                statements = []
                for row in rows:
                    statement = dict(zip(columns, row))
                    statements.append(statement)
                
                return statements
                
        except Exception as e:
            logger.error(f"Error fetching statements: {e}")
            return []
    
    def get_statement_by_id(self, statement_id: int) -> Optional[Dict]:
        """Get statement by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, filename, bank, due_date, last_4_digits, 
                           credit_limit, available_credit, statement_date, 
                           parsed_at, updated_at, raw_data
                    FROM statements 
                    WHERE id = ?
                ''', (statement_id,))
                
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
                
        except Exception as e:
            logger.error(f"Error fetching statement {statement_id}: {e}")
            return None
    
    def update_statement(self, statement_id: int, updates: Dict) -> bool:
        """Update statement fields"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build update query dynamically
                set_clauses = []
                values = []
                
                for field, value in updates.items():
                    if field in ['bank', 'due_date', 'last_4_digits', 'credit_limit', 
                                'available_credit', 'statement_date']:
                        set_clauses.append(f"{field} = ?")
                        values.append(value)
                
                if not set_clauses:
                    return False
                
                # Add updated_at timestamp
                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                values.append(statement_id)
                
                query = f"UPDATE statements SET {', '.join(set_clauses)} WHERE id = ?"
                cursor.execute(query, values)
                
                conn.commit()
                logger.info(f"Statement {statement_id} updated successfully")
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating statement {statement_id}: {e}")
            return False
    
    def delete_statement(self, statement_id: int) -> bool:
        """Delete statement by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM statements WHERE id = ?', (statement_id,))
                conn.commit()
                
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Statement {statement_id} deleted successfully")
                return deleted
                
        except Exception as e:
            logger.error(f"Error deleting statement {statement_id}: {e}")
            return False
    
    def search_statements(self, query: str) -> List[Dict]:
        """Search statements by filename or bank"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, filename, bank, due_date, last_4_digits, 
                           credit_limit, available_credit, statement_date, 
                           parsed_at, updated_at
                    FROM statements 
                    WHERE filename LIKE ? OR bank LIKE ?
                    ORDER BY parsed_at DESC
                ''', (f'%{query}%', f'%{query}%'))
                
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                
                statements = []
                for row in rows:
                    statement = dict(zip(columns, row))
                    statements.append(statement)
                
                return statements
                
        except Exception as e:
            logger.error(f"Error searching statements: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total statements
                cursor.execute('SELECT COUNT(*) FROM statements')
                total_statements = cursor.fetchone()[0]
                
                # Statements by bank
                cursor.execute('''
                    SELECT bank, COUNT(*) as count 
                    FROM statements 
                    GROUP BY bank 
                    ORDER BY count DESC
                ''')
                bank_stats = dict(cursor.fetchall())
                
                # Recent activity
                cursor.execute('''
                    SELECT COUNT(*) FROM statements 
                    WHERE parsed_at >= datetime('now', '-7 days')
                ''')
                recent_week = cursor.fetchone()[0]
                
                return {
                    'total_statements': total_statements,
                    'bank_distribution': bank_stats,
                    'recent_week': recent_week
                }
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
