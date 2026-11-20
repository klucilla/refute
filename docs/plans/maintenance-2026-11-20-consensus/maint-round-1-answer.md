Revisão feita **somente por leitura local**, sem rede, sem alterações e sem acessar o diretório proibido. Datas de publicação e correções dos advisories foram consideradas conforme os dados fornecidos, sem revalidação externa.

### 4a — SURVIVED

**Aprovo soupsieve 4.1 e tornado 6.6.1 e o procedimento proposto.**

Os timestamps do lock satisfazem os 7 dias. A exigência de Python é compatível, e confirmei a ausência dos imports diretos indicados. Isso reduz a exposição às mudanças incompatíveis, mas não comprova compatibilidade de todos os consumidores transitivos.

A aprovação continua condicionada à **suíte completa e aos nove locks verificados nas respectivas tags antes do commit**. O log consultado da suíte atual ainda estava incompleto. Alterar o hash do código atual não exige atualizar os locks históricos.

### 4d — WEAKENED

**Aprovo manter 14 dias e o corte `2026-11-06T00:00:00Z`.** Esse corte satisfaz ambas as carências na data informada.

**Correção concreta:** os números 40/11/10 não descrevem o diff atual contra `bdfeba3`. Encontrei:

- 64 versões alteradas em caminhos existentes.
- 45 entradas adicionadas.
- 35 entradas removidas.
- 403 entradas finais, excluindo a raiz.

Essas são contagens por caminho do lock, incluindo plataformas e mudanças de localização. Um resumo da instalação não substitui esse inventário.

Ainda faltam os gates informados. O `READY` anterior à atualização não valida a árvore nova.

### 4b-1 — SURVIVED, opção B

**Aprovo B**, com corte `2026-11-13T00:00:00Z` e os quatro pins propostos.

A decisão do mantenedor especifica 7 dias para esse ambiente. Isso permite corrigir tornado agora, preservando os 14 dias próprios da árvore npm.

Documente explicitamente as quatro exceções ao ambiente da v0.2.0. Inclua a limitação de `pin_from_refute_lock.py`: atualmente ele mantém o corte antigo e volta a imprimir os pins históricos. O README precisa distinguir essa base das quatro substituições.

### 4b-2 — WEAKENED

**É preciso parar antes de sobrescrever a saída versionada**, sob a exigência literal apresentada.

O [comparador atual](C:/Projetos/refute-site/synthetic/generate.py:308) verifica igualdade de `scenarios` e `method`. Ele não verifica identidade dos bytes do arquivo nem igualdade do documento completo. A atualização de `generated` e do manifest modifica a saída publicada.

**Correção concreta:** obter do mantenedor uma exceção explícita permitindo essas mudanças de proveniência. Depois disso:

- Preservar o original.
- Comparar em JSON canônico **todo o documento, excluindo apenas `generated`**.
- Promover a saída somente se essa comparação passar, com o manifest recalculado.

A necessidade técnica de atualizar os hashes é válida, mas não resolve sozinha o limite da autorização.

### 4b-3 — SURVIVED

**Concordo em não incluir certifi sem autorização adicional e reportar imediatamente.**

O snapshot local registra o alerta crítico no ambiente ativo. Deixá-lo fora respeita o escopo aprovado, mas **não equivale a aceitar seu risco nem a considerar esse ambiente integralmente corrigido**. A decisão adicional cabe ao mantenedor.

### 4c — SURVIVED, opção `not_used`

**Aprovo `not_used`**, considerando o uso atual descrito: registro histórico lido para integridade, sem instalação ou execução desse ambiente pelos fluxos atuais.

O texto proposto tem **266 caracteres**, cabe no limite e descreve corretamente a razão para preservar o arquivo. As 68 ocorrências e a distribuição por pacote conferem no snapshot local.

### 2 — WEAKENED

**A correção dos números está certa**, e é correto não repetir “833 e 747 commits fora do main”. Reproduzi as contagens e confirmei ambas as ancestralidades.

**Correção concreta:** o cabeçalho publicado “Of those commits, SHAs cited…” aparece depois da coluna com zero commits externos. Isso pode atribuir 260/221 ao conjunto vazio.

Substitua por: **“Commits reachable from the branch whose SHAs are cited in files on main”**.

Preservar os ramos e registrar os comandos está correto.

### 5 — WEAKENED

O [roteiro](C:/Projetos/refute/.cache/maint1120/vm-decommission-commands.md) cobre os componentes documentados da instalação e da fase 2. As precedências **C7 após C5, B10 após B9 e D após A5** estão corretas.

**Correções necessárias antes de executá-lo:**

- **Antes de B4/B5:** exigir explicitamente ambas as VMs em `Off`. B1 mostra o estado, mas seu critério não exige isso para `refute-vm`.
- **Antes de B6:** conferir o ID e tipo do switch e confirmar que nenhuma outra VM o utiliza. A localização dos arquivos das VMs não demonstra exclusividade do switch.
- **Antes de B10:** confirmar que nenhum disco ou cadeia de discos de outra VM depende dos arquivos que serão apagados. B2 verifica apenas os anexos diretos apresentados.
- **Em A4/A5:** exigir inventário completo, sem erros de leitura, e correspondência integral entre origem, cópia e arquivo. “0 divergências” entre arquivos encontrados não comprova ausência de omissões.

O script fornecido **não inclui `admin-copy` nem `RefuteVm-backup` em `SOURCES`**. Portanto, o A5 ainda precisa de um procedimento concreto e conferido. As 69 cópias anteriores não satisfazem esse gate.

### 1 — SURVIVED

**Aprovo os dois textos no limite da evidência local consultada.**

Conferem os números científicos, datas e SHAs, incluindo os registros de fechamento, pausa, conclusão do passo 4, release e merge do site. O JUnit da publicação registra **4.847 testes, zero falhas, zero erros e 91 ignorados**. Os DOIs também conferem nos arquivos locais.

Os textos preservam `WEAKENED`, `method_status: not_validated`, a distinção entre previsão e aceitação e a ausência de declaração de inviabilidade. A linguagem permanece sobre resultados e afirmações.

Substitua `#NEWISSUE` pelo número efetivo. A referência ao `check:launch READY` é histórica, relativa à publicação anterior à atualização do item 4d.

