import streamlit as st
import sqlite3
import hashlib
import random
import json
import csv
import io
import math
import time
from datetime import datetime, timedelta
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as pe
import networkx as nx
import numpy as np
from io import StringIO, BytesIO

st.set_page_config(
    page_title="EmergiSim",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

MASTER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --bg-void: #0F172A;
    --bg-deep: #111827;
    --bg-surface: #1E293B;
    --bg-raised: #1E293B;
    --bg-float: #1E293B;

    --accent-primary: #6366F1;
    --accent-secondary: #4F46E5;

    --text-primary: #E5E7EB;
    --text-secondary: #9CA3AF;
    --text-muted: #6B7280;

    --border-subtle: rgba(255,255,255,0.08);
    --border-glow: rgba(99,102,241,0.25);

    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 14px;
    --radius-xl: 18px;
}

*, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: var(--bg-void) !important;
    font-family: 'Inter', sans-serif;
    color: var(--text-primary);
}

[data-testid="stSidebar"],
[data-testid="collapsedControl"],
header[data-testid="stHeader"],
#MainMenu,
footer {
    display: none !important;
}

.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

.stButton > button {
    background: var(--accent-primary) !important;
    color: white !important;
    border-radius: var(--radius-sm) !important;
    border: none !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 10px 18px !important;
}

.stButton > button:hover {
    background: var(--accent-secondary) !important;
}

.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
.stSelectbox div {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
}

.stDataFrame {
    background: var(--bg-surface) !important;
    border-radius: var(--radius-md);
}

.stDataFrame th {
    background: var(--bg-deep) !important;
    color: var(--text-secondary) !important;
}

.stDataFrame td {
    color: var(--text-primary) !important;
}

[data-testid="stMetric"] {
    background: var(--bg-surface) !important;
    border-radius: var(--radius-md);
    padding: 14px !important;
}

[data-testid="stMetricValue"] {
    color: var(--accent-primary) !important;
    font-weight: 700 !important;
}

.es-card, .es-stat-card, .es-form-section {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
}

.es-card::before,
.es-app-wrapper::before,
.es-grid-overlay,
.es-stat-card::after {
    display: none !important;
}

.es-topbar {
    background: var(--bg-deep);
    border-bottom: 1px solid var(--border-subtle);
}

.es-logo-mark {
    display: none !important;
}

.es-activity-dot {
    display: none !important;
}

.es-badge {
    background: rgba(255,255,255,0.05);
    color: var(--text-secondary);
    border: 1px solid var(--border-subtle);
}

.es-chip-blue,
.es-chip-green,
.es-chip-yellow {
    background: rgba(255,255,255,0.05);
    color: var(--text-secondary);
}

label {
    color: var(--text-secondary) !important;
    font-size: 12px !important;
}

</style>
"""

st.markdown(MASTER_CSS, unsafe_allow_html=True)
st.markdown('<div class="es-grid-overlay"></div>', unsafe_allow_html=True)


def get_db():
    conn = sqlite3.connect("emergisim.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Observer',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT NOT NULL,
            description TEXT,
            duration REAL DEFAULT 1.0,
            probability REAL DEFAULT 1.0,
            priority_level INTEGER DEFAULT 1,
            optional_flag INTEGER DEFAULT 0,
            failure_probability REAL DEFAULT 0.0,
            status TEXT DEFAULT 'active',
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS dependencies (
            dependency_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            depends_on_event_id INTEGER NOT NULL,
            dependency_type TEXT DEFAULT 'requires',
            condition_rule TEXT,
            FOREIGN KEY (event_id) REFERENCES events(event_id),
            FOREIGN KEY (depends_on_event_id) REFERENCES events(event_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS simulations (
            simulation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            simulation_name TEXT NOT NULL,
            created_by INTEGER,
            start_timestamp TEXT,
            end_timestamp TEXT,
            run_status TEXT DEFAULT 'pending',
            parameter_set TEXT,
            total_sequences INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sequences (
            sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            simulation_id INTEGER,
            sequence_order TEXT,
            likelihood_score REAL,
            risk_score REAL,
            conflict_flag INTEGER DEFAULT 0,
            remarks TEXT,
            FOREIGN KEY (simulation_id) REFERENCES simulations(simulation_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS conflicts (
            conflict_id INTEGER PRIMARY KEY AUTOINCREMENT,
            simulation_id INTEGER,
            sequence_id INTEGER,
            conflict_type TEXT,
            severity_level TEXT,
            description TEXT,
            resolution_note TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            simulation_id INTEGER,
            report_name TEXT,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP,
            report_type TEXT,
            file_path TEXT,
            created_by INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action_type TEXT,
            action_time TEXT DEFAULT CURRENT_TIMESTAMP,
            target_record TEXT,
            remarks TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS backups (
            backup_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_by INTEGER,
            backup_date TEXT DEFAULT CURRENT_TIMESTAMP,
            backup_location TEXT,
            restore_status TEXT DEFAULT 'available'
        )
    """)
    c.execute("""
        SELECT COUNT(*) FROM users WHERE username = 'admin'
    """)
    if c.fetchone()[0] == 0:
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users (full_name, username, password_hash, role) VALUES (?,?,?,?)",
                  ("System Administrator", "admin", admin_hash, "Administrator"))
        demo_hash = hashlib.sha256("demo123".encode()).hexdigest()
        c.execute("INSERT INTO users (full_name, username, password_hash, role) VALUES (?,?,?,?)",
                  ("Demo Planner", "planner", demo_hash, "Event Planner"))
        analyst_hash = hashlib.sha256("analyst123".encode()).hexdigest()
        c.execute("INSERT INTO users (full_name, username, password_hash, role) VALUES (?,?,?,?)",
                  ("Demo Analyst", "analyst", analyst_hash, "Analyst"))
        observer_hash = hashlib.sha256("observer123".encode()).hexdigest()
        c.execute("INSERT INTO users (full_name, username, password_hash, role) VALUES (?,?,?,?)",
                  ("Demo Observer", "observer", observer_hash, "Observer"))
    conn.commit()
    conn.close()


def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def verify_user(username, password):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND status='active'", (username,))
    row = c.fetchone()
    conn.close()
    if row and row["password_hash"] == hash_password(password):
        return dict(row)
    return None


def register_user(full_name, username, password, role="Observer"):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (full_name, username, password_hash, role) VALUES (?,?,?,?)",
                  (full_name, username, hash_password(password), role))
        conn.commit()
        conn.close()
        return True, "Account created successfully."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username already exists."


def log_action(user_id, action_type, target="", remarks=""):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO audit_logs (user_id, action_type, action_time, target_record, remarks) VALUES (?,?,?,?,?)",
              (user_id, action_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), target, remarks))
    conn.commit()
    conn.close()


