import React, { useEffect, useState } from "react";
import { NavLink, Route, Routes, useLocation } from "react-router-dom";
import Register from "./pages/Register";
import Login from "./pages/Login";
import Slots from "./pages/Slots";
import MyMeetings from "./pages/MyMeetings";
import Consultant from "./pages/Consultant";
import { getSession, logout, type SessionUser } from "./lib/auth";
import { ProtectedRoute, VerifiedRoute, ConsultantRoute } from "./components/ProtectedRoute";

export default function App() {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [loading, setLoading] = useState(true);
  const location = useLocation();

  async function refreshSession() {
    setLoading(true);
    const sess = await getSession();
    setUser(sess?.user ?? null);
    setLoading(false);
  }

  useEffect(() => {
    refreshSession();
  }, [location.pathname]);

  return (
    <div>
      <div className="container">
        <div className="header">
          <div className="nav">
            <NavLink to="/slots">Slots</NavLink>
            {user?.role === "user" && <NavLink to="/my-meetings">My Meetings</NavLink>}
            {user?.role === "consultant" && <NavLink to="/consultant">My Consultations</NavLink>}
          </div>

          <div className="row" style={{ alignItems: "center" }}>
            {loading ? (
              <span className="small">Loading session…</span>
            ) : user ? (
              <>
                <span className="small" data-testid="session-email">
                  {user.email} <span className="badge">{user.role}</span>
                </span>
                <button
                  className="btn secondary"
                  data-testid="logout"
                  onClick={async () => {
                    await logout();
                    await refreshSession();
                  }}
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <NavLink to="/login" data-testid="nav-login">Login</NavLink>
                <NavLink to="/register" data-testid="nav-register">Register</NavLink>
              </>
            )}
          </div>
        </div>

        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login />} />

          <Route
            path="/slots"
            element={
              <ProtectedRoute user={user}>
                <Slots user={user as any} />
              </ProtectedRoute>
            }
          />

          <Route
            path="/my-meetings"
            element={
              <ProtectedRoute user={user}>
                <MyMeetings />
              </ProtectedRoute>
            }
          />

          <Route
            path="/consultant"
            element={
              <ConsultantRoute user={user}>
                <Consultant />
              </ConsultantRoute>
            }
          />
        </Routes>
      </div>
    </div>
  );
}
