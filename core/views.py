from datetime import date
import unicodedata

import requests
from django.core.cache import cache
from django.shortcuts import Http404, render
from django.views.decorators.http import require_GET

from .utils.get_partido_map import get_partido_map
from .utils.plot_generator import generate_congress_plot


CAMARA_API_URL = "https://dadosabertos.camara.leg.br/api/v2"
PAGE_SIZE = 5
LIST_PAGE_SIZE = 25
COMPOSICAO_PAGE_SIZE = 100
PARTY_COLORS = [
    "#10b981", "#38bdf8", "#f59e0b", "#ef4444", "#a78bfa", "#f472b6",
    "#22c55e", "#06b6d4", "#eab308", "#fb7185", "#8b5cf6", "#14b8a6",
    "#84cc16", "#f97316", "#3b82f6", "#d946ef", "#64748b", "#0f766e",
]
PARTY_COLOR_MAP = {
    "PL": "#1d4ed8",
    "PT": "#dc2626",
    "UNIAO": "#2563eb",
    "PP": "#0ea5e9",
    "PSD": "#f59e0b",
    "MDB": "#16a34a",
    "REPUBLICANOS": "#1e40af",
    "PDT": "#ef4444",
    "PSB": "#facc15",
    "PSOL": "#dc2626",
    "PCdoB": "#b91c1c",
    "PV": "#22c55e",
    "NOVO": "#f97316",
    "CIDADANIA": "#ec4899",
    "PODE": "#0f766e",
    "AVANTE": "#0ea5e9",
    "SOLIDARIEDADE": "#2563eb",
    "PRD": "#3b82f6",
    "REDE": "#16a34a",
}


def normalize_party_sigla(sigla):
    normalized = unicodedata.normalize("NFKD", sigla or "")
    return normalized.encode("ascii", "ignore").decode("ascii").upper()


def camara_get(path, params=None):
    response = requests.get(f"{CAMARA_API_URL}{path}", params=params, timeout=10)
    response.raise_for_status()
    return response.json().get("dados", [])


def camara_get_cached(path, params=None, cache_key=None, timeout=900):
    if cache_key:
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

    data = camara_get(path, params)

    if cache_key:
        cache.set(cache_key, data, timeout)
    return data


def camara_get_all(path, params=None, cache_key=None, timeout=900):
    if cache_key:
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

    items = []
    page = 1
    while True:
        page_params = {
            **(params or {}),
            "pagina": page,
            "itens": COMPOSICAO_PAGE_SIZE,
        }
        page_items = camara_get(path, page_params)
        items.extend(page_items)
        if len(page_items) < COMPOSICAO_PAGE_SIZE:
            break
        page += 1

    if cache_key:
        cache.set(cache_key, items, timeout)
    return items


def get_current_legislatura_id():
    cached_id = cache.get("camara_current_legislatura_id")
    if cached_id is not None:
        return cached_id

    legislaturas = camara_get(
        "/legislaturas",
        {"ordem": "DESC", "ordenarPor": "id", "pagina": 1, "itens": 1},
    )
    legislatura_id = legislaturas[0]["id"] if legislaturas else None
    cache.set("camara_current_legislatura_id", legislatura_id, 3600)
    return legislatura_id


def get_current_deputados(params=None, cache_key="camara_deputados_atuais"):
    return camara_get_all(
        "/deputados",
        {"ordem": "ASC", "ordenarPor": "nome", **(params or {})},
        cache_key,
        900,
    )


