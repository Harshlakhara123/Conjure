"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import dynamic from "next/dynamic";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
});
type FileDetails = {
  id: string;
  name: string;
  content: string | null;
  revision: number;
};

type FileViewerProps = {
  projectId: string;
  fileId: string;
  onDirtyChange: (isDirty: boolean) => void;
};
function getEditorLanguage(fileName: string): string {
  switch (fileName.toLowerCase().split(".").pop()) {
    case "py":
      return "python";
    case "js":
    case "jsx":
      return "javascript";
    case "ts":
    case "tsx":
      return "typescript";
    case "json":
      return "json";
    default:
      return "plaintext";
  }
}
export function FileViewer({ projectId, fileId, onDirtyChange }: FileViewerProps) {
  const { getToken } = useAuth();
  const [file, setFile] = useState<FileDetails | null>(null);
  const [error, setError] = useState("");
  const [draft, setDraft] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveMessage, setSaveMessage] = useState("");

  const isDirty = file !== null && draft !== (file.content ?? "");

  useEffect(() => {
    const controller = new AbortController();

    async function loadFile() {
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
          `${apiBaseUrl}/projects/${projectId}/files/${fileId}`,
          {
            headers: { Authorization: `Bearer ${token}` },
            signal: controller.signal,
          },
        );

        if (!response.ok) {
          throw new Error(`Opening the file failed with HTTP ${response.status}.`);
        }

        const data: FileDetails = await response.json();
        if (!controller.signal.aborted) {
          setFile(data);
          setDraft(data.content ?? "");
        }
      } catch (error) {
        if (controller.signal.aborted) return;
        setError(error instanceof Error ? error.message : "Could not open file.");
      }
    }

    void loadFile();
    return () => controller.abort();
  }, [getToken, projectId, fileId]);

  useEffect(() => {
    onDirtyChange(isDirty);
  }, [isDirty, onDirtyChange]);

  if (error) return <p role="alert">{error}</p>;
  if (file === null) return <p role="status">Opening file…</p>;

  async function saveFile() {
  if (!file || !isDirty || isSaving) return;

  setIsSaving(true);
  setSaveError("");
  setSaveMessage("");

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
      `${apiBaseUrl}/projects/${projectId}/files/${fileId}/content`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          content: draft,
          expected_revision: file.revision,
        }),
      },
    );

    if (!response.ok) {
      const body = await response.json().catch(() => null);
      const detail =
        typeof body?.detail === "string"
          ? body.detail
          : `Saving failed with HTTP ${response.status}.`;
      throw new Error(`${detail} Your draft is still here.`);
    }

    const savedFile: FileDetails = await response.json();
    setFile(savedFile);
    setSaveMessage("Saved.");
  } catch (error) {
    setSaveError(error instanceof Error ? error.message : "Could not save file.");
  } finally {
    setIsSaving(false);
  }
}

  return (
  <section className="space-y-2">
    <h2 className="font-semibold">{file.name}</h2>

    <div className="overflow-hidden rounded border">
      <MonacoEditor
        height="360px"
        language={getEditorLanguage(file.name)}
        value={draft}
        loading={<p role="status">Loading editor…</p>}
        options={{
          ariaLabel: `Editing ${file.name}`,
          minimap: { enabled: false },
        }}
        onChange={(value) => {
          setDraft(value ?? "");
          setSaveMessage("");
        }}
      />
    </div>

    <button
      type="button"
      className="rounded border px-3 py-2 disabled:opacity-50"
      onClick={saveFile}
      disabled={isSaving || !isDirty}
    >
      {isSaving ? "Saving…" : "Save"}
    </button>

    {saveError && <p role="alert">{saveError}</p>}
    {!saveError && !isDirty && saveMessage && (
      <p role="status">{saveMessage}</p>
    )}
  </section>
);
}
