import {renderMarkdown} from "$lib/markdown.ts";

interface ChatMessage {
    role: "user" | "assistant";
    content: string;
}

class ChatStore {
    messages = $state<ChatMessage[]>([]);
    renderedMessages = $state<Record<number, string>>({});
    connected = $state(false);
    streaming = $state(false);
    private ws: WebSocket | null = null;
    private documentationId: string | null = null;

    connect(documentationId: string, documents: Set<string>) {
        if (this.ws) return;
        this.documentationId = documentationId;
        const savedMessages = sessionStorage.getItem(`chat-${documentationId}-messages`);
        const savedRenderedMessages = sessionStorage.getItem(`chat-${this.documentationId}-renderedMessages`);
        if (savedMessages) this.messages = JSON.parse(savedMessages);
        if (savedRenderedMessages) this.renderedMessages = JSON.parse(savedRenderedMessages);

        const wsUrl = `${import.meta.env.PUBLIC_WS_URL ?? "ws://localhost:8000"}/api/documentations/${documentationId}/chat`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => { this.connected = true; }

        this.ws.onmessage = (e) => {
            const data = JSON.parse(e.data);
            if (data.type === "chunk") {
                const last = this.messages[this.messages.length - 1];
                if (last?.role === "assistant") last.content += data.content;
                this.persist();
            } else if (data.type === "done") {
                const index: number = this.messages.length - 1;
                renderMarkdown(this.messages[index].content, documentationId, documents)
                    .then((data) => {
                        this.renderedMessages[index] = data;
                        this.persist();
                    });
                this.streaming = false;
            }
        };

        this.ws.onclose = () => { this.connected = false; this.ws = null; };
        this.ws.onerror = () => { this.connected = false; };
    }

    send(content: string, output_language: string) {
        if (!this.ws || this.streaming) return;
        this.messages.push({ role: "user", content });
        this.messages.push({ role: "assistant", content: ""});
        this.streaming = true;
        this.ws.send(JSON.stringify({ message: content, output_language: output_language}));
    }

    disconnect() {
        this.ws?.close();
        this.ws = null;
    }

    private persist() {
        if (this.documentationId) {
            sessionStorage.setItem(`chat-${this.documentationId}-messages`, JSON.stringify(this.messages));
            sessionStorage.setItem(`chat-${this.documentationId}-renderedMessages`, JSON.stringify(this.renderedMessages));
        }
    }
}

export const chatStore = new ChatStore();