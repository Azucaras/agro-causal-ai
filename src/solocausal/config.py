"""Constantes e configuração de domínio.

As "camadas" são a única parte do pipeline que exige conhecimento agronômico.
Tudo o mais é estatística. Se for adaptar o projeto para outra cultura, outro
bioma ou outro tratamento, é aqui que se mexe primeiro.
"""

from __future__ import annotations

SEMENTE = 20260821

# Coeficientes do simulador genérico. Ficam aqui, e não dentro da função que
# gera os dados, porque o gabarito do efeito verdadeiro depende deles — se
# mudarem em um lugar e não no outro, a validação passa a mentir.
COEF_MO_ENZIMA = 11.5   # a enzima ganha isso por unidade de matéria orgânica
RESPOSTA_MO = 0.62      # quanto de matéria orgânica o tratamento adiciona

#: Ordem causal admissível entre os atributos do laudo.
#:
#: A regra é simples: uma aresta só pode ir de uma camada para outra igual ou
#: posterior. Textura não é causada por manejo; a atividade enzimática não
#: causa o teor de argila. Sem isso o algoritmo de descoberta propõe grafos
#: fisicamente impossíveis e o resultado deixa de significar coisa alguma.
CAMADAS_PADRAO: list[list[str]] = [
    # 1. atributos intrínsecos — não mudam com manejo de curto prazo
    ["argila", "areia"],
    # 2. química de base, medida antes da intervenção
    ["ph", "mo_laudo_anterior"],
    # 3. a decisão de manejo (o tratamento)
    ["composto"],
    # 4. atributos medidos depois da intervenção — potenciais mediadores
    ["materia_organica", "ctc", "v_pct", "p_mehlich",
     "k_cmolc", "densidade", "resist_penetracao"],
    # 5. bioindicadores — o desfecho
    ["beta_glicosidase", "arilsulfatase"],
]

TRATAMENTO_PADRAO = "composto"
DESFECHO_PADRAO = "beta_glicosidase"
COLUNA_LINHA_DE_BASE = "mo_laudo_anterior"

#: Nível de significância dos testes de independência condicional.
#: Valores menores deixam o grafo mais esparso, portanto mais conservador.
ALFA_PADRAO = 0.01
