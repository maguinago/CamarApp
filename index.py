import requests
import json
import pprint

pp = pprint.PrettyPrinter()

deputado_id = 220555  # DAIANA
comissao_id = 537239

api_url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputado_id}/orgaos"
orgao_url = f"https://dadosabertos.camara.leg.br/api/v2/orgaos/{comissao_id}/membros"
response = requests.get(orgao_url).json()

pp.pprint(response['dados'])