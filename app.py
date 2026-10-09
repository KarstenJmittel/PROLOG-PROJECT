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
    return templates.TemplateResponse("dashboard.html", {"request": request, "incidents": incidents})

@app.post("/incident/new")
def new_incident(location: str = Form(...)):
    database.create_incident(location)
    return RedirectResponse(url="/", status_code=303)

@app.get("/incident/{id}", response_class=HTMLResponse)
def view_incident(request: Request, id: int):
    incident, reports = database.get_incident_data(id)
    return templates.TemplateResponse("incident.html", {
        "request": request, 
        "incident": incident, 
        "reports": reports
    })

@app.post("/incident/{id}/report")
def add_incident_report(id: int, source_type: str = Form(...), evidence_category: str = Form(...)):
    database.add_report(id, source_type, evidence_category)
    return RedirectResponse(url=f"/incident/{id}", status_code=303)

@app.api_route("/incident/{id}/analyze", methods=["GET", "POST"])
def analyze_incident(id: int):
    incident, reports = database.get_incident_data(id)
    location = incident["location"] if incident else None
    diagnosis = prolog_engine.analyze_incident(id, reports, location)
    database.update_incident_diagnosis(id, diagnosis)
    return RedirectResponse(url=f"/incident/{id}", status_code=303)