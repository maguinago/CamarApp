import requests
import json
import pprint

pp = pprint.PrettyPrinter()

url = 'https://dadosabertos.camara.leg.br/api/v2/deputados/'
deputado_id = 160674

comissoes_resp = requests.get(url).json()

comissoes = []
cargos = []
comissao_members_resp = requests.get(f"{url}{deputado_id}/orgaos").json()

pp.pprint(comissao_members_resp['dados'])


        # pp.pprint(comissao_members_resp['dados'])


# pp.pprint(comissoes_resp)
