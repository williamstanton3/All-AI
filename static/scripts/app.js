import { LLMColumn } from "./llmColumn.js";
import { addColumnID, removeColumnID } from "./state.js";
const container = document.getElementById("llmContainer");
const addColumnBtn = document.getElementById("addColumnBtn");
const submitPromptBtn = document.getElementById("submitPromptBtn");
const promptInput = document.getElementById("promptInput");
let nextColumnId = 1;
// Default models
const defaultModels = ["CHATGPT", "GROK", "GEMINI"];
defaultModels.forEach(model => {
    createColumn(model);
});
function createColumn(modelName = "LLM " + nextColumnId) {
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
    const event = e;
    removeColumnID(event.detail.id);
});
// Broadcast prompt to all current columns
submitPromptBtn.addEventListener("click", () => {
    const prompt = promptInput.value.trim();
    if (!prompt)
        return;
    const outputs = container.querySelectorAll(".llm-output");
    outputs.forEach((output) => {
        output.textContent = "Thinking...\nPrompt: " + prompt;
    });
});
//# sourceMappingURL=app.js.map