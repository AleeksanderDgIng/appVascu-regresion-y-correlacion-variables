document.addEventListener("DOMContentLoaded", function(event) {
    // Esta función se ejecuta cuando el DOM (Document Object Model) está completamente cargado.

    /*===== ENLACE ACTIVO =====*/
    const linkColor = document.querySelectorAll('.nav_link');

    function colorLink() {
        linkColor.forEach(l => l.classList.remove('active'));
        this.classList.add('active');
        localStorage.setItem("activeLink", this.getAttribute("href")); // Almacena la URL del enlace activo
    }

    linkColor.forEach(l => l.addEventListener('click', colorLink));

    // Restaura el enlace activo al cargar la página
    const storedLink = localStorage.getItem("activeLink");
    if (storedLink) {
        linkColor.forEach(l => {
            if (l.getAttribute("href") === storedLink) {
                l.classList.add('active');
            }
        });
    }
});
