from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.auth import (
    DUMMY_PASSWORD,
    DUMMY_USERNAME,
    create_access_token,
    get_current_subject,
)
from app.services import verify_faces
from app.utils import remove_temp_files, save_upload_to_temp_file



router = APIRouter(tags=["Face Verification"])


class TokenResponse(BaseModel):
    access_token: str = Field(..., example="<jwt_token>")
    token_type: str = Field(..., example="bearer")


class LoginRequest(BaseModel):
    username: str = Field(..., example=DUMMY_USERNAME)
    password: str = Field(..., example=DUMMY_PASSWORD)



class VerifyFaceResponse(BaseModel):
    verified: bool = Field(..., example=True)
    distance: float = Field(..., example=0.32)
    message: str = Field(..., example="Face matched successfully")
    threshold: Optional[float] = Field(default=None, example=0.4)


@router.post("/login", response_model=TokenResponse, summary="Get dummy JWT token")
async def token(payload: LoginRequest) -> TokenResponse:
    if payload.username != DUMMY_USERNAME or payload.password != DUMMY_PASSWORD:
        # keep it generic to avoid user enumeration
        raise Exception("Invalid credentials")

    token_str = create_access_token(subject=payload.username)
    return TokenResponse(access_token=token_str, token_type="bearer")


@router.post(
    "/verify-face",
    summary="Verify live face against all registered employees",
)
async def verify_face(
    _subject: str = Depends(get_current_subject),
    live_image: UploadFile = File(
        ...,
        description="Live face image for verification.",
    ),
):
    """Compare the uploaded live image with all employee images listed in employee_data.json."""

    # Load employee dataset

    import json
    import logging
    from pathlib import Path

    logger = logging.getLogger("face-verification")

    base_dir = Path(__file__).resolve().parent
    dataset_path = base_dir / "employee_data.json"

    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))


    live_image_path = ""
    try:
        live_image_path = await save_upload_to_temp_file(live_image)

        best_match = None
        match_threshold = None

        best_match = None
        best_distance = None
        best_threshold = None

        for emp in dataset:
            emp_id = str(emp.get("id"))
            emp_name = str(emp.get("name"))
            # employee_data.json contains relative paths like: "images/shivam.png"
            rel_path = str(emp.get("registered_image_path") or emp.get("registered_image_filename") or "")
            if not rel_path:
                continue

            registered_path = base_dir / rel_path
            if not registered_path.exists():
                logger.info("Skipping missing registered image: %s", registered_path)
                continue

            result = await run_in_threadpool(
                verify_faces,
                str(registered_path),
                live_image_path,
            )

            verified = bool(result.get("verified", False))
            distance = result.get("distance")
            threshold = result.get("threshold")

            logger.info(
                "Verified check emp_name=%s emp_id=%s verified=%s distance=%s threshold=%s",
                emp_name,
                emp_id,
                verified,
                distance,
                threshold,
            )

            # Select BEST match = lowest distance (if available)
            if distance is None:
                continue

            if best_distance is None or float(distance) < float(best_distance):
                best_distance = distance
                best_threshold = threshold
                best_match = {
                    "employee_id": emp_id,
                    "employee_name": emp_name,
                }



        if best_match is None:
            return {
                "success": False,
                "message": "No employee face match found.",
            }

        # Match only if distance < threshold (when threshold available)
        if best_threshold is not None:
            try:
                if float(best_distance) >= float(best_threshold):
                    return {
                        "success": False,
                        "message": "No employee face match found.",
                    }
            except Exception:
                # If parsing fails, fall back to verified boolean only
                pass

        return {
            "success": True,
            "message": "Face matched successfully.",
            "matched_employee_id": best_match["employee_id"],
            "matched_employee_name": best_match["employee_name"],
            "distance": best_distance,
            "threshold": best_threshold,
        }


    finally:
        if live_image_path:
            remove_temp_files(live_image_path)

