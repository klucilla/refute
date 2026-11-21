**A escolha B sobrevive. Nenhum dos critérios citados torna a pausa obrigatória agora.** A justificativa precisa, porém, distinguir a futilidade de D2-F de uma demonstração de inviabilidade de D2.

Revisão documental local, sem alterações, rede, execução de scripts ou testes.

**1. Critérios de pausa: SURVIVED, com correção da justificativa**

Os critérios de G1 são independentes. A rota prospectiva aberta afasta a condição composta de **T2a**, mas não neutralizaria um critério de **D2** efetivamente satisfeito. Essa é a leitura da [seção 7 do plano](C:/Projetos/refute/docs/plans/v0.5.5-fable-core-plan.md:238).

| Critério | Evidência disponível | Resultado |
|---|---|---|
| D1-P fecha todas as saídas admissíveis, sem registro de classe aceito | `d1p-A.json` traz ambas as saídas decisivas como `unresolved` | Não satisfeito |
| D2-F coloca o piso no limite permitido em todas as variantes admissíveis | Contagens estritas de 10 ou 11; superiores de 14, incluindo desconhecidos; todas `unresolved` | Não demonstrado |
| T2a-E libera menos de 40% **e** a rota prospectiva permanece fechada | 2/85 válidos, aproximadamente 2,35%, com 17 desconhecidos; estatuto (d) mantém a rota aberta | Apenas a primeira condição satisfeita |

**D2 exige duas distinções concretas:**

- **14 contra 13 é a comparação com o limiar de “route” de D2-F**, que reserva margem para os estimadores. Não é o teto total de perdas de D2. Na população de 182, com 178 retidos por v0.4, o teto total corresponde a 22 perdas.
- A contagem superior inclui desconhecidos. Mesmo as contagens chamadas “estritas” não são demonstradas como perdas inevitáveis. O desenho e `d2f-A.json` declaram expressamente essa limitação.

Portanto, **a futilidade impede executar B para obter “route” nesse desenho; não demonstra o piso exigido pelo critério de pausa**. Isso não depende de exigir um registro formal de inviabilidade para decidir pausar: a própria grandeza necessária ao critério não foi estabelecida.

**Correção proposta para a motivação:** “R1 não estabeleceu uma rota pelos critérios congelados de seus checks. D2-F ficou fútil e não demonstrou um piso no teto de D2; T2a-E foi empiricamente limitado para a classe examinada. A rota prospectiva permanece aberta.”

**2. R2 no papel e salvaguardas: SURVIVED como preparação**

O [estatuto (d)](C:/Projetos/refute/docs/plans/v0.5.5-charter.md:145) mantém explicitamente a rota aberta e separa sua abertura das decisões de desenho. A decisão das 13h30 respeita essa separação.

As sete salvaguardas continuam obrigações:

- **(d)1:** nova versão e reprodução inalterada dos nove locks históricos. Preparar o procedimento não comprova a reprodução.
- **(d)2:** argumentos congelados antes de qualquer número da nova versão, incluindo pilotos.
- **(d)3:** revisão independente cega.
- **(d)4:** registro e publicação das duas variantes, com primária fundamentada.
- **(d)5:** confirmação em sorteios novos.
- **(d)6:** divulgação dos resultados previamente conhecidos.
- **(d)7:** verificações adversariais obrigatórias das famílias espúrias, sem tratá-las como prova suficiente contra afrouxamento.

**Correções operacionais concretas:**

1. O pacote cego não pode incluir integralmente o rascunho atual das perguntas: ele contém “98 contra 97”, resultados e referências a registros. Deve conter uma extração limpa. Excluir somente R1 e a seção de divulgação seria insuficiente.
2. Aplicar integralmente a [emenda 1(f)](C:/Projetos/refute/docs/plans/v0.5.5-charter-amendment-1.md:126): pacote construído por allowlist, manifesto anterior à revisão, sem clone, histórico ou rede; contaminação invalida a revisão e exige outro revisor.
3. Manter expressamente as duas agregações, lado a lado, para **todo número futuro de D2, D4 e T2a**.
4. A exceção “somente a suíte de testes” não pode produzir números da nova versão antes do congelamento.
5. Contabilizar as duas linhas de consumo sem transferir despesas já incorridas para contornar uma parada.

A compatibilidade da preparação está sustentada. A execução dessas salvaguardas ainda precisará ser verificada nos artefatos.

**3. Preparação de T3b: SURVIVED**

Recontagem datada e levantamento documental são compatíveis com preparar uma futura proposta, preservando a parada antes de qualquer registro ou conclusão de disponibilidade.

**Condições concretas:**

- Separar **recontagem do quadro congelado** de **construção de quadro atualizado**. O desenho de R1 exige desenho próprio de proveniência e autorização para o segundo.
- Fixar previamente quadro, domínio, limiar e leituras que fundamentariam o futuro registro. A emenda 1(e)10 impede escolher esses elementos depois de observar os dados usados.
- Registrar fonte, versão e data efetiva da leitura. Uma consulta antiga não passa a ser atual por receber uma data nova.
- Manter o uso de dados do ExoFOP como **não confirmado** onde faltar evidência documental aplicável.

A preparação não satisfaz, por si, o padrão do estatuto (c) e da emenda 1(e), nem encerra T3b ou altera a regra de avanço.

**4. Antecipação de desenho ou afrouxamento: SURVIVED**

Não identifiquei decisão substantiva antecipada no texto das 13h30. Propor uma primária e justificá-la é parte da preparação; adotá-la e congelá-la continuam sendo a parada do mantenedor.

O corte de CPU antes dos números é uma restrição procedimental. Os tetos próprios são limites de trabalho. Nenhum deles modifica metas científicas.

**Correção concreta:** manter “proposta” explícita nas primárias e não tratar perguntas do rascunho sobre limiares, agregação ou quadro de T3b como autorização para modificá-los.

**Veredito final: SURVIVED.** B, acompanhada apenas da preparação de T3b, é compatível com os documentos. **A pausa não é obrigatória agora.** A justificativa deve abandonar a equivalência entre “check fútil”, “rota científica fechada” e “piso demonstrado no limite permitido”.