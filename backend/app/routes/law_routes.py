from fastapi import APIRouter
from app.services.law_service import (
    extract_law_name_service,
    search_law_service,
    get_law_detail_service,
)

router = APIRouter(prefix="/law", tags=["Law"])

@router.post("/extract-name")
async def extract_name(data: dict):
    return await extract_law_name_service(data.get("text", ""))

@router.get("/search")
async def search_law(q: str):
    return await search_law_service(q)

@router.get("/detail/{law_id}")
async def law_detail(law_id: str):
    return await get_law_detail_service(law_id)
