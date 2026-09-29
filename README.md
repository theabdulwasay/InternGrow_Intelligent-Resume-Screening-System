# ResumeMatch

An AI-assisted resume screening starter app. It extracts text from PDF and DOCX files, detects a curated set of skills, scores each resume against a job description, ranks candidates, and exports results to CSV. The app runs locally and does not persist uploaded resumes.

## Features

- Batch upload of up to 25 PDF/DOCX resumes (10 MB per file).
- Text extraction from digital PDFs and DOCX paragraphs/tables.
- Optional OCR fallback for scanned PDFs using Tesseract.
- NLP-style skills and contextual keyword matching, with a transparent weighted score:
  - 75% job-skill coverage
  - 25% job-description keyword overlap
  - If no recognized job skills are found, the keyword score is used as the overall score.
- Ranked candidate dashboard, match breakdown, detected job skills, and CSV export.
- Per-file errors do not prevent other resumes in the batch from being analyzed.

The matching logic is a deterministic baseline, not a trained model or an employment decision. It can miss unlisted skills and should be reviewed against real hiring criteria.

## Run locally

Requires Python 3.10 or newer.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload
```

Open <http://127.0.0.1:8000>. Interactive API documentation is at <http://127.0.0.1:8000/docs>.

### Scanned PDFs

OCR is attempted when a PDF contains too little embedded text. Install the Tesseract OCR application and ensure its executable is on `PATH`. The Python dependencies for OCR are included in `requirements.txt`. Digital PDFs and DOCX files do not require Tesseract.

## API

- `GET /api/health` — health check.
- `POST /api/analyze` — multipart fields `job_description` and one or more `files`.
- `POST /api/export` — JSON body `{ "results": [...] }`, returning a CSV attachment.

Files are processed in memory and are not written to disk. Add authentication, authorization, retention controls, and legal/privacy review before exposing this service to a network or using it for production hiring.

## Tests

```powershell
python -m unittest discover -s tests -v
```
<img width="1583" height="795" alt="image" src="https://github.com/user-attachments/assets/913eb131-77f0-4b81-87a2-36debd27d3d2" />
<img width="1577" height="789" alt="image" src="https://github.com/user-attachments/assets/cb5e2f66-0808-4dcd-bde7-d7d7b7011eda" />

