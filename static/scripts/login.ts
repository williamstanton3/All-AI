// Select all elements with class "flash"
const flashes = document.querySelectorAll<HTMLDivElement>('.flash');

flashes.forEach((flash) => {
    // Wait 3 seconds
    setTimeout(() => {
        flash.style.opacity = '0'; // fade out

        // Remove from DOM after transition
        setTimeout(() => {
            flash.remove();
        }, 500); // match CSS transition duration
    }, 3000); // show for 3 seconds
});