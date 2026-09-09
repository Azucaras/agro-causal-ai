"""Formatação de resultados para o terminal.

Separado do pipeline de propósito: a mesma análise alimenta a CLI, a API e a
interface web. Só este módulo sabe o que é uma linha de texto.
"""

from __future__ import annotations

from .estimacao import interpretar
from .pipeline import Resultado

LARGURA = 78


def titulo(texto: str) -> str:
    return f"\n{'=' * LARGURA}\n {texto}\n{'=' * LARGURA}"


def formatar(resultado: Resultado, rotulo: str = "") -> str:
    """Relatório completo de uma análise."""
    partes: list[str] = []
    r = resultado

    partes.append(titulo(f"ANÁLISE {rotulo}".strip()))
    partes.append(f" amostras           : {r.n_amostras}")
    partes.append(f" tratamento         : {r.tratamento} "
                  f"({r.n_tratados} tratadas / "
                  f"{r.n_amostras - r.n_tratados} controle)")
    partes.append(f" desfecho           : {r.desfecho}")

    partes.append(titulo("O QUE OS ATALHOS HABITUAIS RESPONDEM"))
    partes.append(f" diferença bruta de médias        : {r.diferenca_bruta:+8.3f}")
    partes.append(f" ajuste por todas as covariáveis  : "
                  f"{r.efeito_ajuste_total.valor:+8.3f}")
    partes.append(" O primeiro ignora que quem trata já tinha solo melhor.")
    partes.append(" O segundo controla por atributos medidos depois da")
    partes.append(" intervenção, que são mediadores — e desconta parte do efeito.")

    partes.append(titulo("GRAFO CAUSAL ESTIMADO"))
    partes.append(f" arestas orientadas pelos dados   : {len(r.cpdag.dirigidas)}")
    partes.append(f" arestas de direção indefinida    : {len(r.cpdag.ambiguas)}")
    vizinhos = r.cpdag.vizinhos_de(r.tratamento)
    partes.append(f" ligadas a '{r.tratamento}': "
                  f"{', '.join(vizinhos) if vizinhos else '(nenhuma)'}")

    partes.append(titulo(f"EFEITO SOB CADA GRAFO ADMISSÍVEL ({r.n_dags} DAGs)"))
    if not r.validos:
        partes.append(" Nenhuma estimativa válida. Revise alfa ou as camadas.")
        return "\n".join(partes)

    minimo, maximo = r.amplitude_estrutural
    piso, teto = r.intervalo_total
    partes.append(f" amplitude entre grafos           : "
                  f"[{minimo:+.3f}, {maximo:+.3f}]")
    partes.append(f" intervalo total (com amostragem) : [{piso:+.3f}, {teto:+.3f}]")
    partes.append(f" mediana                          : {r.mediana:+8.3f}")
    partes.append(f" sinal                            : "
                  f"{'estável' if r.sinal_estavel else 'TROCA ENTRE GRAFOS'}")

    partes.append("\n conjuntos de ajuste usados:")
    for conjunto in sorted({e.ajuste for e in r.validos}, key=len):
        partes.append(f"   {', '.join(conjunto) if conjunto else '(vazio)'}")

    if r.efeito_real is not None:
        veredito = "DENTRO" if r.cobre_efeito_real else "FORA"
        partes.append(f"\n efeito verdadeiro (gabarito da simulação): "
                      f"{r.efeito_real:+.3f} — {veredito} do intervalo")

    partes.append(titulo("SUPORTE COMUM"))
    p = r.efeito_ajuste_total
    partes.append(f" propensão estimada varia de {p.propensao_min:.3f} "
                  f"a {p.propensao_max:.3f}")
    partes.append(" Valores colados em 0 ou 1 indicam solos sem contrafactual")
    partes.append(" comparável: para eles o efeito é extrapolado, não estimado.")

    partes.append(titulo("SENSIBILIDADE A CONFUNDIDOR NÃO MEDIDO"))
    partes.append(f" valor de robustez : {r.robustez:.3f} "
                  f"({interpretar(r.robustez)})")
    partes.append(f" Um fator não medido precisaria explicar "
                  f"{100 * r.robustez:.1f}% da variância")
    partes.append(" residual do tratamento e do desfecho para zerar o efeito.")

    ambiguas = r.cpdag.ambiguas_tocando(r.tratamento)
    if ambiguas:
        partes.append(titulo("O QUE MEDIR PARA ESTREITAR O INTERVALO"))
        for a, b in ambiguas:
            partes.append(f"   {a} — {b}   (direção indeterminada pelos dados)")

    return "\n".join(partes)


def formatar_comparacao(resultados: dict[str, Resultado],
                        efeito_real: float | None = None) -> str:
    """Tabela comparando análises da mesma base sob condições diferentes."""
    partes = [titulo("COMPARAÇÃO")]
    cabecalho = f"{'condição':<34}{'intervalo':>22}{'mediana':>10}{'cobre':>8}"
    partes.append(cabecalho)
    partes.append("-" * len(cabecalho))

    for rotulo, r in resultados.items():
        piso, teto = r.intervalo_total
        cobre = {True: "sim", False: "não", None: "-"}[r.cobre_efeito_real]
        partes.append(f"{rotulo:<34}"
                      f"{f'[{piso:+.2f}, {teto:+.2f}]':>22}"
                      f"{r.mediana:>10.2f}{cobre:>8}")

    if efeito_real is not None:
        partes.append(f"\n efeito verdadeiro: {efeito_real:+.3f}")

    return "\n".join(partes)
