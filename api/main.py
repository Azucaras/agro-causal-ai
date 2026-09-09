"""API HTTP — ponte entre o pipeline e a interface web.

    uvicorn api.main:app --reload

O pipeline devolve um dataclass serializável, então aqui não há lógica de
análise: só transporte. Se você precisar mudar o que a API responde, mude
`Resultado.como_dicionario()` em src/solocausal/pipeline.py.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from solocausal import __version__
from solocausal.config import COLUNA_LINHA_DE_BASE, DESFECHO_PADRAO, TRATAMENTO_PADRAO
from solocausal.dados import Cenario, DESCRICAO_ESQUEMA, simular_laudos, validar
from solocausal.pipeline import analisar

app = FastAPI(title="solocausal", version=__version__)

# o front é servido de outra porta em desenvolvimento
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class PedidoSimulacao(BaseModel):
    n: int = 600
    comparar_linha_de_base: bool = True


@app.get("/saude")
def saude() -> dict:
    return {"status": "ok", "versao": __version__}


@app.get("/esquema")
def esquema() -> dict:
    return {"descricao": DESCRICAO_ESQUEMA}


@app.post("/simular")
def simular(pedido: PedidoSimulacao) -> dict:
    """Roda o pipeline em dados sintéticos com efeito verdadeiro conhecido."""
    if not 50 <= pedido.n <= 5000:
        raise HTTPException(422, "n deve estar entre 50 e 5000")

    laudos, real = simular_laudos(Cenario(n=pedido.n))
    resposta = {
        "efeito_verdadeiro": real,
        "com_linha_de_base": analisar(laudos, efeito_real=real).como_dicionario(),
    }
    if pedido.comparar_linha_de_base:
        resposta["sem_linha_de_base"] = analisar(
            laudos, ignorar=(COLUNA_LINHA_DE_BASE,),
            efeito_real=real).como_dicionario()
    return resposta


@app.post("/analisar")
async def analisar_csv(arquivo: UploadFile = File(...),
                       tratamento: str = TRATAMENTO_PADRAO,
                       desfecho: str = DESFECHO_PADRAO) -> dict:
    """Recebe um CSV de laudos e devolve o intervalo causal."""
    conteudo = await arquivo.read()
    try:
        laudos = pd.read_csv(io.BytesIO(conteudo), sep=None, engine="python")
    except Exception as erro:
        raise HTTPException(400, f"CSV ilegível: {erro}") from erro

    diagnostico = validar(laudos, tratamento, desfecho)
    if not diagnostico.ok:
        raise HTTPException(422, str(diagnostico))

    resultado = analisar(laudos, tratamento=tratamento, desfecho=desfecho)
    return {"avisos": diagnostico.avisos, "resultado": resultado.como_dicionario()}
