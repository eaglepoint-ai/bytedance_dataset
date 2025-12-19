import React from "react";
import { Navigate } from "react-router-dom";
import type { SessionUser } from "../lib/auth";

export function ProtectedRoute({
  user,
  children,
}: {
  user: SessionUser | null;
  children: React.ReactNode;
}) {
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export function VerifiedRoute({
  user,
  children,
}: {
  user: SessionUser | null;
  children: React.ReactNode;
}) {
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export function ConsultantRoute({
  user,
  children,
}: {
  user: SessionUser | null;
  children: React.ReactNode;
}) {
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "consultant") return <div className="card">Consultant only.</div>;
  return <>{children}</>;
}
