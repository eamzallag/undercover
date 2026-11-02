import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "./App";
import { stubApi, summary } from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

it("opens on the queue", async () => {
  stubApi({ "/api/claims": [summary({})] });
  renderAt("/");
  expect(screen.getByRole("heading", { name: "Claims queue" })).toBeDefined();
  expect(await screen.findByText("Maya Patel")).toBeDefined();
  expect(screen.getByText("The claims desk")).toBeDefined();
});

it("says when a page doesn't exist", () => {
  stubApi({});
  renderAt("/nowhere");
  expect(screen.getByRole("heading", { name: "Page not found" })).toBeDefined();
});
