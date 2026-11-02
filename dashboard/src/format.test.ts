import { expect, it } from "vitest";
import { date, dateTime, label, money, pretty } from "./format";

it("formats money in US dollars", () => {
  expect(money(1250)).toBe("$1,250.00");
  expect(money(0)).toBe("$0.00");
  expect(money(420.5)).toBe("$420.50");
});

it("formats dates without shifting the day", () => {
  expect(date("2026-06-24")).toBe("Jun 24, 2026");
  expect(dateTime("2026-11-02T12:07:49Z")).toContain("2026");
});

it("turns codes into labels", () => {
  expect(label("trip_delay")).toBe("Trip delay");
  expect(label("emergency_medical")).toBe("Emergency medical");
  expect(label("baggage")).toBe("Baggage");
});

it("lays out JSON details and leaves other text alone", () => {
  expect(pretty('{"a":1}')).toBe('{\n  "a": 1\n}');
  expect(pretty("Refused")).toBe("Refused");
});
