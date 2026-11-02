import { Link } from "react-router";
import { useApi, type ClaimSummary, type Status } from "./api";
import { DecisionBadge, StatusBadge } from "./Badge";
import { STATUS_LABELS, label, money } from "./format";
import { LoadState } from "./LoadState";

const STATUSES: Status[] = [
  "waiting",
  "in_progress",
  "waiting_for_sign_off",
  "decided",
];

export function QueuePage() {
  const claims = useApi<ClaimSummary[]>("/api/claims");

  return (
    <main className="page">
      <h1>Claims queue</h1>
      {claims.state === "ready" ? (
        <>
          <StatusTiles claims={claims.data} />
          <QueueTable claims={claims.data} />
        </>
      ) : (
        <LoadState result={claims} />
      )}
    </main>
  );
}

function StatusTiles({ claims }: Readonly<{ claims: ClaimSummary[] }>) {
  return (
    <section className="tiles" aria-label="Claims by status">
      {STATUSES.map((status) => (
        <div className="panel tile" key={status}>
          <StatusBadge status={status} />
          <span
            className="tile-count"
            aria-label={`${STATUS_LABELS[status]} count`}
          >
            {claims.filter((claim) => claim.status === status).length}
          </span>
        </div>
      ))}
    </section>
  );
}

function QueueTable({ claims }: Readonly<{ claims: ClaimSummary[] }>) {
  return (
    <section className="panel table-wrap">
      <table>
        <thead>
          <tr>
            <th>Claim</th>
            <th>Customer</th>
            <th>Type</th>
            <th>Summary</th>
            <th className="number">Claimed</th>
            <th>Status</th>
            <th>Decision</th>
            <th className="number">Payout</th>
          </tr>
        </thead>
        <tbody>
          {claims.map((claim) => (
            <tr key={claim.claim_id}>
              <td className="nowrap">
                <Link className="mono" to={`/claims/${claim.claim_id}`}>
                  {claim.claim_id}
                </Link>
              </td>
              <td>{claim.customer_name}</td>
              <td>{label(claim.claim_type)}</td>
              <td>{claim.summary}</td>
              <td className="number mono">{money(claim.amount_claimed)}</td>
              <td>
                <StatusBadge status={claim.status} />
              </td>
              <td>
                {claim.decision && <DecisionBadge decision={claim.decision} />}
              </td>
              <td className="number mono">
                {claim.payout === null ? "" : money(claim.payout)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
