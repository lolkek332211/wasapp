import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database structure"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Sensor data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    temperature REAL,
                    humidity REAL,
                    light_level INTEGER,
                    voltage REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    received_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Device statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY,
                    device_type TEXT,
                    location TEXT,
                    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_records INTEGER DEFAULT 0
                )
            ''')
            
            # Indexes for optimization
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sensor_device_id 
                ON sensor_data(device_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sensor_timestamp 
                ON sensor_data(timestamp)
            ''')
            
            conn.commit()
            self.logger.info("Database initialized successfully")
            
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization error: {e}")
            raise
        finally:
            conn.close()
    
    def save_sensor_data(self, data: Dict) -> bool:
        """Save sensor data to database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Save sensor data
            cursor.execute('''
                INSERT INTO sensor_data 
                (device_id, temperature, humidity, light_level, voltage, received_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data['device_id'],
                data.get('temperature'),
                data.get('humidity'),
                data.get('light_level'),
                data.get('voltage'),
                datetime.now().isoformat()
            ))
            
            # Update device information
            cursor.execute('''
                INSERT OR REPLACE INTO devices 
                (device_id, device_type, location, last_seen, total_records)
                VALUES (?, ?, ?, ?, COALESCE(
                    (SELECT total_records + 1 FROM devices WHERE device_id = ?), 1
                ))
            ''', (
                data['device_id'],
                data.get('device_type', 'sensor_module'),
                data.get('location', 'unknown'),
                datetime.now(),
                data['device_id']
            ))
            
            conn.commit()
            self.logger.info(f"Data saved for device: {data['device_id']}")
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"Error saving data: {e}")
            return False
        finally:
            conn.close()
    
    def get_recent_data(self, device_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get recent records from database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if device_id:
                cursor.execute('''
                    SELECT * FROM sensor_data 
                    WHERE device_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (device_id, limit))
            else:
                cursor.execute('''
                    SELECT * FROM sensor_data 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
            
            results = [dict(row) for row in cursor.fetchall()]
            return results
            
        except sqlite3.Error as e:
            self.logger.error(f"Error reading data: {e}")
            return []
        finally:
            conn.close()
    
    def get_device_statistics(self) -> List[Dict]:
        """Get device statistics"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    device_id,
                    COUNT(*) as record_count,
                    MIN(timestamp) as first_record,
                    MAX(timestamp) as last_record,
                    AVG(temperature) as avg_temperature,
                    AVG(humidity) as avg_humidity,
                    AVG(light_level) as avg_light_level
                FROM sensor_data 
                GROUP BY device_id
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            self.logger.error(f"Error getting statistics: {e}")
            return []
        finally:
            conn.close()

    def export_to_csv(self, filename: str = 'sensor_data_export.csv'):
        """Export data to CSV file"""
        try:
            import csv
            
            data = self.get_recent_data(limit=1000)  # Last 1000 records
            
            if not data:
                self.logger.warning("No data to export")
                return False
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
            
            self.logger.info(f"Data exported to {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Export error: {e}")
            return False