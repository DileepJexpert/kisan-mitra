from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas import OCRRequest, OCRResponse

router = APIRouter()


@router.post("/ocr/extract", response_model=OCRResponse)
async def extract_text(request: OCRRequest):
    """Extract text from an image using PaddleOCR."""
    return JSONResponse(
        status_code=501,
        content={"detail": "OCR extraction endpoint not yet implemented"},
    )
