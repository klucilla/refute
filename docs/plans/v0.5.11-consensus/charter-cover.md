# Capa da minuta da carta v0.5.11 (para o assessor)

Sessão independente, somente leitura, 2026-11-24, `main` em `411173ba`. Nada commitado, rodado
ou comentado no GitHub. Contas minhas (Wilson, poder binomial, `python3 -I`): **exploratórias**.

## Resumo

- **Pergunta:** construir a `discovery.version: 5` em dois níveis: triagem (nível 1) medida na
  população e veredito de hoje (nível 2) idêntico byte a byte, sem mexer nas versões 1 a 4.
- **Etapas, cada uma com conferência determinística:** 0 congelar a especificação; 1 testes
  sintéticos antes do código; 2 mudança em `src/` (parada, com o diff revisto pelo Codex); 2b
  braço comparador TLS/wotan (condicional); 3 calibração em hospedeiras de desenvolvimento, com
  as regras commitadas antes; 4 aceitação pré-registrada; 5 revisão cega e decisão do lock.
- **Entra:** testes de falso positivo do LEO-Vetter **reimplementados dos artigos** (par e
  ímpar, secundário MS4 a MS6, tamanho, forma em V) e a unicidade (MS1 a MS3) como candidata.
  Nenhum código GPL. TLS e wotan, por ora, só como braço comparador.
- **Metas próprias da versão 5:** completude com limite inferior de Wilson de 0,85; efetividade
  de 0,90; guarda de planeta REFUTED (0,05 e 0,10, os números da segunda cláusula da D2).
- **Tetos:** 50 CPU-h (75 com o braço TLS), 30 GB de downloads, 20 GB de pico de disco.
  **Prazo:** 7 dias não são realistas (seis paradas, revisão cega, portão); proponho extensão
  para 14 dias, registrada pelo mantenedor junto com a aprovação.
- **Portão:** revisão Claude independente (há mudança de regra em `src/` e aceitação).
  **Fora:** lock, drand, alvo selado, o claim (d1) e o congelamento do pool (d1).

## As três decisões abertas (recomendação primeiro)

1. **TLS e wotan:** braço comparador isolado, e dependência só por parada posterior, se
   cumprirem uma barra escrita na etapa 0. Alternativas: dependência já; fora da versão 5.
2. **Fim da fase:** na decisão sobre o lock, em 14 dias. Alternativas: 7 dias, até a etapa 2;
   ou incluir a aceitação em hospedeiras seladas (cerca de 1.250).
3. **Estrelas novas (pool DEV-N):** até 250, atrás de uma parada; cada uma fica gasta para
   confirmação. Alternativas: só alvos expostos; decidir depois de contar as expostas.

## Onde discordo do rascunho da especificação e da proposta anterior

- **Guardas "no próprio `centroid_v5`"** (spec, 212 a 218): o módulo serve as versões 2 a 4, e
  a guarda trocaria ERROR por INCONCLUSIVE nelas. Na carta, guarda e semente só na versão 5.
- **Recusa de sensibilidade como "não avaliado"** (spec, 69 a 80): com `unassessed` no
  denominador, a completude 0,85 pode ser inalcançável por construção (parte B: 24 de 100
  decidíveis). Mantive a regra e exigi, na etapa 0, um orçamento de avaliabilidade.
- **TLS e wotan como dependência direta** (o pedido): a perda diagnosticada está nos testes,
  não na busca, e `uv.lock` entra no hash de código de todo lock futuro. Por isso, condicional.
- **Só testes de falso positivo** (plano de incorporação): sem teste de alarme falso, a
  efetividade repousa nos testes de hoje. Incluí a unicidade, com limiares calibrados aqui.
- **Forma em V:** estimador pela geometria do trapézio; só reportada até passar no sintético.
- **Consenso, entrada E, painel pareado, f*, q e os dois usos de 0,10:** estacionados. O único
  0,10 mantido tem origem escrita (D2). O teto de perdas vira a taxa usada para dimensionar N.
- **Centroide e catálogo de EBs** fora do núcleo calibrado: injeção em fluxo não valida píxel.
- **Metas congeladas na etapa 0,** não na 4; e um só z de Wilson (há dois no repositório).

## O que não consegui verificar

- **Os pins:** o repositório registra transitleastsquares 2.3.0 (2026-11-12) e wotan 2.1
  (2026-11-06); minha leitura do PyPI mostrou 2.0.1 (2026-10-11) e 1.10 (2021-09-24) como as
  mais recentes, talvez defasada. MIT nas duas páginas; o texto dentro das wheels não foi lido.
- **Compatibilidade:** numba com o numpy 2.5.3 e Python 3.13; determinismo de TLS e wotan na CI.
- **Artigos:** lidos por ferramenta que resume páginas; a cláusula "F_red > 1,8" e os limiares
  pedem conferência no PDF. A revista (AJ 170, 280) vem de nota do repositório.
- **Contagens:** hospedeiras expostas elegíveis e bytes por hospedeira (0,02 GB, não medido).
  Não rodei código nem testes. 307, 171, 1.367 e o custo do TLS carregam o rótulo da v0.5.10.
