import { useEffect, useState } from "react";

export type Status =
  "waiting" | "in_progress" | "waiting_for_sign_off" | "decided";
export type DecisionName = "approve" | "decline" | "refer";

export interface ClaimSummary {
  claim_id: string;
  customer_name: string;
  claim_type: string;
  summary: string;
  submitted_on: string;
  amount_claimed: number;
  status: Status;
  decision: DecisionName | null;
  payout: number | null;
}

export interface Item {
  description: string;
  category: string;
  amount: number;
}

export interface ClaimDocument {
  name: string;
  type: string;
  content: string;
}

export interface Decision {
  decision: DecisionName;
  payout: number;
  reasons: string;
  policy_section: string;
  decided_at: string;
}

export interface Payment {
  amount: number;
  paid_at: string;
  signed_off_by: string | null;
}

export interface Claim {
  claim_id: string;
  policy_id: string;
  customer_id: string;
  customer_name: string;
  claim_type: string;
  submitted_on: string;
  incident_date: string;
  incident_location: string;
  summary: string;
  story: string;
  items: Item[];
  amount_claimed: number;
  documents: ClaimDocument[];
  status: Status;
  thread_id: string | null;
  decision: Decision | null;
  payment: Payment | null;
}

export interface Plan {
  plan: string;
  name: string;
  deductible: number;
}

export interface AddOn {
  add_on: string;
  name: string;
  effect: string;
}

export interface Policy {
  policy_id: string;
  plan: string;
  add_ons: string[];
  purchased_on: string;
  trip: {
    destination: string;
    departs_on: string;
    returns_on: string;
    trip_cost: number;
  };
  travelers: string[];
  plan_details: Plan;
  add_on_details: AddOn[];
}

export interface PreviousClaim {
  claim_id: string;
  filed_on: string;
  claim_type: string;
  summary: string;
  outcome: string;
  amount_paid: number;
}

export interface ClaimHistory {
  customer_id: string;
  name: string;
  customer_since: string;
  previous_claims: PreviousClaim[];
}

export interface Step {
  step_id: number;
  kind: "tool" | "message";
  title: string;
  detail: string;
  created_at: string;
}

export interface Instructions {
  text: string;
}

export type Result<T> =
  | { state: "loading" }
  | { state: "ready"; data: T }
  | { state: "error"; status: number };

export const REFRESH_MS = 2000;

export function useApi<T>(path: string, refresh = true): Result<T> {
  const [result, setResult] = useState<Result<T>>({ state: "loading" });

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const response = await fetch(path);
        const next: Result<T> = response.ok
          ? { state: "ready", data: (await response.json()) as T }
          : { state: "error", status: response.status };
        if (active) setResult(next);
      } catch {
        if (active) setResult({ state: "error", status: 0 });
      }
    };
    void load();
    const timer = refresh ? setInterval(() => void load(), REFRESH_MS) : 0;
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [path, refresh]);

  return result;
}
