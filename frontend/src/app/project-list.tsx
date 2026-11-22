"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import Link from "next/link";

import { CreateProjectForm, type Project } from "./create-project-form";

type ProjectListState =
  | { status: "loading" }
  | { status: "ready"; projects: Project[] }
  | { status: "error"; message: string };

export function ProjectList() {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const [state, setState] = useState<ProjectListState>({ status: "loading" });

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;

    const controller = new AbortController();

    async function loadProjects() {
      try {
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
        if (!apiBaseUrl) {
          throw new Error("The FastAPI URL is missing from .env.local.");
        }

        const token = await getToken();
        if (!token) {
          throw new Error("Your session is unavailable. Sign in again.");
        }

        const headers = { Authorization: `Bearer ${token}` };

        const bootstrap = await fetch(`${apiBaseUrl}/auth/bootstrap`, {
          method: "POST",
          headers,
          signal: controller.signal,
        });

        if (!bootstrap.ok) {
          throw new Error(`Account setup failed with HTTP ${bootstrap.status}.`);
        }

        const response = await fetch(`${apiBaseUrl}/projects`, {
          headers,
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Loading projects failed with HTTP ${response.status}.`);
        }

        const projects: Project[] = await response.json();
        if (!controller.signal.aborted) {
          setState({ status: "ready", projects });
        }
      } catch (error) {
        if (controller.signal.aborted) return;

        setState({
          status: "error",
          message: error instanceof Error ? error.message : "Could not load projects.",
        });
      }
    }

    void loadProjects();
    return () => controller.abort();
  }, [getToken, isLoaded, isSignedIn]);

  function handleProjectCreated(project: Project) {
    setState((current) => {
      if (current.status !== "ready") return current;

      return {
        status: "ready",
        projects: [project, ...current.projects],
      };
    });
  }

  if (state.status === "loading") {
    return <p role="status">Loading projects…</p>;
  }

  if (state.status === "error") {
    return <p role="alert">{state.message}</p>;
  }

  return (
    <section>
      <h2>Your projects</h2>
      <CreateProjectForm onCreated={handleProjectCreated} />

      {state.projects.length === 0 ? (
        <p>No projects yet.</p>
      ) : (
        <ul>
          {state.projects.map((project) => (
            <li key={project.id}>
              <Link href={`/projects/${project.id}`} className="underline">
                {project.name}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
