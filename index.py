import requests
import json
import pprint

pp = pprint.PrettyPrinter()

deputado_id = 220555
url = 'https://dadosabertos.camara.leg.br/api/v2/deputados/220555'

api_url = "https://dadosabertos.camara.leg.br/api/v2/partidos"


def get_partido_map():
    response = requests.get('https://dadosabertos.camara.leg.br/api/v2/partidos?itens=100&ordem=ASC&ordenarPor=id')
    if response.status_code != 200:
        return {}

    partido_map = response.json()['dados']
    pp.pprint(partido_map)


get_partido_map()