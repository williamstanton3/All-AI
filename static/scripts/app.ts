import { fetchChatGPTResponse } from "./chatgptService.js";

const addColumnBtn = document.getElementById("addColumnBtn") as HTMLButtonElement;
const addColumnContainer = document.getElementById("addColumnContainer") as HTMLDivElement;
const modelDropdown = document.getElementById("modelDropdown") as HTMLDivElement;
const llmContainer = document.getElementById("llmContainer") as HTMLDivElement;
const promptInput = document.getElementById("promptInput") as HTMLInputElement;
const submitPromptBtn = document.getElementById("submitPromptBtn") as HTMLButtonElement;

// Click handler: read prompt, and update columns
submitPromptBtn.addEventListener("click", async () => {
    const prompt = promptInput.value.trim();
    if (!prompt) return;

    const chatgptColumns = Array.from(
        llmContainer.querySelectorAll<HTMLDivElement>(".llm-column")
    ).filter(col => (col.querySelector<HTMLDivElement>(".column-header")?.dataset.model) === "CHATGPT");

    // Append a user bubble element (dark box) and show spinner
    chatgptColumns.forEach(col => {
        const out = col.querySelector<HTMLDivElement>(".llm-output") as HTMLDivElement;

        // Remove placeholder if present
        const placeholder = out.querySelector(".placeholder");
        if (placeholder) placeholder.remove();

        // Create user bubble
        const userBubble = document.createElement("div") as HTMLDivElement;
        userBubble.className = "user-bubble";
        userBubble.textContent = prompt;
        out.appendChild(userBubble);

        // Only add spinner if one isn't already present
        if (!out.querySelector<HTMLSpanElement>(".loading-spinner")) {
            const spinner = document.createElement("span") as HTMLSpanElement;
            spinner.className = "loading-spinner";
            spinner.setAttribute("role", "status");
            const sr = document.createElement("span") as HTMLSpanElement;
            sr.className = "visually-hidden";
            sr.textContent = "Loading";
            spinner.appendChild(sr);
            out.appendChild(spinner);
        }
    });

    // Clear input early
    promptInput.value = "";
    promptInput.focus();

    try {
        const reply = await fetchChatGPTResponse(prompt);

        await Promise.all(chatgptColumns.map(async (col) => {
            const out = col.querySelector<HTMLDivElement>(".llm-output") as HTMLDivElement;

            // Remove spinner if present
            const spinner = out.querySelector<HTMLSpanElement>(".loading-spinner");
            if (spinner) spinner.remove();

            // Animate the model reply word-by-word (30ms per word)
            await typeWords(out, reply, 30);
        }));
    } catch (err) {
        chatgptColumns.forEach(col => {
            const out = col.querySelector<HTMLDivElement>(".llm-output") as HTMLDivElement;
            const spinner = out.querySelector<HTMLSpanElement>(".loading-spinner");
            if (spinner) spinner.remove();
            const errDiv = document.createElement("div") as HTMLDivElement;
            errDiv.className = "error";
            errDiv.textContent = `Error: ${(err as Error).message}`;
            out.appendChild(errDiv);
        });
    }
});

// submit on Enter key
promptInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        e.preventDefault();
        submitPromptBtn.click();
    }
});

// Default LLMs
const defaultLLMs = ["CHATGPT", "GROK", "GEMINI"];

// File: `static/scripts/app.ts` - replace existing typeWords with this
async function typeWords(outContainer: HTMLDivElement, text: string, delay = 30) {
    const modelDiv = document.createElement("div");
    modelDiv.className = "model-response";
    outContainer.appendChild(modelDiv);

    // split keeping whitespace so spacing/newlines are preserved
    const tokens = text.split(/(\s+)/);

    for (const token of tokens) {
        if (!token) continue;

        // Pure whitespace (spaces, tabs, newlines)
        if (/^\s+$/.test(token)) {
            if (token.includes("\n")) {
                // Convert newlines to <br> while preserving any surrounding spaces
                const parts = token.split(/(\n)/);
                for (const part of parts) {
                    if (part === "\n") {
                        modelDiv.appendChild(document.createElement("br"));
                    } else if (part.length > 0) {
                        // append actual space characters as text nodes so layout spacing stays correct
                        modelDiv.appendChild(document.createTextNode(part));
                    }
                }
            } else {
                // simple spaces/tabs -> append as text node
                modelDiv.appendChild(document.createTextNode(token));
            }
            continue; // don't animate whitespace
        }

        // Regular word/token -> animate
        const span = document.createElement("span");
        span.className = "word";
        span.textContent = token;
        modelDiv.appendChild(span);

        // force layout so transition runs
        // eslint-disable-next-line @typescript-eslint/no-unused-expressions
        span.offsetWidth;
        span.classList.add("show");

        await new Promise(resolve => setTimeout(resolve, delay));
    }
}


// Function to create a column
function createLLMColumn(name: string) {
    const col = document.createElement("div") as HTMLDivElement;
    col.className = "llm-column";

    const header = document.createElement("div") as HTMLDivElement;
    header.className = "column-header";
    header.textContent = name;
    header.dataset.model = name;

    const closeBtn = document.createElement("span") as HTMLSpanElement;
    closeBtn.textContent = "×";
    closeBtn.style.float = "right";
    closeBtn.style.cursor = "pointer";
    closeBtn.style.marginLeft = "10px";
    closeBtn.addEventListener("click", () => col.remove());
    header.appendChild(closeBtn);

    const output = document.createElement("div") as HTMLDivElement;
    output.className = "llm-output";
    // Use a placeholder child so we don't rely on textContent for transcript
    const placeholder = document.createElement("div") as HTMLDivElement;
    placeholder.className = "placeholder";
    placeholder.textContent = "Waiting for prompt...";
    output.appendChild(placeholder);

    col.appendChild(header);
    col.appendChild(output);

    llmContainer.insertBefore(col, addColumnContainer);
}

// Initialize default columns
defaultLLMs.forEach(createLLMColumn);

// Show/hide dropdown when + is clicked
addColumnBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    modelDropdown.style.display = modelDropdown.style.display === "block" ? "none" : "block";
});

// Hide dropdown when clicking outside
document.addEventListener("click", (e) => {
    if (!addColumnContainer.contains(e.target as Node)) {
        modelDropdown.style.display = "none";
    }
});

// Dropdown items: add a new column when clicked
modelDropdown.querySelectorAll<HTMLDivElement>(".dropdown-item").forEach(item => {
    item.addEventListener("click", (e) => {
        e.stopPropagation();
        const modelName = (item as HTMLDivElement).textContent;
        if (modelName) {
            createLLMColumn(modelName);
        }
        modelDropdown.style.display = "none";
    });
});