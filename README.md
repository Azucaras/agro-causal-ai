# solocausal

Inferência causal sobre laudos de análise de solo de rotina.

Ferramentas de diagnóstico de solo respondem "como está este solo?". O produtor
precisa da pergunta seguinte: "e se eu mudar o manejo, quanto melhora?". Essa é
uma pergunta causal, e responder por correlação leva a recomendação errada.

Este projeto estima esse efeito a partir do laudo que laboratórios comerciais
já emitem — química, física e os bioindicadores enzimáticos da tecnologia BioAS
(Embrapa) — e, quando o efeito não é identificável, diz **qual medição está
faltando** em vez de devolver um número falsamente preciso.

## Como rodar

```bash
pip install -r requirements.txt
PYTHONPATH=src python -m solocausal.cli simular -n 600

python -m solocausal.cli esquema                    # formato esperado do CSV
python -m solocausal.cli analisar dados/exemplo/laudos_exemplo.csv
python -m solocausal.cli poder                      # curva de viabilidade
python tests/run.py                                 # suíte de testes
```

Como biblioteca:

```python
from solocausal import analisar, simular_laudos

laudos, efeito_real = simular_laudos()
resultado = analisar(laudos, efeito_real=efeito_real)

print(resultado.intervalo_total)      # (13.52, 18.15)
print(resultado.identificavel)        # True
```

## O resultado principal

Validação em dados sintéticos, onde o efeito verdadeiro (**+16,1**) é conhecido
por construção. Os dois procedimentos habituais erram — e erram para lados
opostos:

| método | estimativa |
|---|---|
| diferença bruta de médias | **+25,7** |
| ajuste por todas as covariáveis do laudo | **+7,7** |
| efeito verdadeiro | +16,1 |

O primeiro superestima: quem muda o manejo tende a já ter solo melhor. O
segundo subestima: parte das covariáveis foi medida **depois** da intervenção,
são mediadoras, e ajustar por elas desconta o efeito que se quer medir.

O que resolve não é volume de dados, é uma coluna — a medição anterior à
intervenção:

Cobertura do intervalo — a fração das repetições em que ele contém o efeito
verdadeiro (8 sementes por linha):

| talhões | sem linha de base | com linha de base |
|---|---|---|
| 300 | **0,00** | 0,62 |
| 600 | **0,00** | 0,88 |
| 1200 | **0,00** | 0,75 |

Sem a medição anterior à intervenção a cobertura é **zero em todas as
sementes**, e não melhora com o tamanho amostral. A largura do intervalo, essa
sim, cai com n — ou seja, sem linha de base o resultado fica *mais estreito em
torno do valor errado* conforme se coleta mais. Mais dados produzem mais
confiança num número enviesado.

Com linha de base a cobertura sobe para 0,62–0,88, não para 1. A variabilidade
remanescente vem do poder do teste de independência: em amostras menores o
algoritmo nem sempre recupera a aresta que liga a linha de base ao tratamento,
e quando não recupera o conjunto de ajuste fica vazio. Isso é limitação
conhecida e está registrada em `docs/decisoes.md`.

## Dados reais

`docs/estudo_de_caso_bioas.md` aplica o pipeline a 36 laudos BioAS de uma
fazenda em Minas Gerais. O diagnóstico é que o efeito **não é estimável** com
aquele desenho — os manejos precedem a primeira coleta, e o fósforo Mehlich
separa os grupos por completo (6,6–16,1 no convencional contra 51,1–95,5 nos
policultivos), violando positividade.

Isso não é uma falha do estudo: é a demonstração empírica da tese do projeto.

## Estrutura

```
src/solocausal/
├── config.py            ordem causal em camadas — a única parte que exige
│                        conhecimento agronômico
├── dados/               simulação, mock calibrado, leitura e validação de CSV
├── descoberta/          testes de independência, PC, classe de equivalência
├── estimacao/           DML, efeito heterogêneo, sensibilidade
├── prescricao.py        de tau(x) para regra de decisão e valor da política
├── pipeline.py          orquestração — devolve um objeto serializável
├── relatorio.py         formatação (só aqui se sabe o que é uma linha de texto)
├── experimentos/        curva de viabilidade
└── estudos/             análise dos dados reais

api/                     FastAPI sobre o pipeline
frontend/                interface web sem build
docs/                    método, decisões de projeto, estudo de caso
tests/                   suíte (pytest-compatível, runner próprio incluso)
```

## Interface web

```bash
uvicorn api.main:app --reload          # terminal 1
cd frontend && python -m http.server 5173   # terminal 2
```

## Limitações

Declaradas antes que alguém pergunte:

- A validação é em **dados sintéticos**. Isso prova que a implementação
  recupera o efeito quando as condições são satisfeitas — é calibração de
  instrumento, não evidência agronômica.
- **Suficiência causal** (ausência de confundidor latente) é quase certamente
  falsa em solo. O valor de robustez quantifica a fragilidade; não a elimina.
- Os testes de independência assumem **relações lineares** entre variáveis
  padronizadas. Trocar por HSIC é extensão direta.
- Os dados reais disponíveis **não sustentam prescrição**. A camada existe e
  funciona em simulação.

## Próximos passos

1. Laudos reais com linha de base — rede BioAS, cooperativas, ensaios de longa
   duração.
2. Validação em benchmarks de inferência causal (IHDP, ACIC 2016), já que PC e
   R-learner foram implementados à mão.
3. FCI no lugar do PC, para admitir confundidores latentes.

## Referências principais

Pearl (2009) · Spirtes, Glymour & Scheines (2000) · Meek (1995) ·
Maathuis, Kalisch & Bühlmann (2009) · Robinson (1988) ·
Chernozhukov et al. (2018) · Cinelli & Hazlett (2020) ·
Bang & Didelez (2023) · Mendes et al. (2021, BioAS)

Lista completa em `docs/metodo.md`.

## Licença

MIT.
