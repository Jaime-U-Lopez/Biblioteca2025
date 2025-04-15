console.log("✅ Script JS cargado correctamente");
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


    let flashMessages = {{ get_flashed_messages(with_categories=true) | tojson }};
    
    if (flashMessages.length > 0) {
        flashMessages.forEach(([category, message]) => {
            Swal.fire({
                icon: category === "success" ? "success" : "error",
                title: message
            });
        });
    }

    alert("hola")

});
function reservarLibro(id) {
    fetch("/confirmar_reserva", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ id: id })
    })
    .then(response => response.json())
    .then(data => {
        alert("Reserva realizada con éxito");
        window.location.href = "/home"; // Redirigir al inicio
    })
    .catch(error => console.error("Error al reservar:", error));
}


function cancelarReserva(id) {
    if (confirm("¿Estás seguro de cancelar la reserva?")) {
        // Aquí podrías redirigir o hacer una llamada AJAX
        window.location.href = `/cancelar_reserva/${id}`;
    }
}

