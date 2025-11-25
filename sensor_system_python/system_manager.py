# system_manager.py - Простой интерфейс управления системой сбора данных
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import sqlite3
import subprocess
import sys
import os
from datetime import datetime

class SensorSystemManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Sensor Data System Manager")
        self.root.geometry("800x600")
        
        # Переменные для хранения процессов
        self.server_process = None
        self.emulator_process = None
        self.web_process = None
        
        # Статусы компонентов
        self.server_running = False
        self.emulator_running = False
        self.web_running = False
        
        self.setup_ui()
        self.start_status_monitor()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Создаем вкладки
        notebook = ttk.Notebook(self.root)
        
        # Вкладка управления
        control_frame = ttk.Frame(notebook)
        notebook.add(control_frame, text="Управление")
        
        # Вкладка мониторинга
        monitor_frame = ttk.Frame(notebook)
        notebook.add(monitor_frame, text="Мониторинг")
        
        # Вкладка базы данных
        database_frame = ttk.Frame(notebook)
        notebook.add(database_frame, text="База данных")
        
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === ВКЛАДКА УПРАВЛЕНИЯ ===
        self.setup_control_tab(control_frame)
        
        # === ВКЛАДКА МОНИТОРИНГА ===
        self.setup_monitor_tab(monitor_frame)
        
        # === ВКЛАДКА БАЗЫ ДАННЫХ ===
        self.setup_database_tab(database_frame)
    
    def setup_control_tab(self, parent):
        """Настройка вкладки управления"""
        # Статус системы
        status_frame = ttk.LabelFrame(parent, text="Статус системы", padding=10)
        status_frame.pack(fill=tk.X, pady=5)
        
        # Сервер данных
        self.server_status = tk.Label(status_frame, text="❌ Сервер данных: Остановлен", fg="red")
        self.server_status.pack(anchor=tk.W)
        
        # Эмулятор
        self.emulator_status = tk.Label(status_frame, text="❌ Эмулятор: Остановлен", fg="red")
        self.emulator_status.pack(anchor=tk.W)
        
        # Веб-интерфейс
        self.web_status = tk.Label(status_frame, text="❌ Веб-интерфейс: Остановлен", fg="red")
        self.web_status.pack(anchor=tk.W)
        
        # Кнопки управления
        button_frame = ttk.LabelFrame(parent, text="Управление компонентами", padding=10)
        button_frame.pack(fill=tk.X, pady=5)
        
        # Сервер данных
        server_frame = ttk.Frame(button_frame)
        server_frame.pack(fill=tk.X, pady=2)
        ttk.Label(server_frame, text="Сервер данных (порт 8080):").pack(side=tk.LEFT)
        ttk.Button(server_frame, text="Запуск", command=self.start_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(server_frame, text="Остановка", command=self.stop_server).pack(side=tk.LEFT, padx=5)
        
        # Эмулятор
        emulator_frame = ttk.Frame(button_frame)
        emulator_frame.pack(fill=tk.X, pady=2)
        ttk.Label(emulator_frame, text="Эмулятор датчиков:").pack(side=tk.LEFT)
        ttk.Button(emulator_frame, text="Запуск", command=self.start_emulator).pack(side=tk.LEFT, padx=5)
        ttk.Button(emulator_frame, text="Остановка", command=self.stop_emulator).pack(side=tk.LEFT, padx=5)
        
        # Веб-интерфейс
        web_frame = ttk.Frame(button_frame)
        web_frame.pack(fill=tk.X, pady=2)
        ttk.Label(web_frame, text="Веб-интерфейс (порт 5000):").pack(side=tk.LEFT)
        ttk.Button(web_frame, text="Запуск", command=self.start_web).pack(side=tk.LEFT, padx=5)
        ttk.Button(web_frame, text="Остановка", command=self.stop_web).pack(side=tk.LEFT, padx=5)
        
        # Групповое управление
        group_frame = ttk.Frame(button_frame)
        group_frame.pack(fill=tk.X, pady=10)
        ttk.Button(group_frame, text="▶ Запуск всего", command=self.start_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(group_frame, text="⏹ Остановка всего", command=self.stop_all).pack(side=tk.LEFT, padx=5)
        
        # Ссылки
        link_frame = ttk.LabelFrame(parent, text="Быстрые ссылки", padding=10)
        link_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(link_frame, text="🌐 Открыть веб-интерфейс", 
                  command=self.open_web_interface).pack(side=tk.LEFT, padx=5)
        ttk.Button(link_frame, text="📊 Показать статистику", 
                  command=self.show_statistics).pack(side=tk.LEFT, padx=5)
    
    def setup_monitor_tab(self, parent):
        """Настройка вкладки мониторинга"""
        # Лог в реальном времени
        log_frame = ttk.LabelFrame(parent, text="Лог системы", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # Кнопки управления логом
        log_buttons = ttk.Frame(log_frame)
        log_buttons.pack(fill=tk.X, pady=5)
        
        ttk.Button(log_buttons, text="Очистить лог", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_buttons, text="Экспорт лога", command=self.export_log).pack(side=tk.LEFT, padx=5)
        
        # Статистика в реальном времени
        stats_frame = ttk.LabelFrame(parent, text="Статистика в реальном времени", padding=10)
        stats_frame.pack(fill=tk.X, pady=5)
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=8, width=80)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        self.stats_text.config(state=tk.DISABLED)
    
    def setup_database_tab(self, parent):
        """Настройка вкладки базы данных"""
        # Управление БД
        db_control_frame = ttk.LabelFrame(parent, text="Управление базой данных", padding=10)
        db_control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(db_control_frame, text="Показать все записи", 
                  command=self.show_all_records).pack(side=tk.LEFT, padx=5)
        ttk.Button(db_control_frame, text="Экспорт в CSV", 
                  command=self.export_to_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(db_control_frame, text="Очистить базу", 
                  command=self.clear_database).pack(side=tk.LEFT, padx=5)
        
        # Просмотр данных
        data_frame = ttk.LabelFrame(parent, text="Просмотр данных", padding=10)
        data_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Таблица данных
        columns = ("ID", "Устройство", "Температура", "Влажность", "Свет", "Время")
        self.data_tree = ttk.Treeview(data_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=100)
        
        self.data_tree.pack(fill=tk.BOTH, expand=True)
        
        # Прокрутка для таблицы
        scrollbar = ttk.Scrollbar(data_frame, orient=tk.VERTICAL, command=self.data_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.data_tree.configure(yscrollcommand=scrollbar.set)
    
    def log_message(self, message):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def update_status(self):
        """Обновление статусов компонентов"""
        # Сервер данных
        server_color = "green" if self.check_port(8080) else "red"
        server_text = "✅ Сервер данных: Запущен" if self.check_port(8080) else "❌ Сервер данных: Остановлен"
        self.server_status.config(text=server_text, fg=server_color)
        
        # Веб-интерфейс
        web_color = "green" if self.check_port(5000) else "red"
        web_text = "✅ Веб-интерфейс: Запущен" if self.check_port(5000) else "❌ Веб-интерфейс: Остановлен"
        self.web_status.config(text=web_text, fg=web_color)
        
        # Эмулятор (проверяем по наличию процесса)
        emulator_color = "green" if self.emulator_running else "red"
        emulator_text = "✅ Эмулятор: Запущен" if self.emulator_running else "❌ Эмулятор: Остановлен"
        self.emulator_status.config(text=emulator_text, fg=emulator_color)
    
    def check_port(self, port):
        """Проверка доступности порта"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result == 0
        except:
            return False
    
    def start_status_monitor(self):
        """Запуск мониторинга статуса"""
        def monitor():
            while True:
                self.update_status()
                self.update_statistics()
                self.update_data_view()
                time.sleep(2)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def update_statistics(self):
        """Обновление статистики"""
        try:
            conn = sqlite3.connect('data/sensor_data.db')
            cursor = conn.cursor()
            
            # Общая статистика
            cursor.execute("SELECT COUNT(*) FROM sensor_data")
            total_records = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT device_id) FROM sensor_data")
            device_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT MAX(timestamp) FROM sensor_data")
            last_record = cursor.fetchone()[0]
            
            conn.close()
            
            stats_text = f"""Общая статистика:
• Всего записей: {total_records}
• Устройств: {device_count}
• Последняя запись: {last_record or 'Нет данных'}
• Сервер данных: {'✅ Запущен' if self.check_port(8080) else '❌ Остановлен'}
• Веб-интерфейс: {'✅ Запущен' if self.check_port(5000) else '❌ Остановлен'}"""
            
            self.stats_text.config(state=tk.NORMAL)
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text)
            self.stats_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.stats_text.config(state=tk.NORMAL)
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, f"Ошибка получения статистики: {e}")
            self.stats_text.config(state=tk.DISABLED)
    
    def update_data_view(self):
        """Обновление таблицы данных"""
        try:
            conn = sqlite3.connect('data/sensor_data.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, device_id, temperature, humidity, light_level, timestamp 
                FROM sensor_data 
                ORDER BY timestamp DESC 
                LIMIT 50
            ''')
            
            # Очищаем таблицу
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)
            
            # Добавляем данные
            for row in cursor.fetchall():
                self.data_tree.insert("", tk.END, values=row)
            
            conn.close()
            
        except Exception as e:
            # Если база данных еще не создана, пропускаем ошибку
            pass
    
    # === МЕТОДЫ УПРАВЛЕНИЯ ===
    
    def start_server(self):
        """Запуск сервера данных"""
        try:
            if not self.check_port(8080):
                self.server_process = subprocess.Popen(
                    [sys.executable, "data_server.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self.log_message("Сервер данных запускается...")
                self.server_running = True
            else:
                self.log_message("Сервер данных уже запущен")
        except Exception as e:
            self.log_message(f"Ошибка запуска сервера: {e}")
    
    def stop_server(self):
        """Остановка сервера данных"""
        try:
            if self.server_process:
                self.server_process.terminate()
                self.server_process = None
            self.log_message("Сервер данных остановлен")
            self.server_running = False
        except Exception as e:
            self.log_message(f"Ошибка остановки сервера: {e}")
    
    def start_emulator(self):
        """Запуск эмулятора"""
        try:
            self.emulator_process = subprocess.Popen(
                [sys.executable, "sensor_emulator.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.log_message("Эмулятор запущен")
            self.emulator_running = True
        except Exception as e:
            self.log_message(f"Ошибка запуска эмулятора: {e}")
    
    def stop_emulator(self):
        """Остановка эмулятора"""
        try:
            if self.emulator_process:
                self.emulator_process.terminate()
                self.emulator_process = None
            self.log_message("Эмулятор остановлен")
            self.emulator_running = False
        except Exception as e:
            self.log_message(f"Ошибка остановки эмулятора: {e}")
    
    def start_web(self):
        """Запуск веб-интерфейса"""
        try:
            if not self.check_port(5000):
                self.web_process = subprocess.Popen(
                    [sys.executable, "web_interface.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self.log_message("Веб-интерфейс запускается...")
                self.web_running = True
            else:
                self.log_message("Веб-интерфейс уже запущен")
        except Exception as e:
            self.log_message(f"Ошибка запуска веб-интерфейса: {e}")
    
    def stop_web(self):
        """Остановка веб-интерфейса"""
        try:
            if self.web_process:
                self.web_process.terminate()
                self.web_process = None
            self.log_message("Веб-интерфейс остановлен")
            self.web_running = False
        except Exception as e:
            self.log_message(f"Ошибка остановки веб-интерфейса: {e}")
    
    def start_all(self):
        """Запуск всех компонентов"""
        self.log_message("Запуск всех компонентов системы...")
        self.start_server()
        time.sleep(2)
        self.start_emulator()
        time.sleep(1)
        self.start_web()
    
    def stop_all(self):
        """Остановка всех компонентов"""
        self.log_message("Остановка всех компонентов системы...")
        self.stop_web()
        self.stop_emulator()
        self.stop_server()
    
    def open_web_interface(self):
        """Открытие веб-интерфейса в браузере"""
        import webbrowser
        webbrowser.open("http://localhost:5000")
        self.log_message("Открытие веб-интерфейса в браузере")
    
    def show_statistics(self):
        """Показать подробную статистику"""
        try:
            conn = sqlite3.connect('data/sensor_data.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM sensor_data")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT device_id) FROM devices")
            devices = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT device_id, COUNT(*) as count 
                FROM sensor_data 
                GROUP BY device_id
            ''')
            
            device_stats = ""
            for device_id, count in cursor.fetchall():
                device_stats += f"  {device_id}: {count} записей\n"
            
            conn.close()
            
            messagebox.showinfo(
                "Статистика системы",
                f"Общая статистика:\n\n"
                f"Всего записей в базе: {total}\n"
                f"Зарегистрированных устройств: {devices}\n\n"
                f"Статистика по устройствам:\n{device_stats}"
            )
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить статистику: {e}")
    
    def show_all_records(self):
        """Показать все записи"""
        try:
            conn = sqlite3.connect('data/sensor_data.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, device_id, temperature, humidity, light_level, timestamp 
                FROM sensor_data 
                ORDER BY timestamp DESC
            ''')
            
            records = cursor.fetchall()
            conn.close()
            
            # Создаем окно с записями
            records_window = tk.Toplevel(self.root)
            records_window.title("Все записи базы данных")
            records_window.geometry("900x500")
            
            text_widget = scrolledtext.ScrolledText(records_window, width=100, height=25)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            for record in records:
                text_widget.insert(tk.END, f"{record}\n")
            
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить записи: {e}")
    
    def export_to_csv(self):
        """Экспорт данных в CSV"""
        try:
            import csv
            
            conn = sqlite3.connect('data/sensor_data.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM sensor_data')
            data = cursor.fetchall()
            
            # Получаем названия колонок
            cursor.execute('PRAGMA table_info(sensor_data)')
            columns = [column[1] for column in cursor.fetchall()]
            
            conn.close()
            
            # Сохраняем в файл
            filename = f"sensor_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(columns)
                writer.writerows(data)
            
            self.log_message(f"Данные экспортированы в {filename}")
            messagebox.showinfo("Экспорт", f"Данные успешно экспортированы в {filename}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать данные: {e}")
    
    def clear_database(self):
        """Очистка базы данных"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить всю базу данных?"):
            try:
                conn = sqlite3.connect('data/sensor_data.db')
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM sensor_data')
                cursor.execute('DELETE FROM devices')
                
                conn.commit()
                conn.close()
                
                self.log_message("База данных очищена")
                messagebox.showinfo("Успех", "База данных успешно очищена")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось очистить базу данных: {e}")
    
    def clear_log(self):
        """Очистка лога"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log_message("Лог очищен")
    
    def export_log(self):
        """Экспорт лога в файл"""
        try:
            filename = f"system_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(self.log_text.get(1.0, tk.END))
            
            self.log_message(f"Лог экспортирован в {filename}")
            messagebox.showinfo("Экспорт", f"Лог успешно экспортирован в {filename}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать лог: {e}")

def main():
    """Запуск приложения"""
    root = tk.Tk()
    app = SensorSystemManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()