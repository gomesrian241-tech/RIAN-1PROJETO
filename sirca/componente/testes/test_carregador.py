# -*- coding: utf-8 -*-
"""Testes do carregador.

Os casos verificam a normalização de texto, datas e marcas de presença.
As expectativas originais do material da disciplina foram mantidas.

Execute a partir da raiz do repositorio:
    pytest componente/testes -v
"""

import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import carregador  # noqa: E402


def test_normalizar_texto_remove_espacos_e_padroniza_caixa():
    assert carregador.normalizar_texto("  Maria Jose da Silva ") == "MARIA JOSE DA SILVA"


def test_normalizar_texto_trata_vazio():
    assert carregador.normalizar_texto("") == ""


def test_normalizar_data_aceita_barra():
    assert carregador.normalizar_data("15/05/2025") == datetime.date(2025, 5, 15)


def test_normalizar_data_aceita_iso():
    assert carregador.normalizar_data("2025-07-21") == datetime.date(2025, 7, 21)


def test_normalizar_data_aceita_ano_de_dois_digitos():
    assert carregador.normalizar_data("10-04-25") == datetime.date(2025, 4, 10)


def test_normalizar_presenca_reduz_ao_dominio():
    for valor in ["P", "p", "X", "x", "1", "presente", "PRESENTE"]:
        assert carregador.normalizar_presenca(valor) == "presente"
    for valor in ["F", "f", "0", "falta", "FALTOU"]:
        assert carregador.normalizar_presenca(valor) == "falta"
    for valor in ["J", "justificada"]:
        assert carregador.normalizar_presenca(valor) == "justificada"
    for valor in ["", "-", None]:
        assert carregador.normalizar_presenca(valor) == "indefinido"
