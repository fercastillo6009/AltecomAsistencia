# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import os, json
import firebase_admin
from firebase_admin import credentials, firestore

# ------------------ INICIALIZACIÓN ------------------

app = Flask(__name__)

# 🔹 Cargar credenciales de Firebase desde variable de entorno
cred_data = json.loads(os.environ["FIREBASE_CREDENTIALS"])
cred = credentials.Certificate(cred_data)
firebase_admin.initialize_app(cred)
db = firestore.client()


# ------------------ FUNCIONES AUXILIARES ------------------

# 🔹 Obtener empleados dinámicamente desde Firestore
def obtener_empleados():
    empleados = {}
    usuarios_ref = db.collection("usuarios").get()
    for doc in usuarios_ref:
        data = doc.to_dict()
        nombre = data.get("nombre")
        if nombre:
            empleados[nombre] = doc.id  # Usa el ID del documento como UID
    return empleados


# 🔹 Generar rango de fechas
def fechas_entre(inicio, fin):
    fechas = []
    while inicio <= fin:
        fechas.append(inicio.strftime("%Y-%m-%d"))
        inicio += timedelta(days=1)
    return fechas


# 🔹 Contar asistencias, retardos y faltas
def resumen_empleado(uid, fechas):
    asistencias = retardos = faltas = 0
    for fecha in fechas:
        doc_ref = db.collection("asistencias").document(uid).collection("asistencias").document(fecha)
        doc = doc_ref.get()
        if doc.exists:
            estado = doc.to_dict().get("estado", "puntual")
            if estado == "retardo":
                retardos += 1
            else:
                asistencias += 1
        else:
            faltas += 1
    return asistencias, retardos, faltas


# ------------------ RUTAS (WEB) ------------------

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/resumen', methods=['POST'])
def resumen():
    fecha_inicio = datetime.strptime(request.form['inicio'], "%Y-%m-%d")
    fecha_fin = datetime.strptime(request.form['fin'], "%Y-%m-%d")
    fechas = fechas_entre(fecha_inicio, fecha_fin)

    empleados = obtener_empleados()  # 🔹 Se actualiza automáticamente desde Firestore

    resultados = []
    for nombre, uid in empleados.items():
        asistencias, retardos, faltas = resumen_empleado(uid, fechas)
        resultados.append({
            "nombre": nombre,
            "asistencias": asistencias,
            "retardos": retardos,
            "faltas": faltas
        })

    return render_template('resultado.html', datos=resultados,
                           inicio=request.form['inicio'], fin=request.form['fin'])


# ------------------ RUTA (API PARA ANDROID) ------------------

@app.route('/api/resumen', methods=['POST'])
def api_resumen():
    """
    Endpoint para app móvil.
    Espera un JSON con:
    {
      "inicio": "YYYY-MM-DD",
      "fin": "YYYY-MM-DD"
    }
    Retorna JSON con el resumen de todos los empleados.
    """
    data = request.get_json()
    if not data or "inicio" not in data or "fin" not in data:
        return jsonify({"error": "Parámetros 'inicio' y 'fin' requeridos"}), 400

    try:
        fecha_inicio = datetime.strptime(data["inicio"], "%Y-%m-%d")
        fecha_fin = datetime.strptime(data["fin"], "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido"}), 400

    fechas = fechas_entre(fecha_inicio, fecha_fin)
    empleados = obtener_empleados()  # 🔹 Se actualiza dinámicamente

    resultados = []
    for nombre, uid in empleados.items():
        asistencias, retardos, faltas = resumen_empleado(uid, fechas)
        resultados.append({
            "nombre": nombre,
            "asistencias": asistencias,
            "retardos": retardos,
            "faltas": faltas
        })

    return jsonify(resultados)


# ------------------ EJECUCIÓN ------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
