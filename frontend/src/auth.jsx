import { createContext, useContext, useEffect, useState } from "react";
import { api, setAuthToken, setUnauthorizedHandler } from "./api";

const AuthContext = createContext(null);

const STORAGE_KEY = "carbon_platform_token";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEY));
  const [user, setUser] = useState(null);
  const [tenant, setTenant] = useState(null);
  const [loading, setLoading] = useState(true);

  function clearSession() {
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
    setUser(null);
    setTenant(null);
    setAuthToken(null);
  }

  useEffect(() => {
    setUnauthorizedHandler(clearSession);
  }, []);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    setAuthToken(token);
    api
      .get("/auth/me")
      .then((me) => {
        setUser(me.user);
        setTenant(me.tenant);
      })
      .catch(() => clearSession())
      .finally(() => setLoading(false));
  }, [token]);

  function applySession(data) {
    localStorage.setItem(STORAGE_KEY, data.access_token);
    setAuthToken(data.access_token);
    setToken(data.access_token);
    setUser(data.user);
    setTenant(data.tenant);
  }

  async function login(email, password) {
    const data = await api.post("/auth/login", { email, password });
    applySession(data);
  }

  async function register(tenantName, email, password) {
    const data = await api.post("/auth/register", { tenant_name: tenantName, email, password });
    applySession(data);
  }

  function logout() {
    clearSession();
  }

  return (
    <AuthContext.Provider value={{ token, user, tenant, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
