"use strict";
const addColumnBtn = document.getElementById("addColumnBtn");
const addColumnContainer = document.getElementById("addColumnContainer");
const modelDropdown = document.getElementById("modelDropdown");
const llmContainer = document.getElementById("llmContainer");
// Default LLMs
const defaultLLMs = ["CHATGPT", "GROK", "GEMINI"];
// Function to create a column
function createLLMColumn(name) {
    const col = document.createElement("div");
    col.className = "llm-column";
    const header = document.createElement("div");
    header.className = "column-header";
    header.textContent = name;
    // Add a close button
    const closeBtn = document.createElement("span");
    closeBtn.textContent = "×";
    closeBtn.style.float = "right";
    closeBtn.style.cursor = "pointer";
    closeBtn.style.marginLeft = "10px";
    closeBtn.addEventListener("click", () => col.remove());
    header.appendChild(closeBtn);
    const output = document.createElement("div");
    output.className = "llm-output";
    output.textContent = "Waiting for prompt...";
    col.appendChild(header);
    col.appendChild(output);
    // Insert the column before the plus button
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
    if (!addColumnContainer.contains(e.target)) {
        modelDropdown.style.display = "none";
    }
});
// Dropdown items: add a new column when clicked
modelDropdown.querySelectorAll(".dropdown-item").forEach(item => {
    item.addEventListener("click", (e) => {
        e.stopPropagation();
        const modelName = item.textContent;
        if (modelName) {
            createLLMColumn(modelName);
        }
        modelDropdown.style.display = "none";
    });
});
//# sourceMappingURL=app.js.map