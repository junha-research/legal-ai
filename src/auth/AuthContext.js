import { createContext, useState, useEffect, useContext } from "react";
import { setAuthToken, api } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("idToken");
    if (!token) {
      setLoading(false);
      return;
    }

    setAuthToken(token);

    api.get("/auth/me")
      .then((res) => setUser(res.data))
      .catch(() => {
        localStorage.removeItem("idToken");
        setAuthToken(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (token) => {
    localStorage.setItem("idToken", token);
    setAuthToken(token);

    const res = await api.get("/auth/me");
    setUser(res.data);
  };

  const logout = () => {
    localStorage.removeItem("idToken");
    setAuthToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
