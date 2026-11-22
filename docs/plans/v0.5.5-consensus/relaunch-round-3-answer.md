## Bloqueios

**Nenhum bloqueio para o commit.** Os dois pontos da rodada 2 foram resolvidos.

- **Portas.** A porta 1 agora compara o subgrupo com o restante do braço de planetas, com cobertura não nula e uma regra aplicável quando a taxa de referência é zero. A porta 2 usa o primeiro `FAIL` fatal decisivo, em linha com o agregador. A porta 3 usa a causa registrada pelo teste avaliado. [v0.5.6-plan.md:75](/C:/Projetos/refute/docs/plans/v0.5.6-plan.md:75) · [verdict.py:250](/C:/Projetos/refute/src/refute/core/verdict.py:250)
- **Efemérides.** O plano exige registrar a fonte, as colunas e as chaves antes da aprovação da parte A. A alternativa SPOC depende de insumos aprovados e da checagem do CSV. Se mudar o quadro amostral, exige nova aprovação antes do congelamento. A elegibilidade usa trânsitos previstos por metadados, e a cobertura observada é registrada depois do sorteio. [v0.5.6-plan.md:22](/C:/Projetos/refute/docs/plans/v0.5.6-plan.md:22) · [v0.5.6-plan.md:135](/C:/Projetos/refute/docs/plans/v0.5.6-plan.md:135) · [Registro de fontes:45](/C:/Projetos/refute/docs/plans/sources/v0.5.6-open-sources-2026-11-21.md:45)

## Ressalvas

- **Ledger e verificação.** O parser agora recusa IDs conflitantes antes de ignorar um arquivo sem evento de uso. O JUnit confirma **15 testes, zero falhas, erros ou pulos**, incluindo o caso novo. O `git diff --check` dos arquivos rastreados veio limpo. O resultado **Ruff 0** foi informado pelo mantenedor e ficou sem verificação independente nesta revisão. [ledger_v055.py:482](/C:/Projetos/refute/docs/validation/v0.5.5/ledger_v055.py:482) · [JUnit](/C:/Projetos/refute/.cache/v055/junit-ledger-3.xml)
- **Custo e execução.** Os **35,47 CPU-h** estão descritos como estimativa de planejamento baseada em outra carga. A aprovação da parte A e a checagem das colunas do SPOC continuam pendentes para a execução. O plano, o registro de fontes e o teste novo seguem como arquivos não rastreados no `git status` e precisam entrar no commit. [v0.5.6-plan.md:46](/C:/Projetos/refute/docs/plans/v0.5.6-plan.md:46)

Revisão somente leitura, sem rede, execução de scripts ou testes, ou acesso à pasta vedada.

**Veredito final: SURVIVED.**

