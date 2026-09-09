"""Double Machine Learning no modelo parcialmente linear.

    Y = θ·T + g(Z) + ε ,   T = m(Z) + ν

Estimamos g e m com gradient boosting sob validação cruzada (cross-fitting),
tomamos os resíduos e regredimos um no outro. O coeficiente resultante é θ.

O cross-fitting não é detalhe: sem ele o viés de sobreajuste dos modelos de
nuisance vaza direto para o estimador do efeito.

Referências: Robinson (1988) para o estimador; Chernozhukov et al. (2018) para
a formulação com aprendizado de máquina.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold

from ..config import SEMENTE


@dataclass
class Efeito:
    """Efeito estimado sob um conjunto de ajuste específico."""

    valor: float
    erro_padrao: float
    ajuste: tuple[str, ...]
    propensao_min: float = float("nan")
    propensao_max: float = float("nan")

    @property
    def t(self) -> float:
        if not self.erro_padrao:
            return float("nan")
        return self.valor / self.erro_padrao

    @property
    def ic95(self) -> tuple[float, float]:
        margem = 1.96 * self.erro_padrao
        return self.valor - margem, self.valor + margem

    @property
    def valido(self) -> bool:
        return bool(np.isfinite(self.valor) and np.isfinite(self.erro_padrao))

    def como_dicionario(self) -> dict:
        return {
            "valor": round(self.valor, 4),
            "erro_padrao": round(self.erro_padrao, 4),
            "t": round(self.t, 3),
            "ic95": [round(x, 4) for x in self.ic95],
            "ajuste": list(self.ajuste),
        }


def estimar(desfecho: np.ndarray, tratamento: np.ndarray, ajuste: np.ndarray,
            nomes_ajuste: tuple[str, ...] = (), n_folds: int = 5,
            semente: int = SEMENTE) -> Efeito:
    """Estima o efeito médio do tratamento controlando por `ajuste`."""
    n = len(desfecho)

    if ajuste.shape[1] == 0:
        controles = np.zeros((n, 1))
    else:
        controles = (ajuste - ajuste.mean(axis=0)) / (ajuste.std(axis=0) + 1e-9)

    esperado_y = np.zeros(n)
    esperado_t = np.zeros(n)
    binario = set(np.unique(tratamento)) <= {0.0, 1.0}

    for treino, teste in KFold(n_folds, shuffle=True,
                               random_state=semente).split(controles):
        modelo_y = _regressor(semente).fit(controles[treino], desfecho[treino])
        esperado_y[teste] = modelo_y.predict(controles[teste])

        if binario:
            modelo_t = LogisticRegression(max_iter=1000)
            modelo_t.fit(controles[treino], tratamento[treino])
            esperado_t[teste] = np.clip(
                modelo_t.predict_proba(controles[teste])[:, 1], 0.01, 0.99)
        else:
            modelo_t = _regressor(semente).fit(controles[treino],
                                               tratamento[treino])
            esperado_t[teste] = modelo_t.predict(controles[teste])

    residuo_y = desfecho - esperado_y
    residuo_t = tratamento - esperado_t
    denominador = float((residuo_t ** 2).sum())

    if denominador < 1e-9:
        return Efeito(float("nan"), float("nan"), nomes_ajuste)

    valor = float((residuo_t * residuo_y).sum() / denominador)
    residuo = residuo_y - valor * residuo_t
    variancia = (residuo ** 2 * residuo_t ** 2).sum() / denominador ** 2

    return Efeito(
        valor=valor,
        erro_padrao=float(np.sqrt(variancia)),
        ajuste=nomes_ajuste,
        propensao_min=float(esperado_t.min()),
        propensao_max=float(esperado_t.max()),
    )


def _regressor(semente: int) -> GradientBoostingRegressor:
    return GradientBoostingRegressor(
        n_estimators=150, max_depth=3, learning_rate=0.07, random_state=semente)
