### 4a — SURVIVED

**Aprovo o commit proposto**, incluindo o registro desta rodada no consenso.

Confirmei no XML: **4.847 testes, zero falhas, zero erros e 91 ignorados**. O relatório dos locks registra nove verificações PASS, sem tags ausentes ou problemas.

### 4d — WEAKENED

**Aprovo a política, a contagem corrigida e manter o commit somente local.** Porém, os gates ainda não estão integralmente cumpridos.

Os logs já mostram:

- Build e testes de build: **72/72 PASS**.
- E2e: **139/139 PASS**.
- `check:launch`: **READY**, com 403 entradas.
- Unitários: **284 passaram, um falhou**.

A falha é de infraestrutura: WSL não conseguiu executar `/bin/bash` em `deploy-scripts.test.ts`. **Correção:** obter sucesso desse teste num ambiente com Bash funcional, ou dispensa explícita do mantenedor. Não registrar a suíte como integralmente aprovada.

Comparei os 27 HTMLs existentes: dois mudaram, `index.html` e `pt-br/index.html`. Isso mantém o deploy reservado ao mantenedor.

### 4b — WEAKENED

**Aprovo B, o isolamento no worktree e a parada antes de sobrescrever a saída.** Confirmei que somente os quatro registros de pacotes mudaram, sem pacotes adicionados ou removidos.

O README explica corretamente as exceções e a limitação do helper. Há, contudo, um erro no comentário do `pyproject.toml`:

> `no release uploaded less than 7 days before the cutoff`

Isso exige sete dias **antes do corte**, deslocando indevidamente a carência. Soupsieve 4.1, por exemplo, foi publicado apenas três dias antes desse corte.

**Substituição concreta:**

```toml
# Cutoff fixed at 2026-11-13T00:00:00Z, at least 7 days before
# the 2026-11-20 review. Releases uploaded after this cutoff are excluded.
```

Permanece correta a comparação futura do documento inteiro, exceto `generated`, somente após a exceção do mantenedor.

### 2 — SURVIVED

O texto da correção elimina a ambiguidade: **260/221 referem-se aos commits alcançáveis pelos ramos**, enquanto os commits fora de `main` são zero. Nenhuma correção adicional.

### 5 — WEAKENED

**A4/A5 e a exigência de ambas as VMs em `Off` resolvem os pontos anteriores.** O novo arquivador verifica hashes, cópias locais excedentes e presença das três fontes, sem apagar arquivos.

Resta uma lacuna em **B2c/B9a**: `Get-VHD` consulta o disco anexado e informa somente seu **pai imediato**. Não percorre toda a cadeia.

Uma cadeia externa com dois níveis pode passar pelas verificações e ainda depender de uma base dentro de `C:\Hyper-V`.

**Correções concretas:**

- Percorrer `ParentPath` recursivamente até a base, preservando a identificação da VM.
- Incluir os discos de checkpoints das outras VMs.
- Usar `-ErrorAction Stop` nas consultas e no preview B9. Qualquer falha de leitura deve impedir a exclusão.
- Atualizar o cabeçalho da parte D para exigir **`problems 0` e término bem-sucedido de A5**, acompanhando a saída real do script.

As precedências C7 após C5, B10 após o preview e D após A5 continuam corretas.

### 4c — SURVIVED

**Aprovo o script na revisão estática.**

A execução padrão apenas consulta e apresenta a prévia. A mutação exige `-Apply`, restringe os alvos ao manifest congelado indicado, usa `not_used` e interrompe em falha da API.

O comentário continua dentro do limite de 280 caracteres. Não executei o script nem consultei o GitHub.

