# ResumeMatch backend

FastAPI backend for PDF/DOCX resume text extraction, optional scanned-PDF OCR,
skill and keyword matching, candidate ranking, and CSV export. The backend
serves the project's existing frontend from `../static`, so the browser and API
use the same origin and do not need CORS configuration.

## Run on Windows

Open PowerShell in the `Backend` folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8765 --reload
```

Keep the terminal open. Open <http://127.0.0.1:8765> for the dashboard,
<http://127.0.0.1:8765/docs> for interactive API docs, and
<http://127.0.0.1:8765/api/health> to check that the API is running.

## Endpoints

- `GET /api/health` — health check.
- `POST /api/analyze` — multipart form with `job_description` and one or more
  `files` fields (PDF/DOCX; up to 25 resumes, 10 MB each).
- `POST /api/export` — JSON body `{ "results": [...] }`, returns a CSV file.

Resume files are processed in memory and are not saved to disk. The scoring is
a transparent, deterministic baseline: 75% recognized skill coverage and 25%
keyword overlap. It is decision support, not a trained model or a hiring
decision.

Scanned-PDF OCR also requires the Tesseract OCR application installed and
available on `PATH`. Digital PDFs and DOCX files do not require Tesseract.
