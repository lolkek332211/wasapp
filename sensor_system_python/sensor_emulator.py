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
        """Generate list of emulated devices"""
        devices = []
        locations = ["workshop_1", "workshop_2", "warehouse", "office", "lab"]
        
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
        
        print(f"Created {len(devices)} virtual devices - sensor_emulator.py:29")
        for device in devices:
            print(f"{device['device_id']} ({device['location']}) - sensor_emulator.py:31")
        
        return devices
    
    def generate_sensor_data(self, device):
        """Generate realistic sensor data"""
        # Temperature with small random fluctuations
        temp_base = random.uniform(*device['temperature_range'])
        temperature = round(temp_base + random.uniform(-0.5, 0.5), 2)
        
        # Humidity with temperature correlation
        humidity_base = random.uniform(*device['humidity_range'])
        humidity = round(humidity_base + random.uniform(-2, 2), 2)
        
        # Light level (can be None for some sensors)
        light_level = random.randint(*device['light_range'])
        
        # Battery voltage with gradual decrease
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
        """Send data to server"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            sock.connect((self.config.SERVER.HOST, self.config.SERVER.PORT))
            
            # Send JSON data
            json_data = json.dumps(data)
            sock.send(json_data.encode('utf-8'))
            
            # Receive response
            response = sock.recv(1024).decode('utf-8')
            sock.close()
            
            response_data = json.loads(response)
            return response_data.get('status') == 'success'
            
        except Exception as e:
            print(f"Error sending data: {e} - sensor_emulator.py:82")
            return False
    
    def start_emulation(self):
        """Start microcontroller emulation"""
        print("Starting microcontroller emulation... - sensor_emulator.py:87")
        print(f"Sending data to server {self.config.SERVER.HOST}:{self.config.SERVER.PORT} - sensor_emulator.py:88")
        print(f"Send interval: {self.config.EMULATOR.SEND_INTERVAL} seconds - sensor_emulator.py:89")
        print("Press Ctrl+C to stop\n - sensor_emulator.py:90")
        
        try:
            while True:
                for device in self.devices:
                    # Generate data
                    sensor_data = self.generate_sensor_data(device)
                    
                    # Send to server
                    success = self.send_data_to_server(sensor_data)
                    
                    if success:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {device['device_id']}: - sensor_emulator.py:102"
                              f"Temp: {sensor_data['temperature']}C, "
                              f"Humidity: {sensor_data['humidity']}%, "
                              f"Light: {sensor_data['light_level']}")
                    else:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {device['device_id']}: - sensor_emulator.py:107"
                              f"Send error")
                
                # Wait before next send
                time.sleep(self.config.EMULATOR.SEND_INTERVAL)
                
        except KeyboardInterrupt:
            print("\nEmulation stopped by user - sensor_emulator.py:114")

def main():
    """Main emulator startup function"""
    config = Config()
    config.setup_logging()
    emulator = SensorEmulator(config)
    emulator.start_emulation()

if __name__ == "__main__":
    main()