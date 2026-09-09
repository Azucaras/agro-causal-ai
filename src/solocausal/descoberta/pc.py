"""Algoritmo PC com conhecimento de fundo em camadas.

Implementado à mão em vez de usar `causal-learn` por dois motivos: a restrição
de camadas nos conjuntos separadores não é exposta pelas bibliotecas
disponíveis, e ter o código aberto aqui facilita explicar o método em banca.

Referências: Spirtes, Glymour & Scheines (2000) para o algoritmo; Meek (1995)
para as regras de propagação de orientação.
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from ..config import ALFA_PADRAO
from .conhecimento import Camadas
from .grafo import CPDAG, tem_ciclo
from .independencia import padronizar, testar


def estimar_cpdag(laudos: pd.DataFrame, variaveis: list[str], camadas: Camadas,
                  alfa: float = ALFA_PADRAO,
                  max_condicionantes: int = 3) -> CPDAG:
    """Estima a classe de equivalência de Markov a partir dos dados."""
    dados = padronizar(laudos[variaveis].to_numpy(dtype=float))
    p = len(variaveis)
    niveis = np.array([camadas.nivel(v) for v in variaveis])

    adjacentes = {i: set(range(p)) - {i} for i in range(p)}
    separadores: dict[tuple[int, int], tuple[int, ...]] = {}

    # --- fase 1: esqueleto -------------------------------------------------
    for tamanho in range(max_condicionantes + 1):
        a_remover: list[tuple[int, int]] = []
        for i in range(p):
            for j in adjacentes[i]:
                if j < i:
                    continue
                # A restrição de camadas entra aqui: o separador não pode
                # conter variáveis posteriores às duas sendo testadas.
                teto = max(niveis[i], niveis[j])
                candidatos = sorted(k for k in adjacentes[i] - {j}
                                    if niveis[k] <= teto)
                if len(candidatos) < tamanho:
                    continue
                for subconjunto in itertools.combinations(candidatos, tamanho):
                    independentes, _ = testar(dados, i, j, subconjunto, alfa)
                    if independentes:
                        a_remover.append((i, j))
                        separadores[(i, j)] = subconjunto
                        separadores[(j, i)] = subconjunto
                        break
        for i, j in a_remover:
            adjacentes[i].discard(j)
            adjacentes[j].discard(i)

    # --- fase 2: v-estruturas (i → k ← j) ----------------------------------
    dirigidas: set[tuple[int, int]] = set()
    for k in range(p):
        for i, j in itertools.combinations(sorted(adjacentes[k]), 2):
            if j in adjacentes[i]:
                continue  # i e j adjacentes: não é v-estrutura
            separador = separadores.get((i, j))
            if separador is not None and k not in separador:
                dirigidas.add((i, k))
                dirigidas.add((j, k))

    _propagar_meek(p, adjacentes, dirigidas)
    _aplicar_camadas(variaveis, camadas, dirigidas)
    _desfazer_ciclos(p, dirigidas)

    ambiguas = [
        (i, j)
        for i in range(p) for j in adjacentes[i]
        if i < j and (i, j) not in dirigidas and (j, i) not in dirigidas
    ]
    return CPDAG(variaveis=variaveis, dirigidas=dirigidas, ambiguas=ambiguas)


def _propagar_meek(p: int, adjacentes: dict[int, set[int]],
                   dirigidas: set[tuple[int, int]]) -> None:
    """Regras 1 e 2 de Meek, com guarda de aciclicidade a cada orientação."""

    def existe(a: int, b: int) -> bool:
        return (a, b) in dirigidas

    mudou = True
    while mudou:
        mudou = False
        for i in range(p):
            for j in adjacentes[i]:
                if existe(i, j) or existe(j, i):
                    continue
                # R1: k → i — j, com k e j não adjacentes  ⇒  i → j
                for k in range(p):
                    if (existe(k, i) and k != j and j not in adjacentes[k]
                            and not tem_ciclo(p, dirigidas | {(i, j)})):
                        dirigidas.add((i, j))
                        mudou = True
                        break
                if mudou:
                    break
                # R2: i → k → j  ⇒  i → j
                for k in range(p):
                    if (existe(i, k) and existe(k, j)
                            and not tem_ciclo(p, dirigidas | {(i, j)})):
                        dirigidas.add((i, j))
                        mudou = True
                        break
            if mudou:
                break


def _aplicar_camadas(variaveis: list[str], camadas: Camadas,
                     dirigidas: set[tuple[int, int]]) -> None:
    """Inverte ou remove orientações que violam a ordem declarada."""
    for aresta in list(dirigidas):
        origem, destino = aresta
        if camadas.permite(variaveis[origem], variaveis[destino]):
            continue
        dirigidas.discard(aresta)
        if camadas.permite(variaveis[destino], variaveis[origem]):
            dirigidas.add((destino, origem))


def _desfazer_ciclos(p: int, dirigidas: set[tuple[int, int]]) -> None:
    """Devolve arestas ao status de ambíguas até o grafo ficar acíclico.

    As regras de Meek combinadas com a inversão por camadas podem, em casos
    raros, fechar um ciclo. Perder uma orientação é melhor que abortar.
    """
    while tem_ciclo(p, dirigidas):
        for aresta in sorted(dirigidas):
            if not tem_ciclo(p, dirigidas - {aresta}):
                dirigidas.discard(aresta)
                break
        else:
            dirigidas.discard(sorted(dirigidas)[-1])
