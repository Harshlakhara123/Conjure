"use client";

import { useAuth } from "@clerk/nextjs";
import { useState, type SubmitEvent } from "react";

export type Project = {
  id: string;
  name: string;
};

type CreateProjectFormProps = {
  onCreated: (project: Project) => void;
};

export function CreateProjectForm({ onCreated }: CreateProjectFormProps) {
  const { getToken } = useAuth();
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();

    const projectName = name.trim();
    if (!projectName || isSubmitting) return;

    setError("");
    setIsSubmitting(true);

    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
      if (!apiBaseUrl) {
        throw new Error("The FastAPI URL is missing from .env.local.");
      }

      const token = await getToken();
      if (!token) {
        throw new Error("Sign in before creating a project.");
      }

      const response = await fetch(`${apiBaseUrl}/projects`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name: projectName }),
      });

      if (!response.ok) {
        throw new Error(`Creating the project failed with HTTP ${response.status}.`);
      }

      const project: Project = await response.json();
      onCreated(project);
      setName("");
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not create project.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-2" onSubmit={handleSubmit}>
      <label htmlFor="project-name">Project name</label>
      <input
        className="block rounded border px-3 py-2"
        id="project-name"
        value={name}
        onChange={(event) => setName(event.target.value)}
        required
      />
      <button
        className="rounded border px-3 py-2 disabled:opacity-50"
        type="submit"
        disabled={isSubmitting || !name.trim()}
      >
        {isSubmitting ? "Creating…" : "Create project"}
      </button>
      {error && <p role="alert">{error}</p>}
    </form>
  );
}
