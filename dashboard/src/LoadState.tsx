import type { Result } from "./api";

export function LoadState({ result }: Readonly<{ result: Result<unknown> }>) {
  return (
    <p className="notice">
      {result.state === "loading"
        ? "Loading..."
        : "The backend isn't responding. Check that it's running."}
    </p>
  );
}
