# -*- coding: utf-8 -*-
"""Testes de busca e ordenacao. Comecam falhando, por design."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import busca  # noqa: E402


def test_busca_linear_encontra():
    assert busca.busca_linear([10, 20, 30, 40], 30) == 2


def test_busca_linear_nao_encontra():
    assert busca.busca_linear([10, 20, 30], 99) == -1


def test_busca_binaria_encontra():
    assert busca.busca_binaria([1, 3, 5, 7, 9, 11], 9) == 4


def test_busca_binaria_nao_encontra():
    assert busca.busca_binaria([1, 3, 5], 4) == -1


def test_ordenacao_por_selecao():
    assert busca.ordenacao_por_selecao([5, 2, 9, 1]) == [1, 2, 5, 9]


def test_ordenacao_por_insercao():
    assert busca.ordenacao_por_insercao([5, 2, 9, 1]) == [1, 2, 5, 9]


def test_ordenacao_preserva_quantidade():
    entrada = [3, 1, 4, 1, 5, 9, 2, 6]
    assert len(busca.ordenacao_por_selecao(list(entrada))) == len(entrada)
