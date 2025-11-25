import os
import logging
from dataclasses import dataclass

@dataclass
class ServerConfig:
    HOST: str = 'localhost'
    PORT: int = 8080
    BUFFER_SIZE: int = 1024
    MAX_CONNECTIONS: int = 5

@dataclass
class DatabaseConfig:
    DB_PATH: str = 'data/sensor_data.db'
    BACKUP_DIR: str = 'data/backups'

@dataclass
class EmulatorConfig:
    SEND_INTERVAL: int = 10  # seconds
    NUM_DEVICES: int = 3     # number of emulated devices

@dataclass
class LogConfig:
    LOG_DIR: str = 'logs'
    LOG_FILE: str = 'sensor_system.log'
    LOG_LEVEL: str = 'INFO'

class Config:
    SERVER = ServerConfig()
    DATABASE = DatabaseConfig()
    EMULATOR = EmulatorConfig()
    LOGGING = LogConfig()
    
    @staticmethod
    def initialize_directories():
        """Create necessary directories"""
        os.makedirs('data/backups', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
    
    @staticmethod
    def setup_logging():
        """Setup logging with proper encoding for Windows"""
        logging.basicConfig(
            level=getattr(logging, Config.LOGGING.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()  # Only console output for Windows
            ]
        )