// src/auth/firebase.js
import { initializeApp } from "firebase/app";
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signOut,
} from "firebase/auth";

// --- Firebase Config  ---
const firebaseConfig = {
  apiKey: "AIzaSyCavHNnaKWU88KtfcT7C7fVAXBQPuAfGJU",
  authDomain: "legal-ai-9bd08.firebaseapp.com",
  projectId: "legal-ai-9bd08",
  storageBucket: "legal-ai-9bd08.firebasestorage.app",
  messagingSenderId: "29968935057",
  appId: "1:29968935057:web:abb3f0efad75df6f7ab730",
};

// --- 초기화 (이 순서 절대 바꾸면 안됨) ---
const app = initializeApp(firebaseConfig);

// --- Auth 객체 생성 ---
export const auth = getAuth(app);

// --- Provider 객체 생성 ---
export const provider = new GoogleAuthProvider();

// --- 로그인 함수 ---
export async function loginWithGoogle() {
  const result = await signInWithPopup(auth, provider);
  const token = await result.user.getIdToken();
  return { token, user: result.user };
}

// --- 로그아웃 함수 ---
export async function logoutFirebase() {
  await signOut(auth);
}
