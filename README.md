🚀 Пошаговая инструкция: Эмуляция системы сбора данных на Python + VS Code
📋 Полное решение с эмуляцией микроконтроллера на Python
🎯 Цель проекта
Создать полную систему сбора данных с использованием только Python и VS Code, где:

Микроконтроллер эмулируется Python-скриптом

Сервер принимает данные и сохраняет в SQLite

Все работает на одном компьютере

⏱️ Общее время выполнения: 45 минут
🛠️ ЭТАП 1: ПОДГОТОВКА СРЕДЫ (10 минут)
Шаг 1.1: Установка и настройка VS Code
Действия:

Установите VS Code:

Скачайте с https://code.visualstudio.com

Установите с настройками по умолчанию

Установите расширения Python:

Откройте Extensions (Ctrl+Shift+X)

Найдите и установите:

Python by Microsoft

Python Debugger

SQLite

Проверьте установку Python:

Откройте терминал в VS Code (Ctrl+`)

Выполните:

bash
python --version
# Должен показать Python 3.8+
Шаг 1.2: Создание структуры проекта
Действия:

Создайте папку проекта:

bash
mkdir sensor_system_python
cd sensor_system_python
code .
Создайте структуру файлов в VS Code:

text
sensor_system_python/
├── 📁 data/
├── 📁 logs/
├── 📄 sensor_emulator.py    # Эмулятор микроконтроллера
├── 📄 data_server.py       # Сервер приема данных
├── 📄 database.py          # Работа с SQLite
├── 📄 config.py           # Конфигурация
└── 📄 requirements.txt    # Зависимости
💻 ЭТАП 2: СОЗДАНИЕ СЕРВЕРНОЙ ЧАСТИ (20 минут)
Шаг 2.1: Создание конфигурации (config.py)
Действия: Создайте файл config.py:

python
import os
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
    SEND_INTERVAL: int = 10  # секунды
    NUM_DEVICES: int = 3     # количество эмулируемых устройств

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
        """Создание необходимых директорий"""
        os.makedirs('data/backups', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
Шаг 2.2: Создание модуля базы данных (database.py)
Действия: Создайте файл database.py:

python
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
        """Создание подключения к базе данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Инициализация структуры базы данных"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Таблица сенсорных данных
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
            
            # Таблица для статистики устройств
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
            
            # Индексы для оптимизации запросов
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sensor_device_id 
                ON sensor_data(device_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sensor_timestamp 
                ON sensor_data(timestamp)
            ''')
            
            conn.commit()
            self.logger.info("✅ База данных инициализирована успешно")
            
        except sqlite3.Error as e:
            self.logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
        finally:
            conn.close()
    
    def save_sensor_data(self, data: Dict) -> bool:
        """Сохранение данных сенсора в базу данных"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Сохранение данных сенсора
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
            
            # Обновление информации об устройстве
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
            self.logger.info(f"✅ Данные сохранены для устройства: {data['device_id']}")
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"❌ Ошибка сохранения данных: {e}")
            return False
        finally:
            conn.close()
    
    def get_recent_data(self, device_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Получение последних записей из базы данных"""
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
            self.logger.error(f"❌ Ошибка чтения данных: {e}")
            return []
        finally:
            conn.close()
    
    def get_device_statistics(self) -> List[Dict]:
        """Получение статистики по устройствам"""
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
            self.logger.error(f"❌ Ошибка получения статистики: {e}")
            return []
        finally:
            conn.close()

    def export_to_csv(self, filename: str = 'sensor_data_export.csv'):
        """Экспорт данных в CSV файл"""
        try:
            import csv
            
            data = self.get_recent_data(limit=1000)  # Последние 1000 записей
            
            if not data:
                self.logger.warning("⚠️ Нет данных для экспорта")
                return False
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
            
            self.logger.info(f"✅ Данные экспортированы в {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка экспорта: {e}")
            return False
Шаг 2.3: Создание сервера данных (data_server.py)
Действия: Создайте файл data_server.py:

python
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
        """Настройка системы логирования"""
        logging.basicConfig(
            level=getattr(logging, self.config.LOGGING.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"{self.config.LOGGING.LOG_DIR}/{self.config.LOGGING.LOG_FILE}"),
                logging.StreamHandler()
            ]
        )
    
    def parse_request(self, request_data: str) -> dict:
        """Парсинг входящего запроса"""
        try:
            self.logger.debug(f"📨 Получен запрос: {request_data[:200]}...")
            
            # Пытаемся распарсить как JSON
            data = json.loads(request_data)
            
            # Валидация обязательных полей
            if 'device_id' not in data:
                self.logger.warning("❌ Отсутствует device_id в запросе")
                return None
            
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Ошибка парсинга JSON: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Ошибка обработки запроса: {e}")
            return None
    
    def create_response(self, status: str, message: str, data: dict = None) -> str:
        """Создание JSON ответа"""
        response = {
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if data:
            response.update(data)
        
        return json.dumps(response)
    
    def handle_client(self, client_socket: socket.socket, address: tuple):
        """Обработка подключения клиента"""
        client_ip, client_port = address
        self.logger.info(f"🔗 Новое подключение: {client_ip}:{client_port}")
        
        try:
            # Получение данных
            request_data = client_socket.recv(self.config.SERVER.BUFFER_SIZE).decode('utf-8')
            
            if not request_data:
                self.logger.warning("⚠️ Пустой запрос")
                return
            
            # Парсинг данных
            sensor_data = self.parse_request(request_data)
            
            if not sensor_data:
                response = self.create_response("error", "Неверный формат данных")
                client_socket.send(response.encode('utf-8'))
                return
            
            # Сохранение в базу данных
            if self.db_manager.save_sensor_data(sensor_data):
                response = self.create_response(
                    "success", 
                    "Данные успешно получены и сохранены",
                    {"device_id": sensor_data['device_id']}
                )
                self.logger.info(f"✅ Данные от {sensor_data['device_id']} сохранены")
            else:
                response = self.create_response("error", "Ошибка сохранения в базу данных")
                self.logger.error(f"❌ Ошибка сохранения данных от {sensor_data['device_id']}")
            
            # Отправка ответа
            client_socket.send(response.encode('utf-8'))
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка обработки клиента {client_ip}:{client_port}: {e}")
            try:
                error_response = self.create_response("error", "Внутренняя ошибка сервера")
                client_socket.send(error_response.encode('utf-8'))
            except:
                pass
        finally:
            client_socket.close()
            self.logger.info(f"🔒 Подключение закрыто: {client_ip}:{client_port}")
    
    def start_server(self):
        """Запуск TCP сервера"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.config.SERVER.HOST, self.config.SERVER.PORT))
            self.server_socket.listen(self.config.SERVER.MAX_CONNECTIONS)
            
            self.is_running = True
            self.logger.info(f"🚀 Сервер данных запущен на {self.config.SERVER.HOST}:{self.config.SERVER.PORT}")
            self.logger.info("⏳ Ожидание подключений...")
            
            while self.is_running:
                try:
                    client_socket, address = self.server_socket.accept()
                    
                    # Обработка каждого клиента в отдельном потоке
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
                        self.logger.error(f"❌ Ошибка accept: {e}")
                    continue
                    
        except KeyboardInterrupt:
            self.logger.info("🛑 Сервер остановлен пользователем")
        except Exception as e:
            self.logger.error(f"❌ Ошибка сервера: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
            self.logger.info("✅ Сервер завершил работу")
    
    def stop_server(self):
        """Остановка сервера"""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()

def main():
    """Основная функция запуска сервера"""
    config = Config()
    config.initialize_directories()
    
    server = SensorDataServer(config)
    
    try:
        server.start_server()
    except Exception as e:
        logging.error(f"❌ Не удалось запустить сервер: {e}")

if __name__ == "__main__":
    main()
Шаг 2.4: Создание эмулятора микроконтроллера (sensor_emulator.py)
Действия: Создайте файл sensor_emulator.py:

python
import socket
import json
import time
import random
from datetime import datetime
from config import Config

class SensorEmulator:
    def __init__(self, config: Config):
        self.config = config
        self.devices = self.generate_devices()
        
    def generate_devices(self):
        """Генерация списка эмулируемых устройств"""
        devices = []
        locations = ["цех_1", "цех_2", "склад", "офис", "лаборатория"]
        
        for i in range(self.config.EMULATOR.NUM_DEVICES):
            devices.append({
                "device_id": f"SENSOR_{i+1:03d}",
                "device_type": "temperature_humidity_sensor",
                "location": random.choice(locations),
                "temperature_range": (18.0, 28.0),
                "humidity_range": (40.0, 80.0),
                "light_range": (100, 1000),
                "voltage_range": (3.2, 4.2)
            })
        
        print(f"✅ Создано {len(devices)} виртуальных устройств")
        for device in devices:
            print(f"   - {device['device_id']} ({device['location']})")
        
        return devices
    
    def generate_sensor_data(self, device):
        """Генерация реалистичных данных сенсоров"""
        # Температура с небольшими случайными колебаниями
        temp_base = random.uniform(*device['temperature_range'])
        temperature = round(temp_base + random.uniform(-0.5, 0.5), 2)
        
        # Влажность с корреляцией с температурой
        humidity_base = random.uniform(*device['humidity_range'])
        humidity = round(humidity_base + random.uniform(-2, 2), 2)
        
        # Уровень освещенности (может быть None для некоторых датчиков)
        light_level = random.randint(*device['light_range'])
        
        # Напряжение батареи с постепенным уменьшением
        voltage = round(random.uniform(*device['voltage_range']), 2)
        
        return {
            "device_id": device["device_id"],
            "device_type": device["device_type"],
            "location": device["location"],
            "temperature": temperature,
            "humidity": humidity,
            "light_level": light_level,
            "voltage": voltage,
            "timestamp": datetime.now().isoformat()
        }
    
    def send_data_to_server(self, data):
        """Отправка данных на сервер"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            sock.connect((self.config.SERVER.HOST, self.config.SERVER.PORT))
            
            # Отправка JSON данных
            json_data = json.dumps(data)
            sock.send(json_data.encode('utf-8'))
            
            # Получение ответа
            response = sock.recv(1024).decode('utf-8')
            sock.close()
            
            response_data = json.loads(response)
            return response_data.get('status') == 'success'
            
        except Exception as e:
            print(f"❌ Ошибка отправки данных: {e}")
            return False
    
    def start_emulation(self):
        """Запуск эмуляции работы микроконтроллеров"""
        print("🚀 Запуск эмуляции микроконтроллеров...")
        print(f"📡 Отправка данных на сервер {self.config.SERVER.HOST}:{self.config.SERVER.PORT}")
        print(f"⏰ Интервал отправки: {self.config.EMULATOR.SEND_INTERVAL} секунд")
        print("Нажмите Ctrl+C для остановки\n")
        
        try:
            while True:
                for device in self.devices:
                    # Генерация данных
                    sensor_data = self.generate_sensor_data(device)
                    
                    # Отправка на сервер
                    success = self.send_data_to_server(sensor_data)
                    
                    if success:
                        print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] {device['device_id']}: "
                              f"Температура: {sensor_data['temperature']}°C, "
                              f"Влажность: {sensor_data['humidity']}%, "
                              f"Свет: {sensor_data['light_level']}")
                    else:
                        print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] {device['device_id']}: "
                              f"Ошибка отправки данных")
                
                # Ожидание перед следующей отправкой
                time.sleep(self.config.EMULATOR.SEND_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n🛑 Эмуляция остановлена пользователем")

def main():
    """Основная функция запуска эмулятора"""
    config = Config()
    emulator = SensorEmulator(config)
    emulator.start_emulation()

if __name__ == "__main__":
    main()
Шаг 2.5: Создание файла зависимостей (requirements.txt)
Действия: Создайте файл requirements.txt:

txt
# Все необходимые библиотеки встроены в Python
# Дополнительные зависимости не требуются
🚀 ЭТАП 3: ЗАПУСК И ТЕСТИРОВАНИЕ СИСТЕМЫ (15 минут)
Шаг 3.1: Запуск системы
Действия:

Запустите сервер (в первом терминале VS Code):

bash
python data_server.py
Ожидаемый результат:

text
✅ База данных инициализирована успешно
🚀 Сервер данных запущен на localhost:8080
⏳ Ожидание подключений...
Запустите эмулятор (во втором терминале VS Code):

bash
python sensor_emulator.py
Ожидаемый результат:

text
✅ Создано 3 виртуальных устройств
   - SENSOR_001 (склад)
   - SENSOR_002 (офис)
   - SENSOR_003 (лаборатория)
🚀 Запуск эмуляции микроконтроллеров...
📡 Отправка данных на сервер localhost:8080
⏰ Интервал отправки: 10 секунд

✅ [14:30:25] SENSOR_001: Температура: 22.5°C, Влажность: 65.2%, Свет: 450
✅ [14:30:25] SENSOR_002: Температура: 23.1°C, Влажность: 55.8%, Свет: 320
✅ [14:30:25] SENSOR_003: Температура: 21.8°C, Влажность: 62.3%, Свет: 280
Шаг 3.2: Проверка работы системы
Действия: Создайте файл check_system.py для проверки:

python
# check_system.py - Проверка работы системы
import sqlite3
import json
from datetime import datetime

def check_database():
    """Проверка базы данных"""
    try:
        conn = sqlite3.connect('data/sensor_data.db')
        cursor = conn.cursor()
        
        # Проверка таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("📊 Таблицы в базе данных:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Проверка данных
        cursor.execute("SELECT COUNT(*) FROM sensor_data")
        count = cursor.fetchone()[0]
        print(f"📈 Всего записей: {count}")
        
        # Последние 3 записи
        cursor.execute('''
            SELECT device_id, temperature, humidity, light_level, timestamp 
            FROM sensor_data 
            ORDER BY timestamp DESC 
            LIMIT 3
        ''')
        
        print("\n📝 Последние записи:")
        for row in cursor.fetchall():
            print(f"   Устройство: {row[0]}, Темп: {row[1]}°C, Влаж: {row[2]}%, Свет: {row[3]}, Время: {row[4]}")
        
        # Статистика по устройствам
        cursor.execute('''
            SELECT device_id, COUNT(*) as count 
            FROM sensor_data 
            GROUP BY device_id
        ''')
        
        print("\n📟 Статистика по устройствам:")
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]} записей")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка проверки базы данных: {e}")

def test_server_connection():
    """Тест подключения к серверу"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 8080))
        sock.close()
        
        if result == 0:
            print("✅ Сервер доступен на localhost:8080")
        else:
            print("❌ Сервер недоступен")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования подключения: {e}")

if __name__ == "__main__":
    print("🔍 Проверка системы сбора данных...\n")
    test_server_connection()
    print()
    check_database()
Запустите проверку:

bash
python check_system.py
Ожидаемый результат:

text
🔍 Проверка системы сбора данных...

✅ Сервер доступен на localhost:8080

📊 Таблицы в базе данных:
   - sensor_data
   - devices
📈 Всего записей: 15

📝 Последние записи:
   Устройство: SENSOR_001, Темп: 22.5°C, Влаж: 65.2%, Свет: 450, Время: 2024-01-15 14:30:25
   Устройство: SENSOR_002, Темп: 23.1°C, Влаж: 55.8%, Свет: 320, Время: 2024-01-15 14:30:25
   Устройство: SENSOR_003, Темп: 21.8°C, Влаж: 62.3%, Свет: 280, Время: 2024-01-15 14:30:25

📟 Статистика по устройствам:
   SENSOR_001: 5 записей
   SENSOR_002: 5 записей
   SENSOR_003: 5 записей
✅ ФИНАЛЬНАЯ ПРОВЕРКА СИСТЕМЫ
Что должно работать:
✅ Сервер принимает подключения на порту 8080

✅ Эмулятор генерирует реалистичные данные датчиков

✅ База данных автоматически создается и заполняется

✅ Все данные сохраняются с временными метками и ID устройств

✅ Логи записываются в файл logs/sensor_system.log

Тест завершенности системы:
bash
# Проверка наличия данных
python -c "import sqlite3; conn = sqlite3.connect('data/sensor_data.db'); print('Записей:', conn.execute('SELECT COUNT(*) FROM sensor_data').fetchone()[0]); conn.close()"

# Проверка логов
tail -n 5 logs/sensor_system.log
🎉 ПОЗДРАВЛЯЮ!
Вы успешно создали полную систему сбора данных используя только Python и VS Code!

Итоговый результат:

✅ Эмуляция работы микроконтроллеров

✅ Сервер приема данных через TCP

✅ SQLite база данных с историей измерений

✅ Автоматическое логирование работы системы

✅ Готовность к масштабированию

Преимущества этого решения:

Не требует покупки оборудования

Быстрая разработка и тестирование

Легко модифицировать и расширять

Можно запустить на любом компьютере с Python

Теперь вы можете легко адаптировать эту систему для реальных микроконтроллеров, добавить веб-интерфейс или аналитику данных!

