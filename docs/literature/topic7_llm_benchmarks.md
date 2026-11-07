# Topic 7: LLM benchmarks for geospatial/accessibility QA, abstention, asymmetric errors, knowledge conflict

Verification legend: [V] = metadata checked this session on arXiv / ACL Anthology / proceedings page. [K] = well-known paper cited from background knowledge; URL is canonical but was NOT re-fetched this session. Check [K] items before citing.

## Shortlist: the 8 most important papers for our benchmark

1. **MAP: A Benchmark on Multimodal Accessibility Planning for Real World Places.** Armitage, Tsochantaridis, Mazzone, Yan, Narayanan, Ebling. arXiv preprint 2608.28384, 28 Aug 2026, no venue yet. https://arxiv.org/abs/2608.28384 [V]
   - What it does: presented as the first benchmark of AI assistants answering accessibility questions about real places (feature check, search-by-feature, visual evidence retrieval). It uses safety-ordered labels such as Safe, Unverified, Contradictory, and "Useful but Potentially Unsafe".
   - Numbers: 4,514 places in Zurich; 59 features in 4 disability categories; 1,800 test prompts; 10 models (GPT-5.x, Claude Sonnet 4.6/5, Gemini 3.x, Grok 4.x, Qwen2.5-VL, Gemma 4). Web search made "Contradictory" more common for most closed models (Claude Sonnet 4.6 went from 1 to 85).
   - Figure: https://arxiv.org/html/2608.28384v1/MAP_fig_v4.png (inferred from the relative path in the HTML)
2. **MapEval: A Map-Based Evaluation of Geo-Spatial Reasoning in Foundation Models.** Dihan et al. ICML 2025 (PMLR v267). https://arxiv.org/abs/2501.00316 ; https://proceedings.mlr.press/v267/dihan25a.html [V]
   - What it does: 700 multiple-choice map questions (180 cities, 54 countries) in text, API, and visual modes.
   - Numbers: the best model (Claude-3.5-Sonnet) gets 66.33% on the text mode; every model trails humans by more than 20 points, with distance, direction, and routing the weakest areas. Sources disagree on 28 vs 30 models.
3. **Mitigating Geospatial Knowledge Hallucination in LLMs: Benchmarking and Dynamic Factuality Aligning (GeoHaluBench).** S. Wang, Feng, Liu, Pei, Y. Li. Findings of EMNLP 2025, pp. 870-888. DOI 10.18653/v1/2025.findings-emnlp.45 ; https://aclanthology.org/2025.findings-emnlp.45/ [V]
   - What it does: a hallucination benchmark built from a geospatial knowledge graph (POIs, areas of interest, roads; entity/relation/attribute levels; 13 cities). It tests 20 LLMs and finds more hallucination in less-represented regions. A KTO-based alignment method improves results by more than 29.6%.
4. **AccessEval: Benchmarking Disability Bias in Large Language Models.** Panda, Agarwal, Patel. EMNLP 2025 (Social Impact Award), pp. 32504-32530. DOI 10.18653/v1/2025.emnlp-main.1653 [V]
   - What it does: tests 21 LLMs on paired neutral vs disability-aware queries (6 domains, 9 disability types). Disability-aware queries get more factually wrong answers and more denials, and some answers default wrongly to wheelchair accommodations.
5. **AbstentionBench: Reasoning LLMs Fail on Unanswerable Questions.** Kirichenko, Ibrahim, Chaudhuri, Bell (Meta FAIR). NeurIPS 2025 (D&B). https://arxiv.org/abs/2506.09038 [V]
   - What it does: 20 datasets, more than 35k abstention-worthy questions, 6 scenarios (answer unknown, false premise, stale data, subjective, underspecified context, underspecified intent), 20 models.
   - Numbers: reasoning fine-tuning cuts abstention recall by about 24% on average; scale helps little; the LLM judge agrees with humans 88% of the time.
6. **Know Your Limits: A Survey of Abstention in Large Language Models.** Wen et al. (UW / AI2). TACL vol. 13, 2025, pp. 529-556. DOI 10.1162/tacl_a_00754 ; arXiv 2407.18418 [V]
   - What it does: the reference taxonomy of abstention methods, benchmarks, and metrics, seen from three perspectives: query, model, and human values.
