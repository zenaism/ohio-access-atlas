# Topic 5: Fusing noisy, conflicting sources and quantifying uncertainty (truth discovery, label aggregation, map conflation, active sensing / VoI) for accessibility mapping

Verification method: every DOI below was resolved through the Crossref API (api.crossref.org/works/{DOI}), which returned matching title, authors, venue and year. JMLR pages were fetched directly, and arXiv IDs were checked with the arXiv API. The one-sentence contributions summarise each paper's abstract and well-known content. I did not re-read full texts.

## Q1. Foundational truth-discovery / label-aggregation papers

### Takeaway
Four papers form the methodological core. Dawid & Skene (1979) give per-source confusion matrices fitted by EM. TruthFinder (2008) and CRH (2014) do iterative source-reliability/truth estimation, and CRH handles mixed categorical and continuous attributes. Raykar et al. (2010) learn a classifier jointly with annotator reliability. The Li et al. (2016) survey organises the field. CRH and Raykar map most directly onto "per-source reliability per attribute, with covariates".

### Cited Findings
- **Dawid, A. P. & Skene, A. M. (1979). "Maximum Likelihood Estimation of Observer Error-Rates Using the EM Algorithm." *Applied Statistics (JRSS Series C)* 28(1):20–28.** DOI 10.2307/2346806. Contribution: it treats the true class as latent and estimates a full confusion matrix for each observer by EM, without gold labels. This is the template for per-source, per-attribute error rates on categorical attributes such as curb ramp present/absent. — [DOI](https://doi.org/10.2307/2346806)
- **Yin, X., Han, J. & Yu, P. S. (2008). "Truth Discovery with Multiple Conflicting Information Providers on the Web." *IEEE TKDE* 20(6):796–808.** DOI 10.1109/TKDE.2007.190745. Contribution: TruthFinder, the founding truth-discovery algorithm, iteratively scores source trustworthiness and fact confidence, each from the other, and models implication between similar values. — [DOI](https://doi.org/10.1109/TKDE.2007.190745)
- **Raykar, V. C., Yu, S., Zhao, L. H., Valadez, G. H., Florin, C., Bogoni, L. & Moy, L. (2010). "Learning From Crowds." *JMLR* 11(43):1297–1322.** Contribution: it jointly learns a classifier on item features, each annotator's sensitivity/specificity, and the latent truth by EM. Noisy source labels and features (slope, imagery) can therefore be combined in one model. — [JMLR](https://jmlr.org/papers/v11/raykar10a.html)
- **Li, Q., Li, Y., Gao, J., Zhao, B., Fan, W. & Han, J. (2014). "Resolving Conflicts in Heterogeneous Data by Truth Discovery and Source Reliability Estimation" (CRH). *SIGMOD 2014*.** DOI 10.1145/2588555.2610509. Contribution: an optimisation framework that jointly estimates truths and source weights across heterogeneous data types (categorical and continuous) using type-specific losses. This is the closest off-the-shelf fit for mixed attributes such as ramp presence alongside slope or width. — [DOI](https://doi.org/10.1145/2588555.2610509)
- **Li, Y., Gao, J., Meng, C., Li, Q., Su, L., Zhao, B., Fan, W. & Han, J. (2016). "A Survey on Truth Discovery." *ACM SIGKDD Explorations Newsletter* 17(2).** DOI 10.1145/2897350.2897352; arXiv 1505.02463. Contribution: a unified review that groups methods into iterative, optimisation and probabilistic-graphical-model families. It covers source dependence, input/output types and initialisation, and notes that initialising source reliability affects performance. — [DOI](https://doi.org/10.1145/2897350.2897352); [arXiv](https://arxiv.org/abs/1505.02463)
- Supporting paper: **Zhao, B., Rubinstein, B. I. P., Gemmell, J. & Han, J. (2012). "A Bayesian Approach to Discovering Truth from Conflicting Sources for Data Integration" (Latent Truth Model). *PVLDB* 5(6).** DOI 10.14778/2168651.2168656. Contribution: a Bayesian model with separate false-positive and false-negative rates for each source. This fits OSM, which tends to omit ramps rather than invent them. — [DOI](https://doi.org/10.14778/2168651.2168656)

### Inferences
- "Per-source reliability per attribute" is a Dawid–Skene/LTM confusion matrix indexed by (source, attribute). CRH extends it to continuous attributes. Raykar-style covariates (segment type, neighbourhood) let reliability vary by context.
- Wheelchair-sensor ground truth can serve as partial gold labels (semi-supervised EM), which reduces identifiability problems.

### Gaps
- I did not verify the exact pages of the Li et al. survey. Crossref confirmed the title, authors, venue and 2016 date.

## Q2. Applications of truth discovery / source reliability to geospatial, POI and map data

### Takeaway
Truth discovery has been applied to crowdsourced spatial events (Ouyang et al. 2014/2016; Garcia-Ulloa et al. 2017). OSM quality is a long-standing GIScience topic (Haklay 2010; Omar et al. 2022 for sidewalks). I found no paper that applies formal truth discovery to POI or map conflation itself. The POI-conflation literature focuses on matching.

### Cited Findings
- **Ouyang, R. W., Srivastava, M., Toniolo, A. & Norman, T. J. (2014). "Truth Discovery in Crowdsourced Detection of Spatial Events." *CIKM 2014*.** DOI 10.1145/2661829.2662003. The extended version is in *IEEE TKDE* 28(4):1047–1060 (2016), DOI 10.1109/TKDE.2015.2504928. Contribution: an unsupervised probabilistic model that jointly infers event truth, location popularity, whether participants visited, and three-way participant reliability. It handles the case where "no report" may mean "didn't visit" rather than "no event", which is analogous to 311 complaints and OSM omissions. — [CIKM DOI](https://doi.org/10.1145/2661829.2662003); [TKDE DOI](https://doi.org/10.1109/TKDE.2015.2504928); [Aberdeen record](https://abdn.elsevierpure.com/en/publications/truth-discovery-in-crowdsourced-detection-of-spatial-events/)
- **Garcia-Ulloa, D. A., Xiong, L. & Sunderam, V. (2017). "Truth Discovery for Spatio-Temporal Events from Crowdsourced Data." *PVLDB* 10(11).** DOI 10.14778/3137628.3137662. Contribution (from the title/index only, full text not read): extends truth discovery to events with spatial and temporal extent. — [DOI](https://doi.org/10.14778/3137628.3137662)
- **Haklay, M. (2010). "How Good is Volunteered Geographical Information? A Comparative Study of OpenStreetMap and Ordnance Survey Datasets." *Environment and Planning B* 37(4).** DOI 10.1068/b35097. Contribution: the foundational OSM quality study, comparing OSM against an authoritative dataset for positional accuracy and completeness. It showed that VGI quality varies across space. — [DOI](https://doi.org/10.1068/b35097)
- **Omar, K. S., Moreira, G., Hodczak, D., Hosseini, M. & Miranda, F. (2022). "Crowdsourcing and Sidewalk Data: A Preliminary Study on the Trustworthiness of OpenStreetMap Data in the US."** arXiv 2210.02350. Contribution: compares OSM sidewalk coverage across more than 50 US cities and computes an edit-history-based trustworthiness index for Seattle, Chicago and NYC. Such an index could serve as a per-segment prior on OSM reliability. — [arXiv](https://arxiv.org/abs/2210.02350)
- The POI-conflation systematic review (arXiv 2310.15320) is about matching. It notes that datasets differ in attribute focus and quality, but it does not frame the problem as reliability estimation. — [arXiv](https://arxiv.org/pdf/2310.15320)

### Inferences
- The project needs geometric matching across sources followed by attribute-level truth discovery. Matching errors propagate into the reliability estimates, and no paper found handles the two jointly.

### Gaps
- I found no verified paper that applies Dawid–Skene/truth discovery to OSM attribute values or POI conflation. The SIGSPATIAL proceedings were not exhaustively searched.

## Q3. Active learning / value of information / adaptive sampling for spatial mapping

### Takeaway
Krause, Singh & Guestrin (2008) is the canonical spatial reference: greedy mutual-information placement under a Gaussian process, near-optimal (1−1/e) by submodularity. Krause & Guestrin (2009) give VoI algorithms for chain/tree graphical models. Neither has been applied to accessibility audits.

### Cited Findings
- **Krause, A., Singh, A. & Guestrin, C. (2008). "Near-Optimal Sensor Placements in Gaussian Processes: Theory, Efficient Algorithms and Empirical Studies." *JMLR* 9(8):235–284.** Contribution: places sensors by greedily maximising mutual information between observed and unobserved locations under a GP. It proves near-optimality via submodularity and gives efficient lazy and local-kernel algorithms. — [JMLR](https://jmlr.org/papers/v9/krause08a.html)
- **Krause, A. & Guestrin, C. (2009). "Optimal Value of Information in Graphical Models." *JAIR* 35:557–591.** DOI 10.1613/jair.2737. Contribution: exact and approximate algorithms for selecting which variables to observe so as to maximise decision-theoretic VoI. This ties the choice of segments to audit to downstream decisions such as routing. — [DOI](https://doi.org/10.1613/jair.2737)
- Accessibility precedent: **Hara, K., Sun, J., Moore, R., Jacobs, D. & Froehlich, J. (2014). "Tohme: Detecting Curb Ramps in Google Street View Using Crowdsourcing, Computer Vision, and Machine Learning." *UIST 2014*.** DOI 10.1145/2642918.2647403. Contribution: combines GIS data, computer vision and crowd workers for curb ramps. A workflow controller predicts per-scene CV performance and routes only hard scenes to costlier human labelling, a cost-aware "where to spend human effort" design. — [DOI](https://doi.org/10.1145/2642918.2647403); [PDF](https://makeabilitylab.cs.washington.edu/media/publications/Hara_TohmeDetectingCurbRampsInGoogleStreetViewUsingCrowdsourcingComputerVisionAndMachineLearning_UIST2014.pdf)
- A search for GP active sensing of road or infrastructure condition found crowdsourced GP road-profile estimation, but no "which segment next" selection rule. — [arXiv 2110.06977](https://arxiv.org/abs/2110.06977)

### Inferences
- Sidewalks form a network, so a graph-kernel GP or a chain/tree graphical model along segments would be needed. VoI for routes (would auditing segment s change the recommended route?) is a better objective than entropy. Unequal audit costs (sensor runs versus imagery desk audits) call for budgeted submodular greedy selection.

### Gaps
- I found no verified paper that applies active learning or VoI to choose sidewalk or curb-ramp segments to audit.

## Q4. Work applying these to sidewalk / accessibility data

### Takeaway
**Flag: I found no paper that fuses multiple accessibility sources (OSM, municipal inventories, 311, sensors) with learned per-source reliability and a calibrated probabilistic output.** Existing accessibility work aggregates crowd labels by spatial clustering, validation voting or weighted scores, without latent-truth or reliability models.

### Cited Findings
- **Hara, K., Le, V. & Froehlich, J. (2013). "Combining Crowdsourcing and Google Street View to Identify Street-Level Accessibility Problems." *CHI 2013*.** DOI 10.1145/2470654.2470744. Contribution: shows that minimally trained crowd workers can find and label sidewalk accessibility problems in Street View with reasonable accuracy, and that aggregating multiple workers improves it. — [DOI](https://doi.org/10.1145/2470654.2470744)
- **Saha, M., Saugstad, M., Maddali, H. T., Zeng, A., Holland, R., Bower, S., Dash, A., Chen, S., Li, A., Hara, K. & Froehlich, J. (2019). "Project Sidewalk: A Web-based Crowdsourcing Tool for Collecting Sidewalk Accessibility Data at Scale." *CHI 2019*.** DOI 10.1145/3290605.3300292. Contribution: a city-scale crowdsourcing deployment in Washington DC, collecting labels on curb ramps, missing ramps, obstacles and surface problems, each with severity 1–5. A search summary reports that labels are clustered with type-specific thresholds (2 m for ramps, 7.5 m for other types). The ACM full text returned 403, so I could not confirm this directly. — [DOI](https://doi.org/10.1145/3290605.3300292)
- A Seattle equity study using Project Sidewalk data reports 150k crowd validations with 76.1% agreement. Its authors say more work is needed on crowdworker reliability and note that labels lack timestamps. — [arXiv 2211.11545](https://arxiv.org/pdf/2211.11545)
- **Hosseini, M., Saugstad, M., Miranda, F., Sevtsuk, A., Silva, C. T. & Froehlich, J. E. (2022). "Towards Global-Scale Crowd+AI Techniques to Map and Assess Sidewalks for People with Disabilities."** arXiv 2206.13677. Contribution: a pipeline that combines automated imagery-based sidewalk and crossing mapping with crowdsourced labels to produce segment and crossability scores. The scores are deterministic, not probabilistic. — [arXiv](https://arxiv.org/abs/2206.13677)
- OSM fitness for wheelchair routing has been assessed for completeness at the object, attribute and value levels (Mobasheri et al., *Sustainability* 9:997, 2017). — [MDPI PDF](https://mdpi-res.com/d_attachment/sustainability/sustainability-09-00997/article_deploy/sustainability-09-00997.pdf)

### Inferences
- Reliability-aware probabilistic fusion with VoI-based audit selection for sidewalk accessibility appears to be an open niche. This is subject to a final Scholar check (ASSETS, SIGSPATIAL, Transportation Research Record).

### Gaps
- No exhaustive ASSETS/SIGSPATIAL sweep was done. A targeted search for "Dawid-Skene" or "truth discovery" together with "sidewalk" is recommended before claiming novelty.

## Q5. What remains open (synthesis)

### Takeaway
The gaps lie mostly in adapting these methods to accessibility data, not in the methods themselves.

### Cited Findings
- Crowd reliability and data recency are explicitly unresolved in Project Sidewalk analyses. — [arXiv 2211.11545](https://arxiv.org/pdf/2211.11545)
- Truth-discovery initialisation and source dependence are listed as open issues in the survey. — [arXiv 1505.02463](https://arxiv.org/abs/1505.02463)

### Inferences (open problems)
1. **Spatially varying reliability.** Standard truth discovery assumes one reliability per source, but OSM and 311 quality varies by area (Haklay 2010; Omar et al. 2022). Reliability should be modelled as a spatial field or as a function of covariates.
2. **Missing-not-at-random signals.** The absence of a 311 complaint or OSM tag is not evidence of accessibility. Ouyang et al.'s visit indicators are the nearest precedent and need adapting to reporting propensity, which is likely correlated with demographics.
3. **Joint conflation and truth discovery.** Matching uncertainty is resolved before fusion, so its errors are not propagated.
4. **Temporal staleness.** Sources have different dates, and the truth changes as ramps are built.
5. **Source dependence.** OSM may contain imports from city GIS, which violates the independence assumptions in Dawid–Skene/TruthFinder.
6. **Calibration and transfer.** No study measures calibration of fused accessibility probabilities against sensor ground truth, or whether reliability transfers between cities (Cincinnati to Oxford).
7. **Decision-aware audit selection.** VoI on a street graph tied to routing outcomes, with heterogeneous audit costs, has not been tested.

### Gaps
- Representative figure image URLs: none verified. The ACM DL blocks fetches and the older papers have no arXiv HTML figures. Figure-bearing PDFs: [Tohme](https://makeabilitylab.cs.washington.edu/media/publications/Hara_TohmeDetectingCurbRampsInGoogleStreetViewUsingCrowdsourcingComputerVisionAndMachineLearning_UIST2014.pdf), [Li et al. survey](https://arxiv.org/pdf/1505.02463), [Hosseini et al.](https://arxiv.org/pdf/2206.13677).
