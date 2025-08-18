# core/utils/plot_generator.py

import requests
import json
import pandas as pd
import plotly.express as px
import plotly.io as pio
import dash_bootstrap_templates

api_url = "https://dadosabertos.camara.leg.br/api/v2/"

years = [1998, 2002, 2006, 2010]


def generate_congress_plot():

    data_series = {
        'ano': [],
        'idDeputado': [],
        'nomeDeputado': [],
        'partidoDeputado': []

    }

    for year in years:
        params = {
            'dataInicio': f'{year+1}-02-01',
            'dataFim': f'{year+1}-02-01',
        }
        response = requests.get(api_url + "/deputados", params=params)
        data = json.loads(response.text)['dados']

        for i in data:
            idDeputado = i['id']
            nomeDeputado = i['nome']
            partidoDeputado = i['siglaPartido']
            data_series['ano'].append(year)
            data_series['idDeputado'].append(idDeputado)
            data_series['nomeDeputado'].append(nomeDeputado)
            data_series['partidoDeputado'].append(partidoDeputado)

    df = pd.DataFrame.from_dict(data_series)
    df_grouped = df.groupby(['ano', 'partidoDeputado'], as_index=False)['idDeputado'].nunique()
    df_grouped.rename(columns={'idDeputado': 'Deputados'}, inplace=True)

    all_years = df_grouped['ano'].unique()
    all_parties = df_grouped['partidoDeputado'].unique()

    full_index = pd.MultiIndex.from_product([all_years, all_parties], names=['Ano', 'Partido'])

    df_full = df_grouped.set_index(['ano', 'partidoDeputado']).reindex(full_index, fill_value=0).reset_index()

    # Step 2: Determine total deputies per party (to order and color consistently)
    total_deputados = df_full.groupby('Partido')['Deputados'].sum()
    partido_order = total_deputados.sort_values(ascending=False).index.tolist()

    # Generate consistent colors for each party
    colors = px.colors.qualitative.Dark24 + px.colors.qualitative.Pastel  # more variety
    color_map = {partido: colors[i % len(colors)] for i, partido in enumerate(partido_order)}

    # Create animated bar chart
    fig = px.bar(
        df_full,
        x='Partido',
        y='Deputados',
        color='Partido',
        animation_frame='Ano',
        category_orders={'Partido': partido_order},
        color_discrete_map=color_map,
        labels={'Partido': 'Partido', 'Deputados': 'Número de Deputados'},
        title='Composição da Câmara dos Deputados por Partido e Ano',
    )

    fig.update_layout(
        xaxis_title='Partido',
        yaxis_title='Número de Deputados',
        xaxis_tickangle=-45,
        showlegend=False,
        paper_bgcolor="#343A40",
        plot_bgcolor="rgba(60, 132, 105, 0.1)",
        font=dict(
            color="gray"
        ),
        title=dict(
            font=dict(
                color="rgb(211, 211, 211)",
                size=32,
                weight=900,
            )
        ),
        title_x=0.5,
    )


    return pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
