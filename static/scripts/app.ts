import { LLMColumn } from "./llmColumn.js";
import { currentColumns, addColumnID, removeColumnID } from "./state.js";

const container = document.getElementById("llmContainer") as HTMLDivElement;
const addColumnBtn = document.getElementById("addColumnBtn") as HTMLButtonElement;
const submitPromptBtn = document.getElementById("submitPromptBtn") as HTMLButtonElement;
const promptInput = document.getElementById("promptInput") as HTMLInputElement;

let nextColumnId = 1;

// Default models
const defaultModels = ["CHATGPT", "GROK", "GEMINI"];

defaultModels.forEach(model => {
    createColumn(model);
});

function createColumn(modelName: string = "LLM " + nextColumnId) {
    const col = new LLMColumn(nextColumnId, modelName);
    addColumnID(nextColumnId);
    container.appendChild(col.element);
    nextColumnId++;
}

// Add new column with generic name when + is clicked
addColumnBtn.addEventListener("click", () => {
    createColumn();
});

window.addEventListener("columnDeleted", (e) => {
    const event = e as CustomEvent<{ id: number }>;
    removeColumnID(event.detail.id);
});

// Broadcast prompt to all current columns
submitPromptBtn.addEventListener("click", () => {
    const prompt = promptInput.value.trim();
    if (!prompt) return;

    const outputs = container.querySelectorAll(".llm-output");
    outputs.forEach((output) => {
        output.textContent = "Thinking...\nPrompt: " + prompt;
    });
});
