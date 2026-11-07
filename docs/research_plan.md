# Research plan

## Research questions
- **RQ1 (coverage):** How much wheelchair-relevant information exists for a mid-size hilly city
  (Cincinnati) and a college town (Oxford), and how is it distributed across sources,
  neighbourhoods, and populations (ACS disability prevalence)?
- **RQ2 (agreement):** Where sources overlap (OSM vs. city GIS vs. 311 vs. text vs. field audit),
  how often do they agree, and which is closest to ground truth?
- **RQ3 (fusion):** Does fusing sources measurably improve completeness and accuracy over OSM alone?
- **RQ4 (model):** Can a small language model grounded in the fused data answer accessibility
  questions accurately and, critically, **say "unknown" when the data is missing**, better than
  large general LLMs?

## Contributions, as papers
1. **Dataset + coverage/agreement study** (RQ1 to RQ3): ASSETS, CHI, W4A, ACM SIGSPATIAL, or
   *Transportation Research Record*. Artifacts: ODbL dataset, datasheet, code.
2. **Benchmark + model** (RQ4): grounded QA pairs with evidence, a human-validated test set,
   hallucination/abstention metrics, small-model fine-tune or RAG vs. frontier LLMs.

## Method
1. **Collect** (`atlas fetch`): every source becomes rows of
   `(entity, attribute, value, signal, provenance)`. Raw responses are cached for reproducibility.
2. **Conflate**: link records about the same real-world object across sources using spatial
   tolerance plus type compatibility (e.g. CAGIS ramp ↔ OSM kerb within 10 m). Report sensitivity
   to the tolerance (5/10/20 m).
3. **Ground truth**: stratified random sample (by source, neighbourhood, and signal) of about 200
   ramps, segments and entrances; two auditors; report Cohen's κ.
4. **Derive**: slope from DEM per segment; segment-level accessibility under different user
   profiles (manual vs. power chair; max incline from `research/` profiles).
5. **Benchmark**: generate questions from templates plus LLM paraphrase. The answer comes *from the
   data*, with evidence rows attached. Include unanswerable questions (no data) on purpose.
   Hold out Oxford, or held-out neighbourhoods, for a generalisation test.
6. **Model**: (a) RAG over observations, (b) small model (1 to 4 B) fine-tuned on QA, (c) frontier
   LLM zero-shot. Metrics: accuracy, evidence faithfulness, abstention F1, latency on device.

## Threats to validity (address before reviewers do)
- Coded fields can be misleading: Metro marks about 96% of stops `wheelchair_boarding=2`. Confirm
  semantics with SORTA before using.
- City GIS has geometry but almost no condition data (`ASSETCONDITION` filled on 1 of 833k).
  Presence ≠ usability.
- 311 reflects who reports, not where the barriers are (reporting bias by neighbourhood/income).
  Normalise per capita and discuss.
- Temporal drift: record retrieval dates; ramps get rebuilt and feeds change.
- Rule-based signals are heuristics; validate them against the field audit.

## Timeline (adjust with advisor)
| Weeks | Work |
|---|---|
| 1-2 | All structured sources + slopes; coverage report; emails/data requests; IRB draft |
| 3-4 | Conflation + sensitivity; audit protocol + pilot |
| 5-6 | Field audit; web/PDF extraction with validation sample |
| 7-8 | Dataset paper draft (RQ1 to RQ3) |
| 9-12 | Benchmark, models, evaluation, paper 2 |

## Questions for advisor
- Scope: City of Oxford only, or plus Oxford Township and the Miami campus beyond city limits?
- Target venue and deadline (ASSETS papers are usually due in April)?
- IRB: the field audit (no human subjects?) vs. user interviews (yes).
- Contacts at Miami SDS/Facilities, City of Oxford engineering, CAGIS, SORTA, BCRTA.
