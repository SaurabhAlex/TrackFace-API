# Face Recognition REST API

A simple and clean Face Recognition REST API built with FastAPI and DeepFace.

## Folder Structure

```text
project/
|-- app/
|   |-- __init__.py
|   |-- main.py
|   |-- routes.py
|   |-- services.py
|   `-- utils.py
|-- requirements.txt
`-- README.md
```

## Features

- FastAPI-based REST API
- DeepFace face verification
- Async route handling
- Automatic Swagger docs
- CORS enabled
- Temporary file handling
- Face detection validation before verification
- Clean modular structure

## API Endpoint

### `POST /verify-face`

Accepts two uploaded image files:

- `registered_image`
- `live_image`

Returns:

- `verified`
- `distance`
- `message`
- `threshold` when available

## Sample Response

```json
{
  "verified": true,
  "distance": 0.32,
  "message": "Face matched successfully"
}
```

## Installation

### 1. Create a virtual environment

```bash
python3 -m venv venv
```

### 2. Activate the virtual environment

On macOS/Linux:

```bash
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Run the Server

```bash
uvicorn app.main:app --reload
```

The API will run at:

- `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`

## Example cURL Request

```bash
curl -X POST "http://127.0.0.1:8000/verify-face" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "registered_image=@registered.jpg" \
  -F "live_image=@live.jpg"
```

## Notes

- No database is used.
- The API stores uploaded files only temporarily during processing.
- If no face is detected in either image, the API returns a `400` error.
- If DeepFace processing fails unexpectedly, the API returns a `500` error.
