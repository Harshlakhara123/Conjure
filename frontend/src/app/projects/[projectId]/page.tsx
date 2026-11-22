"use client";

import { SignInButton, useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import type { Project } from "../../create-project-form";
import { FileExplorer } from "./file-explorer";
import { FileViewer } from "./file-viewer";

export default function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const [project, setProject] = useState<Project | null>(null);
  const [error, setError] = useState("");
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;

    const controller = new AbortController();

    async function loadProject() {
      try {
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
        if (!apiBaseUrl) {
          throw new Error("The FastAPI URL is missing from .env.local.");
        }

        const token = await getToken();
        if (!token) {
          throw new Error("Your session is unavailable. Sign in again.");
        }

        const response = await fetch(`${apiBaseUrl}/projects/${projectId}`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        });

        if (response.status === 404) {
          throw new Error("Project not found.");
        }

        if (!response.ok) {
          throw new Error(`Loading the project failed with HTTP ${response.status}.`);
        }

        const data: Project = await response.json();
        if (!controller.signal.aborted) setProject(data);
      } catch (error) {
        if (controller.signal.aborted) return;
        setError(error instanceof Error ? error.message : "Could not load project.");
      }
    }

    void loadProject();
    return () => controller.abort();
  }, [getToken, isLoaded, isSignedIn, projectId]);

  function selectFile(nextFileId: string | null) {
    if (nextFileId === selectedFileId) return;

    if (hasUnsavedChanges && !window.confirm("Discard unsaved changes?")) {
      return;
    }

    setHasUnsavedChanges(false);
    setSelectedFileId(nextFileId);
  }

  return (
    <main>
      <Link href="/" className="underline">
        Back to projects
      </Link>

      {!isLoaded ? (
        <p role="status">Checking session…</p>
      ) : !isSignedIn ? (
        <SignInButton mode="modal" />
      ) : error ? (
        <p role="alert">{error}</p>
      ) : project ? (
        <>
          <h1>{project.name}</h1>
          <FileExplorer
            key={project.id}
            projectId={project.id}
            selectedFileId={selectedFileId}
            onOpenFile={selectFile}
          />

          {selectedFileId && (
            <>
                <button type="button" onClick={() => selectFile(null)}>
                Close editor
                </button>
                <FileViewer
                key={selectedFileId}
                projectId={project.id}
                fileId={selectedFileId}
                onDirtyChange={setHasUnsavedChanges}
                />
            </>
          )}
        </>
      ) : (
        <p role="status">Loading project…</p>
      )}
    </main>
  );
}
