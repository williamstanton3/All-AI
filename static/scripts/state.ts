export let currentColumns: number[] = [];

export function addColumnID(id: number) {
    currentColumns.push(id);
}

export function removeColumnID(id: number) {
    currentColumns = currentColumns.filter(col => col !== id);
}
