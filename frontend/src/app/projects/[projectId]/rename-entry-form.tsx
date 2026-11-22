"use client";

import { useAuth } from "@clerk/nextjs";
import { useState, type FormEvent } from "react";

type RenameEntryFormProps = {
  projectId: string;
  entryId: string;
  currentName: string;
  onRenamed: () => void;
  onCancel: () => void;
};

export function RenameEntryForm({
  projectId,
  entryId,
  currentName,
  onRenamed,
  onCancel,
}: RenameEntryFormProps) {
  const { getToken } = useAuth();
  const [name, setName] = useState(currentName);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
  event.preventDefault();

  const newName = name.trim();
  if (!newName || newName === currentName || isSubmitting) return;

  setError("");
  setIsSubmitting(true);

  try {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    if (!apiBaseUrl) {
      throw new Error("The FastAPI URL is missing from .env.local.");
    }

    const token = await getToken();
    if (!token) {
      throw new Error("Your session is unavailable. Sign in again.");
    }

    const response = await fetch(
      `${apiBaseUrl}/projects/${projectId}/files/${entryId}/name`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name: newName }),
      },
    );

    if (response.status === 409) {
      throw new Error("An entry with that name already exists in this folder.");
    }

    if (!response.ok) {
      throw new Error(`Renaming failed with HTTP ${response.status}.`);
    }

    onRenamed();
  } catch (error) {
    setError(error instanceof Error ? error.message : "Could not rename entry.");
  } finally {
    setIsSubmitting(false);
  }
}
return (
  <form onSubmit={handleSubmit} className="flex flex-wrap items-center gap-2">
    <input
      aria-label={`New name for ${currentName}`}
      className="rounded border px-2 py-1"
      value={name}
      onChange={(event) => setName(event.target.value)}
      disabled={isSubmitting}
      required
    />

    <button
      type="submit"
      disabled={isSubmitting || !name.trim() || name.trim() === currentName}
    >
      {isSubmitting ? "Renaming…" : "Save name"}
    </button>

    <button type="button" onClick={onCancel} disabled={isSubmitting}>
      Cancel
    </button>

    {error && <p role="alert">{error}</p>}
  </form>
);
}