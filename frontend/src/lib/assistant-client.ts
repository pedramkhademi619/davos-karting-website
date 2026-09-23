/** Browser client for the assistant API (`/api/v1/assistant`). The AI provider key never reaches the browser: only the API knows it. */

export const MAX_QUESTION_CHARS = 500; // the backend rejects longer questions
const ENDPOINT = "/api/v1/assistant";

export type AssistantSource = { title: string; url: string };

export type AssistantAnswer = {
  answer: string;
  outcome: string;
  sources: AssistantSource[];
  suggestTicket: boolean;
  interactionId: string | null;
};

export class AssistantError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

const GENERIC_ERROR = "دستیار الان در دسترس نیست. کمی بعد دوباره امتحان کنید یا از صفحه «تماس با ما» استفاده کنید.";

/** Source links come from data, so only in-site paths are ever rendered as links. */
function isInternalPath(url: unknown): url is string {
  return typeof url === "string" && url.startsWith("/") && !url.startsWith("//");
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (body && typeof body === "object" && "message" in body && typeof body.message === "string" && response.status < 500) {
      return body.message; // the API's own Persian message, e.g. rate limiting
    }
  } catch {
    // not JSON: fall through to the generic message
  }
  return GENERIC_ERROR;
}

function parseAnswer(data: unknown): AssistantAnswer {
  if (!data || typeof data !== "object" || !("answer" in data) || typeof data.answer !== "string") {
    throw new AssistantError(GENERIC_ERROR, 502);
  }
  const record = data as Record<string, unknown>;
  const rawSources = Array.isArray(record.sources) ? record.sources : [];
  const sources = rawSources
    .filter((item): item is AssistantSource => !!item && typeof item.title === "string" && isInternalPath(item.url))
    .map(({ title, url }) => ({ title, url }));
  return {
    answer: data.answer,
    outcome: typeof record.outcome === "string" ? record.outcome : "",
    sources,
    suggestTicket: record.suggest_ticket === true,
    interactionId: typeof record.interaction_id === "string" ? record.interaction_id : null,
  };
}

export async function askAssistant(question: string, conversationId: string, signal: AbortSignal): Promise<AssistantAnswer> {
  let response: Response;
  try {
    response = await fetch(`${ENDPOINT}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // Nothing is stored server-side beyond counters unless the visitor opts in, and this widget offers no opt-in.
      body: JSON.stringify({ question, conversation_id: conversationId, consent_to_store: false }),
      signal,
    });
  } catch {
    throw new AssistantError(GENERIC_ERROR, 0);
  }
  if (!response.ok) throw new AssistantError(await errorMessage(response), response.status);
  try {
    return parseAnswer(await response.json());
  } catch (error) {
    throw error instanceof AssistantError ? error : new AssistantError(GENERIC_ERROR, 502);
  }
}

/** Best effort: a failed rating is not worth interrupting the visitor for. */
export async function sendFeedback(interactionId: string, helpful: boolean): Promise<void> {
  try {
    await fetch(`${ENDPOINT}/answers/${encodeURIComponent(interactionId)}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ helpful }),
    });
  } catch {
    // ignored on purpose
  }
}

/** UUID v4. `crypto.randomUUID` needs HTTPS or localhost; `getRandomValues` also works when testing over a plain LAN address. */
export function newId(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0"));
  return `${hex.slice(0, 4).join("")}-${hex.slice(4, 6).join("")}-${hex.slice(6, 8).join("")}-${hex.slice(8, 10).join("")}-${hex.slice(10).join("")}`;
}
