# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
from datetime import datetime, timedelta
import os, json
import firebase_admin
from firebase_admin import credentials, firestore

# Inicializar Flask
app = Flask(__name__)

# 🔹 Cargar credenciales de Firebase desde variable de entorno
# Render permite definir variables de entorno en Settings → Environment
cred_data = json.loads(os.environ["FIREBASE_CREDENTIALS"])
cred = credentials.Certificate(cred_data)
firebase_admin.initialize_app(cred)
db = firestore.client()

# 🔹 Diccionario de empleados (nombre -> UID)
empleados = {
    "Edson Fernando Herrera Castillo": "kvK4IZNfpGRpKDiwlRgl7JdasNu2",
    "Mauro Mauricio Castañeda": "rOr6WiZuK7QE0ac067EiccvGBWu2",
    "Luis Luisin Carrillo": "rfE9ZoOo69guyH2PU3JGRtT5A2h2"
}

# 🔹 Función para generar rango de fechas
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

# 🔹 Rutas
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/resumen', methods=['POST'])
def resumen():
    fecha_inicio = datetime.strptime(request.form['inicio'], "%Y-%m-%d")
    fecha_fin = datetime.strptime(request.form['fin'], "%Y-%m-%d")
    fechas = fechas_entre(fecha_inicio, fecha_fin)

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

# 🔹 Ejecutar localmente
if __name__ == '__main__':
    # El puerto 5000 es default, Render define PORT automáticamente
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
