"""Estudo de caso: laudos BioAS de uma fazenda em Minas Gerais, 2023.

Três manejos — convencional (C), policultivo recente (N) e policultivo
estabelecido (P) — em 3 parcelas cada, amostradas em quatro épocas do ano.

O objetivo deste módulo não é estimar o efeito do manejo. É documentar por
que ele NÃO é estimável com este desenho, quantificando a falha, e isolar o
que os dados de fato sustentam.

Duas checagens estruturam a análise:

1. Unidade experimental. São 36 linhas, mas 9 parcelas. Tratar cada coleta
   como independente é pseudorreplicação — o n para comparar manejos é 9.

2. Positividade. Estimar efeito causal exige que unidades com covariáveis
   parecidas apareçam em ambos os grupos. Se a distribuição de uma covariável
   não se sobrepõe entre grupos, o escore de propensão vai a 0 ou 1 e o efeito
   deixa de ser identificável — não por falta de amostra, mas por ausência de
   contrafactual. Ver Petersen et al. (2012) sobre violação de positividade.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

GRUPOS = {"C": "convencional", "N": "policultivo recente",
          "P": "policultivo estabelecido"}
ORDEM_CONVERSAO = {"C": 0, "N": 1, "P": 2}   # tempo desde a conversão


@dataclass
class Positividade:
    """Sobreposição da distribuição de uma covariável entre grupos."""

    covariavel: str
    faixas: dict[str, tuple[float, float]]
    separacoes: list[tuple[str, str]] = field(default_factory=list)

    @property
    def violada(self) -> bool:
        return bool(self.separacoes)


def carregar(caminho: str | Path) -> pd.DataFrame:
    laudos = pd.read_csv(caminho)
    laudos["parcela"] = laudos["grupo"] + laudos["rep"].astype(str)
    laudos["anos_conversao"] = laudos["grupo"].map(ORDEM_CONVERSAO)
    return laudos


def checar_positividade(laudos: pd.DataFrame,
                        covariaveis: list[str]) -> list[Positividade]:
    """Procura separação completa entre grupos em cada covariável."""
    resultados = []
    for covariavel in covariaveis:
        faixas = {g: (float(sub[covariavel].min()), float(sub[covariavel].max()))
                  for g, sub in laudos.groupby("grupo")}
        separacoes = [
            (a, b)
            for a, b in [("C", "N"), ("C", "P"), ("N", "P")]
            if a in faixas and b in faixas
            and (faixas[a][1] < faixas[b][0] or faixas[b][1] < faixas[a][0])
        ]
        resultados.append(Positividade(covariavel, faixas, separacoes))
    return resultados


def agregar_por_parcela(laudos: pd.DataFrame,
                        variaveis: list[str]) -> pd.DataFrame:
    """Colapsa as coletas para a unidade experimental correta."""
    return (laudos.groupby(["grupo", "parcela"])[variaveis]
            .mean().reset_index())


def estabilidade_sazonal(laudos: pd.DataFrame,
                         desfechos: tuple[str, ...] = ("beta", "aril")
                         ) -> pd.DataFrame:
    """Coeficiente de variação intraparcela ao longo do ano.

    Métrica contrastante com a média: cada parcela é seu próprio controle, o
    que a torna imune ao confundimento de nível entre grupos. Não identifica
    efeito causal, mas descreve um padrão que a comparação de médias não vê.
    """
    cv = (laudos.groupby(["grupo", "parcela"])[list(desfechos)]
          .agg(lambda serie: 100 * serie.std() / serie.mean())
          .reset_index())
    return cv


def tendencia_monotonica(cv: pd.DataFrame, desfecho: str) -> tuple[float, float]:
    """Correlação de Spearman entre tempo de conversão e variabilidade."""
    ordem = cv["grupo"].map(ORDEM_CONVERSAO)
    rho, p = stats.spearmanr(ordem, cv[desfecho])
    return float(rho), float(p)


def analisar_bioas(caminho: str | Path) -> dict:
    """Roda o estudo de caso completo e devolve um dicionário de resultados."""
    laudos = carregar(caminho)
    covariaveis = ["p_mehlich", "ctc", "v_pct", "argila", "ph", "mos"]

    positividade = checar_positividade(laudos, covariaveis)
    por_parcela = agregar_por_parcela(laudos, ["beta", "aril", *covariaveis])
    cv = estabilidade_sazonal(laudos)

    contrastes = {}
    for alvo in ("N", "P"):
        a = por_parcela.loc[por_parcela.grupo == alvo, "beta"]
        b = por_parcela.loc[por_parcela.grupo == "C", "beta"]
        t, p = stats.ttest_ind(a, b)
        contrastes[f"{alvo}_vs_C"] = {
            "diferenca": round(float(a.mean() - b.mean()), 2),
            "t": round(float(t), 2),
            "p": round(float(p), 4),
            "n": f"{len(a)} vs {len(b)}",
        }

    return {
        "n_linhas": len(laudos),
        "n_parcelas": int(laudos["parcela"].nunique()),
        "positividade": positividade,
        "por_parcela": por_parcela,
        "estabilidade": cv,
        "contrastes_ingenuos": contrastes,
        "tendencia_beta": tendencia_monotonica(cv, "beta"),
        "tendencia_aril": tendencia_monotonica(cv, "aril"),
    }
