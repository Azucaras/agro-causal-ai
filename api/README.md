# API

Camada fina sobre `solocausal.pipeline`. Não contém lógica de análise.

```bash
pip install fastapi uvicorn python-multipart
uvicorn api.main:app --reload
```

Documentação interativa em `http://localhost:8000/docs`.

| rota | método | o que faz |
|---|---|---|
| `/saude` | GET | verificação de disponibilidade |
| `/esquema` | GET | formato esperado do CSV |
| `/simular` | POST | roda em dados sintéticos, com e sem linha de base |
| `/analisar` | POST | recebe um CSV e devolve o intervalo causal |

O contrato de resposta é `Resultado.como_dicionario()`. Para mudar o que a API
devolve, mexa lá, não aqui.
