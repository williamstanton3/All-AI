const flashes = document.querySelectorAll<HTMLDivElement>('.flash');

flashes.forEach((flash) => {
    setTimeout(() => {
        flash.style.opacity = '0';

        setTimeout(() => {
            flash.remove();
        }, 500);
    }, 3000);
});