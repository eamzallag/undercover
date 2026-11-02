import { useApi, type ClaimHistory, type Policy } from "./api";
import { date, label, money } from "./format";
import { LoadState } from "./LoadState";

export function PolicyPanel({ policyId }: Readonly<{ policyId: string }>) {
  const policy = useApi<Policy>(`/api/policies/${policyId}`, false);

  return (
    <section className="panel stack" aria-label="Policy">
      <h2>Policy</h2>
      {policy.state === "ready" ? (
        <dl className="facts">
          <dt>Policy</dt>
          <dd className="mono">{policy.data.policy_id}</dd>
          <dt>Plan</dt>
          <dd>{policy.data.plan_details.name}</dd>
          <dt>Add-ons</dt>
          <dd>
            {policy.data.add_on_details.map((a) => a.name).join(", ") || "None"}
          </dd>
          <dt>Trip</dt>
          <dd>
            {policy.data.trip.destination}, {date(policy.data.trip.departs_on)}{" "}
            to {date(policy.data.trip.returns_on)}
          </dd>
          <dt>Trip cost</dt>
          <dd className="mono">{money(policy.data.trip.trip_cost)}</dd>
          <dt>Travelers</dt>
          <dd>{policy.data.travelers.join(", ")}</dd>
          <dt>Bought</dt>
          <dd>{date(policy.data.purchased_on)}</dd>
        </dl>
      ) : (
        <LoadState result={policy} />
      )}
    </section>
  );
}

export function HistoryPanel({ customerId }: Readonly<{ customerId: string }>) {
  const history = useApi<ClaimHistory>(
    `/api/customers/${customerId}/history`,
    false,
  );

  return (
    <section className="panel stack" aria-label="Claim history">
      <h2>Claim history</h2>
      {history.state === "ready" ? (
        <>
          <p className="muted">
            Customer since {date(history.data.customer_since)}
          </p>
          {history.data.previous_claims.length === 0 ? (
            <p>No earlier claims.</p>
          ) : (
            <ul className="history">
              {history.data.previous_claims.map((previous) => (
                <li key={previous.claim_id}>
                  <span className="mono">{previous.claim_id}</span>,{" "}
                  {date(previous.filed_on)}, {label(previous.claim_type)}:{" "}
                  {previous.summary}. {label(previous.outcome)},{" "}
                  <span className="mono">{money(previous.amount_paid)}</span>{" "}
                  paid.
                </li>
              ))}
            </ul>
          )}
        </>
      ) : (
        <LoadState result={history} />
      )}
    </section>
  );
}
