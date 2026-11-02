import type { DecisionName, Status } from "./api";

const usd = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});
const day = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeZone: "UTC",
});
const moment = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
});

export const STATUS_LABELS: Record<Status, string> = {
  waiting: "Waiting",
  in_progress: "In progress",
  waiting_for_sign_off: "Waiting for sign-off",
  decided: "Decided",
};

export const DECISION_LABELS: Record<DecisionName, string> = {
  approve: "Approved",
  decline: "Declined",
  refer: "Referred",
};

export function money(amount: number): string {
  return usd.format(amount);
}

export function date(isoDate: string): string {
  return day.format(new Date(isoDate));
}

export function dateTime(isoDateTime: string): string {
  return moment.format(new Date(isoDateTime));
}

export function label(code: string): string {
  const words = code.replaceAll("_", " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}
