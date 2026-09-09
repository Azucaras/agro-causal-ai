"""Runner mínimo, para rodar a suíte sem pytest instalado.

Os testes são pytest-compatíveis; isto existe só para ambientes sem a
dependência. Com pytest disponível, prefira `pytest tests -q`.
"""

from __future__ import annotations

import importlib.util
import sys
import traceback
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI.parent / "src"))

LENTOS = {"test_linha_de_base_e_o_que_permite_identificacao"}


def carregar(caminho: Path):
    spec = importlib.util.spec_from_file_location(caminho.stem, caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def main(incluir_lentos: bool = False) -> int:
    passou = falhou = pulou = 0
    for arquivo in sorted(AQUI.glob("test_*.py")):
        modulo = carregar(arquivo)
        for nome in dir(modulo):
            if not nome.startswith("test_"):
                continue
            if nome in LENTOS and not incluir_lentos:
                pulou += 1
                print(f"  PULADO  {arquivo.stem}.{nome} (lento)")
                continue
            try:
                getattr(modulo, nome)()
                passou += 1
                print(f"  ok      {arquivo.stem}.{nome}")
            except Exception:
                falhou += 1
                print(f"  FALHOU  {arquivo.stem}.{nome}")
                traceback.print_exc()

    print(f"\n{passou} passaram, {falhou} falharam, {pulou} pulados")
    return 1 if falhou else 0


if __name__ == "__main__":
    raise SystemExit(main("--lentos" in sys.argv))
