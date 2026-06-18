"use client";

import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ApiError, CurrentUser, getCurrentUser, logout } from "@/lib/api";

interface AuthContextValue {
  user: CurrentUser | null;
  isLoading: boolean;
  error: string | null;
  refreshUser: () => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refreshUser() {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getCurrentUser();
      setUser(response.user);
    } catch (caught) {
      setUser(null);
      if (caught instanceof ApiError && caught.status === 401) {
        setError(null);
      } else if (caught instanceof Error) {
        setError(caught.message);
      } else {
        setError("Unable to load the current user.");
      }
    } finally {
      setIsLoading(false);
    }
  }

  async function signOut() {
    try {
      await logout();
    } finally {
      setUser(null);
    }
  }

  useEffect(() => {
    void refreshUser();
  }, []);

  const value = useMemo(
    () => ({ user, isLoading, error, refreshUser, signOut }),
    [user, isLoading, error],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function AuthenticatedShell({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <AuthGate>{children}</AuthGate>
    </AuthProvider>
  );
}

function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, isLoading, error } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !user && !error) {
      router.replace(`/?next=${encodeURIComponent(pathname)}`);
    }
  }, [error, isLoading, pathname, router, user]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <p className="text-sm text-muted-foreground">Loading account...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="max-w-md rounded-lg border bg-card p-6 text-center shadow-sm">
          <h1 className="text-lg font-semibold">Unable to load account</h1>
          <p className="mt-2 text-sm text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return <>{children}</>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return value;
}
