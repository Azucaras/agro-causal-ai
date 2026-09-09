# Método

## O problema

Ferramentas de diagnóstico de solo estimam `P(Y | X)` — a atividade biológica
esperada dado que se observa determinado laudo. A decisão agronômica exige
`P(Y | do(T))`: quanto a atividade muda se a prática de manejo for aplicada.
São quantidades diferentes, e coincidem apenas sob ignorabilidade condicional.

A consequência prática é que erro de predição não serve de métrica. Um modelo
pode ter R² alto e efeito completamente enviesado — na verdade é o caso comum,
porque incluir mediadores melhora a predição e destrói a identificação.

## As quatro etapas

### 1. Ordem em camadas

Declara-se uma ordem parcial entre grupos de variáveis (`config.CAMADAS_PADRAO`):

```
textura  →  química de base  →  manejo  →  química pós-manejo  →  desfecho
```

Isso não é estatística, é conhecimento agronômico, e é a única parte do sistema
que exige um especialista. A ordem tem duas funções: restringe a orientação das
arestas e restringe os conjuntos separadores dos testes de independência.

**A segunda função é a que costuma passar despercebida, e sua ausência é um bug
real deste projeto.** Sem ela, o PC condicionava na arilsulfatase — um
descendente comum do tratamento e do confundidor — para testar a aresta entre a
linha de base e o tratamento. Isso é condicionar em um colisor. Em teoria a
dependência induzida deveria aparecer; na prática ela tinha sinal oposto e
magnitude parecida com a dependência real, e as duas se cancelaram. O teste
devolvia p = 0,78 e o algoritmo apagava uma aresta verdadeira.

Isso é violação de fidelidade, o pressuposto que o PC precisa e que não é
testável. A correção: ao testar `X ⊥ Y | S`, todo elemento de `S` deve estar em
camada não posterior a `max(camada(X), camada(Y))`. Referências: Bang & Didelez
(2023), Andrews, Spirtes & Cooper (2020).

O teste de regressão está em `tests/test_descoberta.py`.

### 2. Descoberta causal

Algoritmo PC (Spirtes, Glymour & Scheines, 2000), implementado em
`descoberta/pc.py`. Esqueleto por testes de independência condicional
(correlação parcial, Fisher-z), orientação por v-estruturas e regras de Meek
(1995). A saída é um CPDAG: uma classe de equivalência, não um grafo.

Implementado à mão porque a restrição de camadas nos separadores não é exposta
pelas bibliotecas disponíveis.

### 3. Efeito sob cada grafo admissível

O CPDAG não é um grafo, é um conjunto de grafos. Estimar em apenas um e
reportar o número como se fosse "o" efeito esconde a incerteza que importa.

`descoberta/equivalencia.py` enumera os membros da classe; para cada um,
`pipeline.analisar` toma os pais do tratamento como conjunto de ajuste (válido
por backdoor, por construção) e estima com DML.

O antecedente direto é o método IDA (Maathuis, Kalisch & Bühlmann, 2009).

### 4. Estimação

Double Machine Learning no modelo parcialmente linear:

```
Y = θ·T + g(Z) + ε ,   T = m(Z) + ν
```

`g` e `m` estimados por gradient boosting sob cross-fitting em 5 folds; θ sai
da regressão dos resíduos. Robinson (1988); Chernozhukov et al. (2018).

O cross-fitting não é detalhe: sem ele o viés de sobreajuste dos modelos de
nuisance vaza direto para o estimador do efeito.

## O que é reportado

Não um ponto, mas dois intervalos:

- **amplitude estrutural** — menor e maior estimativa entre os grafos;
- **intervalo total** — a estrutural somada à incerteza amostral (±1,96 EP).

Reportar só a estrutural produz intervalo degenerado quando todos os grafos
compartilham o mesmo conjunto de ajuste, o que é comum.

Se o sinal do efeito troca entre grafos, a conclusão é que os dados
observacionais não sustentam a afirmação. Isso é uma resposta legítima.

## Diagnósticos

**Suporte comum.** Propensões coladas em 0 ou 1 indicam unidades sem
contrafactual comparável. Para elas o efeito é extrapolado, não estimado.

**Valor de robustez** (Cinelli & Hazlett, 2020). Fração da variância residual
que um confundidor não medido teria de explicar, simultaneamente do tratamento
e do desfecho, para zerar o efeito.

## Pressupostos que podem quebrar

1. **Fidelidade.** Já quebrou uma vez — foi o bug do colisor.
2. **Suficiência causal** (sem confundidor latente). Quase certamente falsa em
   solo; é o que o valor de robustez tenta cercar.
3. **Linearidade** nos testes de independência. O Fisher-z assume relação
   linear entre variáveis padronizadas. Trocar por HSIC é extensão direta — a
   assinatura de `descoberta/independencia.testar` já comporta.
4. **Positividade.** Se a distribuição de uma covariável não se sobrepõe entre
   grupos, o efeito não é identificável de forma não paramétrica. Ver o estudo
   de caso: é exatamente o que acontece nos dados reais.
