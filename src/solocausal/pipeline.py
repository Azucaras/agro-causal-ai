"""Orquestração: laudos entram, intervalo causal sai.

O resultado é um objeto serializável — é o que a CLI imprime e o que a API
devolve como JSON. Nenhuma formatação acontece aqui.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .config import (ALFA_PADRAO, CAMADAS_PADRAO, DESFECHO_PADRAO,
                     TRATAMENTO_PADRAO)
from .dados.esquema import validar
from .descoberta import Camadas, CPDAG, enumerar, estimar_cpdag, pais
from .estimacao import Efeito, estimar, interpretar, valor_de_robustez

LIMITE_DAGS_AVALIADOS = 60


@dataclass
class Resultado:
    """Saída completa de uma análise."""

    tratamento: str
    desfecho: str
    n_amostras: int
    n_tratados: int

    diferenca_bruta: float
    efeito_ajuste_total: Efeito

    cpdag: CPDAG
    n_dags: int
    efeitos: list[Efeito] = field(default_factory=list)

    efeito_real: float | None = None

    @property
    def validos(self) -> list[Efeito]:
        return [e for e in self.efeitos if e.valido]

    @property
    def amplitude_estrutural(self) -> tuple[float, float]:
        """Menor e maior estimativa pontual entre os grafos admissíveis."""
        valores = [e.valor for e in self.validos]
        return (min(valores), max(valores)) if valores else (float("nan"),) * 2

    @property
    def intervalo_total(self) -> tuple[float, float]:
        """Incerteza estrutural somada à amostral.

        Reportar só a estrutural produz intervalo degenerado quando todos os
        grafos compartilham o mesmo conjunto de ajuste, o que é comum.
        """
        if not self.validos:
            return (float("nan"), float("nan"))
        return (min(e.ic95[0] for e in self.validos),
                max(e.ic95[1] for e in self.validos))

    @property
    def mediana(self) -> float:
        valores = [e.valor for e in self.validos]
        return float(np.median(valores)) if valores else float("nan")

    @property
    def sinal_estavel(self) -> bool:
        """O efeito mantém o mesmo sinal em todos os grafos plausíveis?"""
        valores = [e.valor for e in self.validos]
        if not valores:
            return False
        return all(v > 0 for v in valores) or all(v < 0 for v in valores)

    @property
    def robustez(self) -> float:
        if not self.validos:
            return float("nan")
        central = min(self.validos, key=lambda e: abs(e.valor - self.mediana))
        return valor_de_robustez(central.t, self.n_amostras - 5)

    @property
    def cobre_efeito_real(self) -> bool | None:
        if self.efeito_real is None:
            return None
        piso, teto = self.intervalo_total
        return bool(piso <= self.efeito_real <= teto)

    @property
    def identificavel(self) -> bool:
        """Leitura resumida: intervalo finito e de sinal estável."""
        piso, teto = self.intervalo_total
        return bool(np.isfinite(piso) and np.isfinite(teto) and self.sinal_estavel)

    def como_dicionario(self) -> dict:
        piso, teto = self.intervalo_total
        minimo, maximo = self.amplitude_estrutural
        return {
            "tratamento": self.tratamento,
            "desfecho": self.desfecho,
            "n_amostras": self.n_amostras,
            "n_tratados": self.n_tratados,
            "diferenca_bruta": round(self.diferenca_bruta, 4),
            "efeito_ajuste_total": self.efeito_ajuste_total.como_dicionario(),
            "n_dags": self.n_dags,
            "amplitude_estrutural": [round(minimo, 4), round(maximo, 4)],
            "intervalo_total": [round(piso, 4), round(teto, 4)],
            "mediana": round(self.mediana, 4),
            "sinal_estavel": self.sinal_estavel,
            "identificavel": self.identificavel,
            "robustez": round(self.robustez, 4),
            "leitura_robustez": interpretar(self.robustez),
            "efeito_real": self.efeito_real,
            "cobre_efeito_real": self.cobre_efeito_real,
            "arestas_dirigidas": self.cpdag.nomes(self.cpdag.dirigidas),
            "arestas_ambiguas": self.cpdag.nomes(self.cpdag.ambiguas),
            "ambiguas_no_tratamento": self.cpdag.ambiguas_tocando(self.tratamento),
            "efeitos": [e.como_dicionario() for e in self.validos],
        }


def analisar(laudos: pd.DataFrame,
             tratamento: str = TRATAMENTO_PADRAO,
             desfecho: str = DESFECHO_PADRAO,
             camadas: list[list[str]] | None = None,
             alfa: float = ALFA_PADRAO,
             ignorar: tuple[str, ...] = (),
             efeito_real: float | None = None) -> Resultado:
    """Executa o pipeline completo sobre um conjunto de laudos.

    `ignorar` permite rodar a mesma base sem determinadas colunas — é assim que
    se compara o ganho de identificação trazido por uma linha de base.
    """
    diagnostico = validar(laudos, tratamento, desfecho)
    if not diagnostico.ok:
        raise ValueError(str(diagnostico))

    ordem = Camadas(camadas or CAMADAS_PADRAO)
    variaveis = [v for v in ordem.variaveis()
                 if v in laudos.columns and v not in ignorar]
    ordem = ordem.filtrar(variaveis)

    y = laudos[desfecho].to_numpy(dtype=float)
    t = laudos[tratamento].to_numpy(dtype=float)

    tratados = t > 0
    diferenca_bruta = float(y[tratados].mean() - y[~tratados].mean())

    covariaveis = [v for v in variaveis if v not in (tratamento, desfecho)]
    ajuste_total = estimar(y, t, laudos[covariaveis].to_numpy(dtype=float),
                           tuple(covariaveis))

    cpdag = estimar_cpdag(laudos, variaveis, ordem, alfa=alfa)
    dags = enumerar(cpdag, ordem)
    indice = cpdag.indice

    efeitos: list[Efeito] = []
    for dag in dags[:LIMITE_DAGS_AVALIADOS]:
        nomes = tuple(variaveis[i] for i in pais(dag, indice[tratamento])
                      if variaveis[i] not in (tratamento, desfecho))
        matriz = (laudos[list(nomes)].to_numpy(dtype=float) if nomes
                  else np.zeros((len(laudos), 0)))
        efeitos.append(estimar(y, t, matriz, nomes))

    return Resultado(
        tratamento=tratamento, desfecho=desfecho,
        n_amostras=len(laudos), n_tratados=int(tratados.sum()),
        diferenca_bruta=diferenca_bruta, efeito_ajuste_total=ajuste_total,
        cpdag=cpdag, n_dags=len(dags), efeitos=efeitos, efeito_real=efeito_real,
    )
