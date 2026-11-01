import os
from contextlib import asynccontextmanager
from typing import Optional
from urllib.parse import urlencode
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import database
from prolog_engine import prolog_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Safe database startup
    try:
        database.init_db()
    except Exception as e:
        print(f"Startup DB init warning: {e}")
    yield

app = FastAPI(title="GridRescue API", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, status: Optional[str] = None):
    incidents = database.get_all_incidents(status_filter=status)
    try:
        recent_reports = database.get_recent_reports(limit=10)
    except Exception:
        recent_reports = []
    try:
        stats = database.get_incident_stats()
    except Exception:
        stats = {"total": len(incidents), "active": 0, "diagnosed": 0, "resolved": 0, "total_reports": 0}
    return templates.TemplateResponse(request, "dashboard.html", {
        "incidents": incidents,
        "recent_reports": recent_reports,
        "stats": stats,
        "current_filter": status or "all"
    })

@app.post("/incident/new")
def new_incident(location: str = Form(...)):
    database.create_incident(location)
    return RedirectResponse(url="/", status_code=303)

@app.get("/incident/{id}", response_class=HTMLResponse)
def view_incident(request: Request, id: int):
    incident, reports = database.get_incident_data(id)
    return templates.TemplateResponse(request, "incident.html", {
        "incident": incident, 
        "reports": reports
    })

@app.post("/incident/{id}/report")
def add_incident_report(
    id: int, 
    source_type: str = Form(...), 
    evidence_category: str = Form(...),
    custom_evidence: Optional[str] = Form(None)
):
    final_evidence = (custom_evidence.strip() if custom_evidence and custom_evidence.strip() else "Other Technical Observation") if evidence_category == "other" else evidence_category.strip()
    database.add_report(id, source_type, final_evidence)
    return RedirectResponse(url=f"/incident/{id}", status_code=303)

@app.post("/incident/{id}/resolve")
def resolve_incident(id: int, notes: Optional[str] = Form("")):
    database.resolve_incident(id, notes or "")
    return RedirectResponse(url=f"/incident/{id}", status_code=303)

@app.post("/incident/{id}/reopen")
def reopen_incident(id: int):
    database.reopen_incident(id)
    return RedirectResponse(url=f"/incident/{id}", status_code=303)

@app.post("/incident/{id}/delete")
def delete_incident(id: int):
    database.delete_incident(id)
    return RedirectResponse(url="/", status_code=303)

@app.post("/report/{id}/delete")
def delete_report(id: int, redirect_url: Optional[str] = Form(None)):
    incident_id = database.delete_report(id)
    if incident_id:
        try:
            incident, reports = database.get_incident_data(incident_id)
            loc = incident["location"] if incident else None
            diagnosis = prolog_engine.analyze_incident(incident_id, reports, location=loc)
            database.update_incident_diagnosis(incident_id, diagnosis)
        except Exception as e:
            print(f"Auto-analysis notice: {e}")
    if redirect_url:
        return RedirectResponse(url=redirect_url, status_code=303)
    if incident_id:
        return RedirectResponse(url=f"/incident/{incident_id}", status_code=303)
    return RedirectResponse(url="/", status_code=303)

@app.get("/report", response_class=HTMLResponse)
def report_page(request: Request):
    return templates.TemplateResponse(request, "report.html", {})

@app.post("/report")
def submit_public_report(
    location: str = Form(...),
    custom_location: Optional[str] = Form(None),
    source_type: str = Form(...),
    evidence_category: str = Form(...),
    custom_evidence: Optional[str] = Form(None)
):
    final_location = (custom_location.strip() if custom_location and custom_location.strip() else "Other Location") if location == "other" else location.strip()
    final_evidence = (custom_evidence.strip() if custom_evidence and custom_evidence.strip() else "Other Observation") if evidence_category == "other" else evidence_category.strip()

    incident_id = database.get_or_create_open_incident(final_location)
    database.add_report(incident_id, source_type, final_evidence)

    # Automatically re-evaluate incident with Prolog upon report intake
    try:
        incident, reports = database.get_incident_data(incident_id)
        loc = incident["location"] if incident else final_location
        diagnosis = prolog_engine.analyze_incident(incident_id, reports, location=loc)
        database.update_incident_diagnosis(incident_id, diagnosis)
    except Exception as e:
        print(f"Auto-analysis warning: {e}")

    params = urlencode({
        "incident_id": incident_id,
        "location": final_location,
        "source": source_type,
        "evidence": final_evidence
    })
    return RedirectResponse(
        url=f"/report/success?{params}",
        status_code=303
    )

@app.get("/report/success", response_class=HTMLResponse)
def report_success(request: Request, incident_id: int, location: str, source: str, evidence: str):
    return templates.TemplateResponse(request, "report_success.html", {
        "incident_id": incident_id,
        "location": location,
        "source_type": source,
        "evidence_category": evidence
    })

@app.api_route("/incident/{id}/analyze", methods=["GET", "POST"])
def analyze_incident(id: int):
    incident, reports = database.get_incident_data(id)
    location = incident["location"] if incident else None
    diagnosis = prolog_engine.analyze_incident(id, reports, location=location)
    database.update_incident_diagnosis(id, diagnosis)
    return RedirectResponse(url=f"/incident/{id}", status_code=303)

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", 8000))
    uvicorn.run("app:app", host=host, port=port, reload=True)
