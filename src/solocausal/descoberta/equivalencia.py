"""Enumeração dos DAGs membros de uma classe de equivalência.

O CPDAG não é um grafo, é um conjunto de grafos. Estimar o efeito em apenas um
deles e reportar o número como se fosse "o" efeito esconde a incerteza que
importa. Aqui geramos os membros para depois estimar em cada um.

O antecedente direto dessa abordagem é o método IDA (Maathuis, Kalisch &
Bühlmann, 2009).
"""

from __future__ import annotations

import itertools

import numpy as np

from ..config import SEMENTE
from .conhecimento import Camadas
from .grafo import CPDAG, Aresta, tem_ciclo

#: Acima disso o espaço de orientações fica grande demais para enumerar.
LIMITE_ENUMERACAO_EXATA = 18


def enumerar(cpdag: CPDAG, camadas: Camadas, limite: int = 200,
             semente: int = SEMENTE) -> list[set[Aresta]]:
    """Orienta as arestas ambíguas de todas as formas admissíveis.

    Mantém apenas os resultados acíclicos e compatíveis com as camadas. Se o
    espaço for grande demais, amostra em vez de enumerar — o intervalo vira
    aproximado, o que é preferível a não devolver nada.
    """
    n_ambiguas = len(cpdag.ambiguas)
    n_nos = len(cpdag.variaveis)

    if n_ambiguas > LIMITE_ENUMERACAO_EXATA:
        rng = np.random.default_rng(semente)
        combinacoes = [tuple(rng.integers(0, 2, n_ambiguas)) for _ in range(4000)]
    else:
        combinacoes = list(itertools.product([0, 1], repeat=n_ambiguas))

    dags: list[set[Aresta]] = []
    vistos: set[frozenset[Aresta]] = set()

    for combinacao in combinacoes:
        arestas = set(cpdag.dirigidas)
        admissivel = True
        for bit, (i, j) in zip(combinacao, cpdag.ambiguas):
            origem, destino = (i, j) if bit == 0 else (j, i)
            if not camadas.permite(cpdag.variaveis[origem],
                                   cpdag.variaveis[destino]):
                admissivel = False
                break
            arestas.add((origem, destino))

        if not admissivel or tem_ciclo(n_nos, arestas):
            continue

        chave = frozenset(arestas)
        if chave in vistos:
            continue
        vistos.add(chave)
        dags.append(arestas)

        if len(dags) >= limite:
            break

    return dags
