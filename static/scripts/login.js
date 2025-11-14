"use strict";
const flashes = document.querySelectorAll('.flash');
flashes.forEach((flash) => {
    setTimeout(() => {
        flash.style.opacity = '0';
        setTimeout(() => {
            flash.remove();
        }, 500);
    }, 3000);
});
//# sourceMappingURL=login.js.map