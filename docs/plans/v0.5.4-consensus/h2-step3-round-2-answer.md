**Le correzioni principali sono presenti**, ma restano problemi nella probabilità congiunta, nelle riserve e nei rapporti ausiliari. Nessun esperimento eseguito.

### Correzioni confermate

Normalizzazione di flusso ed errori, otto limiti Bonferroni, calibrazione separata, allocazione planetaria di 7,7 CPU-h, errori planetari conteggiati come `INCONCLUSIVE` e popolazioni binarie congelate sono implementati. La banda al solo `τ*` è valida sotto le ipotesi binomiali dichiarate. [script:98](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:98), [script:281](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:281), [script:414](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:414).

La regola sull’incremento continua a evitare il difetto di D2 della versione 5. Sono espliciti il significato limitato di PASS, l’assenza di sensibilità e il divieto di una conclusione negativa. Il riepilogo continua ad addebitare la propria CPU prima di scrivere il risultato.

### Correzioni ancora necessarie

1. **D1 resta marginale, non congiunta.** Il codice richiede probabilità ≥0,95 separatamente per EB1 ed EB2. Questo non soddisfa la condizione congiunta richiamata dal disegno. Con quattro non respinte in ciascuna popolazione congelata, i limiti producono circa **0,9577 e 0,9578**, entrambi accettati, ma il prodotto è circa **0,9173**. Richiedere il prodotto ≥0,95, esplicitando l’indipendenza delle coorti, oppure usare il limite conservatore `1 − Σ(1 − p_f) ≥ 0,95`. Il Bonferroni dei limiti di confidenza non sostituisce questa condizione predittiva. [script:429](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:429), [disegno:77](C:/Projetos/refute/docs/plans/v0.5.4-h2-step3-i3-population.md:77).

2. **La riserva CPU confonde dichiarazione e completamento.** `p not in rows_now` elimina la riserva appena una parte esiste nel ledger, anche se non è partita, è incompleta o si è fermata. Verificare il completamento e riservare il costo residuo delle parti pendenti. Inoltre, la verifica preventiva usa l’allocazione, mentre il driver può superarla e il `hard_cap` resta basato su 50 CPU-h. Per chiamare 40 CPU-h una barriera effettiva, vincolare anche proiezione e consumo durante l’esecuzione, preservando le riserve. [script:245](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:245), [ledger:230](C:/Projetos/refute/docs/validation/v0.5.4/ledger_i.py:230).

3. **`_whole` non verifica tutte le condizioni che attribuisce a C1.** Per PG/PV/PA controlla soltanto il limite superiore ≤0,20, omettendo la frazione osservata ≤0,10. Esempio: `16/150 = 0,1067`, con limite CP circa `0,1851`, passa `_whole` ma viola quel criterio. Aggiungere i criteri puntuali oppure rinominare esplicitamente il rapporto come verifica dei soli tetti CP. [script:316](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:316), [c1.py:682](C:/Projetos/refute/src/refute/packs/tess/calib05/c1.py:682).

4. **`_separation` torna a escludere gli sconosciuti.** I denominatori eliminano errori planetari e binarie non riprodotte; inoltre aggregano EB1 ed EB2. Riutilizzare i denominatori conservatori della decisione e riportare le famiglie separatamente. Queste curve restano descrittive, senza inferenza simultanea sui decili. [script:328](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:328).

5. **Resta uno stop incompatibile con il trattamento annunciato:** qualsiasi binaria eleggibile che non riproduca l’epoca di B0 interrompe il riepilogo prima di essere conteggiata come non respinta. È conservatore, ma diverge dal nuovo disegno. Rimuovere quello stop oppure dichiararlo nel disegno. [script:385](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:385).

Infine, correggere due residui testuali: “six families” nella docstring e “its own sensitivity rule fails” nel passo 2. [script:9](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:9), [step2:50](C:/Projetos/refute/docs/plans/v0.5.4-h2-step2-i3-increment.md:50).

**WEAKENED (com as correções: probabilidade conjunta de D1, reservas e barreira CPU, relatórios auxiliares e coerência dos stops).**