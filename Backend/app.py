from __future__ import annotations

import csv
import io
import re
import zipfile
from pathlib import Path
from typing import Any

import pymupdf as fitz
from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

PROJECT_DIR = Path(__file__).resolve().parent.parent
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_RESUMES = 25

SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "Java": ("java",),
    "JavaScript": ("javascript", "js"),
    "TypeScript": ("typescript",),
    "C++": ("c++", "cpp"),
    "C#": ("c#", "c sharp"),
    "SQL": ("sql",),
    "PostgreSQL": ("postgresql", "postgres"),
    "MySQL": ("mysql",),
    "MongoDB": ("mongodb",),
    "Excel": ("excel", "microsoft excel"),
    "Power BI": ("power bi",),
    "Tableau": ("tableau",),
    "AWS": ("aws", "amazon web services"),
    "Azure": ("azure",),
    "Google Cloud": ("google cloud", "gcp"),
    "Docker": ("docker",),
    "Kubernetes": ("kubernetes", "k8s"),
    "Git": ("git", "github", "gitlab"),
    "Linux": ("linux",),
    "REST API": ("rest api", "restful api", "rest apis"),
    "FastAPI": ("fastapi",),
    "Django": ("django",),
    "Flask": ("flask",),
    "React": ("react", "react.js"),
    "Node.js": ("node.js", "nodejs"),
    "HTML": ("html",),
    "CSS": ("css",),
    "Natural Language Processing": ("natural language processing", "nlp"),
    "Machine Learning": ("machine learning", "ml"),
    "Deep Learning": ("deep learning",),
    "TensorFlow": ("tensorflow",),
    "PyTorch": ("pytorch",),
    "scikit-learn": ("scikit-learn", "sklearn"),
    "Data Analysis": ("data analysis", "data analytics"),
    "Data Visualization": ("data visualization",),
    "Statistics": ("statistics",),
    "Pandas": ("pandas",),
    "NumPy": ("numpy",),
    "Apache Spark": ("apache spark", "pyspark", "spark"),
    "Hadoop": ("hadoop",),
    "OCR": ("ocr", "optical character recognition"),
    "Agile": ("agile", "scrum"),
    "Communication": ("communication",),
    "Leadership": ("leadership",),
    "Project Management": ("project management",),
    "Problem Solving": ("problem solving", "problem-solving"),
    "CI/CD": ("ci/cd", "continuous integration", "continuous delivery"),
}

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "our", "that", "the", "to", "with", "will",
    "you", "your", "we", "this", "have", "has", "must", "should", "candidate",
    "candidates", "job", "role", "work", "experience", "years",
}

app = FastAPI(
    title="ResumeMatch API",
    description="Extract, score, rank, and export resume screening results.",
    version="1.0.0",
)


class CandidateResult(BaseModel):
    filename: str
    status: str
    score: float | None = None
    skill_match: float | None = None
    keyword_match: float | None = None
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    extracted_text_preview: str = ""
    error: str | None = None


class ExportRequest(BaseModel):
    results: list[CandidateResult]


def _contains_phrase(text: str, phrase: str) -> bool:
    pattern = rf"(?<!\w){re.escape(phrase.lower())}(?!\w)"
    return re.search(pattern, text.lower()) is not None


def identify_skills(text: str) -> set[str]:
    return {
        skill
        for skill, aliases in SKILL_ALIASES.items()
        if any(_contains_phrase(text, alias) for alias in aliases)
    }


def _keywords(text: str) -> set[str]:
    return {
        word.lower()
        for word in re.findall(r"[A-Za-z][A-Za-z0-9+#./-]{1,}", text)
        if word.lower() not in STOP_WORDS and not word.isdigit()
    }


def score_resume(resume_text: str, job_description: str) -> dict[str, Any]:
    job_skills = identify_skills(job_description)
    resume_skills = identify_skills(resume_text)
    matched_skills = sorted(job_skills & resume_skills)
    missing_skills = sorted(job_skills - resume_skills)

    job_keywords = _keywords(job_description)
    resume_keywords = _keywords(resume_text)
    keyword_match = (
        len(job_keywords & resume_keywords) / len(job_keywords)
        if job_keywords
        else 0.0
    )
    skill_match = (
        len(matched_skills) / len(job_skills)
        if job_skills
        else keyword_match
    )
    score = (0.75 * skill_match + 0.25 * keyword_match) * 100

    return {
        "score": round(score, 1),
        "skill_match": round(skill_match * 100, 1),
        "keyword_match": round(keyword_match * 100, 1),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
    }


