from typing import Optional
from urllib.parse import urlencode
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import database
from prolog_engine import prolog_engine

app = FastAPI(title="GridRescue API")

app.mount("/static", StaticFiles(directory="static"), name="static")

database.init_db()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    incidents = database.get_all_incidents()
    return templates.TemplateResponse(request, "dashboard.html", {"incidents": incidents})

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
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
