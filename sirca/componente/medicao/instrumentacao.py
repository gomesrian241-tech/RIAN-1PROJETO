# -*- coding: utf-8 -*-
"""Instrumentacao para medir desempenho. PRONTA - nao precisa implementar.

Use assim:

    from instrumentacao import medir

    resultado = medir(minha_funcao, argumento1, argumento2, repeticoes=7)
    print(resultado)
"""

import statistics
import time


def medir(funcao, *args, repeticoes=7, aquecimento=2, **kwargs):
    """Executa a funcao varias vezes e devolve estatisticas de tempo.

    As primeiras execucoes (aquecimento) sao descartadas: a primeira chamada
    costuma ser mais lenta por causa de cache e carregamento, e incluir esse
    tempo distorce a comparacao.
    """
    for _ in range(aquecimento):
        funcao(*args, **kwargs)

    tempos = []
    for _ in range(repeticoes):
        inicio = time.perf_counter()
        funcao(*args, **kwargs)
        tempos.append((time.perf_counter() - inicio) * 1000.0)

    return {
        "repeticoes": repeticoes,
        "media_ms": round(statistics.mean(tempos), 4),
        "mediana_ms": round(statistics.median(tempos), 4),
        "minimo_ms": round(min(tempos), 4),
        "maximo_ms": round(max(tempos), 4),
        "desvio_ms": round(statistics.pstdev(tempos), 4),
    }


def contar_operacoes(funcao):
    """Decorador que conta quantas vezes a funcao decorada foi chamada."""
    def envolvida(*args, **kwargs):
        envolvida.chamadas += 1
        return funcao(*args, **kwargs)
    envolvida.chamadas = 0
    envolvida.__name__ = funcao.__name__
    return envolvida
