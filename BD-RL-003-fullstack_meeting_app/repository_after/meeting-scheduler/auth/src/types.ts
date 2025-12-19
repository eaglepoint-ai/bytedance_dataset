export type Role = "user" | "consultant";

export type SessionUser = {
  id: string;
  email: string;
  role: Role;
};

export type SessionResponse = {
  user: SessionUser;
};