7. **Retrieval-Augmented Generation with Conflicting Evidence (RAMDocs + MADAM-RAG).** H. Wang, Prasad, Stengel-Eskin, Bansal (UNC). arXiv 2504.13079, 2025. The paper says it appeared at COLM 2025; I did not confirm this. https://arxiv.org/abs/2504.13079 [V for arXiv]
   - What it does: RAMDocs mixes ambiguity, misinformation, and noise in retrieved documents, with a varying number of supporting documents per answer.
   - Numbers: the best baseline (Llama3.3-70B) reaches only 32.60 exact match. Multi-agent debate improves results by up to 11.40% on AmbigDocs (v2 abstract; v1 says up to 15.80%). Gains shrink when evidence and misinformation are imbalanced.
8. **Why Language Models Hallucinate.** Kalai, Nachum, Vempala, Zhang (OpenAI). arXiv 2509.04664, Sept 2025. https://arxiv.org/abs/2509.04664 [V]
   - What it does: argues that binary grading rewards guessing, and proposes explicit confidence targets: "Answer only if you are >t confident, since mistakes are penalized t/(1-t) points, while correct answers receive 1 point, and an answer of 'I don't know' receives 0 points."
   - Numbers: 9 of the 10 major benchmarks reviewed give no credit for IDK; WildBench gives partial credit. This is the most direct template for our asymmetric scoring.

Strong runners-up / foundations:
- **Reliable VQA: Abstain Rather Than Answer Incorrectly.** Whitehead et al. ECCV 2022. https://arxiv.org/abs/2204.13631 [V]. Introduces "Effective Reliability", which charges a cost c for a wrong answer and 0 for abstaining; it is the closest existing cost-sensitive QA metric. A learned selector raises coverage at 1% risk from 6.8% to 16.3%.
- **Language Models (Mostly) Know What They Know.** Kadavath et al. (36 authors, Anthropic). arXiv 2207.05221, 2022. [V]. Introduces P(True) self-evaluation and P(IK) "I know" prediction. Calibration improves with scale, but P(IK) generalizes less well to new tasks.
- **Know What You Don't Know: Unanswerable Questions for SQuAD (SQuAD 2.0).** Rajpurkar, Jia, Liang. ACL 2018. https://aclanthology.org/P18-2124/ [K]. Adds about 50k adversarial unanswerable questions; this is where the "unanswerable QA" paradigm comes from.
- **Selective Question Answering under Domain Shift.** Kamath, Jia, Liang. ACL 2020. https://aclanthology.org/2020.acl-main.503/ [K]. Risk-coverage evaluation of QA with a calibrator under distribution shift.
- **Selective Classification for Deep Neural Networks.** Geifman & El-Yaniv. NeurIPS 2017. [K]. The original risk-coverage curve framework.
- **Knowledge Conflicts for LLMs: A Survey.** Xu, Qi, Guo, C. Wang, H. Wang, Y. Zhang, W. Xu. EMNLP 2024, pp. 8541-8565. DOI 10.18653/v1/2024.emnlp-main.486 ; arXiv 2403.08319 [V]. Sorts conflicts into context-memory, inter-context, and intra-memory types.
- **Wheelpedia** (ASSETS 2024). "From Information Seeking to Empowerment: Using LLM Chatbot in Supporting Wheelchair Life in Low Resource Settings". DOI 10.1145/3663548.3675609 [V via search result]. A WhatsApp LLM chatbot deployed with wheelchair users in Nigeria and Kenya. It covers assistive-technology information, not venues, and has no error benchmark.
- **"I wouldn't say offensive but...": Disability-Centered Perspectives on LLMs.** Gadiraju et al. FAccT 2023. DOI 10.1145/3593013.3593989 [V via search result]. Found that chatbots fixate on wheelchairs and physical disability when asked about disability in general.

---

## LLM geospatial knowledge/reasoning benchmarks (2023-2026)

### Takeaway
Frontier models are far from reliable on map reasoning. They stay below about 67% on MapEval, are weakest on distances, directions, and routing, and hallucinate POI/road facts more in less-represented regions.

