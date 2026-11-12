## 1. Driver e orçamento

**A correção corresponde ao desenho solicitado.** A comparação estrutural de `execute` encontrou apenas a marca v3, a reconciliação antecipada, `cap = rule + crash`, a projeção medida e sua anotação.

- A medição segue exatamente a regra descrita: batches fechados usam `max(seconds, committed)`; reconciliados e abertos usam `committed`. [budgeted_v3.py:45](C:/Projetos/refute/docs/validation/v0.5.4/budgeted_v3.py:45)
- A cobrança da queda permanece em `spent_seconds`, no consumo registrado, no guard e em `finish`. O teto recebido do chamador continua limitando o cap por `min(rule + crash, hard_cap_hours)`. [budgeted_v3.py:92](C:/Projetos/refute/docs/validation/v0.5.4/budgeted_v3.py:92), [budgeted_v3.py:105](C:/Projetos/refute/docs/validation/v0.5.4/budgeted_v3.py:105), [budgeted_v3.py:147](C:/Projetos/refute/docs/validation/v0.5.4/budgeted_v3.py:147)
- Gates, identidade, archive, total, hard maximum, condições de parada e fechamento foram preservados. A marca recusa uma parte anterior com identidade, consumo ou tentativas, antes de arquivar ou reconciliar. [budgeted_v3.py:58](C:/Projetos/refute/docs/validation/v0.5.4/budgeted_v3.py:58), [budgeted_v3.py:77](C:/Projetos/refute/docs/validation/v0.5.4/budgeted_v3.py:77)

**Duas ressalvas:** a reconciliação agora precede a verificação de `stop.json` feita pelo driver, podendo alterar charges antes de recusar esse stop, embora não permita executar sob ele. Convém preservar também essa ordem de recusa. Além disso, o watchdog mantém sua tolerância de 10% sobre o **cap ajustado**, incluindo `crash`; não representa um limite de 110% apenas sobre CPU medida. [budgeted_v3.py:102](C:/Projetos/refute/docs/validation/v0.5.4/budgeted_v3.py:102), [driver.py:486](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:486)

Não encontrei retirada da cobrança nem aumento do hard cap recebido.

## 2. Testes

Confirmei no [JUnit existente:1](C:/Projetos/refute/.cache/v054/tests/junit-budgeted-v3.xml:1): **5 passaram, 0 falhas, 0 erros, 0 ignorados**. Não executei novamente.

Os testes são offline, usam shards sintéticos e ledger em `tmp_path`. Demonstram conclusão sob v3, cobrança conservada e recusa da identidade antiga. [test_v054_budgeted_v3.py:45](C:/Projetos/refute/tests/test_v054_budgeted_v3.py:45), [test_v054_budgeted_v3.py:79](C:/Projetos/refute/tests/test_v054_budgeted_v3.py:79), [test_v054_budgeted_v3.py:104](C:/Projetos/refute/tests/test_v054_budgeted_v3.py:104)

**Correções necessárias na força das afirmações:**

- A “interrupção” é um charge aberto fabricado, sem execução anterior nem sidecars. Cobre esse estado sintético, não o ciclo completo de interrupção e retomada. Acrescentar um estado coerente com ledger já marcado v3 e checkpoint parcialmente concluído. [test_v054_budgeted_v3.py:55](C:/Projetos/refute/tests/test_v054_budgeted_v3.py:55)
- O controle v0.5.2 aceita qualquer `stopped`. Deve exigir especificamente a parada por projeção e conferir seu valor. [test_v054_budgeted_v3.py:101](C:/Projetos/refute/tests/test_v054_budgeted_v3.py:101)
- “Uninterrupted unchanged” não compara com v0.5.2; a desigualdade atual é insuficiente. Faltam também casos de cobrança contra hard cap/total e das três categorias de medição. [test_v054_budgeted_v3.py:112](C:/Projetos/refute/tests/test_v054_budgeted_v3.py:112)

O fluxo normal aguarda o encerramento do pool. Os testes não demonstram ausência de processos remanescentes após uma queda real, nem remoção dos diretórios temporários.

## 3. Lançador e reinício

**O caminho normal está correto:** fixa a afinidade antes de criar o filho, usa a Python da venv, restringe o log ao projeto e não possui fallback quando `Popen` recusa o breakaway. BelowNormal continua sendo responsabilidade do driver. Não encerra processos por nome. [launch_detached.py:75](C:/Projetos/refute/docs/validation/v0.5.4/launch_detached.py:75), [driver.py:563](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:563)

**Há uma falha de rastreabilidade:** o processo começa antes de persistir sua identidade. A criação pode ser `null`, ou a escrita do registro pode falhar deixando o processo destacado rodando sem registro válido. Exigir criação válida, protótipos ctypes completos e tratamento que não deixe o trabalho prosseguir sem identidade persistida. [launch_detached.py:50](C:/Projetos/refute/docs/validation/v0.5.4/launch_detached.py:50), [launch_detached.py:88](C:/Projetos/refute/docs/validation/v0.5.4/launch_detached.py:88)

A evidência registra o wrapper da venv, PID **16836**, e o interpretador da sonda, PID **14968**, seu filho. Isso é esperado: o [launcher do CPython](https://github.com/python/cpython/blob/v3.13.16/PC/venvlauncher.c) espera pelo interpretador. A sonda terminou quatro segundos depois, mas **isso ainda não comprova sobrevivência ao reinício do app**. Breakaway pode sair apenas de parte da cadeia de [jobs aninhados](https://learn.microsoft.com/en-us/windows/win32/procthread/nested-jobs).

O teste real deve registrar, exclusivamente em `.cache`:

- PID e criação do wrapper e do interpretador, afinidade efetiva e prioridade.
- Heartbeats com sequência e horários antes, durante e depois do fechamento e reabertura do app.
- Confirmação dos mesmos processos após o reinício, conclusão normal e ausência de remanescentes.

Mantive a revisão em somente leitura. Nenhuma sonda foi iniciada; `launch_affinity.ps1` permanece oficial.

**WEAKENED, corrigir a recusa antes da reconciliação, fortalecer os testes e garantir o registro válido do processo antes do teste real de reinício.**