**WEAKENED**

### Rodada 1

1. **Parcial.** O arquivo automático entrou na regra e a exceção exige adoção explícita. A abertura ainda contradiz o tratamento dos prazos de cortesia.
2. **Parcial.** A revisão cobre aviso ausente e mudança de commit. Ainda precisa definir o efeito de um gate pendente e de registros incompletos sobre a lista.
3. **Resolvido.** O texto preserva o histórico, exige aprovação da correção datada e protege os registros públicos durante o embargo.
4. **Parcial.** GitHub, PyPI e TestPyPI entraram no escopo. Falta vincular a aprovação aos pacotes efetivamente gerados.
5. **Resolvido.** A descrição de v0.4.0 é atribuída à #207 e preserva a incerteza sobre os arquivos.

**As duas mudanças são aceitáveis.** A referência a `right-of-reply.md` deve incorporar todas as condições da seção. A pergunta sobre v0.4.0 pode ficar como está. Os fatos novos têm respaldo na issue e no workflow.

### Ajustes restantes

1. **Linhas 11–13.** “Its only exception” conflita com os prazos de cortesia não bloqueantes das linhas 32–33. “The artifacts are” também pode excluir outros anexos da release.

   > Apply the reply-period restriction in rule 3 to every public release artifact for papers still under embargo, subject to item 2 if the maintainer adopts its exception. Courtesy periods are governed by item 1. The artifacts include:

2. **Linhas 24–31.** Um prazo expirado com gate pendente pode sumir da lista. Um aviso de cortesia sem período também pode ser tratado como incompleto por faltar uma data-limite. [`right-of-reply.md`, condições de publicação](C:/Projetos/refute/docs/right-of-reply.md:88)

   > - **What the `reply/` annexes must show.** Verify the recorded notice, any delivery failure, and, where a reply period applies, its effective deadline including extensions.
   > - **What goes on the list.** Include every open reply period and every paper whose publication eligibility is unresolved, including a gate that has not passed or missing or ambiguous evidence of notice or deadline. Treat unresolved cases as under embargo.
   > - **How a mandatory wait is counted.** A date-only deadline stays open through that date in the time zone recorded for the deadline. Treat an ambiguous cutoff as unresolved. Receiving a reply does not end the wait.

3. **Linhas 34–38 e 43–44.** A checagem precisa impedir uma tag pública se falhar e identificar os pacotes aprovados. O workflow já calcula os SHA-256 antes da aprovação do ambiente. A referência à ordem deve abranger também as condições de publicação. [`release.yml`, build e publicação](C:/Projetos/refute/.github/workflows/release.yml:75)

   **34–38**
   > - **Before any public tag or publication,** recompute the list against the exact commit, actual artifacts and planned public text, using current reply and gate states. Record the commit SHA, date and list or “none” in the release issue. For each package publication, also record the build SHA and the SHA-256 of the wheel and sdist before approving the deployment.
   > 2. **When a release may be published.** The maintainer approves the public text and authorizes each public tag or publication only after the check passes under this item. The maintainer initiates publication, including by approving the deployment for package uploads.

   **43–44**
   > - Publication must meet the conditions in [right-of-reply.md](right-of-reply.md#order-notification-gate-publication), “Order: notification, gate, publication,” and the author-permission requirement in item 7.

