import sqlite3
import os
from werkzeug.security import generate_password_hash

def get_db_path():
    """Determine the appropriate database path for different environments."""
    # Check if we're running on Render
    if 'RENDER' in os.environ:
        return '/var/lib/sqlite/hospital.db'
    else:
        # Local development path
        return os.path.join(os.path.dirname(__file__), 'instance', 'hospital.db')

def init_db():
    """Initialize the database with tables and default admin account."""
    db_path = get_db_path()
    
    # Create directory if it doesn't exist (for local development)
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Drop all tables if they exist (clean setup)
        cursor.executescript('''
        DROP TABLE IF EXISTS staff;
        DROP TABLE IF EXISTS doctors;
        DROP TABLE IF EXISTS patients;
        DROP TABLE IF EXISTS appointments;
        DROP TABLE IF EXISTS prescriptions;
        DROP TABLE IF EXISTS doctor_slots;
        ''')

        # Create tables with improved schema
        cursor.executescript('''
        CREATE TABLE staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            hospital_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            experience INTEGER,
            consultation_fee REAL,
            contact TEXT,
            bio TEXT,
            image_path TEXT,
            username TEXT UNIQUE,
            password TEXT,
            created_by INTEGER,
            hospital_id INTEGER NOT NULL,
            FOREIGN KEY (created_by) REFERENCES staff(id),
            FOREIGN KEY (hospital_id) REFERENCES staff(id)
        );

        CREATE TABLE patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT,
            contact TEXT,
            address TEXT,
            medical_history TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            hospital_id INTEGER NOT NULL,
            FOREIGN KEY (created_by) REFERENCES staff(id),
            FOREIGN KEY (hospital_id) REFERENCES staff(id)
        );

        CREATE TABLE appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            status TEXT DEFAULT 'Scheduled',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            hospital_id INTEGER NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id),
            FOREIGN KEY (hospital_id) REFERENCES staff(id)
        );

        CREATE TABLE prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER NOT NULL UNIQUE,
            diagnosis TEXT NOT NULL,
            medicines TEXT NOT NULL,
            instructions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            hospital_id INTEGER NOT NULL,
            FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE,
            FOREIGN KEY (hospital_id) REFERENCES staff(id)
        );

        CREATE TABLE doctor_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            day TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            break_start TEXT,
            break_end TEXT,
            hospital_id INTEGER NOT NULL,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id),
            FOREIGN KEY (hospital_id) REFERENCES staff(id)
        );
        ''')

        # Add default admin account
        cursor.execute(
            'INSERT INTO staff (name, email, password, hospital_name) VALUES (?, ?, ?, ?)',
            ('Admin', 'admin@hospital.com', generate_password_hash('admin123'), 'City General Hospital')
        )

        conn.commit()
        print(f"Database initialized successfully at {db_path}")
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_db_connection():
    """Create and return a database connection with row factory."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def check_database_exists():
    """Check if database file exists and is accessible."""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        conn.close()
        return True
    except sqlite3.Error:
        return False

if __name__ == '__main__':
    if not check_database_exists():
        print("Initializing database...")
        init_db()
    else:
        print("Database already exists at:", get_db_path())