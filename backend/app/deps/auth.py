# app/deps/auth.py

import os
import json

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

import firebase_admin
from firebase_admin import auth, credentials

from app.db.database import SessionLocal
from app.db.models import User


# =========================
# 🔥 Firebase Admin 초기화
# =========================
firebase_key_json = os.getenv("FIREBASE_ADMIN_KEY")
firebase_key_path = os.getenv("FIREBASE_ADMIN_KEY_PATH")

if not firebase_admin._apps:
    cred = None

    if firebase_key_json:
        # 1) JSON 문자열 방식 (Render 환경에서 주로 사용)
        try:
            data = json.loads(firebase_key_json)
        except json.JSONDecodeError:
            raise Exception("❌ FIREBASE_ADMIN_KEY 는 유효한 JSON 문자열이어야 합니다.")
        cred = credentials.Certificate(data)

    elif firebase_key_path:
        # 2) 로컬/서버에서 JSON 파일 경로를 직접 넘기는 방식
        if not os.path.exists(firebase_key_path):
            raise Exception(f"❌ FIREBASE_ADMIN_KEY_PATH 파일을 찾을 수 없습니다: {firebase_key_path}")
        cred = credentials.Certificate(firebase_key_path)

    else:
        raise Exception("❌ FIREBASE_ADMIN_KEY 또는 FIREBASE_ADMIN_KEY_PATH 중 하나는 반드시 설정해야 합니다.")

    firebase_admin.initialize_app(cred)


# =========================
# 🔁 DB 세션
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# 🔐 HTTP Bearer 인증
# =========================
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    - 프론트에서 Authorization: Bearer <idToken> 을 보내면
    - Firebase ID Token 검증 → uid, email, name 가져와서
    - 내부 User DB에서 조회 / 없으면 생성
    """

    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="인증 토큰이 없습니다.")

    id_token = credentials.credentials

    try:
        decoded = auth.verify_id_token(id_token)
    except Exception:
        raise HTTPException(status_code=401, detail="유효하지 않은 Firebase ID 토큰입니다.")

    firebase_uid = decoded.get("uid")
    email = decoded.get("email")
    name = decoded.get("name")

    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Firebase UID 를 찾을 수 없습니다.")

    # DB에서 유저 조회
    user = db.query(User).filter(User.open_id == firebase_uid).first()

    # 없으면 생성
    if not user:
        user = User(
            open_id=firebase_uid,
            email=email,
            name=name,
            login_method="firebase",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user
