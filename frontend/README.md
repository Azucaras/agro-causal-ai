# Interface web

HTML, CSS e JavaScript puros, sem build. Roda abrindo um servidor estático:

```bash
# terminal 1 — API
uvicorn api.main:app --reload

# terminal 2 — front
cd frontend && python -m http.server 5173
```

Depois abra `http://localhost:5173`.

## Por que sem framework

Nesta fase o front tem duas telas e três chamadas de rede. Um scaffold de React
custaria mais manutenção do que entrega. Se a interface crescer — múltiplos
conjuntos de dados, edição do grafo, comparação de cenários — a migração para
Vite + React é direta: o contrato com a API (`Resultado.como_dicionario()`) não
muda.

## O que a interface mostra

Duas faixas horizontais representando o intervalo causal, com uma marca na
posição do efeito verdadeiro quando ele é conhecido. A faixa fica vermelha
quando o intervalo não contém a verdade. É a forma mais direta de mostrar o
resultado central do projeto: sem a medição de linha de base, o intervalo erra
o alvo.