def get_all_events():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM events WHERE status='active' ORDER BY priority_level DESC, event_id")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_event_by_id(event_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM events WHERE event_id=?", (event_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def create_event(name, description, duration, probability, priority, optional, fail_prob, user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO events (event_name, description, duration, probability, priority_level, optional_flag, failure_probability, created_by)
                 VALUES (?,?,?,?,?,?,?,?)""",
              (name, description, duration, probability, priority, int(optional), fail_prob, user_id))
    event_id = c.lastrowid
    conn.commit()
    conn.close()
    log_action(user_id, "Create Event", str(event_id), name)
    return event_id


def update_event(event_id, name, description, duration, probability, priority, optional, fail_prob, user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("""UPDATE events SET event_name=?, description=?, duration=?, probability=?,
                 priority_level=?, optional_flag=?, failure_probability=? WHERE event_id=?""",
              (name, description, duration, probability, priority, int(optional), fail_prob, event_id))
    conn.commit()
    conn.close()
    log_action(user_id, "Update Event", str(event_id), name)


def delete_event(event_id, user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE events SET status='deleted' WHERE event_id=?", (event_id,))
    c.execute("DELETE FROM dependencies WHERE event_id=? OR depends_on_event_id=?", (event_id, event_id))
    conn.commit()
    conn.close()
    log_action(user_id, "Delete Event", str(event_id))


def clone_event(event_id, user_id):
    ev = get_event_by_id(event_id)
    if not ev:
        return None
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO events (event_name, description, duration, probability, priority_level, optional_flag, failure_probability, created_by)
                 VALUES (?,?,?,?,?,?,?,?)""",
              (ev["event_name"] + " (Copy)", ev["description"], ev["duration"], ev["probability"],
               ev["priority_level"], ev["optional_flag"], ev["failure_probability"], user_id))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    log_action(user_id, "Clone Event", str(new_id), f"Cloned from {event_id}")
    return new_id


def get_dependencies():
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT d.*, e1.event_name as from_name, e2.event_name as to_name
                 FROM dependencies d
                 JOIN events e1 ON d.event_id = e1.event_id
                 JOIN events e2 ON d.depends_on_event_id = e2.event_id""")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def add_dependency(event_id, depends_on, dep_type, condition, user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM dependencies WHERE event_id=? AND depends_on_event_id=?", (event_id, depends_on))
    if c.fetchone():
        conn.close()
        return False, "Dependency already exists."
    c.execute("INSERT INTO dependencies (event_id, depends_on_event_id, dependency_type, condition_rule) VALUES (?,?,?,?)",
              (event_id, depends_on, dep_type, condition))
    conn.commit()
    conn.close()
    log_action(user_id, "Add Dependency", f"{event_id}->{depends_on}")
    return True, "Dependency added."


def delete_dependency(dep_id, user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM dependencies WHERE dependency_id=?", (dep_id,))
    conn.commit()
    conn.close()
    log_action(user_id, "Delete Dependency", str(dep_id))


def validate_dependencies_db():
    events = get_all_events()
    deps = get_dependencies()
    adj = {e["event_id"]: [] for e in events}
    for d in deps:
        if d["event_id"] in adj:
            adj[d["event_id"]].append(d["depends_on_event_id"])
    visited = set()
    stack = set()

    def has_cycle(node):
        visited.add(node)
        stack.add(node)
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in stack:
                return True
        stack.remove(node)
        return False

    for node in adj:
        if node not in visited:
            if has_cycle(node):
                return False, "Circular dependency detected."
    return True, "All dependencies are valid."


def import_events_json(json_str, user_id):
    try:
        data = json.loads(json_str)
        if not isinstance(data, list):
            data = [data]
        imported = 0
        skipped = []
        for item in data:
            try:
                create_event(
                    item.get("event_name", "Unnamed"),
                    item.get("description", ""),
                    float(item.get("duration", 1.0)),
                    float(item.get("probability", 1.0)),
                    int(item.get("priority_level", 1)),
                    bool(item.get("optional_flag", False)),
                    float(item.get("failure_probability", 0.0)),
                    user_id
                )
                imported += 1
            except Exception as ex:
                skipped.append(str(ex))
        log_action(user_id, "Import JSON", remarks=f"Imported {imported}")
        return True, f"Imported {imported} events. Skipped: {len(skipped)}"
    except Exception as e:
        return False, f"Invalid JSON: {e}"


def import_events_csv(csv_str, user_id):
    try:
        reader = csv.DictReader(StringIO(csv_str))
        imported = 0
        skipped = []
        for row in reader:
            try:
                create_event(
                    row.get("event_name", "Unnamed"),
                    row.get("description", ""),
                    float(row.get("duration", 1.0)),
                    float(row.get("probability", 1.0)),
                    int(row.get("priority_level", 1)),
                    row.get("optional_flag", "0") == "1",
                    float(row.get("failure_probability", 0.0)),
                    user_id
                )
                imported += 1
            except Exception as ex:
                skipped.append(str(ex))
        log_action(user_id, "Import CSV", remarks=f"Imported {imported}")
        return True, f"Imported {imported} events. Skipped: {len(skipped)}"
    except Exception as e:
        return False, f"CSV error: {e}"


def export_events_json():
    events = get_all_events()
    return json.dumps(events, indent=2, default=str)


def export_events_csv():
    events = get_all_events()
    if not events:
        return ""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=events[0].keys())
    writer.writeheader()
    writer.writerows(events)
    return output.getvalue()


def run_simulation_engine(sim_name, user_id, num_sequences=8):
    events = get_all_events()
    if not events:
        return None, "No events defined."
    valid, msg = validate_dependencies_db()
    if not valid:
        return None, msg
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO simulations (simulation_name, created_by, start_timestamp, run_status, parameter_set)
                 VALUES (?,?,?,?,?)""",
              (sim_name, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "running",
               json.dumps({"num_sequences": num_sequences})))
    sim_id = c.lastrowid
    conn.commit()
    event_ids = [e["event_id"] for e in events]
    deps = get_dependencies()
    dep_map = {}
    for d in deps:
        dep_map.setdefault(d["event_id"], []).append(d["depends_on_event_id"])

    def topological_sort():
        in_degree = {eid: 0 for eid in event_ids}
        adj = {eid: [] for eid in event_ids}
        for d in deps:
            if d["event_id"] in adj and d["depends_on_event_id"] in in_degree:
                adj[d["depends_on_event_id"]].append(d["event_id"])
                in_degree[d["event_id"]] += 1
        queue = [e for e in event_ids if in_degree[e] == 0]
        result = []
        while queue:
            random.shuffle(queue)
            node = queue.pop(0)
            result.append(node)
            for nb in adj[node]:
                in_degree[nb] -= 1
                if in_degree[nb] == 0:
                    queue.append(nb)
        return result if len(result) == len(event_ids) else event_ids[:]

    sequences_generated = []
    for i in range(num_sequences):
        base = topological_sort()
        stochastic_seq = []
        for eid in base:
            ev = next((e for e in events if e["event_id"] == eid), None)
            if ev:
                if ev["optional_flag"] and random.random() > 0.5:
                    continue
                if random.random() > ev["probability"]:
                    continue
                stochastic_seq.append(eid)
        if not stochastic_seq:
            stochastic_seq = base[:]
        likelihood = round(random.uniform(0.3, 0.99), 3)
        risk = compute_risk_score(stochastic_seq, events, deps)
        has_conflict = 0
        remarks = []
        if len(stochastic_seq) != len(set(stochastic_seq)):
            has_conflict = 1
            remarks.append("Duplicate path detected")
        if len(stochastic_seq) > 5:
            remarks.append("Complex chain")
        missed = [eid for eid in event_ids if eid not in stochastic_seq]
        if missed:
            has_conflict = 1
            remarks.append(f"Missing events: {len(missed)}")
        c.execute("""INSERT INTO sequences (simulation_id, sequence_order, likelihood_score, risk_score, conflict_flag, remarks)
                     VALUES (?,?,?,?,?,?)""",
                  (sim_id, json.dumps(stochastic_seq), likelihood, risk, has_conflict, "; ".join(remarks)))
        sequences_generated.append({
            "sequence": stochastic_seq,
            "likelihood": likelihood,
            "risk": risk,
            "conflict": has_conflict,
            "remarks": "; ".join(remarks)
        })
    detect_and_store_conflicts(c, sim_id, sequences_generated, events)
    c.execute("UPDATE simulations SET run_status='completed', end_timestamp=?, total_sequences=? WHERE simulation_id=?",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), len(sequences_generated), sim_id))
    conn.commit()
    conn.close()
    log_action(user_id, "Run Simulation", str(sim_id), sim_name)
    return sim_id, "Simulation completed successfully."


def compute_risk_score(seq, events, deps):
    base = len(seq) * 8
    for eid in seq:
        ev = next((e for e in events if e["event_id"] == eid), None)
        if ev:
            base += ev["failure_probability"] * 80
            base -= ev["probability"] * 10
            base += (5 - ev["priority_level"]) * 3
    dep_count = sum(1 for d in deps if d["event_id"] in seq and d["depends_on_event_id"] in seq)
    base += dep_count * 4
    return round(min(max(base, 0), 100), 2)


def detect_and_store_conflicts(c, sim_id, sequences, events):
    for i, sq in enumerate(sequences):
        seq = sq["sequence"]
        ev_map = {e["event_id"]: e for e in events}
        for eid in seq:
            ev = ev_map.get(eid)
            if ev and ev["failure_probability"] > 0.7:
                c.execute("""INSERT INTO conflicts (simulation_id, sequence_id, conflict_type, severity_level, description)
                             VALUES (?,?,?,?,?)""",
                          (sim_id, i, "Cascading Failure", "High",
                           f"Event {ev['event_name']} has high failure probability ({ev['failure_probability']:.0%})"))
        if len(seq) > 6:
            c.execute("""INSERT INTO conflicts (simulation_id, sequence_id, conflict_type, severity_level, description)
                         VALUES (?,?,?,?,?)""",
                      (sim_id, i, "Complex Chain", "Medium", f"Sequence has {len(seq)} events — high interdependency risk"))
        for j in range(len(seq) - 1):
            ev_a = ev_map.get(seq[j])
            ev_b = ev_map.get(seq[j + 1])
            if ev_a and ev_b and ev_a["priority_level"] < ev_b["priority_level"]:
                c.execute("""INSERT INTO conflicts (simulation_id, sequence_id, conflict_type, severity_level, description)
                             VALUES (?,?,?,?,?)""",
                          (sim_id, i, "Priority Paradox", "Low",
                           f"Low-priority event '{ev_a['event_name']}' precedes high-priority '{ev_b['event_name']}'"))
                break


def get_simulations():
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT s.*, u.full_name FROM simulations s LEFT JOIN users u ON s.created_by=u.user_id ORDER BY s.simulation_id DESC""")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_simulation_sequences(sim_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM sequences WHERE simulation_id=? ORDER BY risk_score DESC", (sim_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_simulation_conflicts(sim_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM conflicts WHERE simulation_id=? ORDER BY severity_level", (sim_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_all_users():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id, full_name, username, role, status, created_at FROM users ORDER BY user_id")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def update_user_role(uid, role, status):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET role=?, status=? WHERE user_id=?", (role, status, uid))
    conn.commit()
    conn.close()


def delete_user(uid, current_uid):
    if uid == current_uid:
        return False, "Cannot delete your own account."
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET status='inactive' WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()
    log_action(current_uid, "Deactivate User", str(uid))
    return True, "User deactivated."


def get_audit_logs():
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT al.*, u.full_name, u.username FROM audit_logs al 
                 LEFT JOIN users u ON al.user_id=u.user_id 
                 ORDER BY al.log_id DESC LIMIT 200""")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def create_backup(user_id):
    backup_data = {
        "events": get_all_events(),
        "dependencies": get_dependencies(),
        "simulations": get_simulations(),
        "timestamp": datetime.now().isoformat()
    }
    backup_json = json.dumps(backup_data, default=str, indent=2)
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO backups (created_by, backup_location, restore_status) VALUES (?,?,?)",
              (user_id, "local_backup.json", "available"))
    conn.commit()
    conn.close()
    log_action(user_id, "Create Backup")
    return backup_json


def generate_report_data(sim_id, user_id):
    seqs = get_simulation_sequences(sim_id)
    conflicts = get_simulation_conflicts(sim_id)
    events = get_all_events()
    ev_map = {e["event_id"]: e["event_name"] for e in events}
    report_rows = []
    for sq in seqs:
        seq_ids = json.loads(sq["sequence_order"]) if sq["sequence_order"] else []
        names = [ev_map.get(i, str(i)) for i in seq_ids]
        report_rows.append({
            "Sequence": " → ".join(names),
            "Risk Score": sq["risk_score"],
            "Likelihood": sq["likelihood_score"],
            "Conflicts": "Yes" if sq["conflict_flag"] else "No",
            "Remarks": sq["remarks"] or ""
        })
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO reports (simulation_id, report_name, report_type, created_by) VALUES (?,?,?,?)",
              (sim_id, f"Report_Sim{sim_id}_{datetime.now().strftime('%Y%m%d')}", "CSV", user_id))
    conn.commit()
    conn.close()
    log_action(user_id, "Generate Report", str(sim_id))
    output = StringIO()
    if report_rows:
        writer = csv.DictWriter(output, fieldnames=report_rows[0].keys())
        writer.writeheader()
        writer.writerows(report_rows)
    return output.getvalue(), conflicts