def format_brl(value):
    formatted = f"{float(value or 0):,.2f}"
    return "R$ " + formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def build_party_distribution(deputados):
    try:
        party_names = {
            partido.get("sigla"): partido.get("nome")
            for partido in camara_get_all(
                "/partidos",
                {"ordem": "ASC", "ordenarPor": "sigla"},
                "camara_partidos",
                3600,
            )
        }
    except requests.RequestException:
        party_names = {}

    counts = {}
    for deputado in deputados:
        sigla = deputado.get("siglaPartido") or "Sem partido"
        counts[sigla] = counts.get(sigla, 0) + 1

    parties = []
    for index, (sigla, seats) in enumerate(sorted(counts.items(), key=lambda item: (-item[1], item[0]))):
        color = get_party_color(sigla, PARTY_COLORS[index % len(PARTY_COLORS)])
        parties.append({
            "sigla": sigla,
            "nome": party_names.get(sigla, sigla),
            "seats": seats,
            "color": color,
        })

    waffle_seats = []
    for party in parties:
        for _ in range(party["seats"]):
            waffle_seats.append({
                "sigla": party["sigla"],
                "nome": party["nome"],
                "color": party["color"],
            })

    return parties, waffle_seats


def get_party_color(sigla, fallback="#10b981"):
    return PARTY_COLOR_MAP.get(normalize_party_sigla(sigla), fallback)


def attach_party_colors(deputados):
    for deputado in deputados:
        deputado["party_color"] = get_party_color(deputado.get("siglaPartido"))
    return deputados


def get_partido_by_sigla(sigla):
    partidos = camara_get_all(
        "/partidos",
        {"ordem": "ASC", "ordenarPor": "sigla"},
        "camara_partidos",
        3600,
    )
    normalized_sigla = normalize_party_sigla(sigla)
    return next(
        (
            partido for partido in partidos
            if normalize_party_sigla(partido.get("sigla")) == normalized_sigla
        ),
        None,
    )


def get_party_evolution(sigla):
    years = [1998, 2002, 2006, 2010, 2014, 2018, 2022, date.today().year]
    evolution = []
    for year in years:
        try:
            deputados = camara_get_all(
                "/deputados",
                {
                    "siglaPartido": sigla,
                    "dataInicio": f"{year}-02-01",
                    "dataFim": f"{year}-02-01",
                },
                f"camara_party_{sigla}_seats_{year}",
                86400,
            )
        except requests.RequestException:
            deputados = []
        evolution.append({"year": year, "seats": len(deputados)})
    max_seats = max([item["seats"] for item in evolution] or [1])
    for item in evolution:
        item["height"] = int((item["seats"] / max(max_seats, 1)) * 160)
    return evolution


def get_composicao_filters():
    legislatura_id = get_current_legislatura_id()
    partidos = camara_get_all(
        "/partidos",
        {"ordem": "ASC", "ordenarPor": "sigla"},
        "camara_partidos",
        3600,
    )
    ufs = camara_get_cached(
        "/referencias/deputados/siglaUF",
        cache_key="camara_ufs",
        timeout=86400,
    )
    blocos = camara_get_all(
        "/blocos",
        {"idLegislatura": legislatura_id},
        f"camara_blocos_{legislatura_id}",
        3600,
    )
    partidos = sorted(partidos, key=lambda partido: partido.get("sigla", ""))
    ufs = sorted(ufs, key=lambda uf: uf.get("sigla", ""))
    blocos = sorted(blocos, key=lambda bloco: bloco.get("nome", ""))
    return partidos, ufs, blocos, legislatura_id


def get_deputados_params(selected):
    params = {"ordem": "ASC", "ordenarPor": "nome"}
    if selected.get("nome"):
        params["nome"] = selected["nome"].strip()
    if selected.get("partido"):
        params["siglaPartido"] = selected["partido"]
    if selected.get("uf"):
        params["siglaUf"] = selected["uf"]
    if selected.get("sexo"):
        params["siglaSexo"] = selected["sexo"]
    return params


def filter_deputados_by_bloco(deputados, selected):
    bloco_id = selected.get("bloco", "")

    if bloco_id:
        partidos_bloco = camara_get_cached(
            f"/blocos/{bloco_id}/partidos",
            cache_key=f"camara_bloco_partidos_{bloco_id}",
            timeout=3600,
        )
        siglas_partidos = {partido.get("sigla") for partido in partidos_bloco}
        deputados = [
            deputado
            for deputado in deputados
            if deputado.get("siglaPartido") in siglas_partidos
        ]

    return deputados


