import requests
import json
from django.core.cache import cache

api_url = "https://dadosabertos.camara.leg.br/api/v2/partidos"


def get_partido_map():
    partido_map = cache.get('partido_map')
    if not partido_map:
        response = requests.get('https://dadosabertos.camara.leg.br/api/v2/partidos?itens=100&ordem=ASC&ordenarPor=id')
        if response.status_code != 200:
            return {}

        parties = json.loads(response.text)['dados']
        partido_map = {party['sigla']: party['id'] for party in parties}
        cache.set('partido_map', partido_map, timeout=3600)  # cache for 1 hour
    return partido_map
