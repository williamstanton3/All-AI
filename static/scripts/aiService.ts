const MODEL_ENDPOINTS: Record<string, string> = {
    CHATGPT: "/api/chatgpt",
    GEMINI: "/api/gemini",
    CLAUDE: "/api/claude",
    GROK: "/api/grok",
    DEEPSEEK: "/api/deepseek",
    MISTRAL: "/api/mistral",
    BERT: "/api/bert",
    FALCON: "/api/falcon"
};

// Declare 'marked' because it is loaded via CDN in home.html
declare const marked: any;

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

// Helper function to recursively traverse HTML nodes, tokenize text, and apply the typing effect
function processTextNodes(node: Node, targetContainer: HTMLElement, delay: number, currentPromise: Promise<void>): Promise<void> {
    if (node.nodeType === Node.TEXT_NODE && node.textContent && node.textContent.trim().length > 0) {
        // Split text by words and whitespace, keeping whitespace in the tokens array
        const tokens = node.textContent.split(/(\s+)/);

        for (const token of tokens) {
            if (!token) continue;

            if (/^\s+$/.test(token)) {
                // Handle pure whitespace (spaces, tabs, newlines)
                if (token.includes("\n")) {
                    const parts = token.split(/(\n)/);
                    for (const part of parts) {
                        if (part === "\n") targetContainer.appendChild(document.createElement("br"));
                        else if (part.length > 0) targetContainer.appendChild(document.createTextNode(part));
                    }
                } else {
                    targetContainer.appendChild(document.createTextNode(token));
                }
            } else {
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
    } else if (node.nodeType === Node.ELEMENT_NODE) {
        // It's an element node (e.g., <b>, <li>, <p>, <code>), clone it to preserve tags
        const clonedElement = node.cloneNode(false) as HTMLElement;
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


export async function typeWords(outContainer: HTMLDivElement, text: string, delay = 30) {
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

    await currentPromise;

    // Scroll to bottom after typing is finished
    outContainer.scrollTop = outContainer.scrollHeight;
}