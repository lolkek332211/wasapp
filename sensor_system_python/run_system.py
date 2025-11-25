# run_system.py - Основной файл для запуска всей системы
import threading
import time
import subprocess
import sys
import os
from config import Config

def run_server():
    """Запуск сервера данных"""
    print("Starting data server... - run_system.py:11")
    os.system('python data_server.py')

def run_emulator():
    """Запуск эмулятора"""
    print("Starting sensor emulator... - run_system.py:16")
    os.system('python sensor_emulator.py')

def run_web_interface():
    """Запуск веб-интерфейса"""
    print("Starting web interface... - run_system.py:21")
    os.system('python web_interface.py')

def main():
    """Основная функция запуска системы"""
    config = Config()
    config.initialize_directories()
    
    print("= - run_system.py:29" * 60)
    print("🚀 Sensor Data Monitoring System - run_system.py:30")
    print("= - run_system.py:31" * 60)
    print("This system includes: - run_system.py:32")
    print("1. Data Server (localhost:8080)  receives sensor data - run_system.py:33")
    print("2. Sensor Emulator  generates test data - run_system.py:34") 
    print("3. Web Interface (localhost:5000)  monitoring dashboard - run_system.py:35")
    print("= - run_system.py:36" * 60)
    
    # Запускаем сервер в отдельном потоке
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Даем серверу время на запуск
    time.sleep(2)
    
    # Запускаем эмулятор в отдельном потоке
    emulator_thread = threading.Thread(target=run_emulator, daemon=True)
    emulator_thread.start()
    
    # Запускаем веб-интерфейс (блокирующий вызов)
    print("\n🌐 Web interface will be available at: http://localhost:5000 - run_system.py:50")
    print("📡 Data server is listening on: localhost:8080 - run_system.py:51")
    print("⚡ Sensor emulator is generating data... - run_system.py:52")
    print("\nPress Ctrl+C to stop all services\n - run_system.py:53")
    
    run_web_interface()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 System stopped by user - run_system.py:61")
    except Exception as e:
        print(f"❌ Error starting system: {e} - run_system.py:63")