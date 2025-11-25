# web_interface.py - Веб-интерфейс для мониторинга данных
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import sqlite3
import json
from datetime import datetime, timedelta
import threading
import time
from config import Config
import logging

class WebInterface:
    def __init__(self, config: Config):
        self.config = config
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'sensor_system_secret_key'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.setup_routes()
        self.setup_logging()
        
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(level=logging.INFO)
        
    def setup_routes(self):
        """Настройка маршрутов Flask"""
        
        @self.app.route('/')
        def index():
            """Главная страница"""
            return render_template('index.html')
        
        @self.app.route('/api/devices')
        def get_devices():
            """API для получения списка устройств"""
            try:
                devices = self.get_devices_from_db()
                return jsonify({
                    'status': 'success',
                    'devices': devices,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/data/recent')
        def get_recent_data():
            """API для получения последних данных"""
            try:
                device_id = request.args.get('device_id')
                limit = int(request.args.get('limit', 50))
                
                data = self.get_recent_sensor_data(device_id, limit)
                
                return jsonify({
                    'status': 'success',
                    'data': data,
                    'count': len(data)
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/statistics')
        def get_statistics():
            """API для получения статистики"""
            try:
                stats = self.get_system_statistics()
                return jsonify({
                    'status': 'success',
                    'statistics': stats
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/data/export')
        def export_data():
            """API для экспорта данных"""
            try:
                format_type = request.args.get('format', 'json')
                data = self.get_recent_sensor_data(limit=1000)
                
                if format_type == 'csv':
                    return self.export_to_csv(data)
                else:
                    return jsonify({
                        'status': 'success',
                        'data': data,
                        'exported_at': datetime.now().isoformat()
                    })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.socketio.on('connect')
        def handle_connect():
            """Обработчик подключения WebSocket"""
            logging.info('WebSocket client connected - web_interface.py:108')
            self.socketio.emit('connected', {'message': 'Connected to sensor data stream'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Обработчик отключения WebSocket"""
            logging.info('WebSocket client disconnected - web_interface.py:114')
    
    def get_db_connection(self):
        """Создание подключения к базе данных"""
        conn = sqlite3.connect(self.config.DATABASE.DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_devices_from_db(self):
        """Получение списка устройств из базы данных"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    device_id,
                    device_type,
                    location,
                    first_seen,
                    last_seen,
                    total_records
                FROM devices 
                ORDER BY last_seen DESC
            ''')
            
            devices = []
            for row in cursor.fetchall():
                devices.append({
                    'device_id': row['device_id'],
                    'device_type': row['device_type'],
                    'location': row['location'],
                    'first_seen': row['first_seen'],
                    'last_seen': row['last_seen'],
                    'total_records': row['total_records']
                })
            
            conn.close()
            return devices
            
        except Exception as e:
            logging.error(f"Error getting devices: {e}")
            return []
    
    def get_recent_sensor_data(self, device_id=None, limit=50):
        """Получение последних данных сенсоров"""
        try:
            conn = self.get_db_connection()
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
            
            data = []
            for row in cursor.fetchall():
                data.append({
                    'id': row['id'],
                    'device_id': row['device_id'],
                    'temperature': row['temperature'],
                    'humidity': row['humidity'],
                    'light_level': row['light_level'],
                    'voltage': row['voltage'],
                    'timestamp': row['timestamp'],
                    'received_at': row['received_at']
                })
            
            conn.close()
            return data
            
        except Exception as e:
            logging.error(f"Error getting sensor data: {e}")
            return []
    
    def get_system_statistics(self):
        """Получение системной статистики"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Общая статистика
            cursor.execute('SELECT COUNT(*) as total_records FROM sensor_data')
            total_records = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT device_id) as device_count FROM sensor_data')
            device_count = cursor.fetchone()[0]
            
            # Статистика по устройствам
            cursor.execute('''
                SELECT 
                    device_id,
                    COUNT(*) as record_count,
                    AVG(temperature) as avg_temperature,
                    AVG(humidity) as avg_humidity,
                    AVG(light_level) as avg_light,
                    MAX(timestamp) as last_update
                FROM sensor_data 
                GROUP BY device_id
            ''')
            
            device_stats = []
            for row in cursor.fetchall():
                device_stats.append({
                    'device_id': row['device_id'],
                    'record_count': row['record_count'],
                    'avg_temperature': round(row['avg_temperature'], 2) if row['avg_temperature'] else None,
                    'avg_humidity': round(row['avg_humidity'], 2) if row['avg_humidity'] else None,
                    'avg_light': round(row['avg_light'], 2) if row['avg_light'] else None,
                    'last_update': row['last_update']
                })
            
            conn.close()
            
            return {
                'total_records': total_records,
                'device_count': device_count,
                'device_statistics': device_stats,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error getting statistics: {e}")
            return {}
    
    def export_to_csv(self, data):
        """Экспорт данных в CSV формат"""
        import csv
        from io import StringIO
        
        if not data:
            return "No data to export", 400
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow(['ID', 'Device ID', 'Temperature', 'Humidity', 'Light Level', 'Voltage', 'Timestamp'])
        
        # Данные
        for row in data:
            writer.writerow([
                row['id'],
                row['device_id'],
                row['temperature'],
                row['humidity'],
                row['light_level'],
                row['voltage'],
                row['timestamp']
            ])
        
        response = self.app.response_class(
            response=output.getvalue(),
            status=200,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=sensor_data_export.csv'}
        )
        
        return response
    
    def start_realtime_updates(self):
        """Запуск потока для обновления данных в реальном времени"""
        def update_loop():
            while True:
                try:
                    # Получаем последние данные
                    recent_data = self.get_recent_sensor_data(limit=10)
                    
                    # Отправляем через WebSocket
                    self.socketio.emit('data_update', {
                        'data': recent_data,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Обновляем статистику каждые 10 секунд
                    stats = self.get_system_statistics()
                    self.socketio.emit('stats_update', {
                        'statistics': stats,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    logging.error(f"Error in update loop: {e}")
                
                time.sleep(5)  # Обновление каждые 5 секунд
        
        # Запускаем поток обновлений
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
    
    def run(self, host='localhost', port=5000, debug=False):
        """Запуск веб-сервера"""
        self.start_realtime_updates()
        logging.info(f"Starting web interface on http://{host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)

def main():
    """Основная функция запуска веб-интерфейса"""
    config = Config()
    config.initialize_directories()
    
    web_interface = WebInterface(config)
    web_interface.run(host='localhost', port=5000, debug=True)

if __name__ == "__main__":
    main()