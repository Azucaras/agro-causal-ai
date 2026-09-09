"""Prescrição: transforma o efeito estimado em decisão de manejo.

Estimar tau(x) não é prescrever. Prescrever exige três passos que este módulo
separa de propósito, porque cada um pode falhar por motivo diferente:

1. **Regra legível** — uma árvore rasa sobre tau(x). Ninguém adota uma
   recomendação que não consegue ler; "converta se o pH for menor que 5,3 e a
   argila acima de 30%" é acionável, um vetor de 400 predições não é.

2. **Decisão com limiar** — recomendar não é o mesmo que prever benefício.
   Uma prática só se justifica se o ganho esperado superar o custo, e o custo
   entra aqui como limiar explícito, não escondido no modelo.

3. **Valor da política** — de quanto adianta seguir a regra em vez de tratar
   todo mundo ou ninguém. Sem esta comparação não há como saber se a
   personalização vale o esforço; muitas vezes não vale, e é honesto descobrir.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.tree import DecisionTreeRegressor, export_text


@dataclass
class Politica:
    """Decisão de tratar, e o que se ganha com ela."""

    decisao: np.ndarray          # booleano por talhão
    limiar: float
    valor: float                 # ganho médio seguindo a política
    valor_tratar_todos: float
    valor_nao_tratar: float = 0.0

    @property
    def fracao_tratada(self) -> float:
        return float(self.decisao.mean())

    @property
    def ganho_sobre_tratar_todos(self) -> float:
        return self.valor - self.valor_tratar_todos

    @property
    def personalizacao_compensa(self) -> bool:
        """A regra bate a política uniforme mais simples?"""
        return self.valor > max(self.valor_tratar_todos, self.valor_nao_tratar)


def regras(modificadores: np.ndarray, tau: np.ndarray, nomes: list[str],
           profundidade: int = 2, min_folha: int = 30) -> str:
    """Árvore rasa sobre tau(x), em texto.

    Cada folha é uma recomendação condicional; o valor da folha é o ganho
    esperado por unidade de tratamento naquele contexto de solo.
    """
    arvore = DecisionTreeRegressor(max_depth=profundidade,
                                   min_samples_leaf=min_folha,
                                   random_state=0)
    arvore.fit(modificadores, tau)
    return export_text(arvore, feature_names=list(nomes), decimals=2)


def decidir(tau: np.ndarray, custo: float = 0.0) -> np.ndarray:
    """Recomenda tratar onde o ganho esperado supera o custo."""
    return tau > custo


def valor_da_politica(decisao: np.ndarray, tau_verdadeiro: np.ndarray,
                      custo: float = 0.0) -> float:
    """Ganho médio de uma política, dado o efeito verdadeiro.

    Só computável em simulação. Com dado real, use `valor_estimado`.
    """
    return float(np.mean(decisao * (tau_verdadeiro - custo)))


def valor_estimado(decisao: np.ndarray, desfecho: np.ndarray,
                   tratamento: np.ndarray, propensao: np.ndarray,
                   tau: np.ndarray, custo: float = 0.0) -> float:
    """Valor da política por escore duplamente robusto.

    Para tratamento binário. Combina o modelo de desfecho com uma correção por
    propensão inversa, de modo que basta um dos dois estar bem especificado.
    """
    propensao = np.clip(propensao, 0.02, 0.98)
    residuo = desfecho - np.mean(desfecho)
    escore = tau + (tratamento - propensao) / (propensao * (1 - propensao)) * residuo
    return float(np.mean(decisao * (escore - custo)))


def avaliar(tau_estimado: np.ndarray, tau_verdadeiro: np.ndarray,
            custo: float = 0.0) -> Politica:
    """Monta a política a partir de tau estimado e a avalia contra a verdade."""
    decisao = decidir(tau_estimado, custo)
    return Politica(
        decisao=decisao,
        limiar=custo,
        valor=valor_da_politica(decisao, tau_verdadeiro, custo),
        valor_tratar_todos=valor_da_politica(
            np.ones_like(decisao, dtype=bool), tau_verdadeiro, custo),
    )
