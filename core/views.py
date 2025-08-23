# core/views.py
import json
import requests
from django.core.cache import cache
from django.shortcuts import render, Http404
from .utils.plot_generator import generate_congress_plot
from .utils.get_partido_map import get_partido_map


def congress_chart_view(request):
    plot_html = generate_congress_plot()
    return render(request, 'home.html', {'plot_html': plot_html})


def partido_detail(request, sigla):
    global context
    partido_map = get_partido_map()

    # Workaround since context processors aren't in `request.context`
    # Better: pass `partido_map` into the view manually or store it globally

    if sigla not in partido_map:
        raise Http404("Partido não encontrado")

    partido_id = partido_map[sigla]

    # Fetch party details by ID
    try:
        response = requests.get(f"https://dadosabertos.camara.leg.br/api/v2/partidos/{partido_id}")
        data = response.json()["dados"]
        response_deputados = requests.get(f"https://dadosabertos.camara.leg.br/api/v2/deputados")
        data_deputados = response_deputados.json()["dados"]

        # Get deputados do partido
        context = {
            "partido": {
                "idPartido": partido_id,
                "sigla": sigla,
            },
            "deputados": [
            ]
        }

        for deputado in data_deputados:
            if str(partido_id) in deputado['uriPartido']:
                dep_dict = {
                    'id': deputado['id'],
                    'nome': deputado['nome'],
                    'foto': deputado['urlFoto'],
                }
                context['deputados'].append(dep_dict)

    except:
        data = {}

    return render(request, 'partido_detail.html', {'data': context})


def deputado_detail(request, sigla, deputado_id):
    global comissoes, projetos
    sigla = sigla.upper()

    # Fetch deputado info
    try:
        response = requests.get(f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputado_id}")
        response.raise_for_status()  # raises if status != 200
        deputado = response.json()["dados"]
    except Exception as e:
        print("Erro ao buscar deputado:", e)
        raise Http404("Deputado não encontrado.")

    # Validate party (optional)
    if deputado.get('ultimoStatus', {}).get('siglaPartido', '').upper() != sigla:
        raise Http404("Deputado não pertence a este partido.")

    # Initialize commissions list
    # Fetch comissions when loading page
    try:
        comissoes_resp = requests.get(
            f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputado_id}/orgaos").json()
        comissoes = comissoes_resp['dados']
    except Exception as e:
        print("Erro ao buscar comissões:", e)

    try:
        projetos_resp = requests.get(
            'https://dadosabertos.camara.leg.br/api/v2/proposicoes',
            params={"idDeputadoAutor": deputado_id}).json()
        projetos = projetos_resp['dados']
    except Exception as e:
        print("Erro ao buscar projetos do deputado(a):", e)


    # Return the page no matter what
    return render(request, 'deputado_detail.html', {
        'deputado': deputado,
        'sigla': sigla,
        'comissoes': comissoes,
        'projetos': projetos,
        'show_comissoes': bool(comissoes)
    })

def test_view(request):
    return render(request, 'test.html')
