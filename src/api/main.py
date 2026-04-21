from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db, init_db, User, Project, GitHubMetric, AuthorMetric
from .auth import get_password_hash, verify_password, create_access_token, get_current_user
from ..modeling.oracle import MetaMLCore
from ..config import settings
from pydantic import BaseModel

app = FastAPI(title="META ML Enterprise API")

# META ML Core Instance
meta_ml = MetaMLCore()

# Models
class UserCreate(BaseModel):
    username: str
    password: str

class PredictionRequest(BaseModel):
    github_url: str
    abstract: str
    overrides: dict = None

@app.on_event("startup")
def startup_event():
    init_db()

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user_in.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    try:
        new_user = User(
            username=user_in.username,
            hashed_password=get_password_hash(user_in.password)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message": "User created successfully"}
    except Exception as e:
        db.rollback()
        # Check if it's a unique constraint failure
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="Username already registered")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/predict")
def predict_project(
    req: PredictionRequest, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Perform Prediction with optional Sandbox Overrides
    result = meta_ml.predict(req.github_url, req.abstract, overrides=req.overrides)
    
    import json
    
    # Save to Database (Updated for META ML 2.0 Resilience)
    db_project = Project(
        owner_id=current_user.id,
        github_url=req.github_url,
        abstract=req.abstract,
        paper_title=result["metadata"]["scholar_data"]["paper_title"] if result["metadata"]["scholar_data"] else "N/A",
        viability_score=result["success_probability"],
        risk_taxonomy=result["risk_taxonomy"],
        signals_json=json.dumps(result["signals"]),
        consensus_json=json.dumps(result["agent_consensus"]),
        label=1 if result["success_probability"] > 0.6 else 0
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # Save GitHub Metrics
    gh = result["metadata"]["gh_data"]
    if gh:
        db_gh = GitHubMetric(
            project_id=db_project.id,
            stars=gh["stars"],
            forks=gh["forks"],
            commits_count=gh["commits_count"],
            contributors_count=gh["contributors_count"],
            readme_length=gh["readme_length"],
            has_test_files=gh["has_test_files"]
        )
        db.add(db_gh)
        db.commit()
        
    return {
        "project_id": db_project.id,
        "success_probability": result["success_probability"],
        "confidence_index": result["confidence_index"],
        "agent_consensus": result["agent_consensus"],
        "roi_projection": result["roi_projection"],
        "risk_taxonomy": result["risk_taxonomy"],
        "signals": result["signals"],
        "metadata": result["metadata"],
        "explanation": "Meta intelligence vectorized and archived."
    }

@app.get("/history")
def get_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    projects = db.query(Project).filter(Project.owner_id == current_user.id).all()
    return projects
