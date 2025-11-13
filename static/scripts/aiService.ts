const MODEL_ENDPOINTS: Record<string, string> = {
    CHATGPT: "/api/chatgpt",
    GEMINI: "/api/gemini",
    CLAUDE: "/api/claude",
    BARD: "/api/bard",
    LLAMA: "/api/llama",
    GROK: "/api/grok",
    DEEPSEEK: "/api/deepseek"
};

export async function fetchLLMResponse(model: string, prompt: string): Promise<string> {
    const upper = model.toUpperCase();
    const endpoint = MODEL_ENDPOINTS[upper];
    if (!endpoint) throw new Error(`Unsupported model: ${model}`);

    const res = await fetch(endpoint, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ prompt })
    });

    const text = await res.text();
    if (!res.ok) {
        throw new Error(text || `${upper} request failed`);
    }

    let data: any;
    try {
        data = JSON.parse(text);
    } catch {
        throw new Error(`Invalid JSON from ${upper} endpoint`);
    }
    if (!("reply" in data)) {
        throw new Error(`Missing reply field from ${upper}: ${JSON.stringify(data)}`);
    }
    return data.reply;
}

// Keeps existing typing animation
export async function typeWords(outContainer: HTMLDivElement, text: string, delay = 30) {
    const modelDiv = document.createElement("div");
    modelDiv.className = "model-response";
    outContainer.appendChild(modelDiv);

    const tokens = text.split(/(\s+)/);
    for (const token of tokens) {
        if (!token) continue;
        if (/^\s+$/.test(token)) {
            if (token.includes("\n")) {
                const parts = token.split(/(\n)/);
                for (const part of parts) {
                    if (part === "\n") modelDiv.appendChild(document.createElement("br"));
                    else if (part.length > 0) modelDiv.appendChild(document.createTextNode(part));
                }
            } else {
                modelDiv.appendChild(document.createTextNode(token));
            }
            continue;
        }
        const span = document.createElement("span");
        span.className = "word";
        span.textContent = token;
        modelDiv.appendChild(span);
        span.offsetWidth;
        span.classList.add("show");
        await new Promise(r => setTimeout(r, delay));
    }
}