from flask_sqlalchemy import SQLAlchemy
import os

# Configuración de la base de datos
DB_USER = "root"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_NAME = "biblioteca2025"
# Inicializar SQLAlchemy sin importar models.py aquí

class Config:
    SECRET_KEY = os.urandom(24)  # Para sesiones y flash messages
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

db = SQLAlchemy()
