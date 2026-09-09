"""solocausal — inferência causal sobre laudos de análise de solo.

Uso típico:

    from solocausal import analisar, simular_laudos

    laudos, efeito_real = simular_laudos()
    resultado = analisar(laudos, efeito_real=efeito_real)
    print(resultado.intervalo_total)
"""

from .config import CAMADAS_PADRAO
from .dados import Cenario, ler_laudos, simular_bioas, simular_laudos
from .pipeline import Resultado, analisar
from .relatorio import formatar

__version__ = "0.1.0"
__all__ = ["CAMADAS_PADRAO", "Cenario", "ler_laudos", "simular_bioas",
           "simular_laudos", "Resultado", "analisar", "formatar"]
