import { createContext, useContext, useState, useEffect } from "react";
import { getMe } from "../api/auth";
import i18n from "../i18n";

const AuthContext = createContext(null);

function applyLanguage(user) {
  const lang = user?.language || "en";
  localStorage.setItem("language", lang);
  i18n.changeLanguage(lang);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      getMe()
        .then((u) => { setUser(u); applyLanguage(u); })
        .catch(() => localStorage.removeItem("access_token"))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = (token) => {
    localStorage.setItem("access_token", token);
    return getMe().then((u) => { setUser(u); applyLanguage(u); });
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
