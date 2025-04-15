from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from sqlalchemy import text 

# Configuración de la base de datos
DB_USER = "root"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_NAME = "biblioteca2025"

class Config:
    SECRET_KEY = os.urandom(24)  # Para sesiones y flash messages
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# Inicializamos la base de datos
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Definimos el modelo Usuario
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


# Modelo de Libros
class Libro(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(255), nullable=False)
    imagen = db.Column(db.String(255), nullable=False)  # URL o nombre del archivo
    editor = db.Column(db.String(255), nullable=False)
    autor = db.Column(db.String(255), nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)


class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    libro_id = db.Column(db.Integer, db.ForeignKey('libro.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    fecha_reserva = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    estado = db.Column(db.Enum('Pendiente', 'Confirmada', 'Cancelada'), default='Pendiente')
    libro = db.relationship("Libro", backref=db.backref("reservas", lazy=True))
    usuario = db.relationship("Usuario", backref=db.backref("reservas", lazy=True))


# Crear las tablas y un usuario quemado
with app.app_context():
    db.create_all()
    if not Usuario.query.filter_by(email="admin@example.com").first():
        hashed_password = generate_password_hash("admin123")
        admin_user = Usuario(nombre="Admin", email="admin@example.com", password=hashed_password)
        db.session.add(admin_user)
        db.session.commit()

# Función para guardar usuarios
def guardar_usuario(nombre, email, password):
    if Usuario.query.filter_by(email=email).first():
        flash("El email ya está registrado", "warning")
        return False
    hashed_password = generate_password_hash(password)  # Hashear contraseña
    usuario = Usuario(nombre=nombre, email=email, password=hashed_password)
    db.session.add(usuario)
    db.session.commit()
    return True




@app.route("/", methods=["GET", "POST"])
def loginUsuario():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and check_password_hash(usuario.password, password):
            session["usuario_id"] = usuario.id  # Guardar sesión
            flash("Inicio de sesión exitoso", "success")
            return redirect(url_for("home"))
        else:
            flash("Correo o contraseña incorrectos", "danger")
    
    return render_template("login.html")


@app.route("/usuarios", methods=["GET", "POST"])
def usuarios():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        contraseña = request.form["password"]

        if guardar_usuario(nombre, email, contraseña):
            flash("Usuario registrado correctamente", "success")
            return redirect(url_for("usuarios"))

    # Obtener usuarios para mostrar en la tabla
    usuarios = Usuario.query.all()
    return render_template("admin/registrarUser.html", usuarios=usuarios)

# 🔹 API para obtener usuarios en formato JSON (para uso en AJAX o API)
@app.route("/api/usuarios")
def obtener_usuarios():
    usuarios = Usuario.query.all()
    usuarios_json = [{"id": u.id, "nombre": u.nombre, "email": u.email} for u in usuarios]
    return jsonify(usuarios_json)


@app.route("/usuarios/<int:id>", methods=["DELETE"])
def eliminar_usuario(id):
    usuario = Usuario.query.get(id)
    if usuario:
        db.session.delete(usuario)
        db.session.commit()
        return jsonify({"success": True, "message": "Usuario eliminado correctamente"})
    return jsonify({"success": False, "message": "Usuario no encontrado"}), 404

@app.route("/usuarios/<int:id>", methods=["PUT"])
def actualizar_usuario(id):

    session = db.session  # Obtener la sesión actual
    usuario = session.get(Usuario, id)  
    #usuario = Usuario.query.get(id)
    if usuario:
        data = request.get_json()
        print("Datos recibidos:", data)  # <-- Agregar este print para depuración

        usuario.nombre = data.get("nombre", usuario.nombre)
        usuario.email = data.get("email", usuario.email)

        db.session.commit()

        return jsonify({"success": True, "message": "Usuario actualizado correctamente"})

    return jsonify({"success": False, "message": "Usuario no encontrado"}), 404



@app.route("/logout")
def logout():
    session.pop("usuario_id", None)  # Eliminar la sesión
    flash("Has cerrado sesión", "info")
    return redirect(url_for("loginUsuario"))

@app.route("/home")
def home():
    libros = Libro.query.limit(10).all()
    return render_template("home.html", libros=libros)



class Contactos(db.Model):
    __tablename__ = "contactos"  
    idcontactos = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombresApellidos = db.Column(db.String(255), nullable=False)
    correoElectronico = db.Column(db.String(255), nullable=False, unique=True)
    mensaje = db.Column(db.Text, nullable=False)


@app.route("/contacto", methods=["GET", "POST"])
def contacto():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        mensaje = request.form.get("mensaje", "").strip()

        if not nombre or not email or not mensaje:
            flash("⚠️ Todos los campos son obligatorios.", "error")
            return redirect(url_for("contacto"))

        try:
            sql = text("""
            INSERT INTO contactos (nombresApellidos, correoElectronico, mensaje)
            VALUES (:nombre, :email, :mensaje)
            """)
            db.session.execute(sql, {"nombre": nombre, "email": email, "mensaje": mensaje})
            db.session.commit()

            flash("✅ Mensaje enviado correctamente.", "success")
            return redirect(url_for("contacto"))

        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error al enviar el mensaje: {str(e)}", "error")
            print("Error en la BD:", e)  # Debugging

    return render_template("contacto.html")



# Ruta para agregar libros a la BD
@app.route("/agregar_libro", methods=["GET", "POST"])
def agregar_libro():
    if request.method == "POST":
        titulo = request.form.get("titulo")
        imagen = request.form.get("imagen")  # Puede ser una URL o un archivo subido
        editor = request.form.get("editor")
        autor = request.form.get("autor")
        anio = request.form.get("anio")
        precio = request.form.get("precio")

        nuevo_libro = Libro(titulo=titulo, imagen=imagen, editor=editor, autor=autor, anio=anio, precio=precio)
        
        try:
            db.session.add(nuevo_libro)
            db.session.commit()
            flash("✅ Libro agregado con éxito", "success")
            return redirect(url_for("home"))
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error al agregar el libro: {str(e)}", "error")

    return render_template("agregar_libro.html")


@app.route("/reservar", methods=["GET"])
def reservar():
    libros = Libro.query.all()  # Obtener todos los libros
    reservas = Reserva.query.all()  # Obtener historial de reservas
    return render_template("reservar.html", libros=libros, reservas=reservas)


@app.route("/libro/<int:id>", methods=["GET"])
def obtener_libro(id):
    libro = Libro.query.get_or_404(id)
    return jsonify({
        "id": libro.id,
        "titulo": libro.titulo,
        "autor": libro.autor,
        "editor": libro.editor,
        "anio": libro.anio,
        "precio": libro.precio
    })

@app.route("/buscar_libro", methods=["GET"])
def buscar_libro():
    query = request.args.get("q", "")
    if not query:
        return jsonify([])

    libros = Libro.query.filter(
        (Libro.titulo.ilike(f"%{query}%")) |
        (Libro.autor.ilike(f"%{query}%")) |
        (Libro.editor.ilike(f"%{query}%"))
    ).all()

    return jsonify([
        {
            "id": libro.id,
            "titulo": libro.titulo,
            "autor": libro.autor
        }
        for libro in libros
    ])

@app.route("/reservar_libro", methods=["POST"])
def reservar_libro():
    data = request.json
    libro_id = data.get("id")

    libro = Libro.query.get_or_404(libro_id)
    reserva = Reserva(libro_id=libro.id, titulo=libro.titulo, autor=libro.autor)
    db.session.add(reserva)
    db.session.commit()

    return jsonify({"message": "Libro reservado con éxito"})

if __name__ == "__main__":
    app.run(debug=True)
