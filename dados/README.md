# Dados

## `exemplo/`

Laudos sintéticos gerados por `solocausal.dados.simulacao`, no formato que a
CLI consome. Servem para experimentar sem precisar de dado próprio.

## `reais/`

`bioas_fazenda_liberdade_2023.csv` — 36 laudos BioAS de uma fazenda em Madre de
Deus de Minas (MG), cambissolo de Mata Atlântica, milho e feijão, camada
0–10 cm. Três manejos (convencional, policultivo recente, policultivo
estabelecido), 3 parcelas cada, 4 coletas ao longo de 2023.

**Atenção à unidade experimental:** são 36 linhas, mas 9 parcelas. Tratar as
coletas como independentes é pseudorreplicação. Use
`solocausal.estudos.bioas_2023.agregar_por_parcela`.

A análise está em `docs/estudo_de_caso_bioas.md`.
