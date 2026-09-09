"""Esquema esperado do CSV de laudos e validação de entrada."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

COLUNAS_QUIMICAS = ["ph", "materia_organica", "p_mehlich", "k_cmolc",
                    "ctc", "v_pct"]
COLUNAS_FISICAS = ["argila", "areia", "densidade", "resist_penetracao"]
COLUNAS_BIOLOGICAS = ["beta_glicosidase", "arilsulfatase"]

DESCRICAO_ESQUEMA = """\
Uma linha por amostra de solo (talhão × data de coleta).

  QUÍMICO    ph, materia_organica, p_mehlich, k_cmolc, ctc, v_pct
  FÍSICO     argila, areia, densidade, resist_penetracao
  BIOLÓGICO  beta_glicosidase, arilsulfatase  (BioAS, µg p-nitrofenol/g/h)
  MANEJO     composto  — 0/1 ou dose em t/ha (a variável de tratamento)

Opcional, e é o que mais aumenta o poder de identificação:

  mo_laudo_anterior  — matéria orgânica medida ANTES da intervenção

Sem uma medida de linha de base, os atributos do laudo atual são ambíguos
entre confundidor e mediador, e o intervalo causal fica largo demais para
sustentar recomendação.

Onde obter dados reais: laboratórios da Rede Embrapa BioAS, cooperativas com
histórico de laudos por talhão, ensaios de longa duração publicados.
"""


@dataclass
class Diagnostico:
    """Resultado da checagem de um DataFrame contra o esquema."""

    ok: bool
    faltando: list[str]
    avisos: list[str]

    def __str__(self) -> str:
        if self.ok and not self.avisos:
            return "Esquema válido."
        partes = []
        if self.faltando:
            partes.append("Colunas obrigatórias ausentes: "
                          + ", ".join(self.faltando))
        partes.extend(self.avisos)
        return "\n".join(partes)


def validar(laudos: pd.DataFrame, tratamento: str, desfecho: str) -> Diagnostico:
    """Confere se o DataFrame tem o mínimo para rodar o pipeline."""
    faltando = [c for c in (tratamento, desfecho) if c not in laudos.columns]
    avisos: list[str] = []

    if not faltando:
        if laudos[tratamento].nunique() < 2:
            avisos.append(
                f"'{tratamento}' não varia: sem contraste não há efeito a estimar.")
        n_tratados = int((laudos[tratamento] > 0).sum())
        if min(n_tratados, len(laudos) - n_tratados) < 30:
            avisos.append(
                "Menos de 30 amostras em um dos grupos — estimativa instável.")

    covariaveis = [c for c in COLUNAS_QUIMICAS + COLUNAS_FISICAS
                   if c in laudos.columns]
    if len(covariaveis) < 3:
        avisos.append(
            "Poucas covariáveis de laudo: o ajuste por confundimento fica fraco.")

    if "mo_laudo_anterior" not in laudos.columns:
        avisos.append(
            "Sem coluna de linha de base (mo_laudo_anterior). O efeito "
            "provavelmente não será identificável — veja docs/metodo.md.")

    return Diagnostico(ok=not faltando, faltando=faltando, avisos=avisos)
