import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { InstructionsPage } from "./InstructionsPage";
import { stubApi } from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("shows the instructions, read only", async () => {
  stubApi({
    "/api/instructions": { text: "You are the UnderCover Agent.\n\n1. Read." },
  });
  render(<InstructionsPage />);

  expect(
    await screen.findByText(/You are the UnderCover Agent\./),
  ).toBeDefined();
  expect(screen.getByText("Read only")).toBeDefined();
  expect(screen.queryAllByRole("textbox")).toHaveLength(0);
  expect(screen.queryAllByRole("button")).toHaveLength(0);
});
