import { useApi, type Claim, type Step } from "./api";
import { dateTime, pretty } from "./format";
import { LoadState } from "./LoadState";

export function StepsPanel({
  claimId,
  claim,
}: Readonly<{ claimId: string; claim: Claim }>) {
  const steps = useApi<Step[]>(`/api/claims/${claimId}/steps`);

  return (
    <section className="panel stack" aria-label="The agent's steps">
      <h2>The agent&apos;s steps</h2>
      {claim.thread_id && (
        <p className="muted">
          Run <span className="mono">{claim.thread_id}</span>
        </p>
      )}
      {steps.state === "ready" ? (
        <StepList steps={steps.data} working={claim.status === "in_progress"} />
      ) : (
        <LoadState result={steps} />
      )}
    </section>
  );
}

function StepList({
  steps,
  working,
}: Readonly<{ steps: Step[]; working: boolean }>) {
  if (steps.length === 0) {
    return <p className="muted">{working ? "Starting..." : "No steps yet."}</p>;
  }
  return (
    <ol className="steps">
      {steps.map((step) => (
        <li key={step.step_id} className={`step ${step.kind}`}>
          <div className="step-head">
            <span className="step-title">{step.title}</span>
            <span className="muted step-time">{dateTime(step.created_at)}</span>
          </div>
          {step.kind === "message" ? (
            <p>{step.detail}</p>
          ) : (
            <details>
              <summary>Details</summary>
              <pre>{pretty(step.detail)}</pre>
            </details>
          )}
        </li>
      ))}
    </ol>
  );
}
