import requests
import json
import pprint

pp = pprint.PrettyPrinter()

url = 'https://dadosabertos.camara.leg.br/api/v2/orgaos'
deputado_id = 160674

comissoes_resp = requests.get(url).json()

comissoes = []
cargos = []

for comissao in comissoes_resp['dados']:
    # if comissao['codTipoOrgao'] in [1, 2]:
    comissao_members_resp = requests.get(f"{comissao['uri']}/membros").json()
    for membro in comissao_members_resp['dados']:
        if str(deputado_id) in membro['uri']:
            if comissao not in comissoes:
                comissoes.append({comissao: membro})

print(comissoes)


        # pp.pprint(comissao_members_resp['dados'])


# pp.pprint(comissoes_resp)