def search_events(keyword):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM events WHERE status='active' AND (event_name LIKE ? OR description LIKE ?)",
              (f"%{keyword}%", f"%{keyword}%"))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def build_dependency_graph():
    events = get_all_events()
    deps = get_dependencies()
    fig, ax = plt.subplots(figsize=(12, 8), facecolor="#060c12")
    ax.set_facecolor("#060c12")
    if not events:
        ax.text(0.5, 0.5, "No events defined", ha="center", va="center",
                color="#3d6080", fontsize=16, fontname="monospace")
        ax.axis("off")
        return fig
    G = nx.DiGraph()
    ev_map = {}
    for ev in events:
        G.add_node(ev["event_id"], label=ev["event_name"], risk=ev["failure_probability"])
        ev_map[ev["event_id"]] = ev
    for dep in deps:
        G.add_edge(dep["depends_on_event_id"], dep["event_id"])
    try:
        pos = nx.spring_layout(G, k=2.5, iterations=50, seed=42)
    except Exception:
        pos = nx.circular_layout(G)
    risk_vals = [ev_map.get(n, {}).get("failure_probability", 0) for n in G.nodes()]
    node_colors = []
    for r in risk_vals:
        if r > 0.6:
            node_colors.append("#ff3b30")
        elif r > 0.3:
            node_colors.append("#f5a623")
        else:
            node_colors.append("#00d4ff")
    node_sizes = [800 + ev_map.get(n, {}).get("priority_level", 1) * 200 for n in G.nodes()]
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=node_sizes, alpha=0.9)
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#0088cc", arrows=True,
                           arrowsize=20, width=1.5, alpha=0.7,
                           connectionstyle="arc3,rad=0.1")
    labels = {n: G.nodes[n].get("label", str(n))[:14] for n in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, ax=ax, font_color="#e8f4fd",
                            font_size=8, font_family="monospace")
    legend_items = [
        mpatches.Patch(color="#ff3b30", label="High Risk (>60%)"),
        mpatches.Patch(color="#f5a623", label="Medium Risk (30-60%)"),
        mpatches.Patch(color="#00d4ff", label="Low Risk (<30%)"),
    ]
    ax.legend(handles=legend_items, loc="upper left", facecolor="#0a1420",
              edgecolor="#162537", labelcolor="#7fa8c9", fontsize=9)
    ax.set_title("Event Dependency Network", color="#e8f4fd", fontsize=14,
                 fontweight="bold", pad=20)
    ax.axis("off")
    plt.tight_layout()
    return fig


def build_gantt_chart(sim_id=None):
    events = get_all_events()
    fig, ax = plt.subplots(figsize=(14, max(4, len(events) * 0.7 + 2)), facecolor="#060c12")
    ax.set_facecolor("#0a1420")
    if not events:
        ax.text(0.5, 0.5, "No events defined", ha="center", va="center",
                color="#3d6080", fontsize=16)
        ax.axis("off")
        return fig
    colors = ["#00d4ff", "#00e5a0", "#f5a623", "#ff6b35", "#8b5cf6", "#ff3b30"]
    start_times = {}
    current = 0
    sorted_events = sorted(events, key=lambda e: e["priority_level"], reverse=True)
    for ev in sorted_events:
        start_times[ev["event_id"]] = current
        current += ev["duration"] + random.uniform(0.1, 0.5)
    for i, ev in enumerate(sorted_events):
        color = colors[i % len(colors)]
        start = start_times[ev["event_id"]]
        dur = ev["duration"]
        ax.barh(i, dur, left=start, height=0.6, color=color, alpha=0.8,
                edgecolor="#060c12", linewidth=0.5)
        ax.barh(i, dur * ev["failure_probability"], left=start, height=0.6,
                color="#ff3b30", alpha=0.35)
        ax.text(start + dur / 2, i, ev["event_name"][:18],
                va="center", ha="center", color="#e8f4fd",
                fontsize=8, fontweight="bold")
    ax.set_yticks(range(len(sorted_events)))
    ax.set_yticklabels([f"#{e['event_id']} {e['event_name'][:16]}" for e in sorted_events],
                       color="#7fa8c9", fontsize=8)
    ax.set_xlabel("Time Units", color="#7fa8c9", fontsize=10)
    ax.set_title("Event Timeline — Gantt View", color="#e8f4fd", fontsize=14, fontweight="bold", pad=16)
    ax.tick_params(colors="#3d6080")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#162537")
    ax.spines["bottom"].set_color("#162537")
    ax.grid(axis="x", color="#162537", linestyle="--", linewidth=0.5, alpha=0.7)
    plt.tight_layout()
    return fig


def build_risk_radar(sim_id):
    seqs = get_simulation_sequences(sim_id)
    if not seqs:
        fig, ax = plt.subplots(figsize=(8, 8), facecolor="#060c12")
        ax.set_facecolor("#060c12")
        ax.text(0.5, 0.5, "Run a simulation first", ha="center", va="center", color="#3d6080", fontsize=14)
        ax.axis("off")
        return fig
    risks = [sq["risk_score"] for sq in seqs]
    likes = [sq["likelihood_score"] * 100 for sq in seqs]
    conflicts = [sq["conflict_flag"] * 30 for sq in seqs]
    categories = ["Risk", "Likelihood", "Conflict", "Complexity", "Priority Weight", "Failure Exposure"]
    N = len(categories)
    angles = [n / float(N) * 2 * math.pi for n in range(N)]
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True), facecolor="#060c12")
    ax.set_facecolor("#060c12")
    avg_risk = sum(risks) / len(risks)
    avg_like = sum(likes) / len(likes)
    avg_conf = sum(conflicts) / len(conflicts)
    values = [avg_risk, avg_like, avg_conf, len(seqs) * 5, 45, avg_risk * 0.8]
    values += values[:1]
    ax.plot(angles, values, color="#00d4ff", linewidth=2, linestyle="solid")
    ax.fill(angles, values, color="#00d4ff", alpha=0.15)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, color="#7fa8c9", fontsize=9)
    ax.set_ylim(0, 100)
    ax.yaxis.set_tick_params(labelcolor="#3d6080", labelsize=7)
    ax.set_facecolor("#0a1420")
    ax.spines["polar"].set_color("#162537")
    ax.grid(color="#162537", linewidth=0.8)
    ax.set_title("Risk Radar Analysis", color="#e8f4fd", fontsize=14, fontweight="bold", pad=20)
    plt.tight_layout()
    return fig


def build_risk_histogram(sim_id):
    seqs = get_simulation_sequences(sim_id)
    fig, ax = plt.subplots(figsize=(12, 5), facecolor="#060c12")
    ax.set_facecolor("#0a1420")
    if not seqs:
        ax.text(0.5, 0.5, "No simulation data", ha="center", va="center", color="#3d6080", fontsize=14)
        ax.axis("off")
        return fig
    risks = [sq["risk_score"] for sq in seqs]
    n, bins, patches = ax.hist(risks, bins=min(len(risks), 12), edgecolor="#060c12", linewidth=0.5)
    for i, patch in enumerate(patches):
        val = bins[i]
        if val > 70:
            patch.set_facecolor("#ff3b30")
        elif val > 40:
            patch.set_facecolor("#f5a623")
        else:
            patch.set_facecolor("#00d4ff")
        patch.set_alpha(0.85)
    ax.axvline(sum(risks) / len(risks), color="#00e5a0", linewidth=2, linestyle="--",
               label=f"Mean: {sum(risks)/len(risks):.1f}")
    ax.set_xlabel("Risk Score", color="#7fa8c9", fontsize=11)
    ax.set_ylabel("Frequency", color="#7fa8c9", fontsize=11)
    ax.set_title("Risk Score Distribution", color="#e8f4fd", fontsize=14, fontweight="bold", pad=16)
    ax.tick_params(colors="#3d6080")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#162537")
    ax.spines["bottom"].set_color("#162537")
    ax.legend(facecolor="#0a1420", edgecolor="#162537", labelcolor="#7fa8c9")
    plt.tight_layout()
    return fig


def build_3d_surface(sim_id):
    seqs = get_simulation_sequences(sim_id)
    fig = plt.figure(figsize=(12, 8), facecolor="#060c12")
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor("#060c12")
    if not seqs:
        ax.text(0.5, 0.5, 0.5, "No simulation data", ha="center", va="center", color="#3d6080", fontsize=14)
        return fig
    n = max(len(seqs), 4)
    x = np.linspace(0, 10, n)
    y = np.linspace(0, 10, n)
    X, Y = np.meshgrid(x, y)
    risks = [sq["risk_score"] for sq in seqs]
    while len(risks) < n:
        risks.append(risks[-1] if risks else 50)
    risks_arr = np.array(risks[:n])
    Z = np.outer(np.sin(np.linspace(0, np.pi, n)), risks_arr / 100 * 5)
    Z += np.random.normal(0, 0.2, Z.shape)
    surf = ax.plot_surface(X, Y, Z, cmap="coolwarm", alpha=0.85, linewidth=0, antialiased=True)
    fig.colorbar(surf, ax=ax, shrink=0.4, aspect=10, pad=0.1,
                 label="Risk Intensity").ax.yaxis.label.set_color("#7fa8c9")
    ax.set_xlabel("Sequence Index", color="#7fa8c9", fontsize=9, labelpad=10)
    ax.set_ylabel("Event Depth", color="#7fa8c9", fontsize=9, labelpad=10)
    ax.set_zlabel("Risk Score", color="#7fa8c9", fontsize=9, labelpad=10)
    ax.set_title("3D Risk Surface — Stochastic Landscape", color="#e8f4fd", fontsize=13, fontweight="bold", pad=20)
    ax.tick_params(colors="#3d6080", labelsize=7)
    ax.grid(color="#162537", linewidth=0.3)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor("#162537")
    ax.yaxis.pane.set_edgecolor("#162537")
    ax.zaxis.pane.set_edgecolor("#162537")
    plt.tight_layout()
    return fig


def build_bubble_chart(sim_id):
    seqs = get_simulation_sequences(sim_id)
    events = get_all_events()
    fig, ax = plt.subplots(figsize=(12, 7), facecolor="#060c12")
    ax.set_facecolor("#0a1420")
    if not seqs or not events:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center", color="#3d6080", fontsize=14)
        ax.axis("off")
        return fig
    x = [sq["likelihood_score"] * 100 for sq in seqs]
    y = [sq["risk_score"] for sq in seqs]
    sizes = [200 + (sq["conflict_flag"] * 300) for sq in seqs]
    colors_list = ["#ff3b30" if sq["conflict_flag"] else "#00d4ff" for sq in seqs]
    scatter = ax.scatter(x, y, s=sizes, c=colors_list, alpha=0.7, edgecolors="#060c12", linewidth=1.5)
    for i, sq in enumerate(seqs):
        ax.annotate(f"S{i+1}", (x[i], y[i]), ha="center", va="center",
                    color="#e8f4fd", fontsize=8, fontweight="bold")
    ax.set_xlabel("Likelihood (%)", color="#7fa8c9", fontsize=11)
    ax.set_ylabel("Risk Score", color="#7fa8c9", fontsize=11)
    ax.set_title("Sequence Risk vs Likelihood Bubble Chart", color="#e8f4fd", fontsize=14, fontweight="bold", pad=16)
    ax.tick_params(colors="#3d6080")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#162537")
    ax.spines["bottom"].set_color("#162537")
    ax.grid(color="#162537", linestyle="--", linewidth=0.5, alpha=0.5)
    legend_items = [
        mpatches.Patch(color="#ff3b30", label="Has Conflicts"),
        mpatches.Patch(color="#00d4ff", label="No Conflicts"),
    ]
    ax.legend(handles=legend_items, facecolor="#0a1420", edgecolor="#162537", labelcolor="#7fa8c9")
    plt.tight_layout()
    return fig


