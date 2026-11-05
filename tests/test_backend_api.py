"""
Automated Integration Tests for Document Processing and Dashboard API Handlers.

Verifies:
- File format validation and file upload handling.
- Document extraction and Chapter creation from sample documents.
- User-specific document listing and filtering.
- Secure ownership enforcement on document retrieval.
- Document deletion and cleanup.
- Dashboard statistics aggregation.
"""

from __future__ import annotations

import io
import os
from pathlib import Path
import sys
import unittest

# Ensure isolated in-memory test database is used
TEST_DB_PATH = Path(__file__).resolve().parent / "test_api.db"
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"

# Ensure backend is in path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import HTTPException, UploadFile
from database import Base, SessionLocal, engine
import models
from main import (
    delete_document,
    get_dashboard_statistics,
    get_document_details,
    list_user_documents,
    upload_and_process_document,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
DOCS_DIR = FIXTURES_DIR / "documents"


class TestDocumentAPIHandlers(unittest.TestCase):
    """Test suite directly executing FastAPI document management handlers."""

    @classmethod
    def setUpClass(cls) -> None:
        Base.metadata.create_all(bind=engine)

    @classmethod
    def tearDownClass(cls) -> None:
        Base.metadata.drop_all(bind=engine)
        if TEST_DB_PATH.exists():
            try:
                TEST_DB_PATH.unlink()
            except OSError:
                pass

    def setUp(self) -> None:
        self.db = SessionLocal()
        # Clean any existing rows before test
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()

        # Create two distinct test users
        self.user_a = models.User(
            id=1,
            username="student_a",
            email="student_a@pagetovoice.com",
            password_hash="dummy_hash",
            role=models.UserRole.USER,
            is_active=True,
        )
        self.user_b = models.User(
            id=2,
            username="student_b",
            email="student_b@pagetovoice.com",
            password_hash="dummy_hash",
            role=models.UserRole.USER,
            is_active=True,
        )
        self.db.add(self.user_a)
        self.db.add(self.user_b)
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()

    def test_upload_unsupported_format(self) -> None:
        """Verify upload handler rejects unsupported file formats."""
        bad_file = UploadFile(
            filename="presentation.xyz",
            file=io.BytesIO(b"Unsupported binary data"),
        )
        with self.assertRaises(HTTPException) as ctx:
            upload_and_process_document(
                file=bad_file,
                current_user=self.user_a,
                db=self.db,
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Unsupported file format", ctx.exception.detail)

    def test_upload_and_process_txt_document(self) -> None:
        """Verify uploading sample.txt extracts text, creates chapters, and returns response."""
        sample_path = DOCS_DIR / "sample.txt"
        with open(sample_path, "rb") as f:
            content = f.read()

        upload_file = UploadFile(
            filename="lecture_notes.txt",
            file=io.BytesIO(content),
        )

        resp = upload_and_process_document(
            file=upload_file,
            mode="document",
            source_language="en",
            current_user=self.user_a,
            db=self.db,
        )

        self.assertEqual(resp.file_type, "txt")
        self.assertEqual(resp.status, "completed")
        self.assertIn("Page to Voice", resp.raw_text)
        self.assertTrue(len(resp.chapters) >= 5)

        # Verify DB records
        doc_in_db = self.db.query(models.Document).filter_by(id=resp.id).first()
        self.assertIsNotNone(doc_in_db)
        self.assertEqual(doc_in_db.user_id, self.user_a.id)

    def test_list_user_documents_isolation(self) -> None:
        """Verify list_user_documents only returns documents for the authenticated user."""
        f_a = UploadFile(filename="doc_a.txt", file=io.BytesIO(b"User A Content"))
        upload_and_process_document(file=f_a, current_user=self.user_a, db=self.db)

        f_b = UploadFile(filename="doc_b.txt", file=io.BytesIO(b"User B Content"))
        upload_and_process_document(file=f_b, current_user=self.user_b, db=self.db)

        # Query user_a's documents
        list_a = list_user_documents(current_user=self.user_a, db=self.db)
        self.assertEqual(len(list_a), 1)
        self.assertEqual(list_a[0].title, "Doc A")

        # Query user_b's documents
        list_b = list_user_documents(current_user=self.user_b, db=self.db)
        self.assertEqual(len(list_b), 1)
        self.assertEqual(list_b[0].title, "Doc B")

    def test_document_details_and_ownership_security(self) -> None:
        """Verify get_document_details enforces user ownership."""
        f_a = UploadFile(filename="private_notes.txt", file=io.BytesIO(b"Secret thoughts"))
        resp = upload_and_process_document(file=f_a, current_user=self.user_a, db=self.db)

        # User A can view
        detail = get_document_details(document_id=resp.id, current_user=self.user_a, db=self.db)
        self.assertEqual(detail.id, resp.id)
        self.assertIn("Secret thoughts", detail.raw_text)

        # User B cannot view (403 Forbidden)
        with self.assertRaises(HTTPException) as ctx:
            get_document_details(document_id=resp.id, current_user=self.user_b, db=self.db)
        self.assertEqual(ctx.exception.status_code, 403)

    def test_dashboard_statistics(self) -> None:
        """Verify get_dashboard_statistics aggregates metrics accurately."""
        stats0 = get_dashboard_statistics(current_user=self.user_a, db=self.db)
        self.assertEqual(stats0.total_documents, 0)

        f_a = UploadFile(filename="study_guide.txt", file=io.BytesIO(b"Important notes for finals"))
        upload_and_process_document(file=f_a, current_user=self.user_a, db=self.db)

        stats1 = get_dashboard_statistics(current_user=self.user_a, db=self.db)
        self.assertEqual(stats1.total_documents, 1)
        self.assertEqual(stats1.processed_documents, 1)
        self.assertEqual(stats1.processing_documents, 0)
        self.assertEqual(len(stats1.recent_documents), 1)
        self.assertEqual(len(stats1.recent_activities), 1)

    def test_delete_document_success_and_cleanup(self) -> None:
        """Verify delete_document cleans up document and chapters."""
        f_a = UploadFile(filename="obsolete.txt", file=io.BytesIO(b"Delete me"))
        resp = upload_and_process_document(file=f_a, current_user=self.user_a, db=self.db)

        del_result = delete_document(document_id=resp.id, current_user=self.user_a, db=self.db)
        self.assertEqual(del_result["status"], "success")

        with self.assertRaises(HTTPException) as ctx:
            get_document_details(document_id=resp.id, current_user=self.user_a, db=self.db)
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