def get_deputado_despesas(deputado_id, year):
    try:
        rows = camara_get_all(
            f"/deputados/{deputado_id}/despesas",
            {"ano": year, "ordem": "ASC", "ordenarPor": "mes"},
            f"camara_deputado_{deputado_id}_despesas_{year}",
            3600,
        )
    except requests.RequestException:
        rows = []

    total = sum(float(item.get("valorLiquido") or item.get("valorDocumento") or 0) for item in rows)
    by_type = {}
    for item in rows:
        tipo = item.get("tipoDespesa") or "Outras despesas"
        by_type[tipo] = by_type.get(tipo, 0) + float(item.get("valorLiquido") or item.get("valorDocumento") or 0)

    top_types = [
        {"tipo": tipo, "total": format_brl(total_value)}
        for tipo, total_value in sorted(by_type.items(), key=lambda item: item[1], reverse=True)[:3]
    ]
    return {
        "total": total,
        "total_display": format_brl(total),
        "count": len(rows),
        "top_types": top_types,
        "recent": rows[:5],
    }


def get_deputado_eventos(deputado_id, year):
    try:
        eventos = camara_get_all(
            f"/deputados/{deputado_id}/eventos",
            {
                "dataInicio": f"{year}-01-01",
                "dataFim": date.today().isoformat(),
                "ordem": "DESC",
                "ordenarPor": "dataHoraInicio",
            },
            f"camara_deputado_{deputado_id}_eventos_{year}",
            3600,
        )
    except requests.RequestException:
        eventos = []
    return {"count": len(eventos), "recent": eventos[:5]}


def get_deputado_votos_recentes(deputado_id):
    votos_encontrados = []
    try:
        votacoes = camara_get(
            "/votacoes",
            {"pagina": 1, "itens": 12, "ordem": "DESC", "ordenarPor": "dataHoraRegistro"},
        )
    except requests.RequestException:
        return votos_encontrados

    for votacao in votacoes:
        try:
            votos = camara_get(f"/votacoes/{votacao['id']}/votos")
        except requests.RequestException:
            continue

        for voto in votos:
            deputado_voto = voto.get("deputado_") or voto.get("deputado") or {}
            if deputado_voto.get("id") == deputado_id:
                votos_encontrados.append({
                    "id": votacao.get("id"),
                    "voto": voto.get("tipoVoto") or voto.get("voto") or "Registrado",
                    "data": votacao.get("data"),
                    "descricao": votacao.get("descricao"),
                    "siglaOrgao": votacao.get("siglaOrgao"),
                })
                break

        if len(votos_encontrados) >= 5:
            break

    return votos_encontrados


def get_deputado_emendas(deputado_id):
    try:
        proposicoes = camara_get_all(
            "/proposicoes",
            {"idDeputadoAutor": deputado_id, "ordem": "DESC", "ordenarPor": "ano"},
            f"camara_deputado_{deputado_id}_proposicoes_emendas",
            3600,
        )
    except requests.RequestException:
        proposicoes = []

    return [
        proposicao for proposicao in proposicoes
        if (proposicao.get("siglaTipo") or "").upper().startswith("EM")
    ][:8]


def home_view(request):
    deputados = get_current_deputados()
    parties, seats = build_party_distribution(deputados)
    party_lookup = {party["sigla"]: party for party in parties}
    for seat in seats:
        party = party_lookup.get(seat["sigla"], {})
        seat["count"] = party.get("seats", 0)
    return render(request, "home.html", {
        "parties": parties,
        "seats": seats,
        "total_seats": len(seats),
    })


def legislaturas_view(request):
    plot_html = generate_congress_plot()
    return render(request, "legislaturas.html", {"plot_html": plot_html})


def senado_view(request):
    return render(request, "senado.html")


def get_page_number(request):
    try:
        return max(int(request.GET.get("page", 1)), 1)
    except (TypeError, ValueError):
        return 1


