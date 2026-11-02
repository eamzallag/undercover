import { useApi, type Instructions } from "./api";
import { LoadState } from "./LoadState";

export function InstructionsPage() {
  const instructions = useApi<Instructions>("/api/instructions", false);

  return (
    <main className="page">
      <div className="title">
        <h1>Agent instructions</h1>
        <span className="badge read-only">Read only</span>
      </div>
      <p className="lead">
        What the UnderCover Agent is told before it works each claim.
      </p>
      {instructions.state === "ready" ? (
        <section className="panel instructions">
          {instructions.data.text}
        </section>
      ) : (
        <LoadState result={instructions} />
      )}
    </main>
  );
}
