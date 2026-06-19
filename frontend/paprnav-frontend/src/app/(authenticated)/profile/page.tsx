"use client";

import React, { FormEvent, useEffect, useState } from "react";
import { CheckCircle2, Palette, Save, ShieldCheck } from "lucide-react";
import { useAuth } from "@/components/AuthProvider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { PageHeader } from "@/components/PageHeader";
import { ThemeSelect } from "@/components/ThemeToggle";
import { ApiError, updateProfile } from "@/lib/api";

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [name, setName] = useState(user?.name ?? "");
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setName(user?.name ?? "");
  }, [user?.name]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    setMessage(null);

    try {
      await updateProfile({ name });
      await refreshUser();
      setMessage("Profile saved.");
    } catch (caught) {
      if (caught instanceof ApiError || caught instanceof Error) {
        setError(caught.message);
      } else {
        setError("Unable to save profile.");
      }
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <PageHeader
        title="Profile"
        description="Manage your account settings and preferences"
      />

      <div className="mt-8 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
            <CardDescription>
              Update the name shown in paprnav. Email changes are not enabled for the local MVP.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <Label htmlFor="full-name">Full Name</Label>
                <Input
                  id="full-name"
                  name="full-name"
                  type="text"
                  autoComplete="name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Name"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email address</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  value={user?.email ?? ""}
                  readOnly
                />
              </div>

              {user?.memberships.length ? (
                <div className="space-y-2">
                  <Label>Organizations</Label>
                  <div className="space-y-2 rounded-md border bg-muted/30 p-3">
                    {user.memberships.map((membership) => (
                      <div
                        key={membership.organizationId}
                        className="flex flex-col gap-1 text-sm sm:flex-row sm:items-center sm:justify-between"
                      >
                        <span className="font-medium">{membership.organizationName}</span>
                        <span className="text-muted-foreground">{membership.role.replaceAll("_", " ")}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {message ? (
                <p className="flex items-center gap-2 text-sm text-green-700 dark:text-green-400">
                  <CheckCircle2 className="h-4 w-4" />
                  {message}
                </p>
              ) : null}
              {error ? <p className="text-sm text-destructive">{error}</p> : null}

              <div className="flex justify-end">
                <Button type="submit" disabled={isSaving || !name.trim()}>
                  <Save className="mr-2 h-4 w-4" />
                  {isSaving ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <Separator />

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Palette className="h-5 w-5" />
              Appearance
            </CardTitle>
            <CardDescription>
              Customize how paprnav looks on your device
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Theme</Label>
                <p className="text-sm text-muted-foreground mb-3">
                  Select your preferred color theme
                </p>
                <ThemeSelect />
              </div>
            </div>
          </CardContent>
        </Card>

        <Separator />

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5" />
              Account Security
            </CardTitle>
            <CardDescription>
              Authentication is backed by the local paprnav session API.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Password changes are intentionally deferred until email verification and account recovery are defined.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
