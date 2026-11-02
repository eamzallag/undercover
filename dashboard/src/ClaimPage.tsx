import { Link, useParams } from "react-router";
import { useApi, type Claim } from "./api";
import { StatusBadge } from "./Badge";
import { DecisionPanel } from "./DecisionPanel";
import { date, label, money } from "./format";
import { LoadState } from "./LoadState";
import { HistoryPanel, PolicyPanel } from "./PolicyPanel";
import { StepsPanel } from "./StepsPanel";

export function ClaimPage() {
  const { claimId = "" } = useParams();
  return <ClaimView key={claimId} claimId={claimId} />;
}

function ClaimView({ claimId }: Readonly<{ claimId: string }>) {
  const claim = useApi<Claim>(`/api/claims/${claimId}`);

  if (claim.state === "error" && claim.status === 404) {
    return (
      <main className="page">
        <h1>Claim not found</h1>
        <p>
          There is no claim {claimId}. <Link to="/">Back to the queue</Link>
        </p>
      </main>
    );
  }
  if (claim.state !== "ready") {
    return (
      <main className="page">
        <LoadState result={claim} />
      </main>
    );
  }

  const data = claim.data;
  return (
    <main className="page">
      <div className="title">
        <h1 className="mono">{data.claim_id}</h1>
        <StatusBadge status={data.status} />
      </div>
      <p className="lead">
        {data.summary}. {data.customer_name}, {label(data.claim_type)}.
      </p>
      <div className="columns">
        <div className="column">
          <ClaimDetails claim={data} />
          <PolicyPanel policyId={data.policy_id} />
          <HistoryPanel customerId={data.customer_id} />
        </div>
        <div className="column">
          <DecisionPanel claim={data} />
          <StepsPanel claimId={data.claim_id} claim={data} />
        </div>
      </div>
    </main>
  );
}

function ClaimDetails({ claim }: Readonly<{ claim: Claim }>) {
  return (
    <>
      <section className="panel stack" aria-label="The claim">
        <h2>The claim</h2>
        <dl className="facts">
          <dt>Customer</dt>
          <dd>{claim.customer_name}</dd>
          <dt>Incident</dt>
          <dd>
            {date(claim.incident_date)}, {claim.incident_location}
          </dd>
          <dt>Submitted</dt>
          <dd>{date(claim.submitted_on)}</dd>
          <dt>Claimed</dt>
          <dd className="mono">{money(claim.amount_claimed)}</dd>
        </dl>
        <p className="story">{claim.story}</p>
      </section>

      <section className="panel stack" aria-label="Items">
        <h2>Items</h2>
        <table>
          <thead>
            <tr>
              <th>Item</th>
              <th>Category</th>
              <th className="number">Amount</th>
            </tr>
          </thead>
          <tbody>
            {claim.items.map((item) => (
              <tr key={item.description}>
                <td>{item.description}</td>
                <td>{label(item.category)}</td>
                <td className="number mono">{money(item.amount)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <th colSpan={2}>Total</th>
              <td className="number mono">
                {money(claim.items.reduce((sum, item) => sum + item.amount, 0))}
              </td>
            </tr>
          </tfoot>
        </table>
      </section>

      <section className="panel stack" aria-label="Documents">
        <h2>Documents</h2>
        {claim.documents.map((document) => (
          <article className="document" key={document.name}>
            <h3>
              {document.name}{" "}
              <span className="muted">({label(document.type)})</span>
            </h3>
            <p>{document.content}</p>
          </article>
        ))}
      </section>
    </>
  );
}
