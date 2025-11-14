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
const userStatusInput = document.getElementById("userStatus");
const userStatus = (_a = userStatusInput === null || userStatusInput === void 0 ? void 0 : userStatusInput.value) !== null && _a !== void 0 ? _a : "Free";
const MAX_FREE_MODELS = 3;
let promptAlertTimeout;
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
    for (const model of presentModels) {
        yield ((m) => __awaiter(void 0, void 0, void 0, function* () {
            try {
                const reply = yield fetchLLMResponse(m, prompt);
                const columns = getColumnsFor(m);
                columns.forEach(col => {
                    const out = col.querySelector(".llm-output");
                    const spinner = out.querySelector(".loading-spinner");
                    if (spinner)
                        spinner.remove();
                    // start typing animation asynchronously for each column
                    void typeWords(out, reply, 30);
                });
            }
            catch (err) {
                const error = err;
                const columns = getColumnsFor(m);
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
            }
        }))(model);
    }
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
//# sourceMappingURL=app.js.map