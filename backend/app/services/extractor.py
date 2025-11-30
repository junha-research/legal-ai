# app/services/extractor.py

from __future__ import annotations

import io
import os
import tempfile
from typing import Final

from fastapi import UploadFile
from pdf2image import convert_from_bytes
from docx import Document
from google.cloud import vision
from PIL import Image


# MIME 타입들
IMAGE_TYPES: Final[set[str]] = {"image/png", "image/jpeg", "image/jpg"}
PDF_TYPES: Final[set[str]] = {"application/pdf"}
DOCX_TYPES: Final[set[str]] = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}


# ----------------------------------------
# Google Vision OCR 함수
# ----------------------------------------
def google_vision_ocr(img_bytes: bytes) -> str:
    """
    Google Vision OCR로 문자열 추출 (가장 정확함)
    """
    try:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=img_bytes)
        response = client.text_detection(image=image)

        if response.error.message:
            print("❌ Vision API Error:", response.error.message)
            return ""

        return response.full_text_annotation.text or ""

    except Exception as e:
        print("❌ Vision OCR Exception:", e)
        return ""


# ----------------------------------------
# 메인 파일 텍스트 추출 함수
# ----------------------------------------
async def extract_text_from_file(file: UploadFile) -> str:
    """
    업로드된 파일에서 텍스트를 추출 (PDF, 이미지, DOCX, TXT).
    모든 PDF는 이미지로 변환하여 Vision-OCR로 처리 → 정확도 최고.
    """

    filename = file.filename or ""
    content_type = file.content_type or ""
    raw_bytes: bytes = await file.read()

    # 1) Plain Text
    if content_type.startswith("text/"):
        try:
            return raw_bytes.decode("utf-8", errors="ignore")
        except:
            return raw_bytes.decode("cp949", errors="ignore")

    # 2) PDF → 모든 PDF 이미 OCR 처리
    if content_type in PDF_TYPES or filename.lower().endswith(".pdf"):
        try:
            pages = convert_from_bytes(raw_bytes, dpi=300)  # 고해상도로 변환
        except Exception as e:
            raise ValueError(f"❌ PDF 변환 오류: {e}")

        extracted_text = ""

        for page in pages:
            img_byte_arr = io.BytesIO()
            page.save(img_byte_arr, format="PNG")
            img_bytes = img_byte_arr.getvalue()

            page_text = google_vision_ocr(img_bytes)
            extracted_text += page_text + "\n"

        return extracted_text or ""

    # 3) DOCX
    if content_type in DOCX_TYPES or filename.lower().endswith(".docx"):
        try:
            with io.BytesIO(raw_bytes) as f:
                doc = Document(f)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as e:
            raise ValueError(f"❌ DOCX 읽기 오류: {e}")

    # 4) HWP 안내
    if filename.lower().endswith(".hwp"):
        raise ValueError(
            "❌ HWP 파일은 직접 추출 불가합니다.\n"
            "한글 프로그램에서 PDF 또는 HWPX로 변환 후 업로드해 주세요."
        )

    # 5) 이미지 → Vision OCR
    if (
        content_type in IMAGE_TYPES
        or filename.lower().endswith((".png", ".jpg", ".jpeg"))
    ):
        try:
            img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="PNG")
            img_bytes = img_byte_arr.getvalue()
        except:
            raise ValueError("❌ 이미지 파일 로드 오류")

        return google_vision_ocr(img_bytes)

    # 6) 기타 확장자
    raise ValueError(
        f"❌ 지원하지 않는 파일 형식입니다: {filename}\n"
        f"PDF, DOCX, TXT, 이미지(png/jpg/jpeg)만 지원합니다."
    )
