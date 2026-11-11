**Há bloqueios antes da execução.** Revisão somente leitura, com pequenos contraexemplos em memória. Não executei B1.3, adquiri locks, alterei arquivos ou acessei o caminho proibido.

**Correções necessárias**

1. **[P1] E4 não dá peso igual aos hosts.** Em [b1_recal.py:381](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_recal.py:381), concatenar os contrastes faz o peso depender da quantidade disponível por host, tanto nas réplicas quanto nas estimativas centrais. Exemplo verificado: oito zeros de um host e um valor 1 de outro produzem média `0,111`, quando a média com pesos iguais por host seria `0,5`. Aplicar a ponderação igual aos três critérios.

2. **[P1] As salvaguardas do bootstrap só rebaixam PASS.** [b1_recal.py:412](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_recal.py:412) preserva FAIL em bootstrap degenerado e na cauda com menos de 100 contrastes. O desenho manda UNRESOLVED nesses casos. Contraexemplo verificado: quatro hosts com oito valores `z=4` cada geram FAIL na média e na cauda, excluindo E4. Aplicar essas salvaguardas independentemente do resultado anterior.

3. **[P1] As populações de disponibilidade estão incorretas.**
   - Em [b1_recal.py:143](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_recal.py:143), `RefusalProbe` conta também recusas das variâncias auxiliares de odd/even. Verifiquei um caso PSD em que a variância do contraste já é válida, mas uma variância auxiliar zero dispara a inclusão em E1. Contar especificamente a recusa da variância do contraste.
   - [b1_recal.py:439](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_recal.py:439) exclui E2 sem eventos suficientes e E3 que retorna antes de `box_after_model`. Um exemplo com 30 contrastes em 100 tentativas reportou disponibilidade `1,0`, em vez de `0,3`.
   - [b1_recal.py:458](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_recal.py:458) também retira hosts com erro do denominador de E4. Preservar tentativas, elegibilidade, execução, fallback e disponibilidade separadamente.

4. **[P1] O fetch não garante a quota.** Os 50 MB de [b1_data.py:92](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_data.py:92) são uma estimativa, sem limite imposto ao download. Hard links escapam dessa verificação, embora `disk_used()` conte seus tamanhos; `disk_after()` ocorre somente ao final. Além disso, o lock próprio não protege a reserva de saída do screening concorrente. É necessária uma reserva compartilhada de disco, independente do ledger, e escrita limitada pelos bytes restantes. A ausência de tamanhos selados exige uma correção prospectiva do procedimento.

5. **[P2] Proveniência incompleta.** O fingerprint de [b1_recal.py:277](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_recal.py:277) cobre código e chaves dos hosts, mas não os registros C2 que fornecem as efemérides em [b1_recal.py:227](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_recal.py:227), nem os manifests efetivamente lidos. Alterações nessas entradas podem compartilhar a identidade anterior. Também faltam nos registros a configuração ativa e os hashes das funções, exigidos pela seção 0.

**O que confere**

- **Contrastes:** deslocamento de `P/4`, verificação de sobreposição e remoção das janelas verdadeiras estão coerentes. O núcleo A0 reproduz a preparação e medição de `pipeline_v52`. O z de E1 é assinado; E2 exige `e2.gls`; E3 exige GLS sem fallback. [b1_recal.py:108](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_recal.py:108)
- **E4:** confirmei **13** originais OK que passaram o gate. Usá-los é justificável, registrando a alteração de 16 para 13. O sorteio é determinístico, limitado a oito propostas sem reposição de rejeitadas; a medição usa somente background e trata o seletor como certificado. [b1_recal.py:192](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_recal.py:192)
- **Critérios:** tolerâncias, Bonferroni, chi-square, Clopper-Pearson, mínimo de 30 para FAIL, desvio conservador sem FAIL e composição seguem o desenho, ressalvados os bloqueios acima. Cornish-Fisher é aproximado: o erro observado foi cerca de `3,95e-5` com 29 graus de liberdade e `6,68e-10` com 449. A concordância próxima de `1e-10` não vale para todos os tamanhos. [b1_recal.py:312](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_recal.py:312)
- **Dados:** autenticação selada, SHA antes do hard link, SHA final e formato dos manifests estão corretos. O relatório registra metadados dos arquivos concluídos, mas perde esses campos nas falhas de download. A rede reutiliza cinco tentativas, espera de 120 s e timeout de 300 s. [b1_data.py:66](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_data.py:66)
- **Caps e locks:** as partes somam 10 CPU-h, transferidas de `b1_unallocated` antes do dispatch. Caps, identidade e lock integral estão conectados ao driver; o fetch usa outro lock. B1.3 recusará iniciar enquanto B1.2 detiver o ledger. [b1_recal.py:284](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_recal.py:284)

**REFUTED: B1.3 não está pronto para rodar nesta versão, mesmo após postar o procedimento exato no #217; corrigir os bloqueios antes.**

