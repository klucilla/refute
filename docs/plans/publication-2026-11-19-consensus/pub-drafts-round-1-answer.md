A base científica e os hashes conferem, mas **há correções antes da publicação**. Revisão local de `3757b7f` e dos rascunhos, sem rede ou alterações.

1. **#158 anuncia anexos antes de existirem.** O roteiro publica o comentário em [publication-2026-11-19.md:49](C:/Projetos/refute/docs/plans/publication-2026-11-19.md:49), mas o [rascunho de #158:9](C:/Projetos/refute/.cache/pub1119/v03/issue-158-period-ended.draft.md:9) já diz “now attached”. Os anexos só vêm na etapa 1.5. Publicar inicialmente apenas o estado do prazo e anunciar os anexos depois do push. Além disso, uma extensão permite continuar as partes 2 a 4 ([roteiro:25](C:/Projetos/refute/docs/plans/publication-2026-11-19.md:25)), mas deve bloquear especificamente a frase do site que declara o prazo encerrado.

2. **Explicitar o denominador de T2c.** As notas [EN:39](C:/Projetos/refute/.cache/v05/release/release-notes-v0.5.0.en.md:39) e [PT:41](C:/Projetos/refute/.cache/v05/release/release-notes-v0.5.0.pt.md:41) apresentam “2 → 0” sob as 100 curvas. Esse resultado corresponde às **97 estrelas sem as três de desenvolvimento**, conforme [c2/report.json:266](C:/Projetos/refute/calibration/v0.5/runs/c2/report.json:266). Acrescentar essa qualificação.

3. **Os links obrigatórios ainda não estão completos.** Nas notas, `calibration/v0.5/gate/` aparece como código, sem hyperlink ([EN:13](C:/Projetos/refute/.cache/v05/release/release-notes-v0.5.0.en.md:13)). O [Zenodo:11](C:/Projetos/refute/.cache/v05/release/zenodo.draft.json:11) oferece somente o endereço da pausa para os encerramentos. No [diff do site:58](C:/Projetos/refute/.cache/pub1119/site-status-draft.diff:58), a fonte da pausa fica em `internal_sources`, que não são renderizadas. Incluir links públicos dos encerramentos e da pausa; no site, explicitar também **a decisão de 2026-11-13**.

4. **A seção 6 não cobre integralmente a exigência de fontes.** Os registros nomeados existem e sustentam as principais declarações sobre Apache, Gaia, ExoFOP, Archive e TESS-EB. Porém, [metadata-changes.md:72](C:/Projetos/refute/.cache/v05/release/metadata-changes.md:72) dispensa os acknowledgments antigos por antecederem #34. Isso não atende à exigência atual de cobrir **todas** as declarações dos rascunhos. Registrar e mapear em `sources/` os pedidos de crédito ainda sustentados apenas pelo README, como [Lightkurve:629](C:/Projetos/refute/.cache/v05/release/README.draft.md:629), Astropy e Astroquery.

5. **O check de privacidade não verifica a proibição principal.** O roteiro usa esse check em [publication-2026-11-19.md:146](C:/Projetos/refute/docs/plans/publication-2026-11-19.md:146), mas sua [expressão:14](C:/Projetos/refute/.cache/v051/tools/privacy_check.py:14) procura caminhos, `AppData` e nome de usuário. Não procura e-mails nem identificadores de mensagens. **Não encontrei esses dados dos autores nos textos e anexos previstos**, mas o roteiro precisa de uma verificação específica antes do push.

6. **O roteiro ainda não é inteiramente executável como solicitado.** A atualização do DOI fica em “same checks” ([roteiro:237](C:/Projetos/refute/docs/plans/publication-2026-11-19.md:237)); a parte do site permanece em instruções gerais ([roteiro:246](C:/Projetos/refute/docs/plans/publication-2026-11-19.md:246)). Expandir comandos e resultados esperados, incluindo CI associado ao SHA. Separar explicitamente o **[M] go-ahead para anexar** da etapa [A] de execução ([roteiro:83](C:/Projetos/refute/docs/plans/publication-2026-11-19.md:83)). Fixar também o `--target` da release no SHA verificado, em vez de `main` ([roteiro:224](C:/Projetos/refute/docs/plans/publication-2026-11-19.md:224)).

As demais verificações solicitadas passaram:

- Os estados correspondem ao ROADMAP e aos encerramentos. As duas tabelas do README deixaram de mostrar v0.5 em andamento. Não encontrei alteração de meta, inviabilidade declarada ou resultado apresentado como descoberta/confirmado.
- Os passos 1 a 5 de #162 estão contemplados. Conferi os três hashes e tamanhos retidos, os três novos manifestos e seus conteúdos.
- O ensaio preserva exatamente os **5.644 bytes** originais do registro. `annex_record` reconhece os cinco anexos ([verify_dossiers.py:117](C:/Projetos/refute/calibration/v0.3/verify_dossiers.py:117)).
- A análise da causa coincide com o `run.py` fornecido, o commit declarado nos claims e os logs; preserva `INCONCLUSIVE` e `undetermined`.
- Não encontrei destinos locais ausentes nos links conferidos. URLs externas não foram acessadas; os links de `v0.5.0` dependem do tag futuro.
- `calibration/v0.3/` permanece sem alterações.

**WEAKENED, com as correções acima.**

