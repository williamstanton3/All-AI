var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
import { fetchChatGPTResponse } from "./chatgptService.js";
const addColumnBtn = document.getElementById("addColumnBtn");
const addColumnContainer = document.getElementById("addColumnContainer");
const modelDropdown = document.getElementById("modelDropdown");
const llmContainer = document.getElementById("llmContainer");
const promptInput = document.getElementById("promptInput");
const submitPromptBtn = document.getElementById("submitPromptBtn");
const newChatBtn= document.getElementById("newChat");
const threadlist= document.getElementById("threadList");
const userStatus= document.getElementById("userStatus").value;


// Click handler: read prompt, and update columns
submitPromptBtn.addEventListener("click", () => __awaiter(void 0, void 0, void 0, function* () {
    const prompt = promptInput.value.trim();
    if (!prompt)
        return;
    const chatgptColumns = Array.from(llmContainer.querySelectorAll(".llm-column")).filter(col => { var _a; return ((_a = col.querySelector(".column-header")) === null || _a === void 0 ? void 0 : _a.dataset.model) === "CHATGPT"; });
    // Append a user bubble element (dark box) and show spinner
    chatgptColumns.forEach(col => {
        const out = col.querySelector(".llm-output");
        // Remove placeholder if present
        const placeholder = out.querySelector(".placeholder");
        if (placeholder)
            placeholder.remove();
        // Create user bubble
        const userBubble = document.createElement("div");
        userBubble.className = "user-bubble";
        userBubble.textContent = prompt;
        out.appendChild(userBubble);
        // Only add spinner if one isn't already present
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
    // Clear input early
    promptInput.value = "";
    promptInput.focus();
    try {
        const reply = yield fetchChatGPTResponse(prompt);
        yield Promise.all(chatgptColumns.map((col) => __awaiter(void 0, void 0, void 0, function* () {
            const out = col.querySelector(".llm-output");
            // Remove spinner if present
            const spinner = out.querySelector(".loading-spinner");
            if (spinner)
                spinner.remove();
            // Animate the model reply word-by-word (30ms per word)
            yield typeWords(out, reply, 30);
        })));
    }
    catch (err) {
        chatgptColumns.forEach(col => {
            const out = col.querySelector(".llm-output");
            const spinner = out.querySelector(".loading-spinner");
            if (spinner)
                spinner.remove();
            const errDiv = document.createElement("div");
            errDiv.className = "error";
            errDiv.textContent = `Error: ${err.message}`;
            out.appendChild(errDiv);
        });
    }
}));
// submit on Enter key
promptInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        e.preventDefault();
        submitPromptBtn.click();
    }
});
// Default LLMs
const defaultLLMs = ["CHATGPT", "GROK", "GEMINI"];
// Creates a typing words animation
function typeWords(outContainer_1, text_1) {
    return __awaiter(this, arguments, void 0, function* (outContainer, text, delay = 30) {
        const modelDiv = document.createElement("div");
        modelDiv.className = "model-response";
        outContainer.appendChild(modelDiv);
        // split keeping whitespace so spacing/newlines are preserved
        const tokens = text.split(/(\s+)/);
        for (const token of tokens) {
            if (!token)
                continue;
            // Pure whitespace (spaces, tabs, newlines)
            if (/^\s+$/.test(token)) {
                if (token.includes("\n")) {
                    // Convert newlines to <br> while preserving any surrounding spaces
                    const parts = token.split(/(\n)/);
                    for (const part of parts) {
                        if (part === "\n") {
                            modelDiv.appendChild(document.createElement("br"));
                        }
                        else if (part.length > 0) {
                            // append actual space characters as text nodes so layout spacing stays correct
                            modelDiv.appendChild(document.createTextNode(part));
                        }
                    }
                }
                else {
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
            yield new Promise(resolve => setTimeout(resolve, delay));
        }
    });
}
// Function to create a column
function createLLMColumn(name) {
    const col = document.createElement("div");
    col.className = "llm-column";
    const header = document.createElement("div");
    header.className = "column-header";
    header.textContent = name;
    header.dataset.model = name;
    const closeBtn = document.createElement("span");
    closeBtn.textContent = "×";
    closeBtn.style.float = "right";
    closeBtn.style.cursor = "pointer";
    closeBtn.style.marginLeft = "10px";
    closeBtn.addEventListener("click", () => col.remove());
    header.appendChild(closeBtn);
    const output = document.createElement("div");
    output.className = "llm-output";
    // Use a placeholder child so we don't rely on textContent for transcript
    const placeholder = document.createElement("div");
    placeholder.className = "placeholder";
    placeholder.textContent = "Waiting for prompt...";
    output.appendChild(placeholder);
    col.appendChild(header);
    col.appendChild(output);
    llmContainer.appendChild(col);
    llmContainer.appendChild(addColumnContainer)
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
            // only allows Free and Premium amount of colummns
            let maxNumColumns = 3; 
            if (userStatus === "Premium") {
                maxNumColumns = 6;
            }
            const currNumColumns = llmContainer.querySelectorAll(".llm-column").length;
            
            if (currNumColumns < maxNumColumns) {
                createLLMColumn(modelName);
            } else {
                const alertMessage = `You can only have up to ${maxNumColumns} LLM models.`;
                
                if (userStatus === "Free") {
                    alert(`${alertMessage} Upgrade to Premium for more!`);
                } else {
                    alert(alertMessage);
                }
            }
        }
        modelDropdown.style.display = "none";
    });
});
//page is reloaded and new thread is started when newChat is clicked

newChatBtn.addEventListener("click", ()=> {
    window.location.reload();
});



// add event listener when thread is clicked
threadlist.addEventListener("click", (event) => {
    const currThread = event.target.closest(".chat-thread"); // Get the clicked thread
    if (currThread) { // If the thread exists
        const threadId = currThread.dataset.threadId; // Get the thread_id from the data attribute
        if (threadId) {
            // Fetch thread history and dynamically load it
        }
    }

            
});