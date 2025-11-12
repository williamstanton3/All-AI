const addColumnBtn = document.getElementById("addColumnBtn") as HTMLButtonElement;
const addColumnContainer = document.getElementById("addColumnContainer") as HTMLDivElement;
const modelDropdown = document.getElementById("modelDropdown") as HTMLDivElement;
const llmContainer = document.getElementById("llmContainer") as HTMLDivElement;
const promptInput = document.getElementById("promptInput") as HTMLInputElement;
const submitPromptBtn = document.getElementById("submitPromptBtn") as HTMLButtonElement;

// Click handler: read prompt, update columns (optional), clear and focus input
submitPromptBtn.addEventListener("click", () => {
    const prompt = promptInput.value.trim();
    if (!prompt) return; // ignore empty submissions

    console.log("Prompt submitted:", prompt);

    // update each LLM column's output area
    llmContainer.querySelectorAll(".llm-column .llm-output").forEach(el => {
        if (el.textContent === "Waiting for prompt...") {
            el.textContent = "";
        }
        (el as HTMLDivElement).textContent += `${prompt}\n`;
    });

    // Clear the text box and focus it
    promptInput.value = "";
    promptInput.focus();
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

// Function to create a column
function createLLMColumn(name: string) {
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
    if (!addColumnContainer.contains(e.target as Node)) {
        modelDropdown.style.display = "none";
    }
});

// Dropdown items: add a new column when clicked
modelDropdown.querySelectorAll(".dropdown-item").forEach(item => {
    item.addEventListener("click", (e) => {
        e.stopPropagation();
        const modelName = (item as HTMLDivElement).textContent;
        if (modelName) {
            createLLMColumn(modelName);
        }
        modelDropdown.style.display = "none";
    });
});
