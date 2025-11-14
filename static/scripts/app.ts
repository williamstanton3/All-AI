import { fetchLLMResponse, typeWords } from "./aiService.js";

const addColumnBtn = document.getElementById("addColumnBtn") as HTMLButtonElement;
const addColumnContainer = document.getElementById("addColumnContainer") as HTMLDivElement;
const modelDropdown = document.getElementById("modelDropdown") as HTMLDivElement;
const llmContainer = document.getElementById("llmContainer") as HTMLDivElement;
const promptInput = document.getElementById("promptInput") as HTMLInputElement;
const submitPromptBtn = document.getElementById("submitPromptBtn") as HTMLButtonElement;
const mainContainer = document.getElementById("mainContainer") as HTMLDivElement;

let promptAlertTimeout: number | undefined;

function showPromptAlert(message: string) {
    let alert = document.getElementById("promptAlert");
    if (!alert) {
        alert = document.createElement("div");
        alert.id = "promptAlert";
        alert.className = "prompt-alert";
        // Insert directly above the prompt input container
        const pic = document.querySelector(".prompt-input-container");
        if (pic && pic.parentElement) {
            pic.parentElement.insertBefore(alert, pic);
        } else {
            mainContainer.appendChild(alert);
        }
    }
    alert.textContent = message;

    alert.classList.remove("hide");
    alert.classList.add("show");

    if (promptAlertTimeout) {
        clearTimeout(promptAlertTimeout);
    }
    promptAlertTimeout = window.setTimeout(() => {
        alert?.classList.add("hide");
        // remove after animation
        setTimeout(() => alert?.remove(), 300);
    }, 4000);
}

function getColumnsFor(model: string): HTMLDivElement[] {
    return Array.from(llmContainer.querySelectorAll<HTMLDivElement>(".llm-column"))
        .filter(col => col.querySelector<HTMLDivElement>(".column-header")?.dataset.model === model);
}

function getAllPresentModels(): string[] {
    const headers = Array.from(llmContainer.querySelectorAll<HTMLDivElement>(".llm-column .column-header"));
    const models = new Set<string>();
    headers.forEach(h => {
        const m = h.dataset.model;
        if (m) models.add(m);
    });
    return Array.from(models);
}

submitPromptBtn.addEventListener("click", async () => {
    const prompt = promptInput.value.trim();
    if (!prompt) return;

    const presentModels = getAllPresentModels();
    if (presentModels.length === 0) {
        showPromptAlert("Please select at least one LLM model");
        return;
    }

    presentModels.forEach(model => {
        getColumnsFor(model).forEach(col => {
            const out = col.querySelector<HTMLDivElement>(".llm-output")!;
            const placeholder = out.querySelector(".placeholder");
            if (placeholder) placeholder.remove();

            const userBubble = document.createElement("div");
            userBubble.className = "user-bubble";
            userBubble.textContent = prompt;
            out.appendChild(userBubble);

            if (!out.querySelector(".loading-spinner")) {
                const spinner = document.createElement("span");
                spinner.className = "loading-spinner";
                spinner.setAttribute("role", "status");
                const sr = document.createElement("span");
                sr.className = "visually-hidden";
                sr.textContent = "Loading";
                spinner.appendChild(sr);
                out.appendChild(spinner);
            }
        });
    });

    promptInput.value = "";
    promptInput.focus();

    // Start independent async tasks per model so each renders as soon as it returns
    for (const model of presentModels) {
        await (async (m) => {
            try {
                const reply = await fetchLLMResponse(m, prompt);
                const columns = getColumnsFor(m);
                columns.forEach(col => {
                    const out = col.querySelector<HTMLDivElement>(".llm-output")!;
                    const spinner = out.querySelector<HTMLSpanElement>(".loading-spinner");
                    if (spinner) spinner.remove();

                    // start typing animation asynchronously for each column
                    void typeWords(out, reply, 30);
                });
            } catch (err) {
                const error = err as Error;
                const columns = getColumnsFor(m);
                columns.forEach(col => {
                    const out = col.querySelector<HTMLDivElement>(".llm-output")!;
                    const spinner = out.querySelector<HTMLSpanElement>(".loading-spinner");
                    if (spinner) spinner.remove();

                    const errDiv = document.createElement("div");
                    errDiv.className = "error";
                    errDiv.textContent = `Error: ${error.message}`;
                    out.appendChild(errDiv);
                });
            }
        })(model);
    }
});

promptInput.addEventListener("keydown", e => {
    if (e.key === "Enter") {
        e.preventDefault();
        submitPromptBtn.click();
    }
});

const defaultLLMs = ["CHATGPT", "DEEPSEEK", "GEMINI"];

function createLLMColumn(name: string) {
    if (llmContainer.querySelector(`.llm-column .column-header[data-model="${name}"]`)) return;

    const col = document.createElement("div");
    col.className = "llm-column";

    const header = document.createElement("div");
    header.className = "column-header";
    header.dataset.model = name;
    header.textContent = name;

    const closeBtn = document.createElement("span");
    closeBtn.textContent = "×";
    closeBtn.style.float = "right";
    closeBtn.style.cursor = "pointer";
    closeBtn.style.marginLeft = "10px";
    closeBtn.addEventListener("click", () => col.remove());
    header.appendChild(closeBtn);

    const output = document.createElement("div");
    output.className = "llm-output";
    const placeholder = document.createElement("div");
    placeholder.className = "placeholder";
    placeholder.textContent = "Waiting for prompt...";
    output.appendChild(placeholder);

    col.appendChild(header);
    col.appendChild(output);
    llmContainer.insertBefore(col, addColumnContainer);

    // Remove alert if a model is added
    const alert = document.getElementById("promptAlert");
    if (alert) {
        alert.classList.add("hide");
        setTimeout(() => alert.remove(), 250);
    }
}

defaultLLMs.forEach(createLLMColumn);

addColumnBtn.addEventListener("click", e => {
    e.stopPropagation();
    modelDropdown.style.display = modelDropdown.style.display === "block" ? "none" : "block";
});

document.addEventListener("click", e => {
    if (!addColumnContainer.contains(e.target as Node)) {
        modelDropdown.style.display = "none";
    }
});

modelDropdown.querySelectorAll<HTMLDivElement>(".dropdown-item").forEach(item => {
    item.addEventListener("click", e => {
        e.stopPropagation();
        const modelName = item.textContent?.trim();
        if (modelName) createLLMColumn(modelName);
        modelDropdown.style.display = "none";
    });
});