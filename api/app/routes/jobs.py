from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.utils.db_utils import db_manager
from app.models.job import Job
from app.schemas.jobs import JobCreate, JobUpdate, JobResponse

router = APIRouter()

@router.post("/", response_model=JobResponse)
async def create_job(job: JobCreate, db: Session = Depends(db_manager.get_db)):
    db_job = Job(**job.model_dump())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

@router.get("/", response_model=List[JobResponse])
async def read_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(db_manager.get_db)):
    jobs = db.query(Job).offset(skip).limit(limit).all()
    return jobs

@router.get("/{job_id}", response_model=JobResponse)
async def read_job(job_id: int, db: Session = Depends(db_manager.get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.put("/{job_id}", response_model=JobResponse)
async def update_job(job_id: int, job_update: JobUpdate, db: Session = Depends(db_manager.get_db)):
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    update_data = job_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_job, key, value)
    db.commit()
    db.refresh(db_job)
    return db_job

@router.delete("/{job_id}", response_model=JobResponse)
async def delete_job(job_id: int, db: Session = Depends(db_manager.get_db)):
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(db_job)
    db.commit()
    return db_job