def role_badge(role):
    colors = {
        "Administrator": "violet",
        "Event Planner": "primary",
        "Analyst": "emerald",
        "Observer": "gold"
    }
    c = colors.get(role, "primary")
    return f'<span class="es-badge es-badge-{c}">{role}</span>'


def severity_chip(sev):
    m = {"High": "chip-red", "Medium": "chip-yellow", "Low": "chip-green"}
    return f'<span class="es-chip {m.get(sev, "chip-blue")}">{sev}</span>'


def risk_color_class(score):
    if score > 65:
        return "es-risk-high"
    elif score > 35:
        return "es-risk-medium"
    return "es-risk-low"


def render_topbar(user):
    role = user.get("role", "Observer")
    name = user.get("full_name", "User")
    initials = "".join([p[0].upper() for p in name.split()[:2]])
    rb = role_badge(role)
    st.markdown(f"""
    <div class="es-topbar">
        <div class="es-logo">
            <div class="es-logo-mark">E</div>
            <div class="es-logo-text">Emergi<span>Sim</span></div>
        </div>
        <div style="display:flex;align-items:center;gap:24px;">
            <span class="es-badge es-badge-emerald"><span class="es-activity-dot"></span>LIVE</span>
            {rb}
            <div class="es-avatar">{initials}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_nav(current_page, role):
    nav_items = []
    all_pages = [
        ("Dashboard", "dashboard", ["Administrator", "Event Planner", "Analyst", "Observer"]),
        ("Events", "events", ["Administrator", "Event Planner"]),
        ("Dependencies", "dependencies", ["Administrator", "Event Planner"]),
        ("Simulation", "simulation", ["Administrator", "Event Planner", "Analyst"]),
        ("Analytics", "analytics", ["Administrator", "Analyst", "Observer"]),
        ("Reports", "reports", ["Administrator", "Analyst"]),
        ("Administration", "admin", ["Administrator"]),
    ]
    cols = st.columns(len([p for p in all_pages if role in p[2]]) + 1)
    idx = 0
    allowed = [(label, key) for label, key, roles in all_pages if role in roles]
    for label, key in allowed:
        active = "active" if current_page == key else ""
        with cols[idx]:
            if st.button(label, key=f"nav_{key}"):
                st.session_state["page"] = key
                st.rerun()
        idx += 1
    with cols[-1]:
        if st.button("Sign Out", key="nav_signout"):
            st.session_state.clear()
            st.rerun()


def page_dashboard(user):
    events = get_all_events()
    sims = get_simulations()
    deps = get_dependencies()
    users = get_all_users()
    completed_sims = [s for s in sims if s["run_status"] == "completed"]
    total_risk = 0
    if completed_sims:
        last_sim = completed_sims[0]
        seqs = get_simulation_sequences(last_sim["simulation_id"])
        total_risk = max([sq["risk_score"] for sq in seqs], default=0)
    st.markdown("""
    <div class="es-page-header">
        <div class="es-section-label">Mission Control</div>
        <div class="es-page-title">Simulation Command Center</div>
        <div class="es-page-desc">Real-time emergent behavior intelligence — monitor, analyze, and act.</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div style="padding: 32px 80px;">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class="es-stat-card">
            <div class="es-stat-num">{len(events)}</div>
            <div class="es-stat-label">Active Events</div>
            <div class="es-stat-sub">Configured for simulation</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="es-stat-card">
            <div class="es-stat-num">{len(deps)}</div>
            <div class="es-stat-label">Dependencies</div>
            <div class="es-stat-sub">Dependency relationships</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="es-stat-card">
            <div class="es-stat-num">{len(completed_sims)}</div>
            <div class="es-stat-label">Simulations Run</div>
            <div class="es-stat-sub">Completed runs</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        risk_class = risk_color_class(total_risk)
        st.markdown(f"""<div class="es-stat-card">
            <div class="es-stat-num {risk_class}">{total_risk:.0f}</div>
            <div class="es-stat-label">Peak Risk Score</div>
            <div class="es-stat-sub">Highest across last sim</div>
        </div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class="es-stat-card">
            <div class="es-stat-num">{len(users)}</div>
            <div class="es-stat-label">System Users</div>
            <div class="es-stat-sub">Registered accounts</div>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="es-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div style="padding: 40px 80px;">', unsafe_allow_html=True)
    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.markdown('<div class="es-section-label">Dependency Network</div>', unsafe_allow_html=True)
        st.markdown('<div class="es-section-title" style="font-size:22px;margin-bottom:24px;">Event Relationship Graph</div>', unsafe_allow_html=True)
        fig = build_dependency_graph()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    with col_right:
        st.markdown('<div class="es-section-label">Recent Activity</div>', unsafe_allow_html=True)
        st.markdown('<div class="es-section-title" style="font-size:22px;margin-bottom:24px;">Audit Trail</div>', unsafe_allow_html=True)
        logs = get_audit_logs()[:10]
        if logs:
            for log in logs:
                uname = log.get("username", "system")
                st.markdown(f"""<div class="es-log-item">
                    <div class="es-log-time">{log['action_time']} — {uname}</div>
                    <div class="es-log-action">{log['action_type']} · {log.get('target_record', '')}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="es-empty-state">
                <div class="es-empty-icon">⬡</div>
                <div class="es-empty-title">No activity yet</div>
            </div>""", unsafe_allow_html=True)
        st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="es-section-label">Quick Actions</div>', unsafe_allow_html=True)
        if user["role"] in ["Administrator", "Event Planner"]:
            if st.button("Create New Event", key="dash_create_event"):
                st.session_state["page"] = "events"
                st.rerun()
        if user["role"] in ["Administrator", "Event Planner", "Analyst"]:
            if st.button("Run Simulation", key="dash_run_sim"):
                st.session_state["page"] = "simulation"
                st.rerun()
        if st.button("View Analytics", key="dash_analytics"):
            st.session_state["page"] = "analytics"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    if events:
        st.markdown('<div class="es-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div style="padding: 40px 80px;">', unsafe_allow_html=True)
        st.markdown('<div class="es-section-label">Timeline Preview</div>', unsafe_allow_html=True)
        st.markdown('<div class="es-section-title" style="font-size:22px;margin-bottom:24px;">Event Gantt Chart</div>', unsafe_allow_html=True)
        fig_g = build_gantt_chart()
        st.pyplot(fig_g, use_container_width=True)
        plt.close(fig_g)
        st.markdown('</div>', unsafe_allow_html=True)


def page_events(user):
    st.markdown("""
    <div class="es-page-header">
        <div class="es-section-label">Event Management</div>
        <div class="es-page-title">Define Simulation Events</div>
        <div class="es-page-desc">Create, configure, and manage all events that participate in stochastic simulations.</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div style="padding: 32px 80px;">', unsafe_allow_html=True)
    tab_sel = st.radio("", ["Event Library", "Create Event", "Import / Export", "Search Events"], horizontal=True, key="events_tab")
    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
    if tab_sel == "Event Library":
        events = get_all_events()
        if not events:
            st.markdown("""<div class="es-empty-state">
                <div class="es-empty-icon">⬡</div>
                <div class="es-empty-title">No events defined yet</div>
                <div class="es-empty-desc">Switch to "Create Event" tab to add your first event.</div>
            </div>""", unsafe_allow_html=True)
        else:
            for ev in events:
                risk_cls = risk_color_class(ev["failure_probability"] * 100)
                opt_badge = '<span class="es-chip es-chip-yellow">Optional</span>' if ev["optional_flag"] else '<span class="es-chip es-chip-blue">Mandatory</span>'
                with st.expander(f"#{ev['event_id']}  {ev['event_name']}  |  Duration: {ev['duration']} units  |  P(success): {ev['probability']*100:.0f}%"):
                    ec1, ec2, ec3, ec4 = st.columns(4)
                    with ec1:
                        st.markdown(f"**Description:** {ev['description'] or '—'}")
                        st.markdown(f"**Priority Level:** {ev['priority_level']}")
                    with ec2:
                        st.markdown(f"**Failure Prob:** <span class='{risk_cls}'>{ev['failure_probability']*100:.1f}%</span>", unsafe_allow_html=True)
                        st.markdown(f"**Type:** {opt_badge}", unsafe_allow_html=True)
                    with ec3:
                        st.markdown(f"**Created:** {ev.get('created_at','—')[:10]}")
                    with ec4:
                        if user["role"] in ["Administrator", "Event Planner"]:
                            if st.button("Edit", key=f"edit_ev_{ev['event_id']}"):
                                st.session_state["edit_event_id"] = ev["event_id"]
                                st.session_state["events_tab_override"] = "Create Event"
                                st.rerun()
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if st.button("Clone", key=f"clone_ev_{ev['event_id']}"):
                                    clone_event(ev["event_id"], user["user_id"])
                                    st.success("Event cloned!")
                                    st.rerun()
                            with col_b:
                                if st.button("Delete", key=f"del_ev_{ev['event_id']}"):
                                    delete_event(ev["event_id"], user["user_id"])
                                    st.success("Event deleted.")
                                    st.rerun()

    elif tab_sel == "Create Event":
        edit_id = st.session_state.get("edit_event_id")
        existing = get_event_by_id(edit_id) if edit_id else None
        title = "Edit Event" if existing else "Create New Event"
        st.markdown(f'<div class="es-section-title" style="font-size:24px;margin-bottom:28px;">{title}</div>', unsafe_allow_html=True)
        st.markdown('<div class="es-form-section">', unsafe_allow_html=True)
        with st.form("create_event_form"):
            fc1, fc2 = st.columns(2)
            with fc1:
                ev_name = st.text_input("Event Name", value=existing["event_name"] if existing else "")
                ev_desc = st.text_area("Description", value=existing["description"] if existing else "", height=80)
                ev_duration = st.number_input("Duration (time units)", min_value=0.1, max_value=1000.0, step=0.5,
                                               value=float(existing["duration"]) if existing else 1.0)
            with fc2:
                ev_prob = st.slider("Probability of Occurrence", 0.0, 1.0,
                                    float(existing["probability"]) if existing else 0.9, 0.01,
                                    format="%.2f")
                ev_fail = st.slider("Failure Probability", 0.0, 1.0,
                                    float(existing["failure_probability"]) if existing else 0.0, 0.01,
                                    format="%.2f")
                ev_priority = st.selectbox("Priority Level", [1, 2, 3, 4, 5],
                                           index=(existing["priority_level"] - 1) if existing else 0)
                ev_optional = st.checkbox("Mark as Optional", value=bool(existing["optional_flag"]) if existing else False)
            submitted = st.form_submit_button("Save Event" if existing else "Create Event")
            if submitted:
                if not ev_name.strip():
                    st.error("Event name is required.")
                else:
                    if existing:
                        update_event(edit_id, ev_name, ev_desc, ev_duration, ev_prob,
                                     ev_priority, ev_optional, ev_fail, user["user_id"])
                        st.session_state.pop("edit_event_id", None)
                        st.success(f"Event '{ev_name}' updated successfully.")
                    else:
                        eid = create_event(ev_name, ev_desc, ev_duration, ev_prob,
                                           ev_priority, ev_optional, ev_fail, user["user_id"])
                        st.success(f"Event '{ev_name}' created (ID: {eid})")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        if existing:
            if st.button("Cancel Edit"):
                st.session_state.pop("edit_event_id", None)
                st.rerun()

    elif tab_sel == "Import / Export":
        ic1, ic2 = st.columns(2)
        with ic1:
            st.markdown('<div class="es-section-title" style="font-size:20px;margin-bottom:16px;">Import Events</div>', unsafe_allow_html=True)
            import_format = st.radio("Format", ["JSON", "CSV"], horizontal=True, key="import_format")
            uploaded = st.file_uploader("Upload File", type=["json", "csv"], key="event_import_file")
            if uploaded and st.button("Import", key="do_import"):
                content = uploaded.read().decode("utf-8")
                if import_format == "JSON":
                    ok, msg = import_events_json(content, user["user_id"])
                else:
                    ok, msg = import_events_csv(content, user["user_id"])
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
                st.rerun()
            st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="es-info-banner">⬡ JSON format: list of objects with event_name, description, duration, probability, priority_level, optional_flag, failure_probability fields.</div>', unsafe_allow_html=True)
        with ic2:
            st.markdown('<div class="es-section-title" style="font-size:20px;margin-bottom:16px;">Export Events</div>', unsafe_allow_html=True)
            exp_fmt = st.radio("Export Format", ["JSON", "CSV"], horizontal=True, key="export_format")
            if st.button("Generate Export", key="do_export"):
                if exp_fmt == "JSON":
                    data = export_events_json()
                    st.download_button("Download JSON", data, "emergisim_events.json", "application/json")
                else:
                    data = export_events_csv()
                    st.download_button("Download CSV", data, "emergisim_events.csv", "text/csv")

    elif tab_sel == "Search Events":
        st.markdown('<div class="es-section-title" style="font-size:20px;margin-bottom:16px;">Search Events</div>', unsafe_allow_html=True)
        kw = st.text_input("Search by name or description", placeholder="e.g. diagnose, restart, verify...")
        if kw:
            results = search_events(kw)
            if results:
                st.markdown(f'<div class="es-success-banner">Found {len(results)} matching event(s)</div>', unsafe_allow_html=True)
                for ev in results:
                    st.markdown(f"""<div class="es-card" style="margin-bottom:12px;">
                        <strong style="color:var(--text-primary);">#{ev['event_id']} — {ev['event_name']}</strong>
                        <div style="color:var(--text-muted);font-size:12px;margin-top:4px;">{ev['description'] or 'No description'}</div>
                        <div style="margin-top:12px;display:flex;gap:12px;">
                            <span class="es-chip es-chip-blue">Duration: {ev['duration']}u</span>
                            <span class="es-chip es-chip-green">P: {ev['probability']*100:.0f}%</span>
                            <span class="es-chip es-chip-yellow">Priority: {ev['priority_level']}</span>
                        </div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown('<div class="es-warning-banner">No events matched your search.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def page_dependencies(user):
    st.markdown("""
    <div class="es-page-header">
        <div class="es-section-label">Dependency Management</div>
        <div class="es-page-title">Event Dependency Graph</div>
        <div class="es-page-desc">Define which events must precede others. The system validates all relationships for cycles and conflicts.</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div style="padding: 32px 80px;">', unsafe_allow_html=True)
    valid, msg = validate_dependencies_db()
    if valid:
        st.markdown(f'<div class="es-success-banner">✓ {msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="es-error-banner">✗ {msg}</div>', unsafe_allow_html=True)
    tab_d = st.radio("", ["View Dependencies", "Add Dependency", "Visualization"], horizontal=True, key="dep_tab")
    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
    if tab_d == "View Dependencies":
        deps = get_dependencies()
        if not deps:
            st.markdown("""<div class="es-empty-state">
                <div class="es-empty-icon">⬡</div>
                <div class="es-empty-title">No dependencies defined</div>
                <div class="es-empty-desc">Add dependencies to model event sequencing constraints.</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<table class="es-table"><thead><tr>
                <th>ID</th><th>Event</th><th>Depends On</th><th>Type</th><th>Condition</th><th>Action</th>
            </tr></thead><tbody>""", unsafe_allow_html=True)
            for dep in deps:
                dep_type_chip = f'<span class="es-chip es-chip-blue">{dep["dependency_type"]}</span>'
                st.markdown(f"""<tr>
                    <td>{dep['dependency_id']}</td>
                    <td>{dep['from_name']}</td>
                    <td>{dep['to_name']}</td>
                    <td>{dep_type_chip}</td>
                    <td>{dep['condition_rule'] or '—'}</td>
                    <td></td>
                </tr>""", unsafe_allow_html=True)
            st.markdown("</tbody></table>", unsafe_allow_html=True)
            st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
            for dep in deps:
                col_del = st.columns([6, 1])[1]
                with col_del:
                    if st.button("Remove", key=f"del_dep_{dep['dependency_id']}"):
                        delete_dependency(dep["dependency_id"], user["user_id"])
                        st.success("Dependency removed.")
                        st.rerun()

    elif tab_d == "Add Dependency":
        events = get_all_events()
        if len(events) < 2:
            st.markdown('<div class="es-warning-banner">You need at least 2 events to create dependencies.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="es-form-section">', unsafe_allow_html=True)
            with st.form("add_dep_form"):
                ev_options = {f"#{e['event_id']} {e['event_name']}": e["event_id"] for e in events}
                da1, da2 = st.columns(2)
                with da1:
                    dep_from = st.selectbox("Event (Depends On)", list(ev_options.keys()), key="dep_from")
                with da2:
                    dep_to = st.selectbox("Must Complete First", list(ev_options.keys()), key="dep_to")
                da3, da4 = st.columns(2)
                with da3:
                    dep_type = st.selectbox("Dependency Type", ["requires", "triggers", "blocks", "optional"])
                with da4:
                    dep_cond = st.text_input("Condition Rule (optional)", placeholder="e.g. success_only")
                dep_submitted = st.form_submit_button("Add Dependency")
                if dep_submitted:
                    from_id = ev_options[dep_from]
                    to_id = ev_options[dep_to]
                    if from_id == to_id:
                        st.error("An event cannot depend on itself.")
                    else:
                        ok, msg2 = add_dependency(from_id, to_id, dep_type, dep_cond, user["user_id"])
                        if ok:
                            valid2, vmsg = validate_dependencies_db()
                            if not valid2:
                                delete_dependency_by_pair(from_id, to_id)
                                st.error(f"Dependency would create a cycle: {vmsg}")
                            else:
                                st.success(msg2)
                                st.rerun()
                        else:
                            st.error(msg2)
            st.markdown('</div>', unsafe_allow_html=True)

    elif tab_d == "Visualization":
        st.markdown('<div class="es-section-title" style="font-size:20px;margin-bottom:16px;">Network Visualization</div>', unsafe_allow_html=True)
        fig = build_dependency_graph()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    st.markdown('</div>', unsafe_allow_html=True)


def delete_dependency_by_pair(event_id, depends_on):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM dependencies WHERE event_id=? AND depends_on_event_id=?", (event_id, depends_on))
    conn.commit()
    conn.close()


def page_simulation(user):
    st.markdown("""
    <div class="es-page-header">
        <div class="es-section-label">Simulation Engine</div>
        <div class="es-page-title">Stochastic Simulation Runner</div>
        <div class="es-page-desc">Generate all possible event sequences under uncertainty. Detect deadlocks, paradoxes, and cascading failures.</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div style="padding: 32px 80px;">', unsafe_allow_html=True)
    sim_tab = st.radio("", ["Run Simulation", "Simulation History", "Sequence Analysis"], horizontal=True, key="sim_tab")
    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
    if sim_tab == "Run Simulation":
        events = get_all_events()
        if not events:
            st.markdown('<div class="es-warning-banner">No events defined. Create events first before running a simulation.</div>', unsafe_allow_html=True)
        else:
            valid, vmsg = validate_dependencies_db()
            if not valid:
                st.markdown(f'<div class="es-error-banner">✗ Dependency error: {vmsg}</div>', unsafe_allow_html=True)
            col_form, col_preview = st.columns([2, 3])
            with col_form:
                st.markdown('<div class="es-form-section">', unsafe_allow_html=True)
                with st.form("run_sim_form"):
                    sim_name = st.text_input("Simulation Name", placeholder="e.g. IT Outage Scenario - Run 1")
                    num_seqs = st.slider("Number of Sequences to Generate", 4, 50, 8)
                    run_partial = st.checkbox("Run Partial Simulation (random subset)")
                    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
                    run_submitted = st.form_submit_button("Launch Simulation")
                    if run_submitted:
                        if not sim_name.strip():
                            sim_name = f"Simulation {datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        if not valid:
                            st.error("Fix dependency errors before running simulation.")
                        else:
                            with st.spinner("Running stochastic simulation..."):
                                sim_id, result_msg = run_simulation_engine(sim_name, user["user_id"], num_seqs)
                            if sim_id:
                                st.success(result_msg)
                                st.session_state["last_sim_id"] = sim_id
                                st.rerun()
                            else:
                                st.error(result_msg)
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
                if st.button("Validate Dependencies Before Run", key="validate_before_run"):
                    ok, msg = validate_dependencies_db()
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
            with col_preview:
                st.markdown('<div class="es-card">', unsafe_allow_html=True)
                st.markdown('<div class="es-section-label">Simulation Preview</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="color:var(--text-secondary);font-size:14px;margin-bottom:20px;">{len(events)} events loaded and ready for simulation.</div>', unsafe_allow_html=True)
                for ev in events[:8]:
                    risk_pct = ev["failure_probability"] * 100
                    risk_cls = risk_color_class(risk_pct)
                    opt = "Optional" if ev["optional_flag"] else "Mandatory"
                    st.markdown(f"""<div style="padding:12px 0;border-bottom:1px solid var(--border-subtle);">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="color:var(--text-primary);font-weight:500;font-size:13px;">#{ev['event_id']} {ev['event_name']}</span>
                            <span class="es-chip es-chip-{'yellow' if ev['optional_flag'] else 'blue'}">{opt}</span>
                        </div>
                        <div style="display:flex;gap:16px;margin-top:8px;font-size:12px;color:var(--text-muted);">
                            <span>Duration: {ev['duration']}u</span>
                            <span>P: {ev['probability']*100:.0f}%</span>
                            <span class="{risk_cls}">Fail: {risk_pct:.0f}%</span>
                            <span>Priority: {ev['priority_level']}</span>
                        </div>
                    </div>""", unsafe_allow_html=True)
                if len(events) > 8:
                    st.markdown(f'<div style="color:var(--text-muted);font-size:12px;padding-top:8px;">...and {len(events)-8} more events</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    elif sim_tab == "Simulation History":
        sims = get_simulations()
        if not sims:
            st.markdown("""<div class="es-empty-state">
                <div class="es-empty-icon">⬡</div>
                <div class="es-empty-title">No simulations run yet</div>
            </div>""", unsafe_allow_html=True)
        else:
            for sim in sims:
                status_chip = f'<span class="es-chip {"es-chip-green" if sim["run_status"]=="completed" else "es-chip-yellow"}">{sim["run_status"].upper()}</span>'
                with st.expander(f"{sim['simulation_name']}  |  {sim['start_timestamp'][:16] if sim['start_timestamp'] else 'N/A'}  |  {sim['total_sequences']} sequences"):
                    sc1, sc2, sc3 = st.columns(3)
                    with sc1:
                        st.markdown(f"**Status:** {status_chip}", unsafe_allow_html=True)
                        st.markdown(f"**Created by:** {sim.get('full_name','—')}")
                    with sc2:
                        st.markdown(f"**Started:** {sim['start_timestamp'][:19] if sim['start_timestamp'] else 'N/A'}")
                        st.markdown(f"**Completed:** {sim['end_timestamp'][:19] if sim['end_timestamp'] else 'N/A'}")
                    with sc3:
                        st.markdown(f"**Sequences:** {sim['total_sequences']}")
                        if st.button("Analyze", key=f"analyze_sim_{sim['simulation_id']}"):
                            st.session_state["selected_sim_id"] = sim["simulation_id"]
                            st.session_state["page"] = "analytics"
                            st.rerun()

    elif sim_tab == "Sequence Analysis":
        sims = get_simulations()
        completed = [s for s in sims if s["run_status"] == "completed"]
        if not completed:
            st.markdown('<div class="es-warning-banner">Run a simulation first to view sequence analysis.</div>', unsafe_allow_html=True)
        else:
            sim_choices = {f"{s['simulation_name']} ({s['start_timestamp'][:16]})": s["simulation_id"] for s in completed}
            selected_name = st.selectbox("Select Simulation", list(sim_choices.keys()), key="seq_anal_sel")
            sim_id = sim_choices[selected_name]
            seqs = get_simulation_sequences(sim_id)
            events = get_all_events()
            ev_map = {e["event_id"]: e["event_name"] for e in events}
            if seqs:
                sorted_seqs = sorted(seqs, key=lambda x: x["risk_score"], reverse=True)
                for i, sq in enumerate(sorted_seqs):
                    seq_ids = json.loads(sq["sequence_order"]) if sq["sequence_order"] else []
                    names = " → ".join([ev_map.get(eid, f"#{eid}") for eid in seq_ids])
                    risk_cls = risk_color_class(sq["risk_score"])
                    conflict_badge = '<span class="es-chip es-chip-red">HAS CONFLICTS</span>' if sq["conflict_flag"] else '<span class="es-chip es-chip-green">CLEAN</span>'
                    st.markdown(f"""<div class="es-card" style="margin-bottom:12px;">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                            <div>
                                <div style="font-family:'Syne',sans-serif;font-size:12px;color:var(--text-muted);margin-bottom:6px;">SEQUENCE {i+1}</div>
                                <div style="color:var(--text-primary);font-size:13px;font-weight:500;line-height:1.6;">{names}</div>
                            </div>
                            <div style="text-align:right;flex-shrink:0;margin-left:24px;">
                                <div class="es-stat-num {risk_cls}" style="font-size:28px;">{sq['risk_score']:.1f}</div>
                                <div class="es-stat-label">Risk Score</div>
                            </div>
                        </div>
                        <div style="display:flex;gap:12px;margin-top:12px;align-items:center;">
                            {conflict_badge}
                            <span class="es-chip es-chip-blue">Likelihood: {sq['likelihood_score']*100:.0f}%</span>
                            <span style="font-size:12px;color:var(--text-muted);">{sq['remarks'] or ''}</span>
                        </div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown('<div class="es-empty-state"><div class="es-empty-title">No sequences found</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def page_analytics(user):
    st.markdown("""
    <div class="es-page-header">
        <div class="es-section-label">Analytics & Intelligence</div>
        <div class="es-page-title">Emergent Behavior Analysis</div>
        <div class="es-page-desc">Deep insights into stochastic outcomes, conflict detection, and risk intelligence across all simulation runs.</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div style="padding: 32px 80px;">', unsafe_allow_html=True)
    sims = get_simulations()
    completed = [s for s in sims if s["run_status"] == "completed"]
    if not completed:
        st.markdown("""<div class="es-empty-state">
            <div class="es-empty-icon">⬡</div>
            <div class="es-empty-title">No completed simulations</div>
            <div class="es-empty-desc">Run a simulation first to unlock analytics.</div>
        </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return
    sim_choices = {f"{s['simulation_name']} — {s['start_timestamp'][:16]}": s["simulation_id"] for s in completed}
    preselect_id = st.session_state.get("selected_sim_id")
    default_idx = 0
    if preselect_id:
        keys = list(sim_choices.keys())
        vals = list(sim_choices.values())
        if preselect_id in vals:
            default_idx = vals.index(preselect_id)
    selected_name = st.selectbox("Select Simulation to Analyze", list(sim_choices.keys()), index=default_idx, key="analytics_sim_sel")
    sim_id = sim_choices[selected_name]
    seqs = get_simulation_sequences(sim_id)
    conflicts = get_simulation_conflicts(sim_id)
    events = get_all_events()
    ev_map = {e["event_id"]: e["event_name"] for e in events}
    if not seqs:
        st.markdown('<div class="es-warning-banner">No sequence data for this simulation.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return
    risks = [sq["risk_score"] for sq in seqs]
    avg_risk = sum(risks) / len(risks)
    max_risk = max(risks)
    min_risk = min(risks)
    conflict_count = sum(1 for sq in seqs if sq["conflict_flag"])
    am1, am2, am3, am4 = st.columns(4)
    with am1:
        st.markdown(f"""<div class="es-stat-card">
            <div class="es-stat-num es-risk-high">{max_risk:.1f}</div>
            <div class="es-stat-label">Peak Risk</div></div>""", unsafe_allow_html=True)
    with am2:
        st.markdown(f"""<div class="es-stat-card">
            <div class="es-stat-num" style="color:var(--accent-gold)">{avg_risk:.1f}</div>
            <div class="es-stat-label">Average Risk</div></div>""", unsafe_allow_html=True)
    with am3:
        st.markdown(f"""<div class="es-stat-card">
            <div class="es-stat-num es-risk-low">{min_risk:.1f}</div>
            <div class="es-stat-label">Minimum Risk</div></div>""", unsafe_allow_html=True)
    with am4:
        st.markdown(f"""<div class="es-stat-card">
            <div class="es-stat-num es-risk-high">{conflict_count}</div>
            <div class="es-stat-label">Conflict Sequences</div></div>""", unsafe_allow_html=True)
    st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)
    an_tab = st.radio("", ["Risk Overview", "3D Surface", "Conflict Details", "Sequence Comparator", "Gantt Analysis"], horizontal=True, key="analytics_inner_tab")
    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
    if an_tab == "Risk Overview":
        rc1, rc2 = st.columns(2)
        with rc1:
            st.markdown('<div class="es-section-label">Bubble Analysis</div>', unsafe_allow_html=True)
            fig_b = build_bubble_chart(sim_id)
            st.pyplot(fig_b, use_container_width=True)
            plt.close(fig_b)
        with rc2:
            st.markdown('<div class="es-section-label">Risk Distribution</div>', unsafe_allow_html=True)
            fig_h = build_risk_histogram(sim_id)
            st.pyplot(fig_h, use_container_width=True)
            plt.close(fig_h)
        st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
        fig_r = build_risk_radar(sim_id)
        st.pyplot(fig_r, use_container_width=True)
        plt.close(fig_r)

    elif an_tab == "3D Surface":
        st.markdown('<div class="es-section-label">Stochastic Risk Landscape</div>', unsafe_allow_html=True)
        st.markdown('<div class="es-section-title" style="font-size:22px;margin-bottom:20px;">3D Risk Surface Visualization</div>', unsafe_allow_html=True)
        fig_3d = build_3d_surface(sim_id)
        st.pyplot(fig_3d, use_container_width=True)
        plt.close(fig_3d)
        st.markdown('<div class="es-info-banner">The 3D surface maps sequence index (X) against event depth (Y) showing risk intensity (Z). Red peaks indicate high-risk emergent zones.</div>', unsafe_allow_html=True)

    elif an_tab == "Conflict Details":
        if not conflicts:
            st.markdown('<div class="es-success-banner">No conflicts detected in this simulation run.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="es-error-banner">Found {len(conflicts)} conflict(s) requiring attention.</div>', unsafe_allow_html=True)
            type_counts = {}
            for conf in conflicts:
                type_counts[conf["conflict_type"]] = type_counts.get(conf["conflict_type"], 0) + 1
            ct1, ct2, ct3 = st.columns(3)
            cols_list = [ct1, ct2, ct3]
            for idx2, (ctype, cnt) in enumerate(type_counts.items()):
                with cols_list[idx2 % 3]:
                    st.markdown(f"""<div class="es-stat-card">
                        <div class="es-stat-num" style="font-size:28px;color:var(--accent-warm)">{cnt}</div>
                        <div class="es-stat-label">{ctype}</div></div>""", unsafe_allow_html=True)
            st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
            for conf in conflicts:
                sev_chip = severity_chip(conf["severity_level"])
                st.markdown(f"""<div class="es-conflict-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                        <strong style="color:var(--text-primary);font-size:14px;">{conf['conflict_type']}</strong>
                        {sev_chip}
                    </div>
                    <div style="color:var(--text-secondary);font-size:13px;">{conf['description']}</div>
                    {f'<div style="color:var(--accent-emerald);font-size:12px;margin-top:8px;">Resolution: {conf["resolution_note"]}</div>' if conf.get("resolution_note") else ''}
                </div>""", unsafe_allow_html=True)

    elif an_tab == "Sequence Comparator":
        st.markdown('<div class="es-section-title" style="font-size:20px;margin-bottom:16px;">Compare Sequences Side by Side</div>', unsafe_allow_html=True)
        sorted_seqs = sorted(seqs, key=lambda x: x["risk_score"], reverse=True)
        seq_options = {f"Sequence {i+1} (Risk: {sq['risk_score']:.1f})": sq for i, sq in enumerate(sorted_seqs)}
        sc_col1, sc_col2 = st.columns(2)
        with sc_col1:
            sel_a = st.selectbox("Sequence A", list(seq_options.keys()), key="comp_a")
        with sc_col2:
            sel_b = st.selectbox("Sequence B", list(seq_options.keys()), index=min(1, len(seq_options)-1), key="comp_b")
        sq_a = seq_options[sel_a]
        sq_b = seq_options[sel_b]
        cc1, cc2 = st.columns(2)
        for col, sq, label in [(cc1, sq_a, sel_a), (cc2, sq_b, sel_b)]:
            with col:
                seq_ids = json.loads(sq["sequence_order"]) if sq["sequence_order"] else []
                names = [ev_map.get(eid, f"#{eid}") for eid in seq_ids]
                risk_cls = risk_color_class(sq["risk_score"])
                conflict_badge = '<span class="es-chip es-chip-red">CONFLICTS</span>' if sq["conflict_flag"] else '<span class="es-chip es-chip-green">CLEAN</span>'
                st.markdown(f"""<div class="es-card es-card-accent">
                    <div class="es-section-label">{label}</div>
                    <div class="es-stat-num {risk_cls}" style="font-size:36px;">{sq['risk_score']:.1f}</div>
                    <div class="es-stat-label" style="margin-bottom:16px;">Risk Score</div>
                    <div style="margin-bottom:12px;">{conflict_badge}</div>
                    <div style="font-size:12px;color:var(--text-muted);margin-bottom:8px;">EXECUTION PATH</div>
                    {"".join([f'<div style="padding:6px 0;border-bottom:1px solid var(--border-subtle);color:var(--text-secondary);font-size:13px;">→ {n}</div>' for n in names])}
                    <div style="margin-top:12px;font-size:12px;color:var(--text-muted);">Likelihood: {sq['likelihood_score']*100:.0f}%</div>
                </div>""", unsafe_allow_html=True)

    elif an_tab == "Gantt Analysis":
        st.markdown('<div class="es-section-label">Timeline Analysis</div>', unsafe_allow_html=True)
        fig_g = build_gantt_chart(sim_id)
        st.pyplot(fig_g, use_container_width=True)
        plt.close(fig_g)
        st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
        fig_dep = build_dependency_graph()
        st.pyplot(fig_dep, use_container_width=True)
        plt.close(fig_dep)
    st.markdown('</div>', unsafe_allow_html=True)


def page_reports(user):
    st.markdown("""
    <div class="es-page-header">
        <div class="es-section-label">Reporting Center</div>
        <div class="es-page-title">Generate Simulation Reports</div>
        <div class="es-page-desc">Export comprehensive analysis reports including risk scores, conflict summaries, and sequence data.</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div style="padding: 32px 80px;">', unsafe_allow_html=True)
    sims = get_simulations()
    completed = [s for s in sims if s["run_status"] == "completed"]
    if not completed:
        st.markdown('<div class="es-warning-banner">No completed simulations available for reporting.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return
    sim_choices = {f"{s['simulation_name']} ({s['start_timestamp'][:16]})": s["simulation_id"] for s in completed}
    rep_col1, rep_col2 = st.columns([2, 3])
    with rep_col1:
        st.markdown('<div class="es-form-section">', unsafe_allow_html=True)
        st.markdown('<div class="es-section-label">Report Configuration</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        selected_sim_name = st.selectbox("Select Simulation", list(sim_choices.keys()), key="report_sim_sel")
        sim_id = sim_choices[selected_sim_name]
        report_type = st.radio("Report Format", ["CSV", "JSON"], horizontal=True, key="report_format_sel")
        include_conflicts = st.checkbox("Include Conflict Details", value=True)
        include_sequences = st.checkbox("Include Sequence Breakdown", value=True)
        if st.button("Generate Report", key="gen_report_btn"):
            csv_data, conflicts = generate_report_data(sim_id, user["user_id"])
            if report_type == "CSV":
                st.download_button("Download CSV Report", csv_data,
                                   f"emergisim_report_{sim_id}.csv", "text/csv",
                                   key="dl_csv_report")
            else:
                seqs = get_simulation_sequences(sim_id)
                events = get_all_events()
                ev_map = {e["event_id"]: e["event_name"] for e in events}
                json_report = {
                    "simulation_id": sim_id,
                    "generated_at": datetime.now().isoformat(),
                    "sequences": [],
                    "conflicts": []
                }
                for sq in seqs:
                    seq_ids = json.loads(sq["sequence_order"]) if sq["sequence_order"] else []
                    json_report["sequences"].append({
                        "path": [ev_map.get(i, str(i)) for i in seq_ids],
                        "risk_score": sq["risk_score"],
                        "likelihood": sq["likelihood_score"],
                        "has_conflicts": bool(sq["conflict_flag"])
                    })
                if include_conflicts:
                    for cf in conflicts:
                        json_report["conflicts"].append({
                            "type": cf["conflict_type"],
                            "severity": cf["severity_level"],
                            "description": cf["description"]
                        })
                st.download_button("Download JSON Report", json.dumps(json_report, indent=2),
                                   f"emergisim_report_{sim_id}.json", "application/json",
                                   key="dl_json_report")
            st.success("Report generated successfully.")
        st.markdown('</div>', unsafe_allow_html=True)
    with rep_col2:
        st.markdown('<div class="es-section-label">Report Preview</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        seqs = get_simulation_sequences(sim_id)
        conflicts = get_simulation_conflicts(sim_id)
        events = get_all_events()
        ev_map = {e["event_id"]: e["event_name"] for e in events}
        if seqs:
            sorted_seqs = sorted(seqs, key=lambda x: x["risk_score"], reverse=True)
            preview_data = []
            for sq in sorted_seqs[:6]:
                seq_ids = json.loads(sq["sequence_order"]) if sq["sequence_order"] else []
                names = " → ".join([ev_map.get(i, f"#{i}") for i in seq_ids])
                preview_data.append({
                    "Sequence": names[:60] + ("..." if len(names) > 60 else ""),
                    "Risk": f"{sq['risk_score']:.1f}",
                    "Likelihood": f"{sq['likelihood_score']*100:.0f}%",
                    "Conflicts": "Yes" if sq["conflict_flag"] else "No"
                })
            df_prev = pd.DataFrame(preview_data)
            st.dataframe(df_prev, use_container_width=True, hide_index=True)
        if include_conflicts and conflicts:
            st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="es-section-label">Detected Conflicts ({len(conflicts)})</div>', unsafe_allow_html=True)
            for cf in conflicts[:5]:
                sev_chip = severity_chip(cf["severity_level"])
                st.markdown(f"""<div class="es-conflict-card">
                    <div style="display:flex;justify-content:space-between;">
                        <strong style="color:var(--text-primary);font-size:13px;">{cf['conflict_type']}</strong>
                        {sev_chip}
                    </div>
                    <div style="color:var(--text-secondary);font-size:12px;margin-top:4px;">{cf['description']}</div>
                </div>""", unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT r.*, u.full_name FROM reports r LEFT JOIN users u ON r.created_by=u.user_id ORDER BY r.report_id DESC LIMIT 10")
    report_history = [dict(r) for r in c.fetchall()]
    conn.close()
    if report_history:
        st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="es-section-label">Report History</div>', unsafe_allow_html=True)
        for rh in report_history:
            st.markdown(f"""<div class="es-log-item">
                <div class="es-log-time">{rh['created_date'][:19]} — {rh.get('full_name','System')}</div>
                <div class="es-log-action">{rh['report_name']} · {rh['report_type']}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def page_admin(user):
    if user["role"] != "Administrator":
        st.markdown('<div class="es-error-banner">Access denied. Administrator role required.</div>', unsafe_allow_html=True)
        return
    st.markdown("""
    <div class="es-page-header">
        <div class="es-section-label">System Administration</div>
        <div class="es-page-title">Administration Console</div>
        <div class="es-page-desc">Manage users, roles, system configuration, audit logs, and backup operations.</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div style="padding: 32px 80px;">', unsafe_allow_html=True)
    admin_tab = st.radio("", ["User Management", "Audit Logs", "System Backup", "System Settings"], horizontal=True, key="admin_tab")
    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
    if admin_tab == "User Management":
        users = get_all_users()
        ua1, ua2 = st.columns([3, 2])
        with ua1:
            st.markdown('<div class="es-section-title" style="font-size:20px;margin-bottom:16px;">Active Users</div>', unsafe_allow_html=True)
            for u in users:
                rb = role_badge(u["role"])
                status_badge = '<span class="es-chip es-chip-green">Active</span>' if u["status"] == "active" else '<span class="es-chip es-chip-red">Inactive</span>'
                with st.expander(f"{u['full_name']}  (@{u['username']})"):
                    uc1, uc2 = st.columns(2)
                    with uc1:
                        st.markdown(f"**Role:** {rb}", unsafe_allow_html=True)
                        st.markdown(f"**Status:** {status_badge}", unsafe_allow_html=True)
                        st.markdown(f"**Joined:** {u['created_at'][:10]}")
                    with uc2:
                        if u["user_id"] != user["user_id"]:
                            new_role = st.selectbox("Change Role", ["Observer", "Event Planner", "Analyst", "Administrator"],
                                                    index=["Observer", "Event Planner", "Analyst", "Administrator"].index(u["role"]),
                                                    key=f"role_sel_{u['user_id']}")
                            new_status = st.selectbox("Status", ["active", "inactive"],
                                                      index=0 if u["status"] == "active" else 1,
                                                      key=f"status_sel_{u['user_id']}")
                            au_c1, au_c2 = st.columns(2)
                            with au_c1:
                                if st.button("Update", key=f"upd_user_{u['user_id']}"):
                                    update_user_role(u["user_id"], new_role, new_status)
                                    log_action(user["user_id"], "Update User Role", str(u["user_id"]))
                                    st.success("User updated.")
                                    st.rerun()
                            with au_c2:
                                if st.button("Deactivate", key=f"del_user_{u['user_id']}"):
                                    ok, m = delete_user(u["user_id"], user["user_id"])
                                    if ok:
                                        st.success(m)
                                        st.rerun()
                                    else:
                                        st.error(m)
                        else:
                            st.markdown("*(Your account)*")
        with ua2:
            st.markdown('<div class="es-form-section">', unsafe_allow_html=True)
            st.markdown('<div class="es-section-label">Add New User</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            with st.form("admin_add_user"):
                new_fn = st.text_input("Full Name", key="adm_fn")
                new_un = st.text_input("Username", key="adm_un")
                new_pw = st.text_input("Password", type="password", key="adm_pw")
                new_role_sel = st.selectbox("Role", ["Observer", "Event Planner", "Analyst", "Administrator"], key="adm_role")
                adm_submitted = st.form_submit_button("Create User")
                if adm_submitted:
                    if not all([new_fn, new_un, new_pw]):
                        st.error("All fields are required.")
                    else:
                        ok, msg = register_user(new_fn, new_un, new_pw, new_role_sel)
                        if ok:
                            log_action(user["user_id"], "Admin Create User", new_un)
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            st.markdown('</div>', unsafe_allow_html=True)

    elif admin_tab == "Audit Logs":
        logs = get_audit_logs()
        if not logs:
            st.markdown('<div class="es-empty-state"><div class="es-empty-title">No audit logs yet</div></div>', unsafe_allow_html=True)
        else:
            filter_action = st.text_input("Filter by action type", placeholder="e.g. Create Event, Run Simulation...", key="audit_filter")
            filtered_logs = [l for l in logs if not filter_action or filter_action.lower() in l["action_type"].lower()]
            st.markdown(f'<div class="es-info-banner">Showing {len(filtered_logs)} of {len(logs)} log entries.</div>', unsafe_allow_html=True)
            for log in filtered_logs[:50]:
                uname = log.get("username", "system")
                st.markdown(f"""<div class="es-log-item">
                    <div class="es-log-time">{log['action_time']} — {uname}</div>
                    <div class="es-log-action">{log['action_type']} · {log.get('target_record','')} {f'— {log["remarks"]}' if log.get("remarks") else ''}</div>
                </div>""", unsafe_allow_html=True)
            if len(filtered_logs) > 50:
                st.markdown(f'<div style="color:var(--text-muted);font-size:12px;padding:8px 0;">...and {len(filtered_logs)-50} more entries</div>', unsafe_allow_html=True)
            log_export_data = json.dumps([dict(l) for l in filtered_logs], default=str, indent=2)
            st.download_button("Export Audit Log", log_export_data, "emergisim_audit.json", "application/json", key="dl_audit")

    elif admin_tab == "System Backup":
        bu_col1, bu_col2 = st.columns(2)
        with bu_col1:
            st.markdown('<div class="es-section-title" style="font-size:20px;margin-bottom:16px;">Create Backup</div>', unsafe_allow_html=True)
            st.markdown('<div class="es-info-banner">Creates a complete offline backup of all events, dependencies, and simulation data.</div>', unsafe_allow_html=True)
            if st.button("Generate Backup Now", key="gen_backup"):
                backup_json = create_backup(user["user_id"])
                st.download_button("Download Backup File", backup_json,
                                   f"emergisim_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                   "application/json", key="dl_backup")
                st.success("Backup created successfully.")
        with bu_col2:
            st.markdown('<div class="es-section-title" style="font-size:20px;margin-bottom:16px;">Restore from Backup</div>', unsafe_allow_html=True)
            restore_file = st.file_uploader("Upload Backup File", type=["json"], key="restore_upload")
            if restore_file and st.button("Restore System", key="do_restore"):
                st.warning("Restore functionality noted. In production, this would replace current data with backup contents.")
                log_action(user["user_id"], "Restore Backup")

    elif admin_tab == "System Settings":
        st.markdown('<div class="es-section-title" style="font-size:20px;margin-bottom:16px;">System Configuration</div>', unsafe_allow_html=True)
        ss_col1, ss_col2 = st.columns(2)
        with ss_col1:
            st.markdown('<div class="es-form-section">', unsafe_allow_html=True)
            st.markdown('<div class="es-section-label">Simulation Defaults</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            default_sequences = st.number_input("Default Sequences per Run", min_value=4, max_value=50, value=8, key="ss_seqs")
            default_failure = st.slider("Default Failure Probability", 0.0, 1.0, 0.1, 0.01, key="ss_fail")
            enable_notifications = st.checkbox("Enable Completion Notifications", value=True, key="ss_notif")
            if st.button("Save Settings", key="save_sys_settings"):
                st.session_state["sys_default_sequences"] = default_sequences
                st.session_state["sys_default_failure"] = default_failure
                log_action(user["user_id"], "Update System Settings")
                st.success("Settings saved for this session.")
            st.markdown('</div>', unsafe_allow_html=True)
        with ss_col2:
            st.markdown('<div class="es-card">', unsafe_allow_html=True)
            st.markdown('<div class="es-section-label">System Information</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            events = get_all_events()
            sims = get_simulations()
            users_all = get_all_users()
            logs = get_audit_logs()
            info_items = [
                ("Total Events", len(events)),
                ("Total Simulations", len(sims)),
                ("Total Users", len(users_all)),
                ("Audit Log Entries", len(logs)),
                ("Database", "emergisim.db (SQLite)"),
                ("Architecture", "Offline · Local"),
                ("Version", "EmergiSim v1.0"),
            ]
            for label, val in info_items:
                st.markdown(f"""<div style="padding:10px 0;border-bottom:1px solid var(--border-subtle);display:flex;justify-content:space-between;">
                    <span style="color:var(--text-muted);font-size:12px;">{label}</span>
                    <span style="color:var(--text-primary);font-size:13px;font-weight:500;">{val}</span>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_auth_page():
    st.markdown("""
    <div class="es-auth-wrapper">
        <div style="position:absolute;top:0;left:0;right:0;bottom:0;pointer-events:none;">
            <div style="position:absolute;top:-30%;left:-10%;width:500px;height:500px;background:radial-gradient(circle,rgba(0,212,255,0.06) 0%,transparent 70%);border-radius:50%;"></div>
            <div style="position:absolute;bottom:-20%;right:-10%;width:400px;height:400px;background:radial-gradient(circle,rgba(139,92,246,0.05) 0%,transparent 70%);border-radius:50%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        auth_mode = st.session_state.get("auth_mode", "login")
        st.markdown(f"""
        <div class="es-auth-card">
            <div class="es-auth-logo">
                <div class="es-auth-title">EmergiSim</div>
                <div class="es-auth-sub">Emergent Behavior Simulation Platform</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        tab_col1, tab_col2 = st.columns(2)
        with tab_col1:
            if st.button("Sign In", key="auth_login_tab",
                         help="Login to existing account"):
                st.session_state["auth_mode"] = "login"
                st.rerun()
        with tab_col2:
            if st.button("Register", key="auth_register_tab",
                         help="Create new account"):
                st.session_state["auth_mode"] = "register"
                st.rerun()
        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
        if auth_mode == "login":
            st.markdown('<div class="es-form-section">', unsafe_allow_html=True)
            with st.form("login_form"):
                username_inp = st.text_input("Username", placeholder="Enter your username")
                password_inp = st.text_input("Password", type="password", placeholder="Enter your password")
                login_btn = st.form_submit_button("Sign In")
                if login_btn:
                    if not username_inp or not password_inp:
                        st.error("Please enter both username and password.")
                    else:
                        u = verify_user(username_inp, password_inp)
                        if u:
                            st.session_state["user"] = u
                            st.session_state["page"] = "dashboard"
                            log_action(u["user_id"], "Login", username_inp)
                            st.success(f"Welcome back, {u['full_name']}!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials. Please try again.")
            st.markdown('</div>', unsafe_allow_html=True)
           
        else:
            st.markdown('<div class="es-form-section">', unsafe_allow_html=True)
            with st.form("register_form"):
                reg_fn = st.text_input("Full Name", placeholder="Your full name")
                reg_un = st.text_input("Username", placeholder="Choose a username")
                reg_pw = st.text_input("Password", type="password", placeholder="Create a password")
                reg_pw2 = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
                reg_role = st.selectbox("Role Request", ["Observer", "Event Planner", "Analyst"])
                reg_btn = st.form_submit_button("Create Account")
                if reg_btn:
                    if not all([reg_fn, reg_un, reg_pw, reg_pw2]):
                        st.error("All fields are required.")
                    elif reg_pw != reg_pw2:
                        st.error("Passwords do not match.")
                    elif len(reg_pw) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        ok, msg = register_user(reg_fn, reg_un, reg_pw, reg_role)
                        if ok:
                            st.success(f"{msg} Please sign in.")
                            st.session_state["auth_mode"] = "login"
                            st.rerun()
                        else:
                            st.error(msg)
            st.markdown('</div>', unsafe_allow_html=True)


def render_app(user):
    render_topbar(user)
    page = st.session_state.get("page", "dashboard")
    role = user.get("role", "Observer")
    render_nav(page, role)
    page_access = {
        "dashboard": ["Administrator", "Event Planner", "Analyst", "Observer"],
        "events": ["Administrator", "Event Planner"],
        "dependencies": ["Administrator", "Event Planner"],
        "simulation": ["Administrator", "Event Planner", "Analyst"],
        "analytics": ["Administrator", "Analyst", "Observer"],
        "reports": ["Administrator", "Analyst"],
        "admin": ["Administrator"],
    }
    if role not in page_access.get(page, []):
        st.markdown('<div style="padding:48px 80px;"><div class="es-error-banner">Access denied. Your role does not have permission to view this page.</div></div>', unsafe_allow_html=True)
        return
    if page == "dashboard":
        page_dashboard(user)
    elif page == "events":
        page_events(user)
    elif page == "dependencies":
        page_dependencies(user)
    elif page == "simulation":
        page_simulation(user)
    elif page == "analytics":
        page_analytics(user)
    elif page == "reports":
        page_reports(user)
    elif page == "admin":
        page_admin(user)


def main():
    init_db()
    if "user" not in st.session_state:
        render_auth_page()
    else:
        render_app(st.session_state["user"])


if __name__ == "__main__":
    main()