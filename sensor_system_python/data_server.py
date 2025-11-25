import socket
import json
import logging
import threading
from datetime import datetime
from config import Config
from database import DatabaseManager

class SensorDataServer:
    def __init__(self, config: Config):
        self.config = config
        self.db_manager = DatabaseManager(config.DATABASE.DB_PATH)
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.server_socket = None
        
    def setup_logging(self):
        """Setup logging system"""
        # Use basic console logging to avoid encoding issues
        logging.basicConfig(
            level=getattr(logging, self.config.LOGGING.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
    
    def parse_request(self, request_data: str) -> dict:
        """Parse incoming request"""
        try:
            self.logger.debug(f"Received request: {request_data[:200]}...")
            
            # Try to parse as JSON
            data = json.loads(request_data)
            
            # Validate required fields
            if 'device_id' not in data:
                self.logger.warning("Missing device_id in request")
                return None
            
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Request processing error: {e}")
            return None
    
    def create_response(self, status: str, message: str, data: dict = None) -> str:
        """Create JSON response"""
        response = {
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if data:
            response.update(data)
        
        return json.dumps(response)
    
    def handle_client(self, client_socket: socket.socket, address: tuple):
        """Handle client connection"""
        client_ip, client_port = address
        self.logger.info(f"New connection: {client_ip}:{client_port}")
        
        try:
            # Receive data
            request_data = client_socket.recv(self.config.SERVER.BUFFER_SIZE).decode('utf-8')
            
            if not request_data:
                self.logger.warning("Empty request")
                return
            
            # Parse data
            sensor_data = self.parse_request(request_data)
            
            if not sensor_data:
                response = self.create_response("error", "Invalid data format")
                client_socket.send(response.encode('utf-8'))
                return
            
            # Save to database
            if self.db_manager.save_sensor_data(sensor_data):
                response = self.create_response(
                    "success", 
                    "Data received and saved successfully",
                    {"device_id": sensor_data['device_id']}
                )
                self.logger.info(f"Data from {sensor_data['device_id']} saved")
            else:
                response = self.create_response("error", "Error saving to database")
                self.logger.error(f"Error saving data from {sensor_data['device_id']}")
            
            # Send response
            client_socket.send(response.encode('utf-8'))
            
        except Exception as e:
            self.logger.error(f"Error handling client {client_ip}:{client_port}: {e}")
            try:
                error_response = self.create_response("error", "Internal server error")
                client_socket.send(error_response.encode('utf-8'))
            except:
                pass
        finally:
            client_socket.close()
            self.logger.info(f"Connection closed: {client_ip}:{client_port}")
    
    def start_server(self):
        """Start TCP server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.config.SERVER.HOST, self.config.SERVER.PORT))
            self.server_socket.listen(self.config.SERVER.MAX_CONNECTIONS)
            
            self.is_running = True
            self.logger.info(f"Data server started on {self.config.SERVER.HOST}:{self.config.SERVER.PORT}")
            self.logger.info("Waiting for connections...")
            
            while self.is_running:
                try:
                    client_socket, address = self.server_socket.accept()
                    
                    # Handle each client in separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.is_running:
                        self.logger.error(f"Accept error: {e}")
                    continue
                    
        except KeyboardInterrupt:
            self.logger.info("Server stopped by user")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
            self.logger.info("Server shutdown complete")
    
    def stop_server(self):
        """Stop server"""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()

def main():
    """Main server startup function"""
    config = Config()
    config.initialize_directories()
    config.setup_logging()
    
    server = SensorDataServer(config)
    
    try:
        server.start_server()
    except Exception as e:
        logging.error(f"Failed to start server: {e} - data_server.py:167")

if __name__ == "__main__":
    main()