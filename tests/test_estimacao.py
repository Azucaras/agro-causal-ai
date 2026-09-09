"""Testes do estimador de efeito."""

import numpy as np

from solocausal.estimacao import EfeitoHeterogeneo, estimar, valor_de_robustez


def test_dml_recupera_efeito_em_desenho_sem_confundimento():
    rng = np.random.default_rng(2)
    n = 1500
    z = rng.normal(size=n)
    t = rng.binomial(1, 0.5, n).astype(float)   # aleatorizado
    y = 3.0 * t + 2.0 * z + rng.normal(scale=1.0, size=n)

    efeito = estimar(y, t, z.reshape(-1, 1), ("z",))
    assert abs(efeito.valor - 3.0) < 0.25
    assert efeito.valido


def test_dml_corrige_confundimento():
    rng = np.random.default_rng(3)
    n = 2000
    z = rng.normal(size=n)
    t = (rng.uniform(size=n) < 1 / (1 + np.exp(-1.5 * z))).astype(float)
    y = 2.0 * t + 3.0 * z + rng.normal(scale=1.0, size=n)

    ingenuo = float(y[t == 1].mean() - y[t == 0].mean())
    ajustado = estimar(y, t, z.reshape(-1, 1), ("z",)).valor

    assert ingenuo > 3.0                    # confundido para cima
    assert abs(ajustado - 2.0) < 0.25       # corrigido


def test_valor_de_robustez_cresce_com_t():
    fraco = valor_de_robustez(1.5, 500)
    forte = valor_de_robustez(12.0, 500)
    assert 0 < fraco < forte < 1


def test_efeito_heterogeneo_recupera_modulacao():
    rng = np.random.default_rng(4)
    n = 1200
    x = rng.normal(size=n)
    t = rng.binomial(1, 0.5, n).astype(float)
    tau = 1.0 + 2.0 * x
    y = tau * t + rng.normal(scale=1.0, size=n)

    modelo = EfeitoHeterogeneo(n_arvores=200).ajustar(
        y, t, x.reshape(-1, 1), np.zeros((n, 0)))
    estimado = modelo.prever(x.reshape(-1, 1))

    assert np.corrcoef(estimado, tau)[0, 1] > 0.7
