import io
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.document_storage import (
    document_storage_service,
)


client = TestClient(app)


@pytest.fixture
def temporary_upload_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    monkeypatch.setattr(
        document_storage_service,
        "upload_directory",
        tmp_path,
    )

    return tmp_path


def create_valid_docx() -> bytes:
    buffer = io.BytesIO()

    with zipfile.ZipFile(
        buffer,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.writestr(
            "[Content_Types].xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                "<Types></Types>"
            ),
        )

        archive.writestr(
            "word/document.xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                "<document><body><p>KnowFlow AI</p></body></document>"
            ),
        )

    return buffer.getvalue()


def test_supported_document_types() -> None:
    response = client.get(
        "/api/v1/documents/supported-types"
    )

    assert response.status_code == 200
    assert response.json() == {
        "extensions": [".pdf", ".docx", ".txt"],
        "max_upload_size_mb": 10,
    }


def test_upload_valid_pdf(
    temporary_upload_directory: Path,
) -> None:
    pdf_content = (
        b"%PDF-1.7\n"
        b"1 0 obj\n"
        b"<< /Type /Catalog >>\n"
        b"endobj\n"
        b"%%EOF"
    )

    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "company-policy.pdf",
                pdf_content,
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201

    response_body = response.json()

    assert response_body["original_filename"] == (
        "company-policy.pdf"
    )
    assert response_body["file_extension"] == ".pdf"
    assert response_body["content_type"] == "application/pdf"
    assert response_body["size_bytes"] == len(pdf_content)
    assert response_body["status"] == "uploaded"

    stored_file = (
        temporary_upload_directory
        / response_body["stored_filename"]
    )

    assert stored_file.exists()
    assert stored_file.read_bytes() == pdf_content


def test_upload_valid_txt(
    temporary_upload_directory: Path,
) -> None:
    text_content = (
        b"KnowFlow AI enterprise knowledge assistant."
    )

    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "company-notes.txt",
                text_content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 201
    assert response.json()["file_extension"] == ".txt"
    assert response.json()["status"] == "uploaded"

    stored_file = (
        temporary_upload_directory
        / response.json()["stored_filename"]
    )

    assert stored_file.exists()


def test_upload_valid_docx(
    temporary_upload_directory: Path,
) -> None:
    docx_content = create_valid_docx()

    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "employee-handbook.docx",
                docx_content,
                (
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
            )
        },
    )

    assert response.status_code == 201
    assert response.json()["file_extension"] == ".docx"
    assert response.json()["status"] == "uploaded"

    stored_file = (
        temporary_upload_directory
        / response.json()["stored_filename"]
    )

    assert stored_file.exists()


def test_reject_unsupported_extension(
    temporary_upload_directory: Path,
) -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "malware.exe",
                b"not a supported document",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 415
    assert response.json() == {
        "error": {
            "code": "UNSUPPORTED_FILE_TYPE",
            "message": (
                "Only PDF, DOCX, and TXT files are supported."
            ),
        }
    }

    assert list(temporary_upload_directory.iterdir()) == []


def test_reject_empty_file(
    temporary_upload_directory: Path,
) -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "empty.txt",
                b"",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EMPTY_FILE"
    assert list(temporary_upload_directory.iterdir()) == []


def test_reject_fake_pdf(
    temporary_upload_directory: Path,
) -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "fake.pdf",
                b"This is not actually a PDF.",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == (
        "INVALID_PDF_FILE"
    )

    assert list(temporary_upload_directory.iterdir()) == []


def test_reject_binary_txt(
    temporary_upload_directory: Path,
) -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "binary.txt",
                b"\x00\x01\x02\x03",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == (
        "INVALID_TEXT_FILE"
    )

    assert list(temporary_upload_directory.iterdir()) == []


def test_reject_file_larger_than_limit(
    temporary_upload_directory: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "max_upload_size_mb",
        1,
    )

    oversized_content = b"A" * (1024 * 1024 + 1)

    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "oversized.txt",
                oversized_content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"
    assert list(temporary_upload_directory.iterdir()) == []