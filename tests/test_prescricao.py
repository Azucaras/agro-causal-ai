"""Testes da camada de prescrição."""

import numpy as np

from solocausal import prescricao
from solocausal.dados import CenarioBioAS, agregar_por_parcela, simular_bioas


def test_decidir_respeita_limiar():
    tau = np.array([-1.0, 0.5, 2.0, 5.0])
    assert prescricao.decidir(tau, custo=0.0).tolist() == [False, True, True, True]
    assert prescricao.decidir(tau, custo=3.0).tolist() == [False, False, False, True]


def test_politica_bate_tratar_todos_quando_ha_custo():
    rng = np.random.default_rng(5)
    tau = rng.normal(loc=1.0, scale=2.0, size=500)
    politica = prescricao.avaliar(tau, tau, custo=2.0)

    assert politica.valor >= politica.valor_tratar_todos
    assert 0.0 < politica.fracao_tratada < 1.0


def test_regras_produzem_arvore_legivel():
    rng = np.random.default_rng(6)
    x = rng.normal(size=(400, 2))
    tau = 2.0 * x[:, 0]
    texto = prescricao.regras(x, tau, ["ph", "argila"])

    assert "ph" in texto
    assert "value" in texto


def test_mock_bioas_reproduz_amortecimento_sazonal():
    """O gradiente observado no dado real deve emergir do simulador."""
    laudos, _ = simular_bioas(CenarioBioAS(n_parcelas=90))
    cv = laudos.groupby("parcela").apply(
        lambda g: 100 * g["beta"].std() / g["beta"].mean(),
        include_groups=False)
    anos = laudos.groupby("parcela")["anos_policultivo"].first()

    novos = cv[anos <= 1].mean()
    antigos = cv[anos >= 6].mean()
    assert novos > antigos


def test_agregacao_colapsa_para_a_unidade_experimental():
    laudos, _ = simular_bioas(CenarioBioAS(n_parcelas=25))
    por_parcela = agregar_por_parcela(laudos)
    assert len(laudos) == 100          # 25 parcelas x 4 coletas
    assert len(por_parcela) == 25
