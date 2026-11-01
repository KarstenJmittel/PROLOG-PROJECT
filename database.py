import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'Gridrescue'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'kj02'), 
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG, cursor_factory=DictCursor)
    except Exception as e:
        print(f"DATABASE CONNECTION ERROR: {e}")
        raise

def init_db():
    try:
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
                    action_plan TEXT DEFAULT 'PENDING',
                    resolved_at TIMESTAMP,
                    resolution_notes TEXT DEFAULT ''
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
            cursor.execute("ALTER TABLE incidents ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP")
            cursor.execute("ALTER TABLE incidents ADD COLUMN IF NOT EXISTS resolution_notes TEXT DEFAULT ''")
        conn.commit()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"DATABASE INIT WARNING: {e}")

def create_incident(location):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('INSERT INTO incidents (location) VALUES (%s) RETURNING id', (location,))
        incident_id = cursor.fetchone()['id']
    conn.commit()
    conn.close()
    return incident_id

def get_or_create_open_incident(location):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM incidents WHERE location = %s AND status != 'RESOLVED' ORDER BY id DESC LIMIT 1", (location,))
        row = cursor.fetchone()
        if row:
            incident_id = row['id']
        else:
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

def get_all_incidents(status_filter=None):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        base_query = '''
            SELECT i.*, COUNT(r.id) as reports_count
            FROM incidents i
            LEFT JOIN reports r ON r.incident_id = i.id
        '''
        if status_filter == 'active':
            cursor.execute(base_query + " WHERE i.status != 'RESOLVED' GROUP BY i.id ORDER BY i.id DESC")
        elif status_filter == 'resolved':
            cursor.execute(base_query + " WHERE i.status = 'RESOLVED' GROUP BY i.id ORDER BY i.id DESC")
        else:
            cursor.execute(base_query + " GROUP BY i.id ORDER BY i.id DESC")
        incidents = cursor.fetchall()
    conn.close()
    return incidents

def get_recent_reports(limit=15):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('''
            SELECT r.id, r.incident_id, r.source_type, r.evidence_category, i.location, i.status as incident_status, i.severity as incident_severity
            FROM reports r
            JOIN incidents i ON r.incident_id = i.id
            ORDER BY r.id DESC
            LIMIT %s
        ''', (limit,))
        reports = cursor.fetchall()
    conn.close()
    return reports

def get_incident_stats():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as total FROM incidents")
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as active FROM incidents WHERE status != 'RESOLVED'")
        active = cursor.fetchone()['active']
        
        cursor.execute("SELECT COUNT(*) as diagnosed FROM incidents WHERE status = 'DIAGNOSED'")
        diagnosed = cursor.fetchone()['diagnosed']
        
        cursor.execute("SELECT COUNT(*) as resolved FROM incidents WHERE status = 'RESOLVED'")
        resolved = cursor.fetchone()['resolved']

        cursor.execute("SELECT COUNT(*) as total_reports FROM reports")
        total_reports = cursor.fetchone()['total_reports']
    conn.close()
    return {
        "total": total,
        "active": active,
        "diagnosed": diagnosed,
        "resolved": resolved,
        "total_reports": total_reports
    }

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

def resolve_incident(incident_id, notes=""):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('''
            UPDATE incidents 
            SET status = 'RESOLVED',
                resolution_notes = %s,
                resolved_at = CURRENT_TIMESTAMP
            WHERE id = %s
        ''', (notes, incident_id))
    conn.commit()
    conn.close()

def reopen_incident(incident_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('''
            UPDATE incidents 
            SET status = 'REPORTED',
                resolved_at = NULL
            WHERE id = %s
        ''', (incident_id,))
    conn.commit()
    conn.close()

def delete_incident(incident_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('DELETE FROM reports WHERE incident_id = %s', (incident_id,))
        cursor.execute('DELETE FROM incidents WHERE id = %s', (incident_id,))
    conn.commit()
    conn.close()

def delete_report(report_id):
    conn = get_db_connection()
    incident_id = None
    with conn.cursor() as cursor:
        cursor.execute('DELETE FROM reports WHERE id = %s RETURNING incident_id', (report_id,))
        row = cursor.fetchone()
        if row:
            incident_id = row['incident_id']
    conn.commit()
    conn.close()
    return incident_id

