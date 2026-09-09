"""Gerador de laudos sintéticos com mecanismo causal conhecido.

Serve para duas coisas: rodar o pipeline sem depender de dado real, e validar a
implementação — como o efeito verdadeiro é definido aqui, dá para conferir se o
estimador o recupera.

A estrutura reproduz a armadilha metodológica do problema real, e não um caso
fácil:

    argila ──► mo_base ──► ctc
                 │
                 ▼
    ph ──────► composto ──► mo_atual ──► enzima     (caminho mediado)
                 │                          ▲
                 └──────────────────────────┘       (efeito direto)

`mo_atual` é medida depois da aplicação. Ajustar por ela — o que qualquer
pipeline automático faz — bloqueia o caminho mediado e subestima o efeito. Só a
ordem temporal resolve, e ela não está nos dados.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..config import COEF_MO_ENZIMA, RESPOSTA_MO, SEMENTE


@dataclass
class Cenario:
    """Parâmetros do mecanismo gerador."""

    n: int = 900
    efeito_direto: float = 9.0
    ruido: float = 12.0
    semente: int = SEMENTE

    @property
    def efeito_total(self) -> float:
        """Efeito causal verdadeiro: direto + mediado por matéria orgânica."""
        return self.efeito_direto + COEF_MO_ENZIMA * RESPOSTA_MO


def simular_laudos(cenario: Cenario | None = None) -> tuple[pd.DataFrame, float]:
    """Gera laudos sintéticos e devolve (dados, efeito verdadeiro)."""
    c = cenario or Cenario()
    rng = np.random.default_rng(c.semente)
    n = c.n

    # textura: exógena, não é alterada por manejo em escala de safra
    argila = rng.normal(38, 13, n).clip(8, 78)
    areia = (100 - argila - rng.normal(18, 6, n).clip(3, 40)).clip(5, 88)

    # atributos de base, anteriores à intervenção
    ph = (5.4 + 0.010 * (argila - 38) + rng.normal(0, 0.55, n)).clip(3.9, 7.4)
    mo_base = (2.1 + 0.045 * argila + rng.normal(0, 0.7, n)).clip(0.4, 9.0)

    # a decisão do produtor é confundida: quem já tem solo melhor investe mais.
    # É isso que quebra a comparação ingênua de médias.
    logito = (0.85 * (mo_base - mo_base.mean())
              + 0.55 * (ph - 5.4)
              + rng.normal(0, 1.0, n))
    tratamento = rng.binomial(1, 1 / (1 + np.exp(-logito))).astype(float)

    # consequências da intervenção (tudo daqui para baixo é pós-tratamento)
    mo_atual = mo_base + RESPOSTA_MO * tratamento + rng.normal(0, 0.25, n)
    ctc = 2.5 + 0.085 * argila + 1.35 * mo_atual + rng.normal(0, 0.8, n)
    v_pct = (100 / (1 + np.exp(-(1.55 * (ph - 5.2) + rng.normal(0, 0.6, n))))
             ).clip(8, 92)
    p_mehlich = np.exp(rng.normal(2.2, 0.55, n) + 0.10 * tratamento).clip(1, 90)
    k_cmolc = (0.10 + 0.020 * ctc + 0.03 * tratamento
               + rng.normal(0, 0.05, n)).clip(0.02, 1.2)
    densidade = (1.62 - 0.052 * mo_atual - 0.0022 * argila
                 + rng.normal(0, 0.07, n)).clip(0.85, 1.75)
    resist = (2.9 - 0.85 * (mo_atual - mo_atual.mean()) / mo_atual.std()
              + rng.normal(0, 0.45, n)).clip(0.4, 5.5)

    beta = (18 + COEF_MO_ENZIMA * mo_atual + 6.0 * (ph - 5.2) + 0.16 * argila
            + c.efeito_direto * tratamento
            + rng.normal(0, c.ruido, n)).clip(5, None)
    aril = (10 + 6.5 * mo_atual + 9.5 * (ph - 5.2) + 0.09 * argila
            + 0.7 * c.efeito_direto * tratamento
            + rng.normal(0, c.ruido * 0.8, n)).clip(2, None)

    # o laudo da safra anterior: matéria orgânica medida ANTES da aplicação,
    # com erro de laboratório. É a coluna que decide se o efeito é
    # identificável ou não.
    mo_laudo_anterior = mo_base + rng.normal(0, 0.22, n)

    laudos = pd.DataFrame({
        "argila": argila, "areia": areia, "ph": ph,
        "mo_laudo_anterior": mo_laudo_anterior,
        "materia_organica": mo_atual, "ctc": ctc, "v_pct": v_pct,
        "p_mehlich": p_mehlich, "k_cmolc": k_cmolc,
        "densidade": densidade, "resist_penetracao": resist,
        "composto": tratamento,
        "beta_glicosidase": beta, "arilsulfatase": aril,
    })
    return laudos, c.efeito_total
