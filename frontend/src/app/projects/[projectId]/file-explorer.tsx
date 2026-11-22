"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";

import { CreateEntryForm } from "./create-entry-form";
import { RenameEntryForm } from "./rename-entry-form";

type FileEntry = {
  id: string;
  name: string;
  type: "file" | "folder";
};

type FileExplorerProps = {
  projectId: string;
  onOpenFile: (fileId: string) => void;
  selectedFileId: string | null;
};

export function FileExplorer({
  projectId,
  onOpenFile,
  selectedFileId,
}: FileExplorerProps) {
  const { getToken } = useAuth();
  const [folders, setFolders] = useState<FileEntry[]>([]);
  const [entries, setEntries] = useState<FileEntry[] | null>(null);
  const [error, setError] = useState("");
  const [reloadCount, setReloadCount] = useState(0);
  const [renamingEntryId, setRenamingEntryId] = useState<string | null>(null);
  const [deletingEntryId, setDeletingEntryId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState("");

  const parentId = folders[folders.length - 1]?.id;
  const isDeleting = deletingEntryId !== null;

  function reloadEntries() {
    setEntries(null);
    setError("");
    setReloadCount((count) => count + 1);
  }

  function navigate(nextFolders: FileEntry[]) {
    setEntries(null);
    setError("");
    setDeleteError("");
    setRenamingEntryId(null);
    setFolders(nextFolders);
  }

  function canDelete(entry: FileEntry) {
    if (isDeleting) return false;

    return entry.type === "folder"
      ? selectedFileId === null
      : entry.id !== selectedFileId;
  }

  async function deleteEntry(entry: FileEntry) {
    if (!canDelete(entry)) return;

    const message =
      entry.type === "folder"
        ? `Permanently delete "${entry.name}" and every file and folder inside it?`
        : `Permanently delete "${entry.name}"?`;

    if (!window.confirm(message)) return;

    setDeleteError("");
    setDeletingEntryId(entry.id);

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
        `${apiBaseUrl}/projects/${projectId}/files/${entry.id}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      if (!response.ok) {
        throw new Error(`Deleting failed with HTTP ${response.status}.`);
      }

      reloadEntries();
    } catch (error) {
      setDeleteError(
        error instanceof Error ? error.message : "Could not delete the entry.",
      );
    } finally {
      setDeletingEntryId(null);
    }
  }

  useEffect(() => {
    const controller = new AbortController();

    async function loadEntries() {
      try {
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
        if (!apiBaseUrl) {
          throw new Error("The FastAPI URL is missing from .env.local.");
        }

        const token = await getToken();
        if (!token) {
          throw new Error("Your session is unavailable. Sign in again.");
        }

        const url = new URL(`${apiBaseUrl}/projects/${projectId}/files`);
        if (parentId) {
          url.searchParams.set("parent_id", parentId);
        }

        const response = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Loading files failed with HTTP ${response.status}.`);
        }

        const data: FileEntry[] = await response.json();
        if (!controller.signal.aborted) setEntries(data);
      } catch (error) {
        if (controller.signal.aborted) return;
        setError(
          error instanceof Error ? error.message : "Could not load files.",
        );
      }
    }

    void loadEntries();
    return () => controller.abort();
  }, [getToken, projectId, parentId, reloadCount]);

  return (
    <section>
      <h2>Files</h2>
      <p>{["Root", ...folders.map((folder) => folder.name)].join(" / ")}</p>

      {folders.length > 0 && (
        <button
          type="button"
          className="underline disabled:opacity-50"
          disabled={isDeleting}
          onClick={() => navigate(folders.slice(0, -1))}
        >
          Up one level
        </button>
      )}

      <CreateEntryForm
        key={parentId ?? "root"}
        projectId={projectId}
        parentId={parentId}
        onCreated={reloadEntries}
      />

      {selectedFileId !== null && entries?.some((entry) => entry.type === "folder") && (
        <p>Close the editor to delete a folder.</p>
      )}

      {deleteError && <p role="alert">{deleteError}</p>}

      {error ? (
        <p role="alert">{error}</p>
      ) : entries === null ? (
        <p role="status">Loading files…</p>
      ) : entries.length === 0 ? (
        <p>This folder is empty.</p>
      ) : (
        <ul>
          {entries.map((entry) => (
            <li key={entry.id} className="flex flex-wrap items-center gap-2">
              {renamingEntryId === entry.id ? (
                <RenameEntryForm
                  projectId={projectId}
                  entryId={entry.id}
                  currentName={entry.name}
                  onCancel={() => setRenamingEntryId(null)}
                  onRenamed={() => {
                    setRenamingEntryId((id) => (id === entry.id ? null : id));
                    reloadEntries();
                  }}
                />
              ) : (
                <>
                  <button
                    type="button"
                    className="underline disabled:opacity-50"
                    disabled={isDeleting}
                    onClick={() => {
                      if (entry.type === "folder") {
                        navigate([...folders, entry]);
                      } else {
                        onOpenFile(entry.id);
                      }
                    }}
                  >
                    {entry.name}{entry.type === "folder" ? "/" : ""}
                  </button>

                  <button
                    type="button"
                    aria-label={`Rename ${entry.name}`}
                    disabled={entry.id === selectedFileId || isDeleting}
                    className="rounded border px-2 py-1 disabled:opacity-50"
                    onClick={() => setRenamingEntryId(entry.id)}
                  >
                    Rename
                  </button>

                  <button
                    type="button"
                    aria-label={`Delete ${entry.name}`}
                    disabled={!canDelete(entry)}
                    className="rounded border px-2 py-1 disabled:opacity-50"
                    onClick={() => void deleteEntry(entry)}
                  >
                    {deletingEntryId === entry.id ? "Deleting…" : "Delete"}
                  </button>
                </>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}