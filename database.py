import psycopg2
from psycopg2.extras import DictCursor

DB_CONFIG = {
    'dbname': 'Gridrescue',
    'user': 'postgres',
    'password': 'kj02', 
    'host': 'localhost',
    'port': '5432'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=DictCursor)

def init_db():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incidents (
                id SERIAL PRIMARY KEY,
                location VARCHAR(255) NOT NULL,
                status VARCHAR(50) DEFAULT 'REPORTED',
                diagnosed_fault TEXT DEFAULT 'PENDING',
                suspect_component VARCHAR(100) DEFAULT 'PENDING',
                severity VARCHAR(50) DEFAULT 'STANDARD',
                upstream_path TEXT DEFAULT '',
                action_plan TEXT DEFAULT 'PENDING'
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                incident_id INTEGER REFERENCES incidents(id),
                source_type VARCHAR(50) NOT NULL,
                evidence_category VARCHAR(100) NOT NULL
            )
        ''')
        cursor.execute("ALTER TABLE incidents ADD COLUMN IF NOT EXISTS suspect_component VARCHAR(100) DEFAULT 'PENDING'")
        cursor.execute("ALTER TABLE incidents ADD COLUMN IF NOT EXISTS severity VARCHAR(50) DEFAULT 'STANDARD'")
        cursor.execute("ALTER TABLE incidents ADD COLUMN IF NOT EXISTS upstream_path TEXT DEFAULT ''")
        cursor.execute("ALTER TABLE incidents ADD COLUMN IF NOT EXISTS action_plan TEXT DEFAULT 'PENDING'")
    conn.commit()
    conn.close()

def create_incident(location):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('INSERT INTO incidents (location) VALUES (%s) RETURNING id', (location,))
        incident_id = cursor.fetchone()['id']
    conn.commit()
    conn.close()
    return incident_id

def add_report(incident_id, source_type, evidence_category):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('INSERT INTO reports (incident_id, source_type, evidence_category) VALUES (%s, %s, %s)',
                       (incident_id, source_type, evidence_category))
    conn.commit()
    conn.close()

def get_all_incidents():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM incidents ORDER BY id DESC')
        incidents = cursor.fetchall()
    conn.close()
    return incidents

def get_incident_data(incident_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM incidents WHERE id = %s', (incident_id,))
        incident = cursor.fetchone()
        
        cursor.execute('SELECT * FROM reports WHERE incident_id = %s', (incident_id,))
        reports = cursor.fetchall()
    conn.close()
    return incident, reports

def update_incident_fault(incident_id, fault):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('UPDATE incidents SET diagnosed_fault = %s, status = %s WHERE id = %s', 
                       (fault, 'DIAGNOSED', incident_id))
    conn.commit()
    conn.close()

def update_incident_diagnosis(incident_id, diagnosis_data):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('''
            UPDATE incidents 
            SET diagnosed_fault = %s,
                suspect_component = %s,
                severity = %s,
                upstream_path = %s,
                action_plan = %s,
                status = %s
            WHERE id = %s
        ''', (
            diagnosis_data.get('fault', 'UNKNOWN FAULT'),
            diagnosis_data.get('suspect_component', 'unknown'),
            diagnosis_data.get('severity', 'STANDARD'),
            diagnosis_data.get('upstream_path', ''),
            diagnosis_data.get('action_plan', ''),
            'DIAGNOSED',
            incident_id
        ))
    conn.commit()
    conn.close()