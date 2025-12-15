var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var _a;
import { fetchLLMResponse, typeWords } from "./aiService.js";
const addColumnBtn = document.getElementById("addColumnBtn");
const addColumnContainer = document.getElementById("addColumnContainer");
const modelDropdown = document.getElementById("modelDropdown");
const llmContainer = document.getElementById("llmContainer");
const promptInput = document.getElementById("promptInput");
const submitPromptBtn = document.getElementById("submitPromptBtn");
const mainContainer = document.getElementById("mainContainer");
// Sidebar Elements
const sidebarToggle = document.getElementById("sidebarToggle");
const mobileOverlay = document.getElementById("mobileOverlay");
const userStatusInput = document.getElementById("userStatus");
const userStatus = (_a = userStatusInput === null || userStatusInput === void 0 ? void 0 : userStatusInput.value) !== null && _a !== void 0 ? _a : "Free";
const MAX_FREE_MODELS = 3;
let promptAlertTimeout;
// --- Sidebar Logic ---
sidebarToggle.addEventListener("click", () => {
    // Check if we are in mobile view
    if (window.innerWidth <= 768) {
        document.body.classList.toggle("sidebar-mobile-open");
    }
    else {
        document.body.classList.toggle("sidebar-collapsed");
    }
});
function addThreadToSidebar(id, name, date, models) {
    const threadList = document.getElementById("threadList");
    if (!threadList)
        return;
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
function getMaxModels() {
    return userStatus === "Free" ? MAX_FREE_MODELS : Infinity;
}
function showPromptAlert(message) {
    let alert = document.getElementById("promptAlert");
    if (!alert) {
        alert = document.createElement("div");
        alert.id = "promptAlert";
        alert.className = "prompt-alert";
        const pic = document.querySelector(".prompt-input-container");
        if (pic && pic.parentElement) {
            pic.parentElement.insertBefore(alert, pic);
        }
        else {
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
        alert === null || alert === void 0 ? void 0 : alert.classList.add("hide");
        setTimeout(() => alert === null || alert === void 0 ? void 0 : alert.remove(), 300);
    }, 4000);
}
function getColumnsFor(model) {
    return Array.from(llmContainer.querySelectorAll(".llm-column"))
        .filter(col => { var _a; return ((_a = col.querySelector(".column-header")) === null || _a === void 0 ? void 0 : _a.dataset.model) === model; });
}
function getAllPresentModels() {
    const headers = Array.from(llmContainer.querySelectorAll(".llm-column .column-header"));
    const models = new Set();
    headers.forEach(h => {
        const m = h.dataset.model;
        if (m)
            models.add(m);
    });
    return Array.from(models);
}
submitPromptBtn.addEventListener("click", () => __awaiter(void 0, void 0, void 0, function* () {
    const prompt = promptInput.value.trim();
    if (!prompt)
        return;
    const presentModels = getAllPresentModels();
    if (presentModels.length === 0) {
        showPromptAlert("Please select at least one LLM model");
        return;
    }
    //ensure the thread exists
    try {
        const response = yield fetch('/api/ensure_thread', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: prompt,
                models: presentModels
            })
        });
        const data = yield response.json();
        // Only update sidebar if the server says it created a NEW thread
        if (data.status === "created") {
            addThreadToSidebar(data.id, data.name, data.date, data.models);
        }
    }
    catch (err) {
        console.error("Failed to establish thread:", err);
    }
    presentModels.forEach(model => {
        getColumnsFor(model).forEach(col => {
            const out = col.querySelector(".llm-output");
            const placeholder = out.querySelector(".placeholder");
            if (placeholder)
                placeholder.remove();
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
                const out = col.querySelector(".llm-output");
                const spinner = out.querySelector(".loading-spinner");
                if (spinner)
                    spinner.remove();
                // Now uses the updated typeWords function for markdown typing
                typeWords(out, reply);
            });
        }).catch(err => {
            const error = err;
            const columns = getColumnsFor(model);
            columns.forEach(col => {
                const out = col.querySelector(".llm-output");
                const spinner = out.querySelector(".loading-spinner");
                if (spinner)
                    spinner.remove();
                const errDiv = document.createElement("div");
                errDiv.className = "error";
                errDiv.textContent = `Error: ${error.message}`;
                out.appendChild(errDiv);
            });
        });
    });
}));
promptInput.addEventListener("keydown", e => {
    if (e.key === "Enter") {
        e.preventDefault();
        submitPromptBtn.click();
    }
});
const defaultLLMs = ["CHATGPT", "DEEPSEEK", "GEMINI"];
function createLLMColumn(name) {
    if (llmContainer.querySelector(`.llm-column .column-header[data-model="${name}"]`))
        return;
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
    if (!addColumnContainer.contains(e.target)) {
        modelDropdown.style.display = "none";
    }
});
modelDropdown.querySelectorAll(".dropdown-item").forEach(item => {
    item.addEventListener("click", e => {
        var _a;
        e.stopPropagation();
        const modelName = (_a = item.textContent) === null || _a === void 0 ? void 0 : _a.trim();
        if (modelName)
            createLLMColumn(modelName);
        modelDropdown.style.display = "none";
    });
});
// New Chat Button
const newChatBtn = document.getElementById("newChat");
if (newChatBtn) {
    newChatBtn.addEventListener("click", () => __awaiter(void 0, void 0, void 0, function* () {
        try {
            // starts a new session
            yield fetch('/api/new_thread', { method: 'POST' });
            // Clear the UI and resets to default
            document.querySelectorAll(".llm-column").forEach(col => col.remove());
            defaultLLMs.forEach(createLLMColumn);
        }
        catch (err) {
            console.error("Error creating new thread:", err);
        }
    }));
}
// Loads chat history
document.querySelectorAll(".chat-thread").forEach(thread => {
    thread.addEventListener("click", () => {
        if (window.innerWidth <= 768) {
            document.body.classList.remove("sidebar-mobile-open");
        }
        const threadId = thread.getAttribute("data-thread-id");
        if (threadId)
            loadThreadHistory(parseInt(threadId));
    });
    const deleteBtn = thread.querySelector(".delete-thread-btn");
    if (deleteBtn) {
        deleteBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            const threadId = thread.getAttribute("data-thread-id");
            if (threadId)
                deleteThread(parseInt(threadId), thread);
        });
    }
});
// Loads the chat history given the threadID
function loadThreadHistory(threadId) {
    return __awaiter(this, void 0, void 0, function* () {
        try {
            const response = yield fetch(`/api/thread/${threadId}`);
            if (!response.ok)
                throw new Error("Failed to fetch history");
            const data = yield response.json();
            const history = data.history; // Array of {user_input, model_name, model_response, date_saved}
            // Clears the current existing columns
            document.querySelectorAll(".llm-column").forEach(col => col.remove());
            // Find which models in the chat thread history and load them into new columns
            const uniqueModels = new Set();
            history.forEach((h) => uniqueModels.add(h.model_name));
            uniqueModels.forEach(model => createLLMColumn(model));
            // Iterate through history and fill in the chat bubbles
            history.forEach((item) => {
                const columns = getColumnsFor(item.model_name); //finds the column for the specific model
                columns.forEach(col => {
                    const out = col.querySelector(".llm-output");
                    if (!out)
                        return;
                    //removes the "Waiting for prompt" placeholder
                    const placeholder = out.querySelector(".placeholder");
                    if (placeholder)
                        placeholder.remove();
                    // Makes the user Bubble
                    const userBubble = document.createElement("div");
                    userBubble.className = "user-bubble";
                    userBubble.textContent = item.user_input;
                    out.appendChild(userBubble);
                    // Make the AI response bubble
                    const responseDiv = document.createElement("div");
                    responseDiv.className = "model-response";
                    // @ts-ignore (reads marked library so html elements are rendered properly)
                    responseDiv.innerHTML = marked.parse(item.model_response);
                    out.appendChild(responseDiv);
                });
            });
        }
        catch (error) {
            console.error("Error loading history:", error);
            showPromptAlert("Could not load chat history.");
        }
    });
}
function deleteThread(threadId, element) {
    return __awaiter(this, void 0, void 0, function* () {
        if (!confirm("Are you sure you want to delete this chat permanently?"))
            return;
        try {
            const response = yield fetch(`/api/thread/${threadId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                element.remove();
            }
            else {
                alert("Failed to delete thread.");
            }
        }
        catch (err) {
            console.error("Error deleting thread:", err);
        }
    });
}
//# sourceMappingURL=app.js.map