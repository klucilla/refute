**As quatro correções da rodada 2 foram aplicadas. Resta um ajuste no registro de aprovação do site.**

- **Endereços:** `fullmatch` e leitura do índice com `ACMR -z` corrigidos em [address_check.py:23](C:/Projetos/refute/.cache/pub1119/tools/address_check.py:23) e [linha 43](C:/Projetos/refute/.cache/pub1119/tools/address_check.py:43). Os casos sintéticos passaram; os arquivos de publicação examinados continuam sem ocorrências proibidas.
- **DOI:** os dois textos são validados antes das gravações, em [apply_version_doi.py:34](C:/Projetos/refute/.cache/pub1119/tools/apply_version_doi.py:34). Confirmei em memória o caso nominal e a recusa com README divergente, sem gravação.
- **CI:** os oito cenários conferem com os retornos de [wait_ci_strict.py:30](C:/Projetos/refute/.cache/pub1119/tools/wait_ci_strict.py:30). O roteiro exige código 0 antes do tag.
- **Site:** registro antes do fetch, commit antes da aceitação e gate depois da aprovação estão na ordem corrigida, em [roteiro:309](C:/Projetos/refute/docs/plans/publication-2026-11-19.md:309), [334](C:/Projetos/refute/docs/plans/publication-2026-11-19.md:334) e [359](C:/Projetos/refute/docs/plans/publication-2026-11-19.md:359).

**Ajuste restante:** [roteiro:361](C:/Projetos/refute/docs/plans/publication-2026-11-19.md:361) manda atualizar SHA-256, data e fundamento de `approval.json`, mas omite **`approved.site_commit`**. O campo atual ainda aponta para `f03c3e8`, em [approval.json:12](C:/Projetos/refute-site/content/status/approval.json:12). Seguindo apenas os campos descritos, a aprovação nova manteria a referência ao commit antigo.

**Correção:** atualizar também `approved.site_commit` para o SHA completo do commit de **3.3**, e conferir essa igualdade antes do commit dos registros.

Não encontrei outro problema material novo. Os onze hashes das fontes conferem, os destinos locais dos links existem e `calibration/v0.3/` permanece sem alterações. Nenhuma operação de publicação foi executada.

**WEAKENED, com a correção de `approved.site_commit` no roteiro.**

