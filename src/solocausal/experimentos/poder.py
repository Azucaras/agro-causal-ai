"""Estudo de viabilidade: quantas amostras o método exige?

A pergunta prática antes de sair coletando laudo. A resposta interessante não é
"quantas", e sim que a largura do intervalo cai com n, mas a cobertura só
melhora quando existe uma medida de linha de base.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import COLUNA_LINHA_DE_BASE, SEMENTE
from ..dados.simulacao import Cenario, simular_laudos
from ..pipeline import analisar


def curva_de_poder(tamanhos: tuple[int, ...] = (150, 300, 600, 1200),
                   repeticoes: int = 3,
                   semente: int = SEMENTE) -> pd.DataFrame:
    """Roda a simulação variando n, com e sem a coluna de linha de base."""
    linhas = []

    for n in tamanhos:
        medidas = {"sem": ([], []), "com": ([], [])}

        for repeticao in range(repeticoes):
            laudos, real = simular_laudos(
                Cenario(n=n, semente=semente + repeticao))

            for chave, ignorar in (("sem", (COLUNA_LINHA_DE_BASE,)), ("com", ())):
                resultado = analisar(laudos, ignorar=ignorar, efeito_real=real)
                piso, teto = resultado.intervalo_total
                medidas[chave][0].append(teto - piso)
                medidas[chave][1].append(float(resultado.cobre_efeito_real))

        linhas.append(dict(
            n=n,
            largura_sem_base=float(np.nanmean(medidas["sem"][0])),
            cobertura_sem_base=float(np.nanmean(medidas["sem"][1])),
            largura_com_base=float(np.nanmean(medidas["com"][0])),
            cobertura_com_base=float(np.nanmean(medidas["com"][1])),
        ))

    return pd.DataFrame(linhas).round(3)
