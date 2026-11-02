import type { Claim } from "./api";
import { DecisionBadge } from "./Badge";
import { dateTime, money } from "./format";

export function DecisionPanel({ claim }: Readonly<{ claim: Claim }>) {
  const decision = claim.decision;

  return (
    <section className="panel stack" aria-label="Decision">
      <h2>Decision</h2>
      {decision === null ? (
        <p className="muted">
          {claim.status === "in_progress"
            ? "The agent is working on this claim."
            : "The agent hasn't worked this claim yet."}
        </p>
      ) : (
        <>
          <div className="decision">
            <DecisionBadge decision={decision.decision} />
            {decision.decision === "approve" && (
              <span className="payout mono">{money(decision.payout)}</span>
            )}
          </div>
          <p>{decision.reasons}</p>
          <dl className="facts">
            <dt>Policy section</dt>
            <dd>{decision.policy_section}</dd>
            <dt>Decided</dt>
            <dd>{dateTime(decision.decided_at)}</dd>
          </dl>
          {decision.decision === "approve" && <PaymentLine claim={claim} />}
        </>
      )}
    </section>
  );
}

function PaymentLine({ claim }: Readonly<{ claim: Claim }>) {
  const payment = claim.payment;
  if (payment) {
    const signedOff = payment.signed_off_by
      ? `, signed off by ${payment.signed_off_by}`
      : "";
    return (
      <p className="notice">
        Paid {money(payment.amount)} on {dateTime(payment.paid_at)}
        {signedOff}.
      </p>
    );
  }
  if (claim.status === "waiting_for_sign_off" && claim.decision) {
    return (
      <p className="notice alert">
        Payment of {money(claim.decision.payout)} waits for a handler&apos;s
        sign-off.
      </p>
    );
  }
  return <p className="notice">Not paid yet.</p>;
}
