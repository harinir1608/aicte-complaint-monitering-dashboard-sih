@echo off
echo Starting AICTE Dashboard Backend in ps2 conda environment...
echo.

cd /d "%~dp0backend"

call conda activate ps2

echo Running Alembic migrations...
python -m alembic upgrade head

echo Seeding demo data...
python -m app.db.seed

echo.
echo Starting FastAPI server on http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
