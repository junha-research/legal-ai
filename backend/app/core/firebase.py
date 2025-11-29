import firebase_admin
from firebase_admin import credentials
import os

key_path = os.getenv("FIREBASE_ADMIN_KEY_PATH")

if not key_path:
    raise Exception("❌ FIREBASE_ADMIN_KEY_PATH missing!")

if not firebase_admin._apps:
    cred = credentials.Certificate(key_path)
    firebase_admin.initialize_app(cred)
