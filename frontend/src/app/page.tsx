import { Show, SignInButton, UserButton } from "@clerk/nextjs";
import { Suspense } from "react";

import { ProjectList } from "./project-list";

export default function Home() {
  return (
    <main>
      <h1>Conjure</h1>

      <Suspense fallback={null}>
        <Show when="signed-out">
          <SignInButton mode="modal" />
        </Show>

        <Show when="signed-in">
          <UserButton />
          <ProjectList />
        </Show>
      </Suspense>
    </main>
  );
}