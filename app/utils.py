import os
import tempfile
from typing import List

from fastapi import HTTPException, UploadFile, status


ALLOWED_CONTENT_TYPES: List[str] = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
]


async def save_upload_to_temp_file(upload_file: UploadFile) -> str:
    """
    Save an uploaded image to a temporary file and return the file path.
    """
    validate_uploaded_image(upload_file)

    suffix = os.path.splitext(upload_file.filename or "")[1] or ".jpg"
    file_bytes = await upload_file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The file '{upload_file.filename}' is empty.",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name

    await upload_file.seek(0)
    return temp_path


def validate_uploaded_image(upload_file: UploadFile) -> None:
    """
    Validate the uploaded file before saving it.
    """
    if not upload_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    content_type = (upload_file.content_type or "").lower()
    if content_type not in [t.lower() for t in ALLOWED_CONTENT_TYPES]:
        # Swagger / some clients may not send a correct content-type.
        # Fallback to filename extension for validation.
        ext = (os.path.splitext(upload_file.filename or "")[1] or "").lower()
        ext_map = {
            ".jpg": "image/jpg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }
        allowed_by_ext = ext_map.get(ext)
        if allowed_by_ext not in [t.lower() for t in ALLOWED_CONTENT_TYPES]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported file type for '{upload_file.filename}'. "
                    f"Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
                ),
            )



def remove_temp_files(*file_paths: str) -> None:
    """
    Remove temporary files safely after processing.
    """
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
