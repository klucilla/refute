**Os pontos 1 a 4 foram atendidos na preparação. Os pontos 5 e 6 ainda precisam de ajustes.**

Conferi a separação dos comentários de [#158:9](C:/Projetos/refute/.cache/pub1119/v03/issue-158-period-ended.draft.md:9), o denominador corrigido nas notas [EN:44](C:/Projetos/refute/.cache/v05/release/release-notes-v0.5.0.en.md:44) e [PT:46](C:/Projetos/refute/.cache/v05/release/release-notes-v0.5.0.pt.md:46), os novos links e o mapeamento em [metadata-changes.md:72](C:/Projetos/refute/.cache/v05/release/metadata-changes.md:72). Os onze hashes do registro de acknowledgments coincidem com as cópias locais. Os links do site continuam condicionados à preparação de 3.1.

Restam quatro problemas materiais:

1. **O check de endereços permite correspondências parciais.** Em [address_check.py:22](C:/Projetos/refute/.cache/pub1119/tools/address_check.py:22), combinado com `search` na linha 30, um endereço sintético como `noreply@anthropic.com.example.org` passa sem alerta. Além disso, o filtro `AM` na linha 46 omite arquivos renomeados. **Correção:** validar a forma noreply completa e incluir arquivos renomeados/copiados na leitura do índice. Nos arquivos atuais examinados, encontrei **zero ocorrências proibidas**.

2. **A sequência do site ainda não funciona como escrita.**
   - O `fetch` de [roteiro:309](C:/Projetos/refute/docs/plans/publication-2026-11-19.md:309) exige previamente registro e `sources.json`, conforme [fetch-release.ts:24](C:/Projetos/refute-site/lib/fetch-release.ts:24). v0.5.0 ainda não está registrada localmente; falta essa preparação antes do comando.
   - A aceitação em [roteiro:343](C:/Projetos/refute/docs/plans/publication-2026-11-19.md:343) recusará os arquivos de tradução modificados por 3.1: [translation.mjs:29](C:/Projetos/refute-site/scripts/translation.mjs:29) exige que estejam commitados. Falta o commit local intermediário.
   - `check:launch` roda **antes da aprovação editorial**, em [roteiro:328](C:/Projetos/refute/docs/plans/publication-2026-11-19.md:328), quando essa ausência bloqueia o gate. Falta executá-lo novamente depois da aprovação e exigir `READY` antes do deploy.

3. **A ferramenta de DOI pode deixar uma aplicação parcial.** [apply_version_doi.py:31](C:/Projetos/refute/.cache/pub1119/tools/apply_version_doi.py:31) grava `CITATION.cff` antes de validar o trecho do README na linha 45. Reproduzi somente em memória: README divergente causa STOP com CITATION já alterado. O caso nominal funciona. **Correção:** validar as duas entradas e preparar as duas saídas antes da primeira gravação.

4. **A espera de CI retorna sucesso também em falha ou timeout.** [wait_main_ci.py:30](C:/Projetos/refute/.cache/tools/wait_main_ci.py:30) termina sem código de erro quando CI falha, quando permanece incompleta ou quando nenhum run aparece até o prazo. Confirmei com respostas simuladas em memória, sem rede. **Correção:** exigir a CI esperada para o SHA e retornar código diferente de zero nos demais casos.

O go-ahead **[M]**, o target da release fixado no SHA e os comandos do segundo commit estão explicitados. Não encontrei nova alteração de meta ou veredito. `calibration/v0.3/` continua sem alterações.

**WEAKENED, com as quatro correções acima.**

