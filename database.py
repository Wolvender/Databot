# database.py - Database layer for enterprise scalability
"""
Replace JSON file storage with SQLite (dev) or PostgreSQL (prod)
Supports audit logging, user management, and data retention
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import json
from pathlib import Path

class DatabaseManager:
    """Manages all database operations for DataBot."""
    
    def __init__(self, db_path: str = "databot.db"):
        """Initialize database connection."""
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Users table with proper password hashing
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Processed documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                file_hash TEXT UNIQUE NOT NULL,
                file_size INTEGER,
                uploaded_by TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                document_type TEXT,
                status TEXT,
                overall_confidence REAL,
                FOREIGN KEY (uploaded_by) REFERENCES users(username)
            )
        """)
        
        # Extracted records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                record_index INTEGER NOT NULL,
                extracted_data TEXT NOT NULL,  -- JSON blob
                confidence REAL,
                validation_issues TEXT,  -- JSON array
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)
        
        # Audit log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                action TEXT NOT NULL,
                entity_type TEXT,
                entity_id INTEGER,
                details TEXT,  -- JSON blob
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # API usage tracking (for billing)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                model TEXT NOT NULL,
                tokens_used INTEGER,
                cost_estimate REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
    
    def add_document(self, file_name: str, file_hash: str, file_size: int, 
                     uploaded_by: str, document_type: str, status: str, 
                     confidence: float) -> int:
        """Add a new document record."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO documents (file_name, file_hash, file_size, uploaded_by, 
                                   document_type, status, overall_confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (file_name, file_hash, file_size, uploaded_by, document_type, status, confidence))
        self.conn.commit()
        return cursor.lastrowid
    
    def add_record(self, document_id: int, record_index: int, 
                   extracted_data: dict, confidence: float, 
                   validation_issues: list) -> int:
        """Add an extracted record."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO records (document_id, record_index, extracted_data, 
                                confidence, validation_issues)
            VALUES (?, ?, ?, ?, ?)
        """, (document_id, record_index, json.dumps(extracted_data), 
              confidence, json.dumps(validation_issues)))
        self.conn.commit()
        return cursor.lastrowid
    
    def log_audit(self, user: str, action: str, entity_type: str = None, 
                  entity_id: int = None, details: dict = None, ip_address: str = None):
        """Log an audit event."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO audit_log (user, action, entity_type, entity_id, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user, action, entity_type, entity_id, 
              json.dumps(details) if details else None, ip_address))
        self.conn.commit()
    
    def get_all_records(self, user: str = None) -> List[Dict]:
        """Get all processed records, optionally filtered by user."""
        cursor = self.conn.cursor()
        
        if user:
            cursor.execute("""
                SELECT d.file_name, d.file_hash, d.uploaded_at, d.document_type, 
                       r.record_index, r.extracted_data, r.confidence, r.validation_issues
                FROM records r
                JOIN documents d ON r.document_id = d.id
                WHERE d.uploaded_by = ?
                ORDER BY d.uploaded_at DESC
            """, (user,))
        else:
            cursor.execute("""
                SELECT d.file_name, d.file_hash, d.uploaded_at, d.document_type, 
                       r.record_index, r.extracted_data, r.confidence, r.validation_issues
                FROM records r
                JOIN documents d ON r.document_id = d.id
                ORDER BY d.uploaded_at DESC
            """)
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "file": row["file_name"],
                "file_hash": row["file_hash"],
                "timestamp": row["uploaded_at"],
                "document_type": row["document_type"],
                "record_index": row["record_index"],
                "data": json.loads(row["extracted_data"]),
                "confidence": row["confidence"],
                "issues": json.loads(row["validation_issues"]) if row["validation_issues"] else []
            })
        return results
    
    def document_exists(self, file_hash: str) -> bool:
        """Check if document already processed."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM documents WHERE file_hash = ?", (file_hash,))
        return cursor.fetchone() is not None
    
    def delete_all_records(self, user: str):
        """Delete all records for a user."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM documents WHERE uploaded_by = ?", (user,))
        self.conn.commit()
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
