import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import { authAPI } from "./api";

const AuthContext = createContext(null);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("prism_token");
    const savedUser = localStorage.getItem("prism_user");
    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        localStorage.removeItem("prism_token");
        localStorage.removeItem("prism_user");
      }
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (email, password) => {
    const res = await authAPI.login(email, password);
    const { access_token, user: userData } = res.data;
    localStorage.setItem("prism_token", access_token);
    localStorage.setItem("prism_user", JSON.stringify(userData));
    setUser(userData);
    return userData;
  }, []);

  const register = useCallback(
    async (name, email, password) => {
      const res = await authAPI.register(name, email, password);
      const { access_token, user: userData } = res.data;
      localStorage.setItem("prism_token", access_token);
      localStorage.setItem("prism_user", JSON.stringify(userData));
      setUser(userData);
      return userData;
    },
    [],
  );

  const logout = useCallback(() => {
    localStorage.removeItem("prism_token");
    localStorage.removeItem("prism_user");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {!loading && children}
    </AuthContext.Provider>
  );
}
