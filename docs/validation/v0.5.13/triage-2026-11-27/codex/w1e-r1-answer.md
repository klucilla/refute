**WEAKENED**

1. **Linhas 11–12 e 20–23. A lacuna central está coberta, mas a exceção contradiz a redação absoluta.** O patch inclui o arquivo automático, a checagem, o registro e a decisão. A regra 3 diz “nothing about a paper”, enquanto o item 2 permite hashes e metadados neutros. A exceção precisa de aprovação expressa na adoção da regra. [`data-publication.md`, regra 3](C:/Projetos/refute/docs/data-publication.md:12) · [`right-of-reply.md`, item 3](C:/Projetos/refute/docs/right-of-reply.md:41)

   **11–12**
   > Rule 3’s reply-period restriction applies to the automatic Zenodo release archive, subject only to the release-specific exception in item 2 if the maintainer adopts it.

   **20–23**
   > 2. **When a release may be published.** The maintainer approves the public text and authorizes and initiates publication after the check passes. If the list contains a paper whose results are still under embargo, publication may proceed only under an adopted exception and only if the maintainer records in the release issue that every public artifact and text contains only hashes or neutral metadata about that paper. Results may be published only after notice is sent and recorded, the phase gate passes, and any mandatory reply period ends. Publish an author’s reply only with their permission.

2. **Linhas 16–19. A lista precisa partir do conteúdo e ser refeita no commit efetivo.** Os anexos permitem apurar o prazo quando comprovam envio, data-limite e extensões. Um aviso ausente pode escapar da redação atual. Uma resposta recebida não encerra a espera, e um prazo de cortesia não adia a publicação após o gate. A tag também pode apontar para outro SHA depois da primeira checagem. [`right-of-reply.md`, itens 5–7 e ordem de publicação](C:/Projetos/refute/docs/right-of-reply.md:57) · [GitHub, arquivos por tag ou commit](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives)

   > 1. **The list.** Inventory papers from the exact release commit and planned public artifacts and text. Use the `reply/` annexes to verify notice, the effective deadline including extensions, and any delivery failure. List every open reply period and every case where eligibility is unresolved, including missing notice or annex evidence. Treat unresolved cases as embargoed. For a mandatory wait, treat a date-only deadline as open through that date. A reply does not end the wait. Mark courtesy periods as non-blocking once notice is recorded and the gate has passed. Before any public tag or publication, recompute the list against the exact commit and artifacts, recheck current reply and gate status, and record the SHA, date and list or “none” in the release issue.

3. **Linhas 24–27. Preserve o histórico e o embargo nos próprios registros.** O patch não autoriza exclusões, mas a lista, a decisão e a correção também podem expor conteúdo embargado. `CLAUDE.md` exige aprovação para exclusão fora de `.cache/` e reescrita de histórico, além de correção datada separada para registros publicados. [`CLAUDE.md`, registros](C:/Projetos/refute/CLAUDE.md:113) · [`CLAUDE.md`, aprovações](C:/Projetos/refute/CLAUDE.md:332)

   > 3. **If the check blocks publication.** Hold the release unless item 2 permits it. Preserve Git history. If a release breached this rule, prepare a separate dated correction for maintainer approval and reference it in the next release notes.
   >
   > 4. **Public record.** Record the check and decision in the release issue and summarize the list or “none” in the approved release notes. While the embargo applies, use only hashes or neutral metadata in the issue, notes and any public correction.

4. **Linhas 35–36. Inclua GitHub, PyPI e TestPyPI na regra.** O GitHub oferece ZIP e tarball da tag. O workflow monta wheel e sdist a partir de `main`, que pode ter outro SHA. A configuração atual exclui os dossiês desses pacotes, mas a checagem deve usar os artefatos efetivos. Mova a substituição para antes dos itens numerados. [`release.yml`](C:/Projetos/refute/.github/workflows/release.yml:45) · [`pyproject.toml`](C:/Projetos/refute/pyproject.toml:68) · [GitHub, arquivos de release](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)

   > Apply the check to the Zenodo archive, GitHub’s source ZIP and tarball, and the actual wheel and sdist before approval to publish to PyPI or TestPyPI. Record the build SHA and artifact hashes for each package publication.

5. **Linhas 31–34. A pergunta sobre v0.4.0 precisa preservar a incerteza da issue.** A #207 relata 30 arquivos e ausência de decisão registrada. O conteúdo não foi avaliado frente ao embargo. O Zenodo permite editar metadados no registro existente. [Issue #207, captura local](C:/Projetos/refute/.cache/v0513/runs/gh4__c7fa82bd41b7/stdout.txt:1) · [Zenodo, edição de registros publicados](https://help.zenodo.org/docs/deposit/manage-records/)

   > - **The v0.4.0 archive.** Issue #207 reports that the 2026-11-03 Zenodo archive included 30 claim and dossier files for `2309.15704`, whose reply period ran to 2026-11-18. No explicit archive decision was recorded. The issue did not assess whether the files exceeded the embargo. Should the maintainer publish a separate dated note and link it to the Zenodo record under the project’s rules for published records? Zenodo supports metadata-only notes on an existing record.

