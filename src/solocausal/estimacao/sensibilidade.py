"""Sensibilidade a confundidores não observados.

Nenhum ajuste por covariáveis observadas garante ausência de confundimento. O
que dá para fazer é quantificar quão forte teria de ser um fator não medido —
histórico de compactação, calagem antiga, microclima — para derrubar o
resultado.

Referência: Cinelli & Hazlett (2020).
"""

from __future__ import annotations

import numpy as np


def valor_de_robustez(t: float, graus_liberdade: int) -> float:
    """Fração da variância residual que um confundidor não medido teria de
    explicar, simultaneamente do tratamento e do desfecho, para zerar o efeito.

    Próximo de 1 indica achado difícil de derrubar; próximo de 0, achado frágil.
    """
    if not np.isfinite(t) or graus_liberdade <= 0:
        return float("nan")
    f = abs(t) / np.sqrt(graus_liberdade)
    return float(0.5 * (np.sqrt(f ** 4 + 4 * f ** 2) - f ** 2))


def interpretar(valor: float) -> str:
    """Frase curta para relatório."""
    if not np.isfinite(valor):
        return "não calculável"
    if valor < 0.05:
        return "frágil — um confundidor fraco já derrubaria o resultado"
    if valor < 0.15:
        return "moderado"
    return "robusto — exigiria um confundidor forte e não medido"
