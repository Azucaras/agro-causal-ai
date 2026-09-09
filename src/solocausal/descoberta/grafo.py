"""Estruturas de grafo usadas pela descoberta causal."""

from __future__ import annotations

from dataclasses import dataclass, field

Aresta = tuple[int, int]


def tem_ciclo(n_nos: int, arestas: set[Aresta]) -> bool:
    """Detecta ciclo dirigido por busca em profundidade com marcação."""
    cor = [0] * n_nos
    saida: dict[int, list[int]] = {i: [] for i in range(n_nos)}
    for origem, destino in arestas:
        saida[origem].append(destino)

    def visitar(no: int) -> bool:
        cor[no] = 1
        for vizinho in saida[no]:
            if cor[vizinho] == 1:
                return True
            if cor[vizinho] == 0 and visitar(vizinho):
                return True
        cor[no] = 2
        return False

    return any(cor[i] == 0 and visitar(i) for i in range(n_nos))


@dataclass
class CPDAG:
    """Classe de equivalência de Markov estimada.

    `dirigidas` são as arestas cuja direção os dados determinam; `ambiguas` são
    as que ficam indefinidas. Cada aresta ambígua multiplica por dois o número
    de mundos causais compatíveis com os dados.
    """

    variaveis: list[str]
    dirigidas: set[Aresta] = field(default_factory=set)
    ambiguas: list[Aresta] = field(default_factory=list)

    @property
    def indice(self) -> dict[str, int]:
        return {nome: i for i, nome in enumerate(self.variaveis)}

    def nomes(self, arestas) -> list[tuple[str, str]]:
        return [(self.variaveis[a], self.variaveis[b]) for a, b in arestas]

    def vizinhos_de(self, variavel: str) -> list[str]:
        """Variáveis ligadas a esta por aresta dirigida, em qualquer sentido."""
        i = self.indice[variavel]
        ligadas = {b for a, b in self.dirigidas if a == i}
        ligadas |= {a for a, b in self.dirigidas if b == i}
        return sorted(self.variaveis[k] for k in ligadas)

    def ambiguas_tocando(self, variavel: str) -> list[tuple[str, str]]:
        """Arestas de direção indefinida que envolvem esta variável."""
        return [par for par in self.nomes(self.ambiguas) if variavel in par]


def pais(arestas: set[Aresta], no: int) -> list[int]:
    """Pais de um nó no DAG — o conjunto de ajuste pelo critério de backdoor."""
    return sorted({origem for origem, destino in arestas if destino == no})
