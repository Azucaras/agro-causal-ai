"""Testes de integração do pipeline."""

from solocausal import analisar, simular_laudos
from solocausal.config import COLUNA_LINHA_DE_BASE
from solocausal.dados import Cenario, validar


def test_validacao_rejeita_coluna_ausente():
    laudos, _ = simular_laudos(Cenario(n=100))
    diagnostico = validar(laudos, "inexistente", "beta_glicosidase")
    assert not diagnostico.ok
    assert "inexistente" in diagnostico.faltando


def test_validacao_avisa_sobre_linha_de_base_ausente():
    laudos, _ = simular_laudos(Cenario(n=100))
    diagnostico = validar(laudos.drop(columns=[COLUNA_LINHA_DE_BASE]),
                          "composto", "beta_glicosidase")
    assert diagnostico.ok
    assert any("linha de base" in aviso for aviso in diagnostico.avisos)


def test_analisar_devolve_resultado_serializavel():
    laudos, real = simular_laudos(Cenario(n=300))
    resultado = analisar(laudos, efeito_real=real)
    dicionario = resultado.como_dicionario()

    assert dicionario["n_amostras"] == 300
    assert len(dicionario["intervalo_total"]) == 2
    assert dicionario["n_dags"] >= 1


def test_linha_de_base_e_o_que_permite_identificacao():
    """O resultado central do trabalho, como teste de regressão."""
    laudos, real = simular_laudos(Cenario(n=600))

    sem_base = analisar(laudos, ignorar=(COLUNA_LINHA_DE_BASE,),
                        efeito_real=real)
    com_base = analisar(laudos, efeito_real=real)

    assert not sem_base.cobre_efeito_real
    assert com_base.cobre_efeito_real


def test_atalhos_erram_em_direcoes_opostas():
    laudos, real = simular_laudos(Cenario(n=600))
    resultado = analisar(laudos, efeito_real=real)

    assert resultado.diferenca_bruta > real          # superestima
    assert resultado.efeito_ajuste_total.valor < real  # subestima
