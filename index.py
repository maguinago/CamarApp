import requests
import json
import pprint

pp = pprint.PrettyPrinter()

# deputado_id = 220555  # DAIANA
# comissao_id = 537239
#
# # api_url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputado_id}/orgaos"
# # orgao_url = f"https://dadosabertos.camara.leg.br/api/v2/orgaos/{comissao_id}/membros"
#
# api_url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputado_id}/orgaos"
#
#
# response = requests.get(api_url).json()
#
# pp.pprint(response['dados'])

deputado_id = 220555  # DAIANA
comissao_id = 537239

# api_url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputado_id}/orgaos"
# orgao_url = f"https://dadosabertos.camara.leg.br/api/v2/orgaos/{comissao_id}/membros"

# api_url = f"https://dadosabertos.camara.leg.br/api/v2/orgaos/{comissao_id}/membros"
api_url = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes"
params = {
    "idDeputadoAutor": 220555,
    "codTipo": [139, 140, 141],
    "ordem": "DESC",
    "ordenarPor": "ano"
}

response = requests.get(api_url, params=params).json()
data = response['dados']

for projeto in data:
    proj_resp = requests.get(f"{projeto['uri']}/autores").json()
    autores = proj_resp['dados']
    print(f"{projeto['siglaTipo']} {projeto['numero']}/{projeto['ano']}")
    print(f"Ementa: {projeto['ementa']}")
    coautores = []
    for autor in autores:
        if autor['ordemAssinatura'] != 1:
            coautores.append(autor)
        else:
            print(f"Autor(a): {autor['nome']}")
    print(f"Co-autores: ")
    for aut in coautores:
        print(aut['nome'])
# pp.pprint(comissoes)