### Cited Findings
- MapEval: 700 MCQs, 180 cities, 54 countries, textual/API/visual modes. Claude-3.5-Sonnet scored best at 66.33% (textual); all models are more than 20% behind humans; distances, directions, route planning, and place-specific reasoning are hardest — [arXiv 2501.00316](https://arxiv.org/abs/2501.00316), [PMLR](https://proceedings.mlr.press/v267/dihan25a.html)
- Model count reported as 28 (arXiv abstract) vs 30 (ICML listing): a minor inconsistency — [ICML](https://icml.cc/virtual/2025/poster/44415)
- GeoHaluBench: geospatial-KG-based hallucination benchmark, 20 LLMs. Taxonomy covers entity/relation/attribute levels and POI/AOI/road elements in 13 cities. Models invent non-existent urban entities, and hallucination is higher for less-represented areas. KTO alignment gives an improvement of more than 29.6% — [ACL Anthology](https://aclanthology.org/2025.findings-emnlp.45/), [GitHub](https://github.com/tsinghua-fib-lab/GeospatialHallucination)

### Inferences
- Slope-constrained routing ("max 5% slope") combines the weakest MapEval skills (routing, distance) with attribute facts that are rarely documented. Expect closed-book frontier models to do very poorly, which supports including a RAG-over-map condition.
- GeoHaluBench's regional finding suggests that Ohio small towns will show more hallucination than downtown Columbus. Consider stratifying by place popularity.

### Gaps
- I did not re-verify older geospatial-knowledge papers (e.g., GeoLLM, ICLR 2024; GPT4GEO, 2023; "Language Models Represent Space and Time", ICLR 2024) this session, so they are left out of the cited list.

## LLMs for accessibility / disability information or navigation (2023-2026)

### Takeaway
MAP (Aug 2026) is the only benchmark I found that evaluates LLMs on place-level accessibility claims. Other work evaluates disability bias (AccessEval), deploys chatbots without error benchmarks (Wheelpedia), or targets blind/low-vision navigation rather than mobility.

### Cited Findings
- MAP: billed as the first benchmark of multimodal AI as an assistant for accessibility-aware place planning. Tasks are claim verification (feature check, search-by-feature) and visual evidence retrieval — [arXiv 2608.28384](https://arxiv.org/abs/2608.28384)
- MAP data: 4,514 Zurich places, 34 areas, 257 place types, 59 features across mobility/vision/hearing/cognition. 1,800 test prompts (900 feature-check, 600 search-by-feature, 300 visual) — [arXiv HTML](https://arxiv.org/html/2608.28384v1)
- MAP labels: any contradicted claim makes a response "Contradictory"; "Useful but Potentially Unsafe" is used for mixed responses; "Unverified" is used for unresolved claims. The ordering is safety-weighted, but there are no numeric cost weights — [arXiv HTML](https://arxiv.org/html/2608.28384v1)
- MAP: search increased "Contradictory" labels for most closed models (Claude Sonnet 4.6 from 1 to 85; Grok 4.5 from 94 to 211). Visual evidence was correct for 250/300 with Gemini 3.6 Flash — [arXiv HTML](https://arxiv.org/html/2608.28384v1)
- MAP ground truth combines Google Places, Ginto, official sites, reviews, and images. Conflicts are resolved by recency, source type, and agreement; unresolved conflicts are set to null and kept in provenance — [arXiv HTML](https://arxiv.org/html/2608.28384v1)
- MAP limitations: one city; evidence is skewed toward mobility (82.7% of places have mobility evidence vs 4.4% for hearing); no journey-level (route) requirements; the auto-rater (Gemini 3.1 Pro) is also an evaluated model; only 30 human-checked samples; a single run at T=0 — [arXiv HTML](https://arxiv.org/html/2608.28384v1)
- Internal inconsistency in MAP: the text says Gemini 3.1 Pro exceeded 200 "Useful and Safe" with search, but Table 2 shows 89 — [arXiv HTML](https://arxiv.org/html/2608.28384v1)
- AccessEval: 21 LLMs, 6 domains, 9 disability types, paired neutral vs disability-aware queries. Disability-aware queries get more factual errors and denials — [ACL Anthology](https://aclanthology.org/2025.emnlp-main.1653/)
- Wheelpedia (ASSETS 2024): an LLM WhatsApp chatbot for wheelchair users in Nigeria/Kenya, two-month deployment, assistive-technology information — [ACM DL](https://dl.acm.org/doi/fullHtml/10.1145/3663548.3675609)
- Disability-centered perspectives (FAccT 2023): chatbots fixate on wheelchairs and physical disability — [ACM DL](https://dl.acm.org/doi/fullHtml/10.1145/3593013.3593989)
- An analogous accessibility-auditing result: in a PDF accessibility benchmark, Claude-3.5 fabricated alt text in 32% of "Cannot Tell" cases and tended to default to "Passed". This is a bias toward assuming compliance, i.e., exactly the false-"accessible" error we care about — [arXiv 2509.18965](https://arxiv.org/abs/2509.18965)

### Inferences
- MAP is the closest prior work and must be cited and positioned against. Our benchmark differs in five ways: (a) US/Ohio rather than Zurich; (b) route-level questions (slope, A-to-B), which MAP explicitly omits; (c) explicit unanswerable and conflicting-source items rather than nulling them out; (d) a numeric asymmetric harm metric rather than ordinal labels; (e) a comparison with small on-device models.
- The PDF-audit "default to compliant" finding gives direct motivation for weighting false-accessible errors more heavily.

### Gaps
- I found no published ASSETS/CHI study that quantifies LLM error rates on wheelchair venue or route questions besides MAP. The blind/low-vision navigation LLM work I found (e.g., IJHCS 2025 electrotactile route preview) is not about mobility.

## Abstention / selective prediction / unanswerable benchmarks

### Takeaway
Abstention is still unsolved: reasoning models abstain less, and scale does not fix it. The field has standard taxonomies (Wen et al.) and benchmarks (AbstentionBench, SQuAD 2.0), but none is specific to geography or accessibility.

### Cited Findings
- AbstentionBench: 20 datasets, more than 35k questions, 6 scenarios. Reasoning models (DeepSeek R1 Distill, s1.1) show about a 24% average drop in abstention recall vs their instruction-tuned bases; models express uncertainty in reasoning traces but still give definite final answers; system prompts help only partly; the LLM judge is 88% accurate vs humans — [arXiv 2506.09038](https://arxiv.org/abs/2506.09038), [NeurIPS 2025](https://mlanthology.org/neurips/2025/kirichenko2025neurips-abstentionbench)
- Wen et al. survey: defines abstention as a spectrum from partial (hedged) to full ("I don't know") and frames it from query, model, and human-values perspectives. TACL 13:529-556, DOI 10.1162/tacl_a_00754 — [arXiv 2407.18418](https://arxiv.org/abs/2407.18418)
- Kadavath et al.: large models are well calibrated on multiple-choice/true-false questions; P(True) self-evaluation works and improves with scale; P(IK) can be trained but generalizes imperfectly to new tasks; P(IK) rises when relevant source material is in context — [arXiv 2207.05221](https://arxiv.org/abs/2207.05221)
- Embodied-QA abstention (AbstainEQA) and the geospatial open-data system OGD4All (30 negative/unanswerable examples) show abstention spreading into spatial domains — [arXiv 2512.04597](https://arxiv.org/html/2512.04597v1), [arXiv 2602.00012](https://arxiv.org/pdf/2602.00012) (preprints, not deeply verified)

### Inferences
- Our "unanswerable because the map lacks the tag" items fit AbstentionBench's "Answer Unknown" and "Underspecified Context" scenarios. "Stale data" maps onto outdated OSM/Google data.
- Kadavath's finding that P(IK) rises with in-context sources predicts that RAG will abstain better, but MAP shows search also increases contradictions. Measure both.

### Gaps
- SQuAD 2.0 (Rajpurkar et al., ACL 2018) and Kamath et al. 2020 were not re-fetched this session (marked [K]).

## Cost-sensitive / asymmetric-error evaluation; risk-coverage

### Takeaway
There are established templates for penalizing wrong answers more than abstentions: Effective Reliability (cost c) and Kalai et al.'s t/(1-t) confidence-target scoring. None of them distinguishes the direction of an error (a false "yes" vs a false "no"), and that distinction is the core of our metric.

### Cited Findings
- Whitehead et al. ECCV 2022: frames VQA as selective prediction using coverage and risk. The Effective Reliability metric "places a larger cost on incorrect answers compared to abstentions". A learned multimodal selector raises coverage at 1% risk from 6.8% to 16.3% (2.4x) — [arXiv 2204.13631](https://arxiv.org/abs/2204.13631), [ECCV](https://www.ecva.net/papers/eccv_2022/papers_ECCV/html/2576_ECCV_2022_paper.php)
- Kalai et al. 2025: hallucinations persist because binary grading rewards guessing. They propose "Answer only if you are >t confident, since mistakes are penalized t/(1-t) points, while correct answers receive 1 point, and an answer of 'I don't know' receives 0 points". Only 1 of the 10 dominant benchmarks they reviewed (WildBench) gives any IDK credit — [arXiv 2509.04664](https://arxiv.org/abs/2509.04664)

### Inferences
- A natural metric for us: +1 for correct, 0 for abstain, -c_FA for a false "accessible", -c_FN for a false "not accessible", with c_FA > c_FN. Report it across several thresholds or costs, as Kalai et al. suggest, plus risk-coverage curves split by error direction.

### Gaps
- I found no LLM QA paper that scores directional (false-positive vs false-negative) harm with abstention. Classic cost-sensitive classification exists but was not surveyed here.

## Knowledge-conflict / conflicting-evidence RAG benchmarks

### Takeaway
Conflicting-evidence RAG is hard: the best baselines reach about 33 EM on RAMDocs. The standard taxonomy separates context-memory conflicts from inter-context conflicts, and our conflicting-source items are inter-context.

### Cited Findings
- Xu et al. survey (EMNLP 2024): three conflict types (context-memory, inter-context, intra-memory) and solutions grouped by goal (faithful to context, discriminating misinformation, disentangling sources, improving factuality) — [ACL Anthology](https://preview.aclanthology.org/setup/2024.emnlp-main.486), [arXiv 2403.08319](https://arxiv.org/abs/2403.08319)
- RAMDocs/MADAM-RAG: combines ambiguity, misinformation, and noise. Llama3.3-70B gets 32.60 EM. Per-document agents debate, with an aggregator. Gains are up to 11.40% on AmbigDocs (v2) or up to 15.80% on misinformation (v1). A large gap remains when evidence is imbalanced — [arXiv 2504.13079](https://arxiv.org/abs/2504.13079)
- MAP handles accessibility source conflicts by resolution or nulling, not by testing models on them — [arXiv HTML](https://arxiv.org/html/2608.28384v1)

### Inferences
- "OSM says wheelchair=yes, a Google review says three steps" is an inter-context conflict. The right answer is arguably "sources conflict" plus a conservative recommendation, which our scoring should reward explicitly.

### Gaps
- ConflictBank (NeurIPS 2024) and FaithEval were not verified this session.

## What remains open

### Takeaway
I found NO published benchmark that combines accessibility QA with deliberately unanswerable items, conflicting-source items, and an asymmetric (direction-aware) harm metric. MAP (2026) is the nearest. It has safety-ordered labels and an "Unverified"/"None" option, but it nulls out conflicts, has no numeric asymmetric cost, no route/slope questions, and no on-device model comparison.

### Cited Findings
- MAP explicitly omits journey-level requirements and nulls unresolved conflicts — [arXiv HTML](https://arxiv.org/html/2608.28384v1)
- Searches combining accessibility QA + abstention + OSM found nothing beyond MAP, AccessEval, and general abstention benchmarks — see search results above ([AbstentionBench](https://arxiv.org/abs/2506.09038), [AccessEval](https://aclanthology.org/2025.emnlp-main.1653/))

### Inferences
- Open problems our benchmark could address: (1) direction-aware harm scoring for accessibility; (2) route-level constraint reasoning (slope, curb cuts); (3) conflict-aware answers ("sources disagree"); (4) calibration and abstention of small on-device models vs frontier vs RAG; (5) US/Ohio coverage and regional hallucination disparities; (6) handling stale data.

### Gaps
- This was a limited search of about 15 tool calls. ACM DL (ASSETS/CHI 2025-2026) was not searched exhaustively, so a niche venue paper could exist.
