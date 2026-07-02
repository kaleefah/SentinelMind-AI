# from cognee_memory import store_incident_memory, search_incident_memory

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional

import models
from database import engine, SessionLocal
from ai_engine import analyze_incident


# Create all tables on startup
models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="SentinelMind AI",
    description="Cybersecurity Incident Memory Assistant API",
    version="1.0.0"
)


# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()



@app.get("/")
def root():

    return {
        "message": "SentinelMind AI is running",
        "status": "ok"
    }



@app.post("/incident")
async def create_incident(
    data: dict,
    db: Session = Depends(get_db)
):

    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    system = data.get("system", "").strip()


    if not title or not description:

        raise HTTPException(
            status_code=400,
            detail="Title and description are required."
        )


    # AI Analysis
    ai_result = analyze_incident(description)



    # Save incident in database
    incident = models.Incident(

        title=title,
        description=description,
        system=system,

        category=ai_result["category"],
        severity=ai_result["severity"],
        recommendation=ai_result["recommendation"]

    )


    db.add(incident)

    db.commit()

    db.refresh(incident)



    # SAVE INCIDENT INTO COGNEE MEMORY
    # await store_incident_memory(

    #     title,
    #     description,
    #     system,
    #     ai_result["recommendation"]

    # )



    return {

        "message": "Incident processed successfully",

        "id": incident.id,

        "result": ai_result

    }





@app.get("/incident/similar")
def get_similar_incidents(

    q: str,
    db: Session = Depends(get_db)

):

    # Clean query and extract keywords with length >= 2 to support shorter terms like SQL, MFA
    q_clean = q.strip().lower()
    keywords = [kw for kw in q_clean.split() if len(kw) >= 2]
    if not keywords and q_clean:
        keywords = [q_clean]

    incidents = db.query(models.Incident).all()

    matches = []
    for incident in incidents:
        # Search across title, description, system, category, and recommendation
        combined = " ".join([
            incident.title or "",
            incident.description or "",
            incident.system or "",
            incident.category or "",
            incident.recommendation or ""
        ]).lower()

        if keywords and any(kw in combined for kw in keywords):
            matches.append({
                "id": incident.id,
                "title": incident.title,
                "description": incident.description,
                "severity": incident.severity,
                "category": incident.category,
                "system": incident.system,
                "recommendation": incident.recommendation
            })

    return {

        "query": q,

        "count": len(matches),

        "incidents": matches

    }





@app.get("/incidents")
def list_incidents(

    db: Session = Depends(get_db)

):


    incidents = db.query(models.Incident)\
        .order_by(models.Incident.id.desc())\
        .all()



    stats = {


        "total": len(incidents),


        "critical": sum(
            1 for i in incidents 
            if i.severity == "Critical"
        ),


        "high": sum(
            1 for i in incidents 
            if i.severity == "High"
        ),


        "medium": sum(
            1 for i in incidents 
            if i.severity == "Medium"
        ),


        "low": sum(
            1 for i in incidents 
            if i.severity == "Low"
        )

    }



    return {


        "stats": stats,


        "incidents": [

            {

                "id": i.id,

                "title": i.title,

                "system": i.system,

                "category": i.category,

                "severity": i.severity

            }

            for i in incidents

        ]

    }