"""Pide los datos de la red electrica a la API de Carbon Intensity.

Todo lo que tiene que ver con internet esta metido aqui, asi el resto del
proyecto solo tiene que llamar a estas funciones y no se entera de nada.
"""

from datetime import datetime, timezone

import requests

URL_BASE = "https://api.carbonintensity.org.uk"

# Si la pagina tarda mas de 10 segundos, mejor rendirse que quedarse colgado.
ESPERA_MAXIMA = 10

# La API contesta en ingles y yo quiero enseñarlo en español.
NOMBRES = {
    "wind": "viento",
    "solar": "sol",
    "nuclear": "nuclear",
    "gas": "gas",
    "coal": "carbon",
    "biomass": "biomasa",
    "hydro": "agua",
    "imports": "importada",
    "other": "otras",
}

# La API dice "low", "moderate" o "high". Lo paso a español.
NIVELES = {
    "very low": "muy limpia",
    "low": "limpia",
    "moderate": "normal",
    "high": "sucia",
    "very high": "muy sucia",
}

# El mismo nivel, pero en nombre de clase de CSS, para pintar los colores.
CLASES = {
    "very low": "muy-limpia",
    "low": "limpia",
    "moderate": "normal",
    "high": "sucia",
    "very high": "muy-sucia",
}


def _pedir(camino):
    """Le pide algo a la API y devuelve la respuesta convertida a diccionario.

    El guion bajo del principio quiere decir "esto es de uso interno",
    o sea que solo lo usan las otras funciones de este archivo.
    """
    respuesta = requests.get(
        URL_BASE + camino,
        headers={"Accept": "application/json"},
        timeout=ESPERA_MAXIMA,
    )
    respuesta.raise_for_status()
    return respuesta.json()


def _hora_bonita(texto):
    """Pasa '2026-09-24T18:30Z' a '18:30', ya en la hora de aqui."""
    momento = datetime.fromisoformat(texto.replace("Z", "+00:00"))
    return momento.astimezone().strftime("%H:%M")


def intensidad_actual():
    """Cuanto CO2 cuesta la luz ahora mismo.

    Devuelve un diccionario con los gramos por kWh y si eso es mucho o poco.
    """
    datos = _pedir("/intensity")
    ahora = datos["data"][0]

    # A veces el dato medido todavia no esta y viene vacio.
    # En ese caso uso el que habian pronosticado.
    medido = ahora["intensity"]["actual"]
    pronosticado = ahora["intensity"]["forecast"]
    indice = ahora["intensity"]["index"]

    return {
        "gramos": medido if medido is not None else pronosticado,
        "indice": indice,
        "nivel": NIVELES.get(indice, "no se sabe"),
        "clase": CLASES.get(indice, "normal"),
        "desde": ahora["from"],
        "hasta": ahora["to"],
    }


def mezcla_actual():
    """De donde viene la luz ahora mismo.

    Devuelve una lista de parejas (fuente, porcentaje), ordenada de la que
    mas manda a la que menos.
    """
    datos = _pedir("/generation")
    mezcla = datos["data"]["generationmix"]

    fuentes = []
    for fuente in mezcla:
        nombre = NOMBRES.get(fuente["fuel"], fuente["fuel"])
        fuentes.append((nombre, fuente["perc"]))

    fuentes.sort(key=lambda pareja: pareja[1], reverse=True)
    return fuentes


def pronostico():
    """Lo que va a pasar en las proximas 48 horas, hora a hora.

    La API contesta en tramos de media hora. Junto cada dos para tener una
    barra por hora, que si no la grafica queda demasiado apretada.
    """
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    datos = _pedir("/intensity/" + ahora + "/fw48h")

    tramos = []
    for tramo in datos["data"]:
        gramos = tramo["intensity"]["forecast"]
        if gramos is not None:
            tramos.append((tramo["from"], gramos, tramo["intensity"]["index"]))

    horas = []
    for i in range(0, len(tramos) - 1, 2):
        cuando, gramos_a, indice = tramos[i]
        gramos_b = tramos[i + 1][1]
        horas.append({
            "hora": _hora_bonita(cuando),
            "gramos": round((gramos_a + gramos_b) / 2),
            "clase": CLASES.get(indice, "normal"),
        })

    return horas


def mejor_y_peor(horas, cuantas=24):
    """Busca la mejor y la peor hora de las proximas 24.

    No miro las 48 enteras porque de nada sirve decirte "pon la lavadora
    pasado manana": para entonces ya la habras puesto.
    """
    proximas = horas[:cuantas]
    mejor = min(proximas, key=lambda hora: hora["gramos"])
    peor = max(proximas, key=lambda hora: hora["gramos"])
    return mejor, peor


# Esto solo se ejecuta si lanzo este archivo directamente.
# Si lo importa otro archivo, no pasa nada. Sirve para probar.
if __name__ == "__main__":
    ahora = intensidad_actual()
    print("La luz esta a", ahora["gramos"], "gramos de CO2 por kWh")
    print("O sea que la luz esta", ahora["nivel"])
    print()

    print("Ahora mismo viene de:")
    for nombre, porcentaje in mezcla_actual():
        if porcentaje > 0:
            print("  ", nombre, "->", porcentaje, "%")
    print()

    horas = pronostico()
    mejor, peor = mejor_y_peor(horas)
    print("La mejor hora es a las", mejor["hora"], "con", mejor["gramos"], "gramos")
    print("La peor hora es a las", peor["hora"], "con", peor["gramos"], "gramos")
    print("Diferencia:", peor["gramos"] - mejor["gramos"], "gramos por kWh")
