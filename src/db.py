"""
Database schema and helper functions for the scraper system.
Uses SQLite for local storage with tables for sites, scrape runs, listing pages, and addresses.
"""

import sqlite3
import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class Database:
    """Manages SQLite database connections and operations."""
    
    def __init__(self, db_path: str = "data/scraper.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Connected to database: {self.db_path}")
    
    def create_tables(self):
        """Create all necessary tables if they don't exist."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                config_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manager_name TEXT NOT NULL,
                manager_domain TEXT NOT NULL,
                market_name TEXT,
                config_file TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(manager_domain)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scrape_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER NOT NULL,
                config_id INTEGER,
                status TEXT DEFAULT 'queued',
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                pages_visited INTEGER DEFAULT 0,
                listing_pages_found INTEGER DEFAULT 0,
                addresses_extracted INTEGER DEFAULT 0,
                current_page INTEGER DEFAULT 0,
                total_pages_estimate INTEGER DEFAULT 0,
                logs TEXT,
                error_message TEXT,
                config_snapshot TEXT,
                FOREIGN KEY (site_id) REFERENCES sites(id),
                FOREIGN KEY (config_id) REFERENCES configs(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS listing_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scrape_run_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                discovered_from_url TEXT,
                page_type TEXT,
                html_content TEXT,
                fetch_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_valid_listing BOOLEAN DEFAULT NULL,
                classification_method TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scrape_run_id) REFERENCES scrape_runs(id),
                UNIQUE(scrape_run_id, url)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS address_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_page_id INTEGER NOT NULL,
                address_raw TEXT,
                extraction_method TEXT,
                html_snippet TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (listing_page_id) REFERENCES listing_pages(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_page_id INTEGER NOT NULL,
                address_candidate_id INTEGER,
                address_raw TEXT,
                address_line1 TEXT,
                address_line2 TEXT,
                city TEXT,
                state TEXT,
                postal_code TEXT,
                country TEXT,
                inferred_market TEXT,
                inference_method TEXT,
                confidence_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (listing_page_id) REFERENCES listing_pages(id),
                FOREIGN KEY (address_candidate_id) REFERENCES address_candidates(id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_listing_pages_run 
            ON listing_pages(scrape_run_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_addresses_listing 
            ON addresses(listing_page_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scrape_runs_config 
            ON scrape_runs(config_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scrape_runs_status 
            ON scrape_runs(status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_configs_active 
            ON configs(is_active)
        """)
        
        self.conn.commit()
        logger.info("Database tables created/verified")
    
    def insert_site(self, manager_name: str, manager_domain: str,
                    market_name: str = None, config_file: str = None) -> int:
        """Insert or update a site record and return its ID."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sites (manager_name, manager_domain, market_name, config_file)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(manager_domain) DO UPDATE SET
                manager_name = excluded.manager_name,
                market_name = excluded.market_name,
                config_file = excluded.config_file,
                updated_at = CURRENT_TIMESTAMP
        """, (manager_name, manager_domain, market_name, config_file))
        self.conn.commit()

        # Get the site ID (works for both insert and update)
        cursor.execute("SELECT id FROM sites WHERE manager_domain = ?", (manager_domain,))
        return cursor.fetchone()[0]
    
    def get_site_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get site by domain."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sites WHERE manager_domain = ?", (domain,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def create_scrape_run(self, site_id: int, config_snapshot: str = None, config_id: int = None, status: str = 'queued') -> int:
        """Create a new scrape run."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO scrape_runs (site_id, config_id, config_snapshot, status)
            VALUES (?, ?, ?, ?)
        """, (site_id, config_id, config_snapshot, status))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_scrape_run(self, run_id: int, status: str = None, 
                         pages_visited: int = None, listing_pages_found: int = None,
                         addresses_extracted: int = None, error_message: str = None,
                         current_page: int = None, total_pages_estimate: int = None):
        """Update scrape run metrics."""
        updates = []
        params = []
        
        if status:
            updates.append("status = ?")
            params.append(status)
            if status in ['completed', 'failed', 'cancelled']:
                updates.append("end_time = CURRENT_TIMESTAMP")
        
        if pages_visited is not None:
            updates.append("pages_visited = ?")
            params.append(pages_visited)
        
        if listing_pages_found is not None:
            updates.append("listing_pages_found = ?")
            params.append(listing_pages_found)
        
        if addresses_extracted is not None:
            updates.append("addresses_extracted = ?")
            params.append(addresses_extracted)
        
        if error_message:
            updates.append("error_message = ?")
            params.append(error_message)
        
        if current_page is not None:
            updates.append("current_page = ?")
            params.append(current_page)
        
        if total_pages_estimate is not None:
            updates.append("total_pages_estimate = ?")
            params.append(total_pages_estimate)
        
        if updates:
            params.append(run_id)
            cursor = self.conn.cursor()
            cursor.execute(f"""
                UPDATE scrape_runs 
                SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            self.conn.commit()
    
    def insert_listing_page(self, scrape_run_id: int, url: str, 
                           discovered_from_url: str = None,
                           html_content: str = None) -> int:
        """Insert a listing page."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO listing_pages 
                (scrape_run_id, url, discovered_from_url, html_content)
                VALUES (?, ?, ?, ?)
            """, (scrape_run_id, url, discovered_from_url, html_content))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            cursor.execute("""
                SELECT id FROM listing_pages 
                WHERE scrape_run_id = ? AND url = ?
            """, (scrape_run_id, url))
            return cursor.fetchone()[0]
    
    def update_listing_page(self, page_id: int, is_valid_listing: bool = None,
                           classification_method: str = None, page_type: str = None):
        """Update listing page classification."""
        updates = []
        params = []
        
        if is_valid_listing is not None:
            updates.append("is_valid_listing = ?")
            params.append(is_valid_listing)
        
        if classification_method:
            updates.append("classification_method = ?")
            params.append(classification_method)
        
        if page_type:
            updates.append("page_type = ?")
            params.append(page_type)
        
        if updates:
            params.append(page_id)
            cursor = self.conn.cursor()
            cursor.execute(f"""
                UPDATE listing_pages 
                SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            self.conn.commit()
    
    def insert_address_candidate(self, listing_page_id: int, address_raw: str,
                                 extraction_method: str, html_snippet: str = None) -> int:
        """Insert an address candidate."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO address_candidates 
            (listing_page_id, address_raw, extraction_method, html_snippet)
            VALUES (?, ?, ?, ?)
        """, (listing_page_id, address_raw, extraction_method, html_snippet))
        self.conn.commit()
        return cursor.lastrowid
    
    def insert_address(self, listing_page_id: int, address_data: Dict[str, Any]) -> int:
        """Insert a normalized address."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO addresses (
                listing_page_id, address_candidate_id, address_raw,
                address_line1, address_line2, city, state, postal_code, country,
                inferred_market, inference_method, confidence_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            listing_page_id,
            address_data.get('address_candidate_id'),
            address_data.get('address_raw'),
            address_data.get('address_line1'),
            address_data.get('address_line2'),
            address_data.get('city'),
            address_data.get('state'),
            address_data.get('postal_code'),
            address_data.get('country', 'USA'),
            address_data.get('inferred_market'),
            address_data.get('inference_method'),
            address_data.get('confidence_score', 0.0)
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_listing_pages_for_run(self, scrape_run_id: int, 
                                  is_valid_listing: bool = None) -> List[Dict[str, Any]]:
        """Get all listing pages for a scrape run."""
        cursor = self.conn.cursor()
        if is_valid_listing is not None:
            cursor.execute("""
                SELECT * FROM listing_pages 
                WHERE scrape_run_id = ? AND is_valid_listing = ?
                ORDER BY id
            """, (scrape_run_id, is_valid_listing))
        else:
            cursor.execute("""
                SELECT * FROM listing_pages 
                WHERE scrape_run_id = ?
                ORDER BY id
            """, (scrape_run_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_address_candidates_for_page(self, listing_page_id: int) -> List[Dict[str, Any]]:
        """Get all address candidates for a listing page."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM address_candidates 
            WHERE listing_page_id = ?
            ORDER BY id
        """, (listing_page_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_scrape_run_results(self, scrape_run_id: int) -> List[Dict[str, Any]]:
        """Get complete results for a scrape run (for CSV export)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                s.manager_name,
                s.manager_domain,
                s.market_name,
                lp.url as listing_url,
                lp.discovered_from_url as source_page_url,
                lp.fetch_time as first_seen_at,
                lp.fetch_time as last_seen_at,
                a.address_line1,
                a.address_line2,
                a.city,
                a.state,
                a.postal_code,
                a.country,
                a.confidence_score,
                a.inference_method,
                a.inferred_market
            FROM listing_pages lp
            JOIN scrape_runs sr ON lp.scrape_run_id = sr.id
            JOIN sites s ON sr.site_id = s.id
            LEFT JOIN addresses a ON lp.id = a.listing_page_id
            WHERE sr.id = ?
            ORDER BY lp.id
        """, (scrape_run_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def insert_config(self, name: str, config_data: Dict[str, Any], is_active: bool = True) -> int:
        """Insert a new configuration."""
        cursor = self.conn.cursor()
        config_json = json.dumps(config_data)
        cursor.execute("""
            INSERT INTO configs (name, config_data, is_active)
            VALUES (?, ?, ?)
        """, (name, config_json, is_active))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_config(self, config_id: int = None, name: str = None) -> Optional[Dict[str, Any]]:
        """Get a configuration by ID or name."""
        cursor = self.conn.cursor()
        if config_id is not None:
            cursor.execute("SELECT * FROM configs WHERE id = ?", (config_id,))
        elif name is not None:
            cursor.execute("SELECT * FROM configs WHERE name = ?", (name,))
        else:
            return None
        
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result['config_data'] = json.loads(result['config_data'])
            return result
        return None
    
    def get_all_configs(self, is_active: bool = None) -> List[Dict[str, Any]]:
        """Get all configurations, optionally filtered by active status."""
        cursor = self.conn.cursor()
        if is_active is not None:
            cursor.execute("SELECT * FROM configs WHERE is_active = ? ORDER BY created_at DESC", (is_active,))
        else:
            cursor.execute("SELECT * FROM configs ORDER BY created_at DESC")
        
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result['config_data'] = json.loads(result['config_data'])
            results.append(result)
        return results
    
    def update_config(self, config_id: int, name: str = None, config_data: Dict[str, Any] = None, is_active: bool = None) -> bool:
        """Update an existing configuration."""
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        
        if config_data is not None:
            updates.append("config_data = ?")
            params.append(json.dumps(config_data))
        
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(config_id)
            cursor = self.conn.cursor()
            cursor.execute(f"""
                UPDATE configs 
                SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            self.conn.commit()
            return cursor.rowcount > 0
        return False
    
    def delete_config(self, config_id: int) -> bool:
        """Delete a configuration."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM configs WHERE id = ?", (config_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_scrape_runs_filtered(self, config_id: int = None, status: str = None, 
                                 start_date: str = None, end_date: str = None,
                                 limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get scrape runs with optional filters."""
        cursor = self.conn.cursor()
        
        where_clauses = []
        params = []
        
        if config_id is not None:
            where_clauses.append("config_id = ?")
            params.append(config_id)
        
        if status is not None:
            where_clauses.append("status = ?")
            params.append(status)
        
        if start_date is not None:
            where_clauses.append("start_time >= ?")
            params.append(start_date)
        
        if end_date is not None:
            where_clauses.append("start_time <= ?")
            params.append(end_date)
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        params.extend([limit, offset])
        
        cursor.execute(f"""
            SELECT * FROM scrape_runs 
            {where_sql}
            ORDER BY start_time DESC
            LIMIT ? OFFSET ?
        """, params)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def append_run_log(self, run_id: int, log_message: str):
        """Append a log message to a scrape run."""
        cursor = self.conn.cursor()
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {log_message}\n"
        
        cursor.execute("""
            UPDATE scrape_runs 
            SET logs = COALESCE(logs, '') || ?
            WHERE id = ?
        """, (log_entry, run_id))
        self.conn.commit()
    
    def update_run_progress(self, run_id: int, current_page: int, total_pages_estimate: int = None):
        """Update the progress of a scrape run."""
        cursor = self.conn.cursor()
        if total_pages_estimate is not None:
            cursor.execute("""
                UPDATE scrape_runs 
                SET current_page = ?, total_pages_estimate = ?
                WHERE id = ?
            """, (current_page, total_pages_estimate, run_id))
        else:
            cursor.execute("""
                UPDATE scrape_runs 
                SET current_page = ?
                WHERE id = ?
            """, (current_page, run_id))
        self.conn.commit()
    
    def get_run_statistics(self, config_id: int = None, days: int = 30) -> Dict[str, Any]:
        """Get statistics about scrape runs."""
        cursor = self.conn.cursor()
        
        where_clause = ""
        params = []
        
        if config_id is not None:
            where_clause = "WHERE config_id = ? AND "
            params.append(config_id)
        else:
            where_clause = "WHERE "
        
        params.append(days)
        
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_runs,
                COALESCE(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END), 0) as completed,
                COALESCE(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), 0) as failed,
                COALESCE(SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END), 0) as running,
                COALESCE(SUM(CASE WHEN status = 'queued' THEN 1 ELSE 0 END), 0) as queued,
                COALESCE(SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END), 0) as cancelled,
                COALESCE(SUM(pages_visited), 0) as total_pages_visited,
                COALESCE(SUM(listing_pages_found), 0) as total_listing_pages,
                COALESCE(SUM(addresses_extracted), 0) as total_addresses_extracted,
                AVG(CASE WHEN status = 'completed' AND end_time IS NOT NULL 
                    THEN (julianday(end_time) - julianday(start_time)) * 86400 
                    ELSE NULL END) as avg_duration_seconds
            FROM scrape_runs
            {where_clause}start_time >= datetime('now', '-' || ? || ' days')
        """, params)
        
        row = cursor.fetchone()
        return dict(row) if row else {}
    
    def get_scrape_run(self, run_id: int) -> Optional[Dict[str, Any]]:
        """Get a single scrape run by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM scrape_runs WHERE id = ?", (run_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
