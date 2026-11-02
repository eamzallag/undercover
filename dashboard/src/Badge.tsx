import type { DecisionName, Status } from "./api";
import { DECISION_LABELS, STATUS_LABELS } from "./format";

export function StatusBadge({ status }: Readonly<{ status: Status }>) {
  return <span className={`badge ${status}`}>{STATUS_LABELS[status]}</span>;
}

export function DecisionBadge({
  decision,
}: Readonly<{ decision: DecisionName }>) {
  return (
    <span className={`badge ${decision}`}>{DECISION_LABELS[decision]}</span>
  );
}
