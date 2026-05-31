from typing import Any, Dict, Optional

import cv2
import numpy as np
from fastapi import HTTPException, status


OPENCV_FALLBACK_THRESHOLD = 0.45


def get_deepface() -> Optional[Any]:
    """
    Import DeepFace lazily. Return None when it is not available so the API
    can fall back to a lightweight OpenCV-based verifier.
    """
    try:
        from deepface import DeepFace
    except Exception:
        return None

    return DeepFace


def extract_face_with_opencv(image_path: str, image_label: str) -> np.ndarray:
    """
    Detect and crop the most prominent face from the image using Haar cascades.
    """
    image = cv2.imread(image_path)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read the {image_label}.",
        )

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    faces = detector.detectMultiScale(
        gray_image,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),
    )

    if len(faces) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No face detected in the {image_label}.",
        )

    # Use the largest detected face for comparison.
    x, y, w, h = max(faces, key=lambda face: face[2] * face[3])
    face_region = gray_image[y : y + h, x : x + w]
    return cv2.resize(face_region, (160, 160))


def build_face_embedding(face_image: np.ndarray) -> np.ndarray:
    """
    Convert a face crop into a normalized vector for lightweight comparison.
    """
    normalized = cv2.equalizeHist(face_image)
    vector = normalized.astype("float32").flatten()
    norm = np.linalg.norm(vector)
    if norm == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to build a valid face representation.",
        )
    return vector / norm


def compare_faces_with_opencv(
    registered_image_path: str,
    live_image_path: str,
) -> Dict[str, Any]:
    """
    Fallback verifier used when DeepFace is unavailable in the environment.
    """
    registered_face = extract_face_with_opencv(
        registered_image_path,
        "registered image",
    )
    live_face = extract_face_with_opencv(live_image_path, "live image")

    registered_vector = build_face_embedding(registered_face)
    live_vector = build_face_embedding(live_face)

    similarity = float(np.dot(registered_vector, live_vector))
    distance = float(1.0 - similarity)
    verified = distance <= OPENCV_FALLBACK_THRESHOLD

    return {
        "verified": verified,
        "distance": round(distance, 4),
        "message": (
            "Face matched successfully"
            if verified
            else "Face did not match"
        ),
        "threshold": OPENCV_FALLBACK_THRESHOLD,
    }


def verify_faces_with_deepface(
    deepface: Any,
    registered_image_path: str,
    live_image_path: str,
) -> Dict[str, Any]:
    """
    Validate both images and compare the detected faces using DeepFace.
    """
    try:
        deepface.extract_faces(
            img_path=registered_image_path,
            detector_backend="retinaface",
            enforce_detection=True,
        )
        deepface.extract_faces(
            img_path=live_image_path,
            detector_backend="retinaface",
            enforce_detection=True,
        )
    except ValueError as exc:
        error_message = str(exc).lower()
        if "img1" in error_message or "registered" in error_message:
            detail = "No face detected in the registered image."
        elif "img2" in error_message or "live" in error_message:
            detail = "No face detected in the live image."
        else:
            detail = "No face detected in one of the uploaded images."
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the uploaded images.",
        ) from exc

    try:
        result = deepface.verify(
            img1_path=registered_image_path,
            img2_path=live_image_path,
            detector_backend="retinaface",
            model_name="Facenet512",
            enforce_detection=True,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Face verification failed because a face could not be processed.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred during face verification.",
        ) from exc

    verified = bool(result.get("verified", False))
    distance = float(result.get("distance", 0.0))
    threshold = result.get("threshold")

    response: Dict[str, Any] = {
        "verified": verified,
        "distance": distance,
        "message": (
            "Face matched successfully"
            if verified
            else "Face did not match"
        ),
    }

    if threshold is not None:
        response["threshold"] = float(threshold)

    return response


def verify_faces(registered_image_path: str, live_image_path: str) -> Dict[str, Any]:
    """
    Use DeepFace when installed, otherwise fall back to OpenCV verification.
    """
    deepface = get_deepface()
    if deepface is not None:
        try:
            return verify_faces_with_deepface(
                deepface,
                registered_image_path,
                live_image_path,
            )
        except HTTPException:
            # DeepFace couldn't detect/process faces; fall back to OpenCV.
            pass
        except Exception:
            pass

    return compare_faces_with_opencv(registered_image_path, live_image_path)

