### 1. Regra perdida? **NO**

O verificador encontrou zero linhas e zero sentenças faltantes. A comparação direta também confirmou que os três blocos foram copiados literalmente e que o restante do `CLAUDE.md` foi preservado.

### 2. Mudança de significado? **YES**

- **Publicação e Git.** O bloco original estabelecia duas proibições permanentes: outputs brutos acima de 5 MB nunca entram no Git, e o agente nunca publica um registro no Zenodo. Agora, uma sessão pode colocar um output grande no índice com `git add` antes de cogitar um commit, ou publicar um registro pequeno já preparado, sem acionar a leitura. [CLAUDE.md:221](C:/Projetos/refute/CLAUDE.md:221), [data-publication.md:13](C:/Projetos/refute/docs/agents/data-publication.md:13), [data-publication.md:19](C:/Projetos/refute/docs/agents/data-publication.md:19)
- **Referências.** Os links Markdown da política de publicação e do consenso que define os itens bloqueantes de CI passaram a apontar para `docs/agents/docs/...` quando renderizados. Os dois destinos existem sob `docs/`. A nota no cabeçalho explica a intenção de usar caminhos a partir da raiz, mas o destino dos links continua incorreto. [data-publication.md:17](C:/Projetos/refute/docs/agents/data-publication.md:17), [ci-two-level.md:15](C:/Projetos/refute/docs/agents/ci-two-level.md:15)

### 3. Gatilho insuficiente? **YES**

- **Publicação e Git.** O gatilho omite o staging de outputs grandes e a publicação de um registro Zenodo pequeno já preparado. [CLAUDE.md:221](C:/Projetos/refute/CLAUDE.md:221)
- **CI.** Uma sessão pode avaliar um run concluído como evidência de testes, ou acionar CI manualmente, sem fazer push, abrir PR, esperar por CI ou executar uma etapa condicionada a CI. O bloco também rege essas situações. [CLAUDE.md:282](C:/Projetos/refute/CLAUDE.md:282), [ci-two-level.md:29](C:/Projetos/refute/docs/agents/ci-two-level.md:29), [ci-two-level.md:44](C:/Projetos/refute/docs/agents/ci-two-level.md:44)
- **VM/JEA.** Uma verificação de rede feita na máquina do mantenedor pode ocorrer sem uma operação na VM, no endpoint JEA ou por SSH. O texto movido atribui expressamente essas verificações ao agente. [CLAUDE.md:301](C:/Projetos/refute/CLAUDE.md:301), [vm-jea.md:13](C:/Projetos/refute/docs/agents/vm-jea.md:13)

### Veredito

`CHANGE_OF_MEANING`

### Correções mínimas

- **Publicação e CI.** Recolocar os dois blocos literalmente nas posições originais em `CLAUDE.md`. Isso restaura a leitura automática e os destinos dos links, sem editar as regras.
- **VM/JEA.** Substituir o gatilho por `Before planning, assigning or performing any VM-related step, including host-side network checks, JEA endpoint operations, SSH, Administrator or Hyper-V work, read [docs/agents/vm-jea.md](docs/agents/vm-jea.md).`