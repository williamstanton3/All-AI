var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
const MODEL_ENDPOINTS = {
    CHATGPT: "/api/chatgpt",
    GEMINI: "/api/gemini",
    CLAUDE: "/api/claude",
    GROK: "/api/grok",
    DEEPSEEK: "/api/deepseek",
    MISTRAL: "/api/mistral",
    BERT: "/api/bert",
    FALCON: "/api/falcon"
};
export function fetchLLMResponse(model, prompt) {
    return __awaiter(this, void 0, void 0, function* () {
        const upper = model.toUpperCase();
        const endpoint = MODEL_ENDPOINTS[upper];
        if (!endpoint)
            throw new Error(`Unsupported model: ${model}`);
        const res = yield fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt })
        });
        const text = yield res.text();
        if (!res.ok) {
            throw new Error(text || `${upper} request failed`);
        }
        let data;
        try {
            data = JSON.parse(text);
        }
        catch (_a) {
            throw new Error(`Invalid JSON from ${upper} endpoint`);
        }
        if (!("reply" in data)) {
            throw new Error(`Missing reply field from ${upper}: ${JSON.stringify(data)}`);
        }
        return data.reply;
    });
}
export function typeWords(outContainer_1, text_1) {
    return __awaiter(this, arguments, void 0, function* (outContainer, text, delay = 30) {
        const modelDiv = document.createElement("div");
        modelDiv.className = "model-response";
        outContainer.appendChild(modelDiv);
        const tokens = text.split(/(\s+)/);
        for (const token of tokens) {
            if (!token)
                continue;
            if (/^\s+$/.test(token)) {
                if (token.includes("\n")) {
                    const parts = token.split(/(\n)/);
                    for (const part of parts) {
                        if (part === "\n")
                            modelDiv.appendChild(document.createElement("br"));
                        else if (part.length > 0)
                            modelDiv.appendChild(document.createTextNode(part));
                    }
                }
                else {
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
            yield new Promise(r => setTimeout(r, delay));
        }
    });
}
//# sourceMappingURL=aiService.js.map