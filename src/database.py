from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
from .config import settings

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="researcher") # researcher, admin
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    projects = relationship("Project", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    github_url = Column(String, index=True, nullable=False) # Removed unique to allow different users to audit same repo
    paper_title = Column(String)
    abstract = Column(Text)
    viability_score = Column(Float, default=0.0)
    label = Column(Integer)  # 1 for Deployed, 0 for Abandoned
    
    # Intelligence Persistence (New for META ML 2.0)
    risk_taxonomy = Column(String) # Technical Debt, Research Isolation, etc.
    signals_json = Column(Text) # Prioritized Driving Signals
    consensus_json = Column(Text) # Multi-Agent Vote Breakdown
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    github_metrics = relationship("GitHubMetric", back_populates="project", uselist=False)
    author_metrics = relationship("AuthorMetric", back_populates="project")

class GitHubMetric(Base):
    __tablename__ = "github_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    commits_count = Column(Integer, default=0)
    contributors_count = Column(Integer, default=0)
    readme_length = Column(Integer, default=0)
    last_commit_date = Column(DateTime)
    has_test_files = Column(Integer, default=0)  # 0 or 1
    
    project = relationship("Project", back_populates="github_metrics")

class AuthorMetric(Base):
    __tablename__ = "author_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    author_name = Column(String)
    h_index = Column(Integer, default=0)
    citation_count = Column(Integer, default=0)
    institution_type = Column(String)  # Lab, University, Independent
    
    project = relationship("Project", back_populates="author_metrics")

# Database setup
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
