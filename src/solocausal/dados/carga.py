"""Leitura de laudos a partir de arquivo."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def ler_laudos(caminho: str | Path) -> pd.DataFrame:
    """Lê um CSV de laudos, tolerando separador ',' ou ';' e vírgula decimal."""
    caminho = Path(caminho)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    laudos = pd.read_csv(caminho, sep=None, engine="python")

    # laboratórios brasileiros costumam exportar com vírgula decimal
    for coluna in laudos.columns:
        if laudos[coluna].dtype == object:
            convertido = pd.to_numeric(
                laudos[coluna].astype(str).str.replace(",", ".", regex=False),
                errors="coerce")
            if convertido.notna().mean() > 0.9:
                laudos[coluna] = convertido

    return laudos
