"""Efeito heterogêneo de tratamento (CATE) pelo R-learner.

O módulo `dml.py` estima um efeito médio: um número para toda a população.
Isso responde "converter funciona?". A prescrição exige a pergunta seguinte —
"funciona *neste* talhão?" — e para isso é preciso estimar

    tau(x) = E[Y(1) - Y(0) | X = x]

A decomposição de Robinson (1988) dá o caminho. Com os resíduos ortogonalizados
Ỹ = Y - E[Y|Z] e T̃ = T - E[T|Z], tau minimiza E[(Ỹ - tau(x)·T̃)²]. Isso é uma
regressão ponderada: alvo Ỹ/T̃, peso T̃². Qualquer aprendiz flexível serve; aqui
usamos floresta, o que aproxima o CausalForestDML do EconML sem a dependência.

Referências: Nie & Wager (2021) para o R-learner; Athey & Wager (2019) para a
versão em floresta generalizada.
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold

from ..config import SEMENTE


class EfeitoHeterogeneo:
    """Estima tau(x) por R-learner com floresta."""

    def __init__(self, n_folds: int = 5, n_arvores: int = 400,
                 min_folha: int = 20, semente: int = SEMENTE):
        self.n_folds = n_folds
        self.n_arvores = n_arvores
        self.min_folha = min_folha
        self.semente = semente

    def ajustar(self, desfecho: np.ndarray, tratamento: np.ndarray,
                modificadores: np.ndarray, controles: np.ndarray
                ) -> "EfeitoHeterogeneo":
        """Ajusta o modelo.

        `modificadores` são as variáveis em que o efeito pode variar — as que
        entram na regra de prescrição. `controles` são os confundidores a
        bloquear. Uma variável pode aparecer nos dois papéis.
        """
        n = len(desfecho)
        contexto = np.column_stack([modificadores, controles])
        contexto = (contexto - contexto.mean(0)) / (contexto.std(0) + 1e-9)

        esperado_y = np.zeros(n)
        esperado_t = np.zeros(n)
        binario = set(np.unique(tratamento)) <= {0.0, 1.0}

        for treino, teste in KFold(self.n_folds, shuffle=True,
                                   random_state=self.semente).split(contexto):
            modelo_y = self._aprendiz().fit(contexto[treino], desfecho[treino])
            esperado_y[teste] = modelo_y.predict(contexto[teste])

            if binario:
                modelo_t = LogisticRegression(max_iter=1000).fit(
                    contexto[treino], tratamento[treino])
                esperado_t[teste] = np.clip(
                    modelo_t.predict_proba(contexto[teste])[:, 1], 0.02, 0.98)
            else:
                modelo_t = self._aprendiz().fit(contexto[treino],
                                                tratamento[treino])
                esperado_t[teste] = modelo_t.predict(contexto[teste])

        residuo_y = desfecho - esperado_y
        residuo_t = tratamento - esperado_t

        peso = residuo_t ** 2
        alvo = np.divide(residuo_y, residuo_t, out=np.zeros_like(residuo_y),
                         where=np.abs(residuo_t) > 1e-6)

        self.modelo_ = RandomForestRegressor(
            n_estimators=self.n_arvores, min_samples_leaf=self.min_folha,
            max_features="sqrt", random_state=self.semente, n_jobs=-1)
        self.modelo_.fit(modificadores, alvo, sample_weight=peso)

        self._residuo_y = residuo_y
        self._residuo_t = residuo_t
        self.propensao_ = esperado_t
        return self

    def prever(self, modificadores: np.ndarray) -> np.ndarray:
        """tau(x) para cada linha."""
        return self.modelo_.predict(modificadores)

    def efeito_medio(self) -> tuple[float, float]:
        """ATE pelo mesmo ajuste, com erro padrão — âncora de sanidade."""
        denominador = float((self._residuo_t ** 2).sum())
        valor = float((self._residuo_t * self._residuo_y).sum() / denominador)
        resto = self._residuo_y - valor * self._residuo_t
        variancia = (resto ** 2 * self._residuo_t ** 2).sum() / denominador ** 2
        return valor, float(np.sqrt(variancia))

    def _aprendiz(self) -> GradientBoostingRegressor:
        return GradientBoostingRegressor(
            n_estimators=150, max_depth=3, learning_rate=0.07,
            random_state=self.semente)
