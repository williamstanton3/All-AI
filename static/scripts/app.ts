import { fetchLLMResponse, typeWords } from "./aiService.js";

const addColumnBtn = document.getElementById("addColumnBtn") as HTMLButtonElement;
const addColumnContainer = document.getElementById("addColumnContainer") as HTMLDivElement;
const modelDropdown = document.getElementById("modelDropdown") as HTMLDivElement;
const llmContainer = document.getElementById("llmContainer") as HTMLDivElement;
const promptInput = document.getElementById("promptInput") as HTMLInputElement;
const submitPromptBtn = document.getElementById("submitPromptBtn") as HTMLButtonElement;
const mainContainer = document.getElementById("mainContainer") as HTMLDivElement;

// Sidebar Elements
const sidebarToggle = document.getElementById("sidebarToggle") as HTMLButtonElement;
const mobileOverlay = document.getElementById("mobileOverlay") as HTMLDivElement;

const userStatusInput = document.getElementById("userStatus") as HTMLInputElement | null;
const userStatus = userStatusInput?.value ?? "Free";
const MAX_FREE_MODELS = 3;

let promptAlertTimeout: number | undefined;

// --- Sidebar Logic ---
sidebarToggle.addEventListener("click", () => {
    // Check if we are in mobile view
    if (window.innerWidth <= 768) {
        document.body.classList.toggle("sidebar-mobile-open");
    } else {
        document.body.classList.toggle("sidebar-collapsed");
    }
});

function addThreadToSidebar(id: number, name: string, date: string, models: string) {
    const threadList = document.getElementById("threadList");
    if (!threadList) return;

    const div = document.createElement("div");
    div.className = "chat-thread";
    div.setAttribute("data-thread-id", id.toString());
    
    div.innerHTML = `
        <div class="thread-header">
            <span class="thread-title">${name}</span>
            <span class="delete-thread-btn" title="Delete Chat">×</span>
        </div>
        <div class="thread-details">
            <span class="thread-models">${models}</span>
            <span class="thread-date">${date}</span>
        </div>
    `;

    div.addEventListener("click", () => {
        if (window.innerWidth <= 768) {
            document.body.classList.remove("sidebar-mobile-open");
        }
        loadThreadHistory(id);
    });

    const deleteBtn = div.querySelector(".delete-thread-btn");
    if (deleteBtn) {
        deleteBtn.addEventListener("click", (e) => {
            e.stopPropagation(); // Stop the click from opening the chat
            deleteThread(id, div);
        });
    }

    threadList.prepend(div);
}

// Close mobile sidebar when clicking overlay
mobileOverlay.addEventListener("click", () => {
    document.body.classList.remove("sidebar-mobile-open");
});

function getMaxModels(): number {
    return userStatus === "Free" ? MAX_FREE_MODELS : Infinity;
}

function showPromptAlert(message: string) {
    let alert = document.getElementById("promptAlert");
    if (!alert) {
        alert = document.createElement("div");
        alert.id = "promptAlert";
        alert.className = "prompt-alert";
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
    //ensure the thread exists
    try {
        const response = await fetch('/api/ensure_thread', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                prompt: prompt,
                models: presentModels 
            })
        });

        const data = await response.json();
        
        // Only update sidebar if the server says it created a NEW thread
        if (data.status === "created") {
           addThreadToSidebar(data.id, data.name, data.date, data.models);
        }
    } catch (err) {
        console.error("Failed to establish thread:", err);
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

    presentModels.forEach(model => {
        const p = fetchLLMResponse(model, prompt);
        p.then(reply => {
            const columns = getColumnsFor(model);
            columns.forEach(col => {
                const out = col.querySelector<HTMLDivElement>(".llm-output")!;
                const spinner = out.querySelector<HTMLSpanElement>(".loading-spinner");
                if (spinner) spinner.remove();

                // Now uses the updated typeWords function for markdown typing
                typeWords(out, reply);
            });
        }).catch(err => {
            const error = err as Error;
            const columns = getColumnsFor(model);
            columns.forEach(col => {
                const out = col.querySelector<HTMLDivElement>(".llm-output")!;
                const spinner = out.querySelector<HTMLSpanElement>(".loading-spinner");
                if (spinner) spinner.remove();

                const errDiv = document.createElement("div");
                errDiv.className = "error";
                errDiv.textContent = `Error: ${error.message}`;
                out.appendChild(errDiv);
            });
        });
    });
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

    const currentCount = getAllPresentModels().length;
    const max = getMaxModels();
    if (currentCount >= max) {
        showPromptAlert(`Free accounts are limited to ${MAX_FREE_MODELS} models. Upgrade to Premium for more.`);
        return;
    }

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

    const alert = document.getElementById("promptAlert");
    if (alert) {
        alert.classList.add("hide");
        setTimeout(() => alert.remove(), 250);
    }
}

