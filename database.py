import os
import psycopg2
from psycopg2.extras import DictCursor
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Create and return a database connection with row factory."""
    if 'RENDER' in os.environ:
        # Production - Render PostgreSQL
        conn = psycopg2.connect(
            dbname=os.getenv('PGDATABASE'),
            user=os.getenv('PGUSER'),
            password=os.getenv('PGPASSWORD'),
            host=os.getenv('PGHOST'),
            port=os.getenv('PGPORT'),
            cursor_factory=DictCursor
        )
    else:
        # Development - SQLite
        import sqlite3
        os.makedirs('instance', exist_ok=True)
        conn = sqlite3.connect('instance/hospital.db')
        conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with tables and default admin account."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if 'RENDER' in os.environ:
            # PostgreSQL schema
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                hospital_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctors (
                id SERIAL PRIMARY KEY,
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
            ''')
            
            # Add other tables similarly...
            
            # Add default admin account
            cursor.execute(
                'INSERT INTO staff (name, email, password, hospital_name) VALUES (%s, %s, %s, %s)',
                ('Admin', 'admin@hospital.com', generate_password_hash('admin123'), 'City General Hospital')
            )
        else:
            # SQLite schema
            cursor.executescript('''
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                hospital_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS doctors (
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
            ''')
            
            # Add default admin account
            cursor.execute(
                'INSERT INTO staff (name, email, password, hospital_name) VALUES (?, ?, ?, ?)',
                ('Admin', 'admin@hospital.com', generate_password_hash('admin123'), 'City General Hospital')
            )

        conn.commit()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        conn.close()

def check_database_exists():
    """Check if database is accessible."""
    try:
        conn = get_db_connection()
        conn.close()
        return True
    except Exception:
        return False

if __name__ == '__main__':
    if not check_database_exists():
        print("Initializing database...")
        init_db()
    else:
        print("Database already exists")
