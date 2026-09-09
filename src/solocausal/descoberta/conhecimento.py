"""Conhecimento de fundo em camadas (tiered background knowledge).

Referências: Bang & Didelez (2023); Andrews, Spirtes & Cooper (2020).

Declara-se uma ordem parcial entre grupos de variáveis. Duas consequências, e
a segunda costuma passar despercebida:

1. orientação — uma aresta entre camadas diferentes só pode apontar para a
   camada posterior;
2. separação — ao testar se duas variáveis são independentes, o conjunto
   condicionante não pode conter variáveis de camada posterior a ambas.

Sem (2), o algoritmo condiciona em um colisor a jusante e apaga uma aresta
verdadeira por cancelamento de caminhos. Isso não é hipotético: aconteceu na
primeira versão deste código, e a aresta que sumia era justamente a que ligava
a linha de base ao tratamento.
"""

from __future__ import annotations


class Camadas:
    """Ordem causal parcial entre variáveis."""

    def __init__(self, camadas: list[list[str]],
                 proibidas: list[tuple[str, str]] | None = None):
        self.camadas = camadas
        self._nivel = {var: i for i, grupo in enumerate(camadas) for var in grupo}
        self.proibidas = set(proibidas or [])

    def nivel(self, variavel: str) -> int:
        """Camada da variável; variáveis desconhecidas caem na primeira."""
        return self._nivel.get(variavel, 0)

    def permite(self, origem: str, destino: str) -> bool:
        """A aresta origem → destino é admissível?"""
        if (origem, destino) in self.proibidas:
            return False
        return self.nivel(origem) <= self.nivel(destino)

    def filtrar(self, variaveis: list[str]) -> "Camadas":
        """Nova instância restrita às variáveis presentes."""
        presentes = set(variaveis)
        camadas = [[v for v in grupo if v in presentes] for grupo in self.camadas]
        return Camadas([g for g in camadas if g], list(self.proibidas))

    def variaveis(self) -> list[str]:
        """Todas as variáveis declaradas, em ordem de camada."""
        return [v for grupo in self.camadas for v in grupo]