def _extract_pdf(content: bytes) -> str:
    with fitz.open(stream=content, filetype="pdf") as pdf:
        pages = list(pdf)[:30]
        text = "\n".join(page.get_text() for page in pages).strip()
        if len(text) >= 30:
            return text

        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            raise ValueError(
                "This PDF has no readable text. Install pytesseract and Pillow, "
                "then install the Tesseract OCR application to read scanned PDFs."
            ) from exc

        ocr_pages = []
        for page in pages[:10]:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.open(io.BytesIO(pixmap.tobytes("png")))
            ocr_pages.append(pytesseract.image_to_string(image))

        text = "\n".join(ocr_pages).strip()
        if not text:
            raise ValueError(
                "No text could be read from this PDF. Check the scan quality and "
                "Tesseract OCR installation."
            )
        return text


def extract_resume_text(filename: str, content: bytes) -> str:
    extension = Path(filename).suffix.lower()
    if extension == ".pdf":
        text = _extract_pdf(content)
    elif extension == ".docx":
        document = Document(io.BytesIO(content))
        parts = [paragraph.text for paragraph in document.paragraphs]
        for table in document.tables:
            parts.extend(cell.text for row in table.rows for cell in row.cells)
        text = "\n".join(parts).strip()
    else:
        raise ValueError("Unsupported file type. Upload a PDF or DOCX resume.")

    if not text.strip():
        raise ValueError("No readable text was found in this resume.")
    return text


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze_resumes(
    job_description: str = Form(..., max_length=12000),
    files: list[UploadFile] = File(...),
) -> dict[str, Any]:
    if not job_description.strip():
        raise HTTPException(status_code=422, detail="Enter a job description.")
    if not files:
        raise HTTPException(status_code=422, detail="Upload at least one resume.")
    if len(files) > MAX_RESUMES:
        raise HTTPException(
            status_code=413,
            detail=f"Upload no more than {MAX_RESUMES} resumes at a time.",
        )

    results: list[dict[str, Any]] = []
    for uploaded_file in files:
        filename = Path(uploaded_file.filename or "resume").name
        try:
            if Path(filename).suffix.lower() not in {".pdf", ".docx"}:
                raise ValueError("Unsupported file type. Upload a PDF or DOCX resume.")

            content = await uploaded_file.read(MAX_FILE_SIZE + 1)
            if len(content) > MAX_FILE_SIZE:
                raise ValueError("File exceeds the 10 MB limit.")

            resume_text = extract_resume_text(filename, content)
            results.append(
                {
                    "filename": filename,
                    "status": "analyzed",
                    **score_resume(resume_text, job_description),
                    "extracted_text_preview": " ".join(resume_text.split())[:300],
                }
            )
        except (
            ValueError,
            RuntimeError,
            fitz.FileDataError,
            PackageNotFoundError,
            zipfile.BadZipFile,
            OSError,
        ) as exc:
            results.append(
                {
                    "filename": filename,
                    "status": "error",
                    "error": str(exc),
                }
            )
        finally:
            await uploaded_file.close()

    results.sort(
        key=lambda result: (
            result["status"] != "analyzed",
            -(result.get("score") or 0),
            result["filename"].casefold(),
        )
    )
    analyzed_count = sum(result["status"] == "analyzed" for result in results)
    average_score = (
        sum(result["score"] for result in results if result.get("score") is not None)
        / analyzed_count
        if analyzed_count
        else 0.0
    )
    return {
        "results": results,
        "summary": {
            "total": len(results),
            "analyzed": analyzed_count,
            "errors": len(results) - analyzed_count,
            "average_score": round(average_score, 1),
            "job_skills": sorted(identify_skills(job_description)),
        },
    }


@app.post("/api/export")
def export_results(request: ExportRequest) -> StreamingResponse:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        [
            "Candidate",
            "Status",
            "Overall score",
            "Skill match",
            "Keyword match",
            "Matched skills",
            "Missing skills",
            "Error",
        ]
    )
    for result in request.results:
        writer.writerow(
            [
                result.filename,
                result.status,
                result.score if result.score is not None else "",
                result.skill_match if result.skill_match is not None else "",
                result.keyword_match if result.keyword_match is not None else "",
                ", ".join(result.matched_skills),
                ", ".join(result.missing_skills),
                result.error or "",
            ]
        )

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="resume-results.csv"'},
    )


app.mount(
    "/",
    StaticFiles(directory=PROJECT_DIR / "static", html=True),
    name="frontend",
)
