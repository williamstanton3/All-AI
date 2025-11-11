const addColumnBtn = document.getElementById("addColumnBtn") as HTMLButtonElement;
const addColumnContainer = document.getElementById("addColumnContainer") as HTMLDivElement;
const modelDropdown = document.getElementById("modelDropdown") as HTMLDivElement;

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

// Dropdown items do nothing
modelDropdown.querySelectorAll(".dropdown-item").forEach(item => {
    item.addEventListener("click", (e) => {
        e.stopPropagation();
        modelDropdown.style.display = "none"; // just close dropdown
    });
});
