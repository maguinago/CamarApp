# core/urls.py


"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('legislaturas/', views.legislaturas_view, name='legislaturas'),
    path('senado/', views.senado_view, name='senado'),
    path('comissoes/', views.comissoes_page, name='comissoes'),
    path('comissoes/<int:comissao_id>/', views.comissao_detail_page, name='comissao_detail'),
    path('votacoes/', views.votacoes_page, name='votacoes'),
    path('votacoes/<str:votacao_id>/', views.votacao_detail_page, name='votacao_page'),
    path('projetos/', views.projetos_page, name='projetos'),
    path('projetos/<int:projeto_id>/', views.projeto_detail_page, name='projeto_detail'),
    path('legislatura_atual/', views.composicao_atual, name='composicao_atual'),
    path('legislatura_atual/partidos/<str:sigla>/', views.partido_detail, name='partido_detail'),
    path('legislatura_atual/partidos/<str:sigla>/<int:deputado_id>/', views.deputado_detail, name='deputado_detail'),
    path('htmx/comissoes/<int:comissao_id>/', views.comissao_modal, name='comissao_modal'),
    path('htmx/votacoes/<str:votacao_id>/', views.votacao_detail, name='votacao_detail'),
    path('htmx/comissoes/<int:comissao_id>/votacoes/', views.comissao_votacoes, name='comissao_votacoes'),
    path('htmx/comissoes/<int:comissao_id>/eventos/', views.comissao_eventos, name='comissao_eventos'),
    path('htmx/projetos/<int:projeto_id>/', views.projeto_modal, name='projeto_modal'),
    path('htmx/projetos/<int:projeto_id>/tramitacoes/', views.projeto_tramitacoes, name='projeto_tramitacoes'),
    path('htmx/projetos/<int:projeto_id>/eventos/', views.projeto_eventos, name='projeto_eventos'),
    path('test/', views.test_view, name='test')
]
