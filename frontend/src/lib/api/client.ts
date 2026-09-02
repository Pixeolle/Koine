import type { ApiClient } from "$lib/api/interface.ts";

const API_BASE = import.meta.env.SSR
    ? import.meta.env.INTERNAL_API_URL ?? "http://localhost:8000"
    : import.meta.env.PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
    constructor(
        public status: number,
        public detail: string,
        public existingDocumentationId?: string
    ) {
        super(detail);
    }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}/api${path}`, {
        ...init,
        headers: { "Content-Type": "application/json", ...init?.headers },
    });

    if (!response.ok) {
        const body = await response.json().catch(() => ({ detail: response.statusText }));
        const detail = typeof body.detail === "string" ? body.detail : body.detail?.detail ?? "Erreur inconnue";
        const existingId = typeof body.detail === "object" ? body.detail?.existing_documentation_id : undefined;
        throw new ApiError(response.status, detail, existingId);
    }
    return response.status === 204 ? (undefined as T) : response.json();
}

export const api: ApiClient = {
    generate: (payload) => request("/generate", { method: "POST", body: JSON.stringify(payload) }),
    listDocumentations: () => request("/documentations"),
    deleteDocumentation: (documentationId) => request(`/documentations/${documentationId}`, { method: "DELETE", }),
    listDocuments: (documentationId) => request(`/documentations/${documentationId}/documents`),
    getDocument: (documentationId, documentName) => request(`/documentations/${documentationId}/document/${documentName}`),
    listPlatforms: () => request("/metadata/supported_platforms"),
    listLanguages: () => request("/metadata/output_languages"),
    subscribeToProgress(documentationId, onEvent) {
        const es = new EventSource(`${API_BASE}/api/generate/${documentationId}/progress`)
        es.onmessage = (e) => onEvent(JSON.parse(e.data));
        return () => es.close();
    }
}