"""Teste de independência condicional por correlação parcial (Fisher-z).

Assume relações aproximadamente lineares entre as variáveis padronizadas. Para
laudos de solo isso é defensável na maioria dos atributos, mas é a primeira
hipótese a questionar se o grafo resultante parecer estranho.

Trocar por um teste não paramétrico (HSIC, por exemplo) é extensão direta:
basta respeitar a assinatura de `testar`.
"""

from __future__ import annotations

import numpy as np
from scipy import stats


def correlacao_parcial(dados: np.ndarray, i: int, j: int,
                       condicionantes: tuple[int, ...]) -> float:
    """Correlação entre as colunas i e j, removido o efeito das demais."""
    indices = [i, j, *condicionantes]
    matriz = np.corrcoef(dados[:, indices], rowvar=False)
    try:
        precisao = np.linalg.pinv(matriz)
    except np.linalg.LinAlgError:
        return 0.0
    denominador = np.sqrt(precisao[0, 0] * precisao[1, 1])
    if denominador <= 0:
        return 0.0
    return float(-precisao[0, 1] / denominador)


def testar(dados: np.ndarray, i: int, j: int,
           condicionantes: tuple[int, ...], alfa: float) -> tuple[bool, float]:
    """Testa i ⊥ j | condicionantes. Retorna (independentes?, p-valor)."""
    graus = dados.shape[0] - len(condicionantes) - 3
    if graus <= 0:
        return True, 1.0

    r = np.clip(correlacao_parcial(dados, i, j, condicionantes), -0.9999, 0.9999)
    z = 0.5 * np.log((1 + r) / (1 - r)) * np.sqrt(graus)
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    return p > alfa, float(p)


def padronizar(dados: np.ndarray) -> np.ndarray:
    """Centra e escala colunas; a correlação parcial pressupõe isso."""
    return (dados - dados.mean(axis=0)) / (dados.std(axis=0) + 1e-12)
