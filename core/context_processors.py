import requests

def partidos_list(request):
    try:
        response = requests.get("https://dadosabertos.camara.leg.br/api/v2/partidos?itens=100&ordem=ASC&ordenarPor=sigla")
        data = response.json()
        partidos = [item['sigla'] for item in data['dados']]

        partidos = []
        partido_map = {}

        for item in data["dados"]:
            sigla = item["sigla"].upper()
            id_partido = item["id"]
            partidos.append(sigla)
            partido_map[sigla] = id_partido

        short_parties = sorted([p for p in partidos if len(p) <= 6])
        long_parties = sorted([p for p in partidos if len(p) > 6])

    except Exception:
        short_parties = []
        long_parties = []
        partido_map = {}


    return {
        'short_parties': short_parties,
        'long_parties': long_parties,
        'partido_map': partido_map
    }