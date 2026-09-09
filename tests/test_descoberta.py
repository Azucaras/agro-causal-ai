"""Testes da camada de descoberta causal."""

import numpy as np

from solocausal.dados import Cenario, simular_laudos
from solocausal.descoberta import Camadas, enumerar, estimar_cpdag, tem_ciclo
from solocausal.descoberta.independencia import correlacao_parcial, testar
from solocausal.config import CAMADAS_PADRAO


def test_correlacao_parcial_remove_confundidor():
    """X e Y correlacionados só por Z devem ficar independentes dado Z."""
    rng = np.random.default_rng(0)
    z = rng.normal(size=800)
    x = z + rng.normal(scale=0.4, size=800)
    y = z + rng.normal(scale=0.4, size=800)
    dados = np.column_stack([x, y, z])

    bruta = abs(np.corrcoef(x, y)[0, 1])
    parcial = abs(correlacao_parcial(dados, 0, 1, (2,)))
    assert bruta > 0.7
    assert parcial < 0.15


def test_teste_independencia_detecta_dependencia():
    rng = np.random.default_rng(1)
    x = rng.normal(size=500)
    y = 0.8 * x + rng.normal(scale=0.5, size=500)
    dados = np.column_stack([x, y])
    independentes, p = testar(dados, 0, 1, (), alfa=0.01)
    assert not independentes
    assert p < 0.01


def test_camadas_bloqueiam_aresta_para_tras():
    camadas = Camadas([["argila"], ["ph"], ["composto"]])
    assert camadas.permite("argila", "composto")
    assert not camadas.permite("composto", "argila")


def test_tem_ciclo():
    assert tem_ciclo(3, {(0, 1), (1, 2), (2, 0)})
    assert not tem_ciclo(3, {(0, 1), (1, 2)})


def test_cpdag_recupera_linha_de_base_como_pai_do_tratamento():
    """Regressão do bug do colisor.

    Sem a restrição de camadas nos separadores, o PC condicionava na
    arilsulfatase — descendente comum — e apagava a aresta verdadeira
    mo_laudo_anterior → composto por cancelamento de caminhos.
    """
    laudos, _ = simular_laudos(Cenario(n=700))
    variaveis = [v for grupo in CAMADAS_PADRAO for v in grupo
                 if v in laudos.columns]
    camadas = Camadas(CAMADAS_PADRAO)
    cpdag = estimar_cpdag(laudos, variaveis, camadas)

    indice = cpdag.indice
    pais_do_tratamento = {variaveis[a] for a, b in cpdag.dirigidas
                          if b == indice["composto"]}
    assert "mo_laudo_anterior" in pais_do_tratamento


def test_enumeracao_respeita_aciclicidade_e_camadas():
    laudos, _ = simular_laudos(Cenario(n=400))
    variaveis = [v for grupo in CAMADAS_PADRAO for v in grupo
                 if v in laudos.columns]
    camadas = Camadas(CAMADAS_PADRAO)
    cpdag = estimar_cpdag(laudos, variaveis, camadas)
    dags = enumerar(cpdag, camadas)

    assert len(dags) >= 1
    for dag in dags:
        assert not tem_ciclo(len(variaveis), dag)
        for origem, destino in dag:
            assert camadas.permite(variaveis[origem], variaveis[destino])
