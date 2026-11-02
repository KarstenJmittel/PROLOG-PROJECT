# GridRescue - Power Grid Decision Support System

An intelligent electrical power grid incident decision-support system that combines a **FastAPI** web backend with a **SWI-Prolog** logical inference engine and **PostgreSQL** database.

---

## ⚡ Overview
During power outages, information arrives in fragments from disparate sources (citizens, field linemen, SCADA breaker alerts, commercial factories). **GridRescue** correlates these multi-party signals, recursively traces power network topology, identifies suspect root components, and prescribes prioritized emergency response actions.

---

## 🛠️ Technologies Used
- **Python 3.10+** – Web backend & API services
- **FastAPI** – High-performance asynchronous web framework
- **SWI-Prolog** – Symbolic AI, logical reasoning, and graph traversal
- **PostgreSQL** – Relational incident & evidence persistence
- **Jinja2 & CSS** – Responsive Operator & Citizen interfaces

---

## 📁 Project Structure
```text
PROLOG-PROJECT/
├── prolog/
│   └── knowledge_base.pl     # Grid topology, fault correlation rules, priority triage
├── static/
│   └── style.css             # Unified application styling & portal status badges
├── templates/
│   ├── base.html             # Base layout with portal-mode indicator
│   ├── dashboard.html        # Operator console with metrics & status filters
│   ├── incident.html         # Incident details, visual topology map & resolution protocol
│   ├── report.html           # Public citizen outage reporting portal
│   └── report_success.html   # Report ingestion confirmation
├── tests/
│   └── test_prolog.py        # Automated unit tests for Prolog deduction & atoms
├── app.py                    # FastAPI application routes & lifecycle management
├── database.py               # PostgreSQL connection & data access layer
├── prolog_engine.py          # SWI-Prolog process execution & atom sanitizer
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .env                      # Local configuration file (git-ignored)
└── README.md
```

---

## 🚀 Installation & Setup

### 1. Prerequisites
- **Python 3.10+**
- **SWI-Prolog** (Ensure `swipl` is installed and accessible in your system PATH)
- **PostgreSQL** (Running locally or accessible via network)

### 2. Configure Environment Variables
Copy the `.env.example` file to `.env` and adjust database credentials:
```ini
DB_NAME=Gridrescue
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

APP_HOST=127.0.0.1
APP_PORT=8000
```

### 3. Install Dependencies
```bash
python -m venv venv
venv\Scripts\activate      # On Windows
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```
Or with Uvicorn directly:
```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🌐 Application Portals

- **Operator Console**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
  - Live incident log, summary statistics cards (Total, Active, Diagnosed, Resolved)
  - Status filtering tabs (`All`, `Active / Open`, `Resolved`)
  - Run automated Prolog tree diagnosis and view root-cause analysis
  - Record technician closeout notes to officially resolve incidents

- **Public Report Portal**: [http://127.0.0.1:8000/report](http://127.0.0.1:8000/report)
  - Citizen & community hazard intake
  - Supports predefined power zones and custom "Other" district specifications
  - Supports standard blackout/sparking observations and custom hazard descriptions

---

## 🧪 Running Automated Tests
Run the Prolog reasoning test suite:
```bash
python -m unittest tests/test_prolog.py
```

---

## 📄 License
This project is available for educational and learning purposes.
