from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from sqlalchemy import text 
from functools import wraps


from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}



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
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Definimos el modelo Usuario
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(100), unique=True, nullable=False)


# Modelo de Libros
class Libro(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(255), nullable=False)
    imagen = db.Column(db.String(255), nullable=False)  # URL o nombre del archivo
    editor = db.Column(db.String(255), nullable=False)
    autor = db.Column(db.String(255), nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    disponibilidad = db.Column(db.Integer, nullable=False)


class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    libro_id = db.Column(db.Integer, db.ForeignKey('libro.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    fecha_reserva = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    estado = db.Column(db.Enum('Pendiente', 'Aprobada', 'Rechazada'), default='Pendiente')
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



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


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
            session["usuario_id"] = usuario.id  
            session["usuario_nombre"] = usuario.nombre  
            session["usuario_rol"] = usuario.rol  
            flash("Inicio de sesión exitoso", "success")
            return redirect(url_for("home"))
        else:
            flash("Correo o contraseña incorrectos", "danger")
    
    return render_template("login.html")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:  # aquí el cambio
            flash("Debes iniciar sesión para acceder a esta página.", "error")
            return redirect(url_for('loginUsuario'))
        return f(*args, **kwargs)
    return decorated_function

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
@login_required
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
    session.clear()  
    flash("Has cerrado sesión", "info")
    return redirect(url_for("loginUsuario"))

@app.route("/home")
@login_required
def home():
    libros = Libro.query.limit(10).all()
    nombre_usuario = session.get("usuario_nombre")
    rol_usuario = session.get("usuario_rol")
    return render_template("home.html", libros=libros , nombre=nombre_usuario , rol=rol_usuario)



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


@app.route("/agregar_libro", methods=["GET", "POST"])
def agregar_libro():
    if request.method == "POST":
        titulo = request.form.get("titulo")
        editor = request.form.get("editor")
        autor = request.form.get("autor")
        anio = request.form.get("anio")
        precio = request.form.get("precio")
        disponibilidad = request.form.get("disponibilidad")

        imagen_file = request.files.get("imagen_file")

        if imagen_file and allowed_file(imagen_file.filename):
            filename = secure_filename(imagen_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagen_file.save(image_path)
            imagen_url = f"/{image_path}"  # Ruta accesible desde HTML

            nuevo_libro = Libro(
                titulo=titulo,
                imagen=imagen_url,
                editor=editor,
                autor=autor,
                anio=anio,
                precio=precio,
                disponibilidad=disponibilidad
            )

            try:
                db.session.add(nuevo_libro)
                db.session.commit()
                flash("✅ Libro agregado con éxito", "success")
                return redirect(url_for("home"))
            except Exception as e:
                db.session.rollback()
                flash(f"❌ Error al agregar el libro: {str(e)}", "error")
        else:
            flash("⚠️ Debes cargar una imagen válida (png, jpg, jpeg, gif).", "error")
            return redirect(url_for("agregar_libro"))

    # GET method
    return render_template("agregar_libro.html")



@app.route("/reservar", methods=["GET"])
def reservar():
    libros = Libro.query.all()  # Obtener todos los libros
    reservas = db.session.query(
        Reserva.id, 
        Libro.titulo, 
        Libro.autor, 
        Reserva.fecha_reserva,
        Reserva.estado

    ).join(Libro, Reserva.libro_id == Libro.id).all()
 
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


@app.route("/confirmar_reserva", methods=["POST"])
def confirmar_reserva():
    try:
        #data = request.form  # Usar form en lugar de json para enviar desde HTML
        data = request.get_json()
        libro_id = data.get("id")
        usuario_id ="1"
        print("📌 Datos recibidos:", data)  # Ver qué datos están llegando

        if not libro_id:
            return jsonify({"success": False, "message": "ID de libro no proporcionado"}), 400
            
        libro = Libro.query.get_or_404(libro_id)
        
        # Crear nueva reserva
        nueva_reserva = Reserva(
            libro_id=libro_id,
            usuario_id=usuario_id
        )
        
        db.session.add(nueva_reserva)
        db.session.commit()
  
        return jsonify({
            "success": True,
            "message": "Reserva confirmada exitosamente"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/reservaid/<int:id>')
def reservaid(id):
     # Buscar el libro en la base de datos
    libro = Libro.query.filter_by(id=id).first()  # Usa filter_by en vez de recorrer la lista
    if libro:
        return render_template('reservaid.html', libro=libro)
    return "Libro no encontrado", 404

@app.route("/cancelar_reserva/<int:id>")
def cancelar_reserva(id):
 
    flash("Reserva cancelada correctamente")
    return redirect(url_for("home"))

@app.route("/admin/reservas")
def admin_reservas():
    estado = request.args.get('estado')  # Puede ser Pendiente, Aprobada, Rechazada
    fecha_inicio = request.args.get('fecha_inicio')  # Formato: YYYY-MM-DD
    fecha_fin = request.args.get('fecha_fin')

    query = db.session.query(
        Reserva.id,
        Libro.titulo,
        Libro.autor,
        Reserva.fecha_reserva,
        Reserva.estado,
        Usuario.nombre.label("nombre_usuario")
    ).join(Libro, Reserva.libro_id == Libro.id
    ).join(Usuario, Reserva.usuario_id == Usuario.id)

    # Aplicar filtros si están presentes
    if estado:
        query = query.filter(Reserva.estado == estado)

    if fecha_inicio:
        query = query.filter(Reserva.fecha_reserva >= fecha_inicio)

    if fecha_fin:
        query = query.filter(Reserva.fecha_reserva <= fecha_fin)

    reservas_filtradas = query.all()

    return render_template(
        "admin/admin_reservas.html",
        reservas=reservas_filtradas,
        estado_seleccionado=estado,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )

@app.route("/admin/reserva/<int:reserva_id>/<accion>", methods=["POST"])
def procesar_reserva(reserva_id, accion):
    reserva = Reserva.query.get_or_404(reserva_id)
    
    if accion == "aprobar":
        reserva.estado = "Aprobada"
    elif accion == "rechazar":
        reserva.estado = "Rechazada"
    else:
        return jsonify({"message": "Acción no válida"}), 400

    db.session.commit()
    return jsonify({"message": f"Reserva {accion}da correctamente."})


@app.route('/tu_ruta_de_vista')
def ver_registros():
    estado = request.args.get('estado')
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')

    query = db.session.query(Libro)

    if estado:
        query = query.filter(Libro.estado == estado)
    if fecha_inicio:
        query = query.filter(Libro.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Libro.fecha <= fecha_fin)

    libros = query.all()
    return render_template('tu_template.html', libros=libros)



if __name__ == "__main__":
    app.run(debug=True)