def comissoes_page(request):
    page = get_page_number(request)
    try:
        comissoes = camara_get(
            "/orgaos",
            {"pagina": page, "itens": LIST_PAGE_SIZE},
        )
    except requests.RequestException:
        comissoes = []

    context = {
        "comissoes": comissoes,
        "next_page": page + 1,
        "has_more": len(comissoes) == LIST_PAGE_SIZE,
        "is_htmx": bool(request.headers.get("HX-Request")),
    }

    if request.headers.get("HX-Request"):
        return render(request, "partials/comissoes_cards.html", context)

    return render(request, "comissoes.html", context)


def comissao_detail_page(request, comissao_id):
    try:
        context = {
            "comissao": camara_get(f"/orgaos/{comissao_id}"),
            "membros": camara_get(f"/orgaos/{comissao_id}/membros"),
            "votacoes": camara_get(
                f"/orgaos/{comissao_id}/votacoes",
                {"pagina": 1, "itens": PAGE_SIZE},
            ),
            "eventos": camara_get(
                f"/orgaos/{comissao_id}/eventos",
                {"pagina": 1, "itens": PAGE_SIZE},
            ),
            "comissao_id": comissao_id,
            "next_page": 2,
        }
    except requests.RequestException:
        raise Http404("Comissao nao encontrada.")
    return render(request, "comissao_detail.html", context)


def votacoes_page(request):
    page = get_page_number(request)
    current_year = date.today().year
    data_inicio = request.GET.get("dataInicio") or f"{current_year}-01-01"
    data_fim = request.GET.get("dataFim") or date.today().isoformat()
    params = {
        "pagina": page,
        "itens": LIST_PAGE_SIZE,
        "dataInicio": data_inicio,
        "dataFim": data_fim,
        "ordem": "DESC",
        "ordenarPor": "dataHoraRegistro",
    }

    try:
        votacoes = camara_get("/votacoes", params)
    except requests.RequestException:
        votacoes = []

    context = {
        "votacoes": votacoes,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "next_page": page + 1,
        "has_more": len(votacoes) == LIST_PAGE_SIZE,
        "is_htmx": bool(request.headers.get("HX-Request")),
    }

    if request.headers.get("HX-Request"):
        return render(request, "partials/votacoes_cards.html", context)

    return render(request, "votacoes.html", context)


def votacao_detail_page(request, votacao_id):
    try:
        context = {
            "votacao": camara_get(f"/votacoes/{votacao_id}"),
            "orientacoes": camara_get(f"/votacoes/{votacao_id}/orientacoes"),
            "votos": camara_get(f"/votacoes/{votacao_id}/votos"),
        }
    except requests.RequestException:
        raise Http404("Votacao nao encontrada.")
    return render(request, "votacao_detail_page.html", context)


def projetos_page(request):
    page = get_page_number(request)
    current_year = date.today().year
    ano = request.GET.get("ano") or str(current_year)
    sigla_tipo = request.GET.get("siglaTipo", "")
    params = {
        "pagina": page,
        "itens": LIST_PAGE_SIZE,
        "ano": ano,
        "ordem": "DESC",
        "ordenarPor": "id",
    }
    if sigla_tipo:
        params["siglaTipo"] = sigla_tipo

    try:
        projetos = camara_get("/proposicoes", params)
    except requests.RequestException:
        projetos = []

    context = {
        "projetos": projetos,
        "ano": ano,
        "sigla_tipo": sigla_tipo,
        "next_page": page + 1,
        "has_more": len(projetos) == LIST_PAGE_SIZE,
        "is_htmx": bool(request.headers.get("HX-Request")),
    }

    if request.headers.get("HX-Request"):
        return render(request, "partials/projetos_cards.html", context)

    return render(request, "projetos.html", context)


def projeto_detail_page(request, projeto_id):
    try:
        context = {
            "projeto": camara_get(f"/proposicoes/{projeto_id}"),
            "autores": camara_get(f"/proposicoes/{projeto_id}/autores"),
            "tramitacoes": camara_get(f"/proposicoes/{projeto_id}/tramitacoes"),
            "votacoes": camara_get(f"/proposicoes/{projeto_id}/votacoes"),
            "projeto_id": projeto_id,
        }
    except requests.RequestException:
        raise Http404("Projeto nao encontrado.")
    return render(request, "projeto_detail_page.html", context)