defaultLLMs.forEach(createLLMColumn);

addColumnBtn.addEventListener("click", e => {
    e.stopPropagation();
    const currentCount = getAllPresentModels().length;
    const max = getMaxModels();
    if (currentCount >= max) {
        showPromptAlert(`Free accounts are limited to ${MAX_FREE_MODELS} models. Upgrade to Premium for more.`);
        return;
    }
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

// New Chat Button
const newChatBtn = document.getElementById("newChat");
if (newChatBtn) {
    newChatBtn.addEventListener("click", async () => {
        try {
            // starts a new session
            await fetch('/api/new_thread', { method: 'POST' });

            // Clear the UI and resets to default
            document.querySelectorAll(".llm-column").forEach(col => col.remove());
            defaultLLMs.forEach(createLLMColumn);
        } catch (err) {
            console.error("Error creating new thread:", err);
        }
    });
}

// Loads chat history
document.querySelectorAll(".chat-thread").forEach(thread => {

    thread.addEventListener("click", () => {
        if (window.innerWidth <= 768) {
            document.body.classList.remove("sidebar-mobile-open");
        }
        const threadId = thread.getAttribute("data-thread-id");
        if (threadId) loadThreadHistory(parseInt(threadId));
    });

    const deleteBtn = thread.querySelector(".delete-thread-btn");
    if (deleteBtn) {
        deleteBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            const threadId = thread.getAttribute("data-thread-id");
            if (threadId) deleteThread(parseInt(threadId), thread as HTMLElement);
        });
    }
});
// Loads the chat history given the threadID
async function loadThreadHistory(threadId: number) {
    try {
        const response = await fetch(`/api/thread/${threadId}`);
        if (!response.ok) throw new Error("Failed to fetch history");
        
        const data = await response.json();
        const history = data.history; // Array of {user_input, model_name, model_response, date_saved}

        // Clears the current existing columns
        document.querySelectorAll(".llm-column").forEach(col => col.remove());

        // Find which models in the chat thread history and load them into new columns
        const uniqueModels = new Set<string>();
        history.forEach((h: any) => uniqueModels.add(h.model_name));
        uniqueModels.forEach(model => createLLMColumn(model));

        // Iterate through history and fill in the chat bubbles
        history.forEach((item: any) => {
            const columns = getColumnsFor(item.model_name); //finds the column for the specific model
            columns.forEach(col => {
                const out = col.querySelector(".llm-output");
                if (!out) return;
                //removes the "Waiting for prompt" placeholder
                const placeholder = out.querySelector(".placeholder");
                if (placeholder) placeholder.remove();

                // Makes the user Bubble
                const userBubble = document.createElement("div");
                userBubble.className = "user-bubble";
                userBubble.textContent = item.user_input;
                out.appendChild(userBubble);
                
                // Make the AI response bubble
                const responseDiv = document.createElement("div");
                 // @ts-ignore (reads marked library so html elements are rendered properly)
                responseDiv.innerHTML = marked.parse(item.model_response);
                out.appendChild(responseDiv);
            });
        });

    } catch (error) {
        console.error("Error loading history:", error);
        showPromptAlert("Could not load chat history.");
    }
}

async function deleteThread(threadId: number, element: HTMLElement) {
    if (!confirm("Are you sure you want to delete this chat permanently?")) return;

    try {
        const response = await fetch(`/api/thread/${threadId}`, {
            method: 'DELETE'
        });
        if (response.ok) {
            element.remove();
        } else {
            alert("Failed to delete thread.");
        }
    } catch (err) {
        console.error("Error deleting thread:", err);
    }
}