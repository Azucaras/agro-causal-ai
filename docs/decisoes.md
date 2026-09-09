# Decisões de projeto

Registro do porquê, não do quê. O código diz o que faz; isto diz por que assim.

## Por que implementar o PC em vez de usar `causal-learn`

A restrição de camadas nos conjuntos separadores não é exposta pelas
bibliotecas disponíveis, e ela é necessária — sem ela o algoritmo apagava uma
aresta verdadeira nos nossos dados (ver `docs/metodo.md`). Como efeito
colateral, ter o código aberto aqui facilita defender o método em banca.

Custo aceito: a implementação é PC-stable simplificado, testa subconjuntos
apenas a partir da vizinhança de um dos nós, e limita o conjunto condicionante
a três variáveis. Para grafos maiores, migrar.

## Por que DML parcialmente linear em vez de Causal Forest

O alvo aqui é o efeito médio, não o heterogêneo. Estimar CATE exige amostra
grande, e a curva de poder mostra que não fecha com os tamanhos disponíveis.
Para o ATE, o DML parcialmente linear é mais eficiente e mais estável.

A estimação heterogênea existe em `estimacao/heterogeneo.py` e é usada pela
camada de prescrição — mas só faz sentido com dado sintético ou com centenas de
talhões.

## Por que reportar intervalo em vez de ponto

Ver `docs/metodo.md`, etapa 3. Resumindo: o CPDAG é um conjunto de grafos, e
escolher um deles arbitrariamente transforma incerteza estrutural em falsa
precisão.

## Por que dois simuladores

`dados/simulacao.py` é genérico: mecanismo simples, controlado, para validar a
implementação. `dados/mock_bioas.py` é calibrado pelas distribuições dos laudos
reais e parametriza as duas patologias encontradas no dado de campo
(acoplamento do fósforo ao manejo, ausência de linha de base), permitindo
testar cada uma isoladamente.

## Por que o front sem framework

Duas telas e três chamadas de rede. Um scaffold de React custaria mais
manutenção do que entrega nesta fase. Ver `frontend/README.md`.

## Por que um runner de testes próprio

Os testes são pytest-compatíveis. `tests/run.py` existe para ambientes sem
pytest instalado. Com pytest disponível, use `pytest tests -q`.

## Cobertura não chega a 1, e por quê

Com linha de base, a cobertura do intervalo fica entre 0,62 e 0,88 (8 sementes,
n de 300 a 1200) — não em 1. A causa é o poder do teste de independência: em
amostras menores o PC nem sempre recupera a aresta entre a linha de base e o
tratamento, e quando falha o conjunto de ajuste sai vazio, produzindo o mesmo
viés do cenário sem linha de base.

Duas saídas possíveis, nenhuma implementada ainda: relaxar alfa nessa camada
específica, ou forçar a linha de base como covariável de ajuste obrigatória
quando ela existir, em vez de deixar a decisão para o algoritmo. A segunda é
mais honesta com o conhecimento de domínio — uma medição anterior à intervenção
não pode ser mediadora — mas troca descoberta por imposição, e isso precisa ser
declarado.

O contraste que importa sobrevive: sem linha de base a cobertura é zero em
todas as sementes testadas.

## O que foi deliberadamente deixado de fora

- **Prescrição sobre dado real.** A camada existe e funciona em simulação, mas
  os dados de campo disponíveis não a sustentam. Publicar recomendações a
  partir deles seria irresponsável.
- **Validação em benchmarks (IHDP, ACIC).** Próximo passo natural: responde
  antecipadamente a "como sei que sua implementação não tem bug?", já que PC e
  R-learner foram escritos à mão.
- **Descoberta causal com variáveis latentes (FCI).** Suficiência causal é
  falsa em solo. FCI seria mais honesto, ao custo de intervalos ainda mais
  largos.
