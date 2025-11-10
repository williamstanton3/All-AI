export let currentColumns = [];
export function addColumnID(id) {
    currentColumns.push(id);
}
export function removeColumnID(id) {
    currentColumns = currentColumns.filter(col => col !== id);
}
//# sourceMappingURL=state.js.map