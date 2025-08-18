import requests
import json
import pprint
import dash.exceptions
from dash import Dash, html, dash_table, dcc, Input, Output, State, callback
from dash.dash_table.Format import Format, Scheme, Symbol
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

pp = pprint.PrettyPrinter(indent=4)

idDeputado = 220639  # Boulos

api_url = f'https://dadosabertos.camara.leg.br/api/v2/'

headers = {'Content-Type': 'application/json'}

params = {
}

response_personal_data = requests.get(f'{api_url}deputados/{idDeputado}', params=params, headers=headers)

data = json.loads(response_personal_data.text)['dados']
nome = data['nomeCivil'].title()
partido = data['ultimoStatus']['siglaPartido']

uf = data['ultimoStatus']['siglaUf']


print(f"Nome: {nome}\n"
      f"Partido: {partido} - {uf}\n"
      f"Projetos:\n"
      f""
      )

params_projetos = {
    'idDeputadoAutor': idDeputado,
    'ordem': 'desc'
}
response_projetos = requests.get(f'{api_url}proposicoes', params=params_projetos, headers=headers)
projetos = json.loads(response_projetos.text)['dados']



# pp.pprint(projetos)

count = 1
for projeto in projetos:
    print(f"{count}. Projeto nº: {projeto['id']}"
          f"\nAssunto: {projeto['ementa']}")
    count += 1
#
# # # Real code:
#
#
# data_series = {
#     'ano': [],
#     'idDeputado': [],
#     'nomeDeputado': [],
#     'partidoDeputado': []
#
# }
# years = [1999, 2003, 2007, 2011]
#
# for year in years:
#     params = {
#         'dataInicio': f'{year}-02-01',
#         'dataFim': f'{year}-02-01',
#     }
#     response = requests.get(api_url + "/deputados", params=params)
#     data = json.loads(response.text)['dados']
#
#     for i in data:
#         idDeputado = i['id']
#         nomeDeputado = i['nome']
#         partidoDeputado = i['siglaPartido']
#         data_series['ano'].append(year)
#         data_series['idDeputado'].append(idDeputado)
#         data_series['nomeDeputado'].append(nomeDeputado)
#         data_series['partidoDeputado'].append(partidoDeputado)
#
# # # Save locally for writing code:
# # with open('temporal_series.json', 'w') as f:
# #     json.dump(data_series, f, indent=2)
#
# df = pd.DataFrame.from_dict(data_series)
# df_grouped = df.groupby(['ano', 'partidoDeputado'], as_index=False)['idDeputado'].nunique()
# df_grouped.rename(columns={'idDeputado': 'Deputados'}, inplace=True)
#
# all_years = df_grouped['ano'].unique()
# all_parties = df_grouped['partidoDeputado'].unique()
#
# full_index = pd.MultiIndex.from_product([all_years, all_parties], names=['Ano', 'Partido'])
#
# df_full = df_grouped.set_index(['ano', 'partidoDeputado']).reindex(full_index, fill_value=0).reset_index()
#
# # Step 2: Determine total deputies per party (to order and color consistently)
# total_deputados = df_full.groupby('Partido')['Deputados'].sum()
# partido_order = total_deputados.sort_values(ascending=False).index.tolist()
#
# # Generate consistent colors for each party
# colors = px.colors.qualitative.Dark24 + px.colors.qualitative.Pastel  # more variety
# color_map = {partido: colors[i % len(colors)] for i, partido in enumerate(partido_order)}
#
# # Create animated bar chart
# fig = px.bar(
#     df_full,
#     x='Partido',
#     y='Deputados',
#     color='Partido',
#     animation_frame='Ano',
#     category_orders={'Partido': partido_order},
#     color_discrete_map=color_map,
#     labels={'Partido': 'Partido', 'Deputados': 'Número de Deputados'},
#     title='Composição da Câmara dos Deputados por Partido e Ano'
# )
#
# fig.update_layout(
#     xaxis_title='Partido',
#     yaxis_title='Número de Deputados',
#     xaxis_tickangle=-45,
#     showlegend=False
# )
#
# fig.show()
#
# print(df_full)
#
# # ppy = duckdb.sql(
# #     "SELECT partidoDeputado as Partido, ano as Ano, count(DISTINCT(idDeputado)) as Deputados FROM df GROUP BY Ano, "
# #     "Partido"
# # )
# #
# # fig = px.bar(
# #     ppy,
# #     x='Ano',
# #     y='Deputados',
# #     color='Partido',
# #     height=1000
# # )
# # fig.show()
#
# # for year in years:
# #     params = {
# #         'dataInicio': f'{year}-02-01',
# #         'dataFim': f'{year}-02-01',
# #     }
# #     response = requests.get(api_url + "/deputados", params=params)
# #     data = json.loads(response.text)['dados']
# #     if year not in data_series.keys():
# #         data_series[year] = {}
# #     for i in data:
# #         idDeputado = i['id']
# #         nomeDeputado = i['nome']
# #         partidoDeputado = i['siglaPartido']
# #         if partidoDeputado not in data_series[year]:
# #             data_series[year][partidoDeputado] = {}
# #         data_series[year][partidoDeputado][idDeputado] = i
#
# # with open('mock_data.json', 'w') as f:
# #     json.dump(data_series, f, indent=2)
#
# #
# # with open('mock_data.json', 'r') as f:
# #     mock_series = json.load(f)
# # data = mock_series
# #
# #
# # df = pd.DataFrame.from_dict(data)
# #
# # column_names = ['party', 'congress_person', 'year', 'data']
# # df.columns = column_names