def composicao_atual(request):
    selected = {
        "nome": request.GET.get("nome", ""),
        "partido": request.GET.get("partido", ""),
        "uf": request.GET.get("uf", ""),
        "sexo": request.GET.get("sexo", ""),
        "bloco": request.GET.get("bloco", ""),
    }

    partidos, ufs, blocos, legislatura_id = get_composicao_filters()
    deputados_params = get_deputados_params(selected)
    deputados_cache_key = "camara_deputados_atuais_" + "_".join(
        f"{key}-{value}" for key, value in sorted(deputados_params.items())
    )
    deputados = attach_party_colors(get_current_deputados(deputados_params, deputados_cache_key))
    deputados = filter_deputados_by_bloco(deputados, selected)

    context = {
        "deputados": deputados,
        "partidos": partidos,
        "ufs": ufs,
        "blocos": blocos,
        "selected": selected,
        "legislatura_id": legislatura_id,
    }

    if request.headers.get("HX-Request"):
        return render(request, "partials/deputados_grid.html", context)

    return render(request, "composicao_atual.html", context)


def partido_detail(request, sigla):
    partido_map = get_partido_map()
    normalized_sigla = normalize_party_sigla(sigla)
    partido_info = get_partido_by_sigla(sigla)
    partido_id = partido_map.get(sigla) or partido_map.get(normalized_sigla) or (partido_info or {}).get("id")

    if not partido_id and not partido_info:
        raise Http404("Partido nao encontrado")

    partido_info = partido_info or {"id": partido_id, "sigla": sigla}

    try:
        data_deputados = get_current_deputados({"siglaPartido": sigla}, f"camara_deputados_partido_{sigla}")
        context = {
            "partido": {
                "idPartido": partido_id,
                "sigla": sigla,
                "info": partido_info,
                "color": get_party_color(sigla),
            },
            "deputados": attach_party_colors(data_deputados),
            "evolution": get_party_evolution(sigla),
            "feature_suggestions": [
                "lideranças atuais do partido",
                "comparação com partidos do mesmo bloco",
                "mapa por UF dos deputados eleitos",
                "projetos mais recentes de autores do partido",
            ],
        }
    except requests.RequestException:
        context = {
            "partido": {
                "idPartido": partido_id,
                "sigla": sigla,
                "info": partido_info,
                "color": get_party_color(sigla),
            },
            "deputados": [],
            "evolution": [],
            "feature_suggestions": [],
        }

    return render(request, 'partido_detail.html', {'data': context})


def deputado_detail(request, sigla, deputado_id):
    sigla = sigla.upper()
    current_year = date.today().year

    try:
        deputado = camara_get(f"/deputados/{deputado_id}")
    except requests.RequestException as e:
        print("Erro ao buscar deputado:", e)
        raise Http404("Deputado nao encontrado.")

    if deputado.get('ultimoStatus', {}).get('siglaPartido', '').upper() != sigla:
        raise Http404("Deputado nao pertence a este partido.")

    try:
        comissoes = camara_get(f"/deputados/{deputado_id}/orgaos")
    except requests.RequestException as e:
        print("Erro ao buscar comissoes:", e)
        comissoes = []

    try:
        projetos = camara_get(
            "/proposicoes",
            {"idDeputadoAutor": deputado_id, "codTipo": [139, 140, 141]},
        )
    except requests.RequestException as e:
        print("Erro ao buscar projetos do deputado(a):", e)
        projetos = []

    sugestoes = [
        "Discursos em plenário",
        "Histórico de mandatos",
        "Profissões e ocupações declaradas",
        "Participação em frentes parlamentares",
    ]

    return render(request, 'deputado_detail.html', {
        'deputado': deputado,
        'sigla': sigla,
        'comissoes': comissoes,
        'projetos': projetos,
        'show_comissoes': bool(comissoes),
        'despesas': get_deputado_despesas(deputado_id, current_year),
        'eventos': get_deputado_eventos(deputado_id, current_year),
        'votos': get_deputado_votos_recentes(deputado_id),
        'emendas': get_deputado_emendas(deputado_id),
        'current_year': current_year,
        'sugestoes': sugestoes,
    })


