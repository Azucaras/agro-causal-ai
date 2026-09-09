"""Gerador de laudos sintéticos calibrado pelos dados reais da fazenda.

Diferente de `simulacao.py`, que usa um cenário genérico, este módulo replica
as distribuições observadas nos 36 laudos BioAS de 2023 — médias, dispersão,
componente sazonal e a razão entre variância dentro e entre parcelas.

A razão de existir: nos dados reais o efeito do manejo não é identificável,
por dois motivos independentes. Aqui os dois viram parâmetros, o que permite
testar o pipeline sob cada patologia isoladamente:

    acoplamento_fosforo  1.0 reproduz a fazenda (fósforo separa os grupos por
                         completo, positividade violada); 0.0 desacopla a
                         adubação do manejo e restaura a sobreposição.

    linha_de_base        se True, inclui a atividade enzimática medida antes
                         da conversão — a coluna que os dados reais não têm.

Rodar o pipeline variando esses dois parâmetros mostra, separadamente, quanto
cada problema custa em identificação.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..config import SEMENTE

#: Efeito sazonal médio observado em 2023 (desvio da média anual, beta).
SAZONALIDADE = {"03": 10.5, "06": -27.4, "09": 0.9, "12": 16.0}

#: Camadas causais para os laudos BioAS. A conversão para policultivo é a
#: intervenção; tudo abaixo dela é posterior no tempo.
CAMADAS_BIOAS: list[list[str]] = [
    ["argila", "areia"],
    ["ph", "beta_linha_de_base"],
    ["anos_policultivo"],
    ["mos", "ctc", "h_al", "v_pct", "p_mehlich"],
    ["beta", "aril"],
]


@dataclass
class CenarioBioAS:
    """Parâmetros do gerador, calibrados pelos laudos de 2023."""

    n_parcelas: int = 60
    coletas: tuple[str, ...] = ("03", "06", "09", "12")

    # efeito causal verdadeiro, por ano de policultivo (termo médio)
    efeito_por_ano: float = 3.2

    # --- heterogeneidade do efeito -------------------------------------
    # Sem isto o efeito é constante e não há o que prescrever: a resposta
    # ótima seria "converter todo mundo". A prescrição só faz sentido se o
    # retorno depender das condições do talhão.
    #
    # Dois modificadores, ambos com leitura agronômica:
    #   pH ácido      -> mais espaço para ganho (atividade limitada por acidez)
    #   argila        -> mais superfície para estabilizar carbono
    # E um freio: solo que já parte com atividade alta ganha menos.
    mod_ph: float = 2.6          # por unidade de pH abaixo de 5.4
    mod_argila: float = 0.9      # por desvio-padrão de argila
    mod_saturacao: float = -1.1  # por desvio-padrão de atividade inicial
    # cada ano de policultivo reduz a amplitude sazonal nesta fração
    amortecimento_sazonal: float = 0.09

    # 1.0 = fósforo determinado pelo manejo (fazenda real, sem sobreposição)
    acoplamento_fosforo: float = 1.0
    linha_de_base: bool = False

    ruido_parcela: float = 15.3   # dp entre parcelas, observado
    ruido_coleta: float = 12.0    # dp residual dentro de parcela
    semente: int = SEMENTE

    @property
    def efeito_total(self) -> float:
        """Efeito médio de 5 anos de policultivo (referência)."""
        return 5 * self.efeito_por_ano


def simular_bioas(cenario: CenarioBioAS | None = None
                  ) -> tuple[pd.DataFrame, float]:
    """Gera laudos sintéticos no formato BioAS.

    Retorna o DataFrame em formato longo (uma linha por parcela × coleta) e o
    efeito causal verdadeiro de 5 anos de policultivo sobre a beta-glicosidase.
    """
    c = cenario or CenarioBioAS()
    rng = np.random.default_rng(c.semente)
    n = c.n_parcelas

    # --- atributos intrínsecos, calibrados pelos laudos --------------------
    argila = rng.normal(30.9, 2.7, n).clip(24, 40)
    areia = (100 - argila - rng.normal(19, 4, n)).clip(35, 60)
    ph = rng.normal(5.43, 0.34, n).clip(4.6, 6.3)

    # --- linha de base: atividade antes da conversão -----------------------
    beta_base = (86 + 1.1 * argila + 8.0 * (ph - 5.43)
                 + rng.normal(0, c.ruido_parcela, n))

    # --- tratamento: anos de policultivo (dose contínua) -------------------
    # a adoção é confundida — talhões com solo já melhor convertem antes
    propensao = (0.6 * (beta_base - beta_base.mean()) / beta_base.std()
                 + 0.4 * (argila - argila.mean()) / argila.std()
                 + rng.normal(0, 1.0, n))
    anos = np.clip(np.round(3.5 + 2.2 * propensao), 0, 12)

    # --- fósforo: acoplado ao manejo em grau controlável -------------------
    # com acoplamento 1.0 reproduz a separação completa observada na fazenda
    fosforo_manejo = 8 + 7.5 * anos
    fosforo_livre = np.exp(rng.normal(3.3, 0.85, n)).clip(5, 100)
    p_mehlich = (c.acoplamento_fosforo * fosforo_manejo
                 + (1 - c.acoplamento_fosforo) * fosforo_livre
                 + rng.normal(0, 5, n)).clip(4, 120)

    # --- química pós-conversão --------------------------------------------
    mos = (33.5 + 0.6 * anos * 0.1 + 0.05 * argila
           + rng.normal(0, 3.0, n)).clip(28, 46)
    h_al = (4.4 - 0.9 * (ph - 5.43) + rng.normal(0, 0.9, n)).clip(2.0, 8.0)
    ctc = (13.4 - 0.35 * anos + 0.06 * argila + 0.4 * h_al
           + rng.normal(0, 1.6, n)).clip(10, 24)
    v_pct = (78 - 1.6 * anos + 6 * (ph - 5.43)
             + rng.normal(0, 4, n)).clip(50, 90)

    efeito_parcela = rng.normal(0, c.ruido_parcela * 0.4, n)

    # --- efeito causal heterogêneo, por ano de policultivo -----------------
    z_argila = (argila - argila.mean()) / argila.std()
    z_base = (beta_base - beta_base.mean()) / beta_base.std()
    tau_por_ano = (c.efeito_por_ano
                   + c.mod_ph * (5.43 - ph)
                   + c.mod_argila * z_argila
                   + c.mod_saturacao * z_base)

    # --- desfechos por coleta ---------------------------------------------
    linhas = []
    for i in range(n):
        amplitude = max(0.15, 1 - c.amortecimento_sazonal * anos[i])
        for mes in c.coletas:
            sazonal = SAZONALIDADE[mes] * amplitude
            beta = (beta_base[i]
                    + tau_por_ano[i] * anos[i]
                    + efeito_parcela[i]
                    + sazonal
                    + rng.normal(0, c.ruido_coleta))
            aril = (0.70 * beta + 38 + 4.0 * (ph[i] - 5.43)
                    + rng.normal(0, 9))
            registro = {
                "parcela": f"T{i:03d}",
                "mes": f"2023-{mes}",
                "argila": argila[i], "areia": areia[i], "ph": ph[i],
                "anos_policultivo": anos[i],
                "mos": mos[i], "ctc": ctc[i], "h_al": h_al[i],
                "v_pct": v_pct[i], "p_mehlich": p_mehlich[i],
                "beta": max(beta, 40.0), "aril": max(aril, 30.0),
            }
            if c.linha_de_base:
                registro["beta_linha_de_base"] = beta_base[i]
            # gabarito: efeito verdadeiro por ano naquele talhão
            registro["tau_real"] = tau_por_ano[i]
            linhas.append(registro)

    return pd.DataFrame(linhas).round(2), c.efeito_total


def agregar_por_parcela(laudos: pd.DataFrame) -> pd.DataFrame:
    """Colapsa as coletas na unidade experimental — evita pseudorreplicação."""
    numericas = laudos.select_dtypes("number").columns
    return laudos.groupby("parcela")[list(numericas)].mean().reset_index()
