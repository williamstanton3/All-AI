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
    LLAMA: "/api/llama",
    QWEN: "/api/qwen"
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
// Helper function to recursively traverse HTML nodes, tokenize text, and apply the typing effect
function processTextNodes(node, targetContainer, delay, currentPromise) {
    if (node.nodeType === Node.TEXT_NODE && node.textContent && node.textContent.trim().length > 0) {
        // Split text by words and whitespace, keeping whitespace in the tokens array
        const tokens = node.textContent.split(/(\s+)/);
        for (const token of tokens) {
            if (!token)
                continue;
            if (/^\s+$/.test(token)) {
                // Handle pure whitespace (spaces, tabs, newlines)
                if (token.includes("\n")) {
                    const parts = token.split(/(\n)/);
                    for (const part of parts) {
                        if (part === "\n")
                            targetContainer.appendChild(document.createElement("br"));
                        else if (part.length > 0)
                            targetContainer.appendChild(document.createTextNode(part));
                    }
                }
                else {
                    targetContainer.appendChild(document.createTextNode(token));
                }
            }
            else {
                // This is a word: wrap it and chain the animation promise
                const span = document.createElement("span");
                span.className = "word";
                span.textContent = token;
                targetContainer.appendChild(span);
                currentPromise = currentPromise.then(() => {
                    span.offsetWidth; // Trigger reflow for transition
                    span.classList.add("show");
                    return new Promise(resolve => setTimeout(resolve, delay));
                });
            }
        }
    }
    else if (node.nodeType === Node.ELEMENT_NODE) {
        // It's an element node (e.g., <b>, <li>, <p>, <code>), clone it to preserve tags
        const clonedElement = node.cloneNode(false);
        targetContainer.appendChild(clonedElement);
        // Recursively process its children to find the text nodes
        let child = node.firstChild;
        while (child) {
            currentPromise = processTextNodes(child, clonedElement, delay, currentPromise);
            child = child.nextSibling;
        }
    }
    return currentPromise;
}
export function typeWords(outContainer_1, text_1) {
    return __awaiter(this, arguments, void 0, function* (outContainer, text, delay = 30) {
        if (typeof marked === 'undefined') {
            // Fallback if marked.js didn't load
            outContainer.textContent = text;
            return;
        }
        const modelDiv = document.createElement("div");
        modelDiv.className = "model-response";
        outContainer.appendChild(modelDiv);
        // 1. Convert Markdown to full HTML structure
        const htmlContent = marked.parse(text);
        // 2. Create a temporary container to hold the HTML structure
        const tempContainer = document.createElement('div');
        tempContainer.innerHTML = htmlContent;
        // 3. Start the recursive typing/tokenization process
        let currentPromise = Promise.resolve();
        let child = tempContainer.firstChild;
        while (child) {
            currentPromise = processTextNodes(child, modelDiv, delay, currentPromise);
            child = child.nextSibling;
        }
        yield currentPromise;
        // Scroll to bottom after typing is finished
        outContainer.scrollTop = outContainer.scrollHeight;
    });
}
//# sourceMappingURL=aiService.js.map