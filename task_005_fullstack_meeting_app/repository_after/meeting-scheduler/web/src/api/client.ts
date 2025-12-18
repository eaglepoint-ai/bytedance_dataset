const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function apiFetch(path: string, init: RequestInit = {}) {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(init.headers || {}),
      },
    });

    const text = await res.text();
    let data: any = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = text;
    }

    if (!res.ok) {
      const message = data?.detail || data?.error || res.statusText;
      const err = new Error(message);
      (err as any).status = res.status;
      (err as any).data = data;
      throw err;
    }
    return data;
  } catch (error: any) {
    // Handle network errors (CORS, connection refused, etc.)
    if (error.name === "TypeError" || error.message === "Failed to fetch") {
      const networkErr = new Error("Unable to connect to server. Please check if the API is running.");
      (networkErr as any).status = 0;
      (networkErr as any).isNetworkError = true;
      throw networkErr;
    }
    // Re-throw other errors
    throw error;
  }
}
