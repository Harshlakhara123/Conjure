"use client";

import { useAuth } from "@clerk/nextjs";
import { useState, type SubmitEvent } from "react";

type EntryType = "file" | "folder";

type CreateEntryFormProps = {
  projectId: string;
  parentId: string | undefined;
  onCreated: () => void;
};

export function CreateEntryForm({
  projectId,
  parentId,
  onCreated,
}: CreateEntryFormProps) {
  const { getToken } = useAuth();
  const [name, setName] = useState("");
  const [entryType, setEntryType] = useState<EntryType>("file");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();

    const entryName = name.trim();
    if (!entryName || isSubmitting) return;

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

      const response = await fetch(`${apiBaseUrl}/projects/${projectId}/files`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: entryName,
          type: entryType,
          parent_id: parentId ?? null,
        }),
      });

      if (response.status === 409) {
        throw new Error("A file or folder with that name already exists here.");
      }

      if (!response.ok) {
        throw new Error(`Creating the entry failed with HTTP ${response.status}.`);
      }

      setName("");
      onCreated();
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not create entry.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <label htmlFor="entry-type" className="block">Type</label>
      <select
        id="entry-type"
        className="rounded border px-3 py-2"
        value={entryType}
        onChange={(event) =>
          setEntryType(event.target.value === "folder" ? "folder" : "file")
        }
      >
        <option value="file">File</option>
        <option value="folder">Folder</option>
      </select>

      <label htmlFor="entry-name" className="block">Name</label>
      <input
        id="entry-name"
        className="block rounded border px-3 py-2"
        value={name}
        onChange={(event) => setName(event.target.value)}
        required
      />

      <button
        type="submit"
        className="rounded border px-3 py-2 disabled:opacity-50"
        disabled={isSubmitting || !name.trim()}
      >
        {isSubmitting ? "Creating…" : `Create ${entryType}`}
      </button>

      {error && <p role="alert">{error}</p>}
    </form>
  );
}