def test_view(request):
    return render(request, 'test.html')


@require_GET
def comissao_modal(request, comissao_id):
    try:
        context = {
            "comissao": camara_get(f"/orgaos/{comissao_id}"),
            "membros": camara_get(f"/orgaos/{comissao_id}/membros"),
            "votacoes": camara_get(
                f"/orgaos/{comissao_id}/votacoes",
                {"pagina": 1, "itens": PAGE_SIZE},
            ),
            "eventos": camara_get(
                f"/orgaos/{comissao_id}/eventos",
                {"pagina": 1, "itens": PAGE_SIZE},
            ),
            "comissao_id": comissao_id,
            "next_page": 2,
        }
    except requests.RequestException:
        return render(request, "partials/error.html")

    return render(request, "partials/comissao_modal_content.html", context)


@require_GET
def votacao_detail(request, votacao_id):
    try:
        context = {
            "votacao": camara_get(f"/votacoes/{votacao_id}"),
            "orientacoes": camara_get(f"/votacoes/{votacao_id}/orientacoes"),
            "votos": camara_get(f"/votacoes/{votacao_id}/votos"),
        }
    except requests.RequestException:
        return render(request, "partials/error.html")

    return render(request, "partials/votacao_detail.html", context)


@require_GET
def comissao_votacoes(request, comissao_id):
    page = int(request.GET.get("page", 1))
    votacoes = camara_get(
        f"/orgaos/{comissao_id}/votacoes",
        {"pagina": page, "itens": PAGE_SIZE},
    )
    return render(
        request,
        "partials/comissao_votacoes.html",
        {
            "votacoes": votacoes,
            "comissao_id": comissao_id,
            "next_page": page + 1,
        },
    )


@require_GET
def comissao_eventos(request, comissao_id):
    page = int(request.GET.get("page", 1))
    eventos = camara_get(
        f"/orgaos/{comissao_id}/eventos",
        {"pagina": page, "itens": PAGE_SIZE},
    )
    return render(
        request,
        "partials/comissao_eventos.html",
        {
            "eventos": eventos,
            "comissao_id": comissao_id,
            "next_page": page + 1,
        },
    )


@require_GET
def projeto_modal(request, projeto_id):
    try:
        context = {
            "projeto": camara_get(f"/proposicoes/{projeto_id}"),
            "autores": camara_get(f"/proposicoes/{projeto_id}/autores"),
            "tramitacoes": camara_get(f"/proposicoes/{projeto_id}/tramitacoes"),
            "votacoes": camara_get(f"/proposicoes/{projeto_id}/votacoes"),
            "projeto_id": projeto_id,
        }
    except requests.RequestException:
        return render(request, "partials/error.html")

    return render(request, "partials/projeto_modal_content.html", context)


@require_GET
def projeto_tramitacoes(request, projeto_id):
    page = int(request.GET.get("page", 1))
    tramitacoes = camara_get(
        f"/proposicoes/{projeto_id}/tramitacoes",
        {"pagina": page, "itens": PAGE_SIZE},
    )
    return render(
        request,
        "partials/projeto_tramitacoes.html",
        {
            "tramitacoes": tramitacoes,
            "projeto_id": projeto_id,
            "next_page": page + 1,
        },
    )


@require_GET
def projeto_eventos(request, projeto_id):
    page = int(request.GET.get("page", 1))
    eventos = camara_get(
        f"/proposicoes/{projeto_id}/eventos",
        {"pagina": page, "itens": PAGE_SIZE},
    )
    return render(
        request,
        "partials/projeto_eventos.html",
        {
            "eventos": eventos,
            "projeto_id": projeto_id,
            "next_page": page + 1,
        },
    )
