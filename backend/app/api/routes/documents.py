from fastapi import APIRouter, File, UploadFile, status

from app.core.config import settings
from app.schemas.chunk import ChunkingConfigurationResponse
from app.schemas.document import (
    DocumentProcessingResponse,
    DocumentUploadResponse,
    SupportedDocumentTypesResponse,
)
from app.services.chunking import document_chunking_service
from app.services.document_processing import (
    document_processing_service,
)
from app.services.document_storage import (
    document_storage_service,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an enterprise document",
    description=(
        "Uploads and validates a PDF, DOCX, or UTF-8 TXT document."
    ),
)
async def upload_document(
    file: UploadFile = File(
        ...,
        description="PDF, DOCX, or UTF-8 TXT document.",
    ),
) -> DocumentUploadResponse:
    return await document_storage_service.save_document(file)


@router.get(
    "/supported-types",
    response_model=SupportedDocumentTypesResponse,
    status_code=status.HTTP_200_OK,
    summary="List supported document formats",
)
async def get_supported_document_types(
) -> SupportedDocumentTypesResponse:
    return SupportedDocumentTypesResponse(
        extensions=list(settings.allowed_document_extensions),
        max_upload_size_mb=settings.max_upload_size_mb,
    )


@router.get(
    "/chunking/configuration",
    response_model=ChunkingConfigurationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get chunking configuration",
)
async def get_chunking_configuration(
) -> ChunkingConfigurationResponse:
    return document_chunking_service.get_configuration()


@router.post(
    "/{document_id}/process",
    response_model=DocumentProcessingResponse,
    status_code=status.HTTP_200_OK,
    summary="Process an uploaded document",
    description=(
        "Extracts structured text and metadata from an uploaded document."
    ),
)
async def process_document(
    document_id: str,
) -> DocumentProcessingResponse:
    return document_processing_service.process_document(document_id)


@router.post(
    "/{document_id}/chunk/validate",
    status_code=status.HTTP_200_OK,
    summary="Validate document for chunking",
    description=(
        "Validates that processed document data is available for chunking."
    ),
)
async def validate_document_for_chunking(
    document_id: str,
) -> dict[str, str | int]:
    processed_document = (
        document_chunking_service.validate_processed_document(document_id)
    )

    sections = processed_document["sections"]

    return {
        "document_id": document_id,
        "status": "ready_for_chunking",
        "sections_available": len(sections),
    }