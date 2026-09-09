"""Interface de linha de comando."""

from __future__ import annotations

import argparse
import json
import sys

from .config import (ALFA_PADRAO, COLUNA_LINHA_DE_BASE, DESFECHO_PADRAO,
                     TRATAMENTO_PADRAO)
from .dados import (Cenario, DESCRICAO_ESQUEMA, ler_laudos, simular_laudos,
                    validar)
from .experimentos import curva_de_poder
from .pipeline import analisar
from .relatorio import formatar, formatar_comparacao, titulo


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="solocausal",
        description="Inferência causal sobre laudos de análise de solo.")
    sub = parser.add_subparsers(dest="comando", required=True)

    simular = sub.add_parser(
        "simular", help="roda o pipeline em dados sintéticos com gabarito")
    simular.add_argument("-n", type=int, default=900, help="número de amostras")
    simular.add_argument("--alfa", type=float, default=ALFA_PADRAO)
    simular.add_argument("--json", action="store_true")

    analisar_cmd = sub.add_parser("analisar", help="roda sobre um CSV de laudos")
    analisar_cmd.add_argument("csv")
    analisar_cmd.add_argument("--tratamento", default=TRATAMENTO_PADRAO)
    analisar_cmd.add_argument("--desfecho", default=DESFECHO_PADRAO)
    analisar_cmd.add_argument("--alfa", type=float, default=ALFA_PADRAO)
    analisar_cmd.add_argument("--json", action="store_true")

    poder = sub.add_parser("poder", help="curva de viabilidade por tamanho amostral")
    poder.add_argument("--repeticoes", type=int, default=3)

    sub.add_parser("esquema", help="mostra o formato esperado do CSV")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)

    if args.comando == "esquema":
        print(DESCRICAO_ESQUEMA)
        return 0

    if args.comando == "poder":
        print(titulo("VIABILIDADE — largura e cobertura do intervalo por n"))
        print(curva_de_poder(repeticoes=args.repeticoes).to_string(index=False))
        print("\n A largura cai com n nos dois casos. A cobertura, não:")
        print(" sem uma medida de linha de base, o intervalo continua não")
        print(" contendo o efeito verdadeiro por mais amostras que se colete.")
        return 0

    if args.comando == "simular":
        laudos, real = simular_laudos(Cenario(n=args.n))
        sem_base = analisar(laudos, alfa=args.alfa,
                            ignorar=(COLUNA_LINHA_DE_BASE,), efeito_real=real)
        com_base = analisar(laudos, alfa=args.alfa, efeito_real=real)

        if args.json:
            print(json.dumps({"sem_linha_de_base": sem_base.como_dicionario(),
                              "com_linha_de_base": com_base.como_dicionario()},
                             ensure_ascii=False, indent=2))
            return 0

        print(formatar(sem_base, "— só o laudo atual"))
        print(formatar(com_base, "— com o laudo da safra anterior"))
        print(formatar_comparacao({"só o laudo atual": sem_base,
                                   "com laudo da safra anterior": com_base},
                                  efeito_real=real))
        return 0

    if args.comando == "analisar":
        laudos = ler_laudos(args.csv)
        diagnostico = validar(laudos, args.tratamento, args.desfecho)
        if not diagnostico.ok:
            print(diagnostico, file=sys.stderr)
            return 1
        for aviso in diagnostico.avisos:
            print(f"aviso: {aviso}", file=sys.stderr)

        resultado = analisar(laudos, tratamento=args.tratamento,
                             desfecho=args.desfecho, alfa=args.alfa)
        print(json.dumps(resultado.como_dicionario(), ensure_ascii=False, indent=2)
              if args.json else formatar(resultado))
        return 0

    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        # acontece ao encanar a saída para `head`; não é erro do programa
        sys.stdout = None
        raise SystemExit(0)
