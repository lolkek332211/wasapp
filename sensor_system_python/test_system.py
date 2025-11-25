# test_system.py - Simple system test
import sqlite3
import socket

def test_database():
    """Test database functionality"""
    try:
        conn = sqlite3.connect('data/sensor_data.db')
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        print("Database tables: - test_system.py:14", tables)
        
        # Check data count
        cursor.execute("SELECT COUNT(*) FROM sensor_data")
        count = cursor.fetchone()[0]
        print(f"Total records: {count} - test_system.py:19")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Database test failed: {e} - test_system.py:25")
        return False

def test_server_connection():
    """Test server connection"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 8080))
        sock.close()
        
        if result == 0:
            print("Server is running on localhost:8080 - test_system.py:37")
            return True
        else:
            print("Server is not available - test_system.py:40")
            return False
            
    except Exception as e:
        print(f"Connection test failed: {e} - test_system.py:44")
        return False

if __name__ == "__main__":
    print("Testing system... - test_system.py:48")
    print("1. Testing database... - test_system.py:49")
    db_ok = test_database()
    
    print("2. Testing server connection... - test_system.py:52")
    server_ok = test_server_connection()
    
    if db_ok and server_ok:
        print("All tests passed! System is working correctly. - test_system.py:56")
    else:
        print("Some tests failed. Check the issues above. - test_system.py:58")