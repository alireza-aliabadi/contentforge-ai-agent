const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";
const API_PREFIX = "/api/v1";

export type Platform =
  | "linkedin"
  | "twitter"
  | "blog"
  | "medium"
  | "youtube_community"
  | "custom";

export type JobStatus =
  | "pending"
  | "processing"
  | "evaluating"
  | "improving"
  | "completed"
  | "failed";

export type ContentStatus = "draft" | "ready" | "scheduled" | "published" | "archived";

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface PlatformInfo {
  id: Platform;
  label: string;
  max_length: number | null;
  style_notes: string;
}

export interface Asset {
  id: string;
  filename: string;
  content_type: string;
  asset_type: "document" | "image";
  storage_key: string;
  extracted_text?: string | null;
  metadata_json?: Record<string, unknown> | null;
  created_at: string;
}

export interface ContentPackage {
  id: string;
  job_id: string;
  title: string;
  body: string;
  platform: Platform;
  status: ContentStatus;
  originality_score?: number | null;
  relevance_score?: number | null;
  expertise_score?: number | null;
  banner_storage_key?: string | null;
  metadata_json?: Record<string, unknown> | null;
  created_at: string;
}

export interface ContentJob {
  id: string;
  prompt: string;
  platform: Platform;
  status: JobStatus;
  asset_ids?: string[] | null;
  plan_json?: Record<string, unknown> | null;
  evaluation_json?: Record<string, unknown> | null;
  error_message?: string | null;
  regeneration_count: number;
  created_at: string;
  updated_at: string;
  packages: ContentPackage[];
}

export interface CreateJobInput {
  prompt: string;
  platform: Platform;
  asset_ids?: string[];
}

async function parseError(response: Response): Promise<Error> {
  let detail = response.statusText || "Request failed";
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") {
      detail = body.detail;
    } else if (Array.isArray(body.detail)) {
      detail = body.detail
        .map((item) =>
          typeof item === "object" && item && "msg" in item
            ? String((item as { msg: unknown }).msg)
            : JSON.stringify(item),
        )
        .join("; ");
    }
  } catch {
    // keep statusText
  }
  return new Error(detail);
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers = new Headers(init.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${API_PREFIX}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function register(
  email: string,
  password: string,
  fullName?: string,
): Promise<{ id: string; email: string }> {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({
      email,
      password,
      full_name: fullName || null,
    }),
  });
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function listPlatforms(): Promise<PlatformInfo[]> {
  return request("/platforms");
}

export function listJobs(token: string): Promise<ContentJob[]> {
  return request("/content/jobs", {}, token);
}

export function createJob(token: string, input: CreateJobInput): Promise<ContentJob> {
  return request(
    "/content/jobs",
    {
      method: "POST",
      body: JSON.stringify({
        prompt: input.prompt,
        platform: input.platform,
        asset_ids: input.asset_ids ?? [],
      }),
    },
    token,
  );
}

export function uploadDocument(token: string, file: File): Promise<Asset> {
  const body = new FormData();
  body.append("file", file);
  return request("/assets/documents", { method: "POST", body }, token);
}

export function uploadImage(token: string, file: File): Promise<Asset> {
  const body = new FormData();
  body.append("file", file);
  return request("/assets/images", { method: "POST", body }, token);
}
