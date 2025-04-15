document.addEventListener("DOMContentLoaded", function () {
    // Efecto de animación en los cuadros y círculos
    const shapes = document.querySelectorAll(".shape");
    
    shapes.forEach((shape) => {
        let speed = Math.random() * 2 + 1; // Velocidad aleatoria
        let direction = Math.random() > 0.5 ? 1 : -1; // Dirección aleatoria
        let position = 0;
        
        function animateShape() {
            position += speed * direction;
            shape.style.transform = `translateY(${position}px)`;
            
            if (position > 50 || position < -50) {
                direction *= -1; // Cambia de dirección si llega a un límite
            }
            
            requestAnimationFrame(animateShape);
        }
        
        animateShape();
    });

    // Manejo del formulario
    const form = document.querySelector("#myForm");
    
    form.addEventListener("submit", function (event) {
        event.preventDefault(); // Evita que la página se recargue
        
        const name = document.querySelector("#name").value;
        const email = document.querySelector("#email").value;
        const message = document.querySelector("#message").value;

        if (name && email && message) {
            alert("Formulario enviado correctamente 🎉");
            form.reset(); // Limpia el formulario después de enviarlo
        } else {
            alert("Por favor, completa todos los campos.");
        }
    });
});
