import type { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest) {
  const body = await req.text();

  let backendResponse: Response;
  try {
    backendResponse = await fetch(`${BACKEND_URL}/agent`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: req.headers.get("accept") ?? "text/event-stream",
      },
      body,
    });
  } catch {
    return new Response("Could not reach the agent backend.", { status: 502 });
  }

  if (!backendResponse.ok || !backendResponse.body) {
    return new Response("The agent backend returned an error.", {
      status: 502,
    });
  }

  return new Response(backendResponse.body, {
    headers: {
      "Content-Type": backendResponse.headers.get("content-type") ?? "text/event-stream",
    },
  });
}
