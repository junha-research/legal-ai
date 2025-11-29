# app/services/law_service.py

# 법령 이름 추출
async def extract_law_name_service(text: str):
    # TODO: 실제 구현
    return {"law_name": "dummy_law"}

# 법령 검색
async def search_law_service(query: str):
    # TODO: 실제 구현
    return {"results": ["result 1", "result 2"]}

# 법령 상세 조회
async def get_law_detail_service(law_id: str):
    # TODO: 실제 구현
    return {"law_id": law_id, "detail": "dummy detail"}
