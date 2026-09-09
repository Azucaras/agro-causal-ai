# Estudo de caso: laudos BioAS, Minas Gerais, 2023

Este documento registra o que os dados reais permitem e não permitem concluir.
Ele existe porque o resultado negativo — o efeito do manejo não é estimável
com este desenho — é a demonstração empírica da tese do projeto, e não uma
falha a ser escondida.

## Os dados

Uma fazenda em Madre de Deus de Minas (MG), cambissolo de Mata Atlântica,
milho e feijão, camada 0–10 cm. Laudos completos da tecnologia BioAS: as três
enzimas, textura, pH, CTC, bases trocáveis, H+Al, saturação e fósforo Mehlich.

| manejo | descrição | parcelas | coletas |
|---|---|---|---|
| C | convencional | 3 | mar, jun, set, dez |
| N | policultivo recente | 3 | mar, jun, set, dez |
| P | policultivo estabelecido (anos) | 3 | mar, jun, set, dez |

São 36 linhas, mas **9 unidades experimentais**. Cada parcela foi medida
quatro vezes; tratar as coletas como observações independentes seria
pseudorreplicação e inflaria artificialmente a significância de qualquer
comparação entre manejos.

## Por que o efeito causal não é identificável

### 1. A intervenção antecede a primeira medição

Os três manejos já estavam implantados antes de março de 2023. Não existe
linha de base: toda covariável do laudo é pós-tratamento. Isso corresponde
exatamente ao cenário que a simulação do projeto mostra ter cobertura zero,
por mais amostras que se colete.

### 2. Positividade violada no fósforo

Estimar efeito causal exige sobreposição: unidades com covariáveis parecidas
precisam aparecer nos dois grupos. O fósforo Mehlich separa os grupos por
completo.

| covariável | convencional | policultivo recente | policultivo estabelecido |
|---|---|---|---|
| P Mehlich (mg/dm³) | 6,6 – 16,1 | 51,1 – 67,5 | 58,0 – 95,5 |
| CTC | 14,2 – 18,2 | 15,2 – 21,3 | 11,6 – 17,0 |
| argila (%) | 26 – 32 | 28 – 34 | 30 – 36 |
| pH | 4,9 – 6,0 | 4,9 – 5,9 | 4,9 – 5,8 |

Não há uma única parcela convencional com fósforo comparável ao de qualquer
parcela de policultivo. O escore de propensão é 0 ou 1, e o efeito deixa de
ser identificável de forma não paramétrica — não por escassez amostral, mas
por ausência de contrafactual. Ver Petersen et al. (2012).

Consequência prática: nestes dados, "policultivo" e "adubação fosfatada alta"
são estatisticamente a mesma variável. Qualquer diferença de atividade
enzimática atribuída ao manejo pode ser atribuída ao fósforo com igual
suporte empírico.

### 3. O contraste ingênuo, e por que não deve ser reportado como efeito

Comparando médias por parcela, beta-glicosidase:

| contraste | diferença | p |
|---|---|---|
| policultivo estabelecido vs convencional | +24,4 | 0,0001 |
| policultivo recente vs convencional | −9,7 | 0,005 |

Os dois são "significativos" e nenhum dos dois é um efeito causal. Note ainda
que o padrão não é monotônico: o policultivo recente está **abaixo** do
convencional. Isso é compatível com um custo transitório de conversão, mas com
três parcelas por grupo a hipótese não é testável — é apenas levantada.

## O que os dados sustentam

A comparação de médias entre grupos é confundida. A **variabilidade sazonal
dentro de cada parcela** não é, porque cada parcela funciona como seu próprio
controle: a métrica é um contraste intraparcela, imune às diferenças de nível
entre grupos.

Coeficiente de variação da atividade enzimática ao longo das quatro coletas:

| manejo | CV beta-glicosidase | CV arilsulfatase |
|---|---|---|
| convencional | 22,3 % | 8,4 % |
| policultivo recente | 16,3 % | 8,6 % |
| policultivo estabelecido | 9,2 % | 5,1 % |

A tendência é monotônica e forte para a beta-glicosidase (Spearman ρ = −0,95;
p < 0,001) e mais fraca para a arilsulfatase (ρ = −0,69; p = 0,042). O solo
convencional oscila mais que o dobro do policultivo estabelecido ao longo do
ano.

Isso continua sendo associação, não causa — as parcelas não foram alocadas ao
acaso. Mas é uma associação que sobrevive ao confundimento de nível, o que a
torna qualitativamente mais informativa que a diferença de médias.

## Ressalva sobre a leitura de gradiente

Ler C → N → P como trajetória temporal é substituição de espaço por tempo
(*space-for-time substitution*). A abordagem pressupõe que os sítios diferem
essencialmente na idade e seguem a mesma trajetória — pressuposto que a
literatura documenta como frequentemente violado por heterogeneidade
ambiental e efeitos de legado (Walker et al., 2010). Aqui ele é claramente
violado: os grupos diferem em adubação fosfatada.

## O que mudaria o quadro

Em ordem de impacto:

1. **Mais parcelas, não mais coletas.** Trinta parcelas medidas uma vez valem
   mais, para comparar manejos, do que nove medidas trinta vezes.
2. **Anos desde a conversão, por parcela.** Transforma o tratamento de
   categoria em dose contínua e permite testar a não monotonicidade como curva.
3. **Histórico de adubação fosfatada.** Sem ele, o efeito estimado é o do
   pacote inteiro, e isso precisa ser dito explicitamente.
4. **Parcelas de referência** (mata nativa ou pastagem na mesma classe de
   solo), como o próprio protocolo BioAS recomenda, para ancorar a escala.

## Referências

- Petersen, M. L. et al. Diagnosing and responding to violations in the
  positivity assumption. *Statistical Methods in Medical Research*, v. 21,
  n. 1, p. 31-54, 2012.
- Walker, L. R. et al. The use of chronosequences in studies of ecological
  succession and soil development. *Journal of Ecology*, v. 98, n. 4,
  p. 725-736, 2010.
- Mendes, I. de C. et al. *Tecnologia BioAS: uma maneira simples e eficiente
  de avaliar a saúde do solo*. Planaltina: Embrapa Cerrados, 2021.
