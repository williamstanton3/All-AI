export class LLMColumn {
    constructor(id, modelName) {
        this.id = id;
        this.modelName = modelName;
        this.element = document.createElement("div");
        this.element.className = "llm-column";
        this.element.dataset.columnId = id.toString();
        this.element.innerHTML = `
            <div class="column-header">
                <span class="llm-title">${this.modelName}</span>
                <button class="delete-column-btn">✖</button>
            </div>
            <div class="llm-output">
                Waiting for prompt...
            </div>
        `;
        const deleteBtn = this.element.querySelector(".delete-column-btn");
        deleteBtn.addEventListener("click", () => {
            this.element.remove();
            const event = new CustomEvent("columnDeleted", { detail: { id: this.id } });
            window.dispatchEvent(event);
        });
    }
}
//# sourceMappingURL=llmColumn.js.map