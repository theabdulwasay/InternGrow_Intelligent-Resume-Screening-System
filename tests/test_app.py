import io
import unittest

import pymupdf
from docx import Document

from app import extract_resume_text, identify_skills, score_resume


class SkillMatchingTests(unittest.TestCase):
    def test_identifies_skills_without_matching_substrings(self):
        self.assertEqual(
            identify_skills("Python, SQL, and machine learning"),
            {"Python", "SQL", "Machine Learning"},
        )
        self.assertNotIn("Java", identify_skills("JavaScript developer"))

    def test_scores_skill_and_keyword_coverage(self):
        result = score_resume(
            "Python SQL data analysis reporting",
            "Seeking Python, SQL and Tableau skills for data analysis.",
        )
        self.assertEqual(result["matched_skills"], ["Data Analysis", "Python", "SQL"])
        self.assertEqual(result["missing_skills"], ["Tableau"])
        self.assertGreater(result["score"], 0)
        self.assertLess(result["score"], 100)

    def test_uses_keyword_score_when_role_has_no_recognized_skills(self):
        result = score_resume(
            "Experienced in stakeholder engagement and quarterly reporting",
            "Seeking stakeholder engagement and quarterly reporting experience",
        )
        self.assertEqual(result["skill_match"], result["keyword_match"])
        self.assertEqual(result["score"], result["keyword_match"])


class ResumeExtractionTests(unittest.TestCase):
    def test_rejects_unsupported_resume_type(self):
        with self.assertRaisesRegex(ValueError, "Unsupported file type"):
            extract_resume_text("resume.txt", b"not a resume")

    def test_extracts_docx_paragraphs_and_table_cells(self):
        document = Document()
        document.add_paragraph("Python engineer")
        table = document.add_table(rows=1, cols=2)
        table.cell(0, 0).text = "SQL"
        table.cell(0, 1).text = "Data analysis"
        buffer = io.BytesIO()
        document.save(buffer)

        text = extract_resume_text("resume.docx", buffer.getvalue())

        self.assertIn("Python engineer", text)
        self.assertIn("SQL", text)
        self.assertIn("Data analysis", text)

    def test_extracts_text_from_digital_pdf(self):
        document = pymupdf.open()
        page = document.new_page()
        page.insert_text((72, 72), "Python engineer with SQL experience")

        text = extract_resume_text("resume.pdf", document.tobytes())

        self.assertIn("Python engineer", text)
        self.assertIn("SQL", text)


if __name__ == "__main__":
    unittest.main()
