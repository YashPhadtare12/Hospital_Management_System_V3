import sqlite3
import os
from werkzeug.security import generate_password_hash

def get_db_path():
    """Determine the appropriate database path for different environments."""
    # Check if we're running on Render
    if 'RENDER' in os.environ:
        # Render provides persistent storage at this location
        return '/var/lib/sqlite/hospital.db'
    else:
        # Local development path - creates database in instance folder
        os.makedirs(os.path.join(os.path.dirname(__file__), 'instance'), exist_ok=True)
        return os.path.join(os.path.dirname(__file__), 'instance', 'hospital.db')

def init_db():
    """Initialize the database with tables and default admin account."""
    db_path = get_db_path()
    
    # Create directory if it doesn't exist (for local development)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Enable foreign key constraints
        cursor.execute('PRAGMA foreign_keys = ON;')

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
            consultation_fee REAL NOT NULL,
            contact TEXT NOT NULL,
            bio TEXT,
            image_path TEXT,
            username TEXT UNIQUE,
            password TEXT,
            created_by INTEGER,
            hospital_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES staff(id),
            FOREIGN KEY (hospital_id) REFERENCES staff(id)
        );

        CREATE TABLE patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            contact TEXT NOT NULL,
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
            status TEXT DEFAULT 'Scheduled' CHECK(status IN ('Scheduled', 'Completed', 'Cancelled')),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            hospital_id INTEGER NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
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
            day TEXT NOT NULL CHECK(day IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            break_start TEXT,
            break_end TEXT,
            hospital_id INTEGER NOT NULL,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
            FOREIGN KEY (hospital_id) REFERENCES staff(id),
            UNIQUE(doctor_id, day, hospital_id)
        );
        ''')

        # Add default admin account if in development
        if not 'RENDER' in os.environ:
            cursor.execute(
                'INSERT INTO staff (name, email, password, hospital_name) VALUES (?, ?, ?, ?)',
                ('Admin', 'admin@hospital.com', generate_password_hash('admin123'), 'City General Hospital')
            )

        conn.commit()
        print(f"✅ Database initialized successfully at: {db_path}")
    except sqlite3.Error as e:
        print(f"❌ Error initializing database: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_db_connection():
    """Create and return a database connection with row factory."""
    db_path = get_db_path()
    
    # Initialize database if it doesn't exist
    if not os.path.exists(db_path):
        init_db()
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Enable foreign key constraints
    conn.execute('PRAGMA foreign_keys = ON;')
    
    return conn

def check_database_exists():
    """Check if database file exists and has all required tables."""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        return False
    
    required_tables = ['staff', 'doctors', 'patients', 'appointments', 'prescriptions', 'doctor_slots']
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if all tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"Missing tables: {missing_tables}")
            return False
            
        return True
    except sqlite3.Error as e:
        print(f"Database check error: {e}")
        return False
    finally:
        conn.close()

def backup_database():
    """Create a backup of the database file."""
    db_path = get_db_path()
    backup_path = f"{db_path}.backup"
    
    try:
        # Simple file copy for SQLite
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

if __name__ == '__main__':
    if not check_database_exists():
        print("⚠️ Database not found or incomplete. Initializing new database...")
        init_db()
    else:
        print("✅ Database already exists and appears valid")
    
    # Create a test backup
    backup_database()
