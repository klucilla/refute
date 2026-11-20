**A alteração atende à decisão informada, sem enfraquecer o teste anterior.**

1. **Status aprovado:** `as_of` corresponde a **20/11/2026**. São 14 fases: 3 released (v0.1, v0.2, v0.4), 4 ended (v0.2.1, v0.5.1–v0.5.3), 3 closed (v0.3, v0.5, v0.5.4) e 4 planned (v0.6–v0.8, v1.0), sem inProgress. As datas das encerradas são 27/10, 08/11, 10/11 e 12/11; os trechos verificados correspondem às traduções. Veja [pages.spec.ts:111](C:/Projetos/refute-site/tests/e2e/pages.spec.ts:111), [status.yaml:41](C:/Projetos/refute-site/content/status/status.yaml:41) e [en.ts:548](C:/Projetos/refute-site/src/i18n/en.ts:548).

   v0.3 está sem `results_after`; o teste exige ausência de datas e de “no earlier than”, além de confirmar o término do prazo de resposta. [status.yaml:72](C:/Projetos/refute-site/content/status/status.yaml:72), [pages.spec.ts:144](C:/Projetos/refute-site/tests/e2e/pages.spec.ts:144).

2. **Garantias preservadas ou ampliadas:** aprovação continua visível, agora exigindo estado approved, frase de aprovação e ausência de draft. Permanecem a ausência de “Current phase”, de evidências nas fases fechadas e a restrição de todos os links dessas fases a `ROADMAP.md#L…`. A proibição textual de fontes internas foi ampliada para as três fases fechadas. **Nenhuma verificação anterior foi enfraquecida ou perdida**; a retirada da espera até 18/11 acompanha o texto aprovado. [pages.spec.ts:113](C:/Projetos/refute-site/tests/e2e/pages.spec.ts:113), [pages.spec.ts:138](C:/Projetos/refute-site/tests/e2e/pages.spec.ts:138), [pages.spec.ts:147](C:/Projetos/refute-site/tests/e2e/pages.spec.ts:147).

3. **Robustez:** não identifiquei armadilhas de strict mode. As verificações coletivas usam arrays ou contagens; as individuais usam `nth()`, e o único link ended tem cardinalidade explicitamente verificada. A dependência de ordem corresponde ao `status.phases.map` da página. O HTML é estático, sem temporizadores ou dependência de outros testes. [pages.spec.ts:127](C:/Projetos/refute-site/tests/e2e/pages.spec.ts:127), [Status.astro:97](C:/Projetos/refute-site/src/views/Status.astro:97). Conferi também o [HTML gerado:12](C:/Projetos/refute-site/dist/status/index.html:12).

4. **Escopo:** branch e HEAD conferem. `git status` e `git diff HEAD` mostram somente `tests/e2e/pages.spec.ts`, com 32 inserções e 13 remoções. O diff salvo coincide. YAML, traduções e aprovação permanecem intactos.

Revisão somente leitura, sem rede ou reexecução das suítes; os resultados de execução são os informados.

SURVIVED

