"""La web de HoraVerde.

Aqui solo esta la parte de la pagina. Los datos los pide carbon_api.py.
"""

from flask import Flask, render_template

import carbon_api

app = Flask(__name__)


@app.route("/")
def inicio():
    """La pagina principal: como esta la luz y a que hora conviene gastarla."""
    ahora = carbon_api.intensidad_actual()
    mezcla = carbon_api.mezcla_actual()
    horas = carbon_api.pronostico()
    mejor, peor = carbon_api.mejor_y_peor(horas)

    # Para dibujar las barras necesito saber cual es la mas alta de todas,
    # y asi calcular que altura le toca a cada una en tanto por ciento.
    tope = max(hora["gramos"] for hora in horas)
    for hora in horas:
        hora["alto"] = round(hora["gramos"] / tope * 100)
        hora["destacada"] = hora is mejor

    return render_template(
        "inicio.html",
        ahora=ahora,
        mezcla=mezcla,
        horas=horas,
        mejor=mejor,
        peor=peor,
        ahorro=peor["gramos"] - mejor["gramos"],
    )


if __name__ == "__main__":
    app.run(debug=True)
