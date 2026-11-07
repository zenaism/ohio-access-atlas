# Topic 4: Accessible pedestrian routing for wheelchair users (personalization, uncertainty, LLM assistants)

Method note: I checked bibliographic metadata (title, authors, venue, year, DOI) against Crossref or arXiv for every paper in the core list. Abstract-level claims come from arXiv or Crossref abstracts, or from search-result snippets. Where a claim comes only from a snippet, it is marked "(snippet)". I did not verify any representative figure-image URLs (ACM pages returned 403), so none are given.

## Core list (8 most important papers)

| # | Paper | Venue / year | DOI / URL | One-sentence contribution | Key numbers |
|---|---|---|---|---|---|
| 1 | Beale, Field, Briggs, Picton, Matthews, "Mapping for Wheelchair Users: Route Navigation in Urban Spaces" | The Cartographic Journal 43(1):68-81, 2006 | https://doi.org/10.1179/000870406X93517 | Early GIS route-planning tool (MAGUS) built from wheelchair users' situated knowledge of barriers. | Tested in Northampton, UK (snippet, [Kingston eprint](https://eprints.kingston.ac.uk/id/eprint/105)) |
| 2 | Kasemsuppakorn & Karimi, "Personalised routing for wheelchair navigation" | Journal of Location Based Services 3(1):24-54, 2009 | https://doi.org/10.1080/17489720902837936 | Canonical personalized multi-criteria wheelchair cost function over a sidewalk network, with user weights from three methods (absolute restriction, relative restriction, path reduction). | 6 criteria: width, distance, slope, surface, elevation change, sidewalk traffic; weights from a 15-question registration questionnaire ([RESNA 2016](https://resna.org/sites/default/files/conference/2016/wheelchair_seating/karimi.html)) |
| 3 | Kasemsuppakorn, Karimi, Ding, Ojeda, "Understanding route choices for wheelchair navigation" | Disability & Rehabilitation: Assistive Technology 10(3):198-210, 2015 (online 2014) | https://doi.org/10.3109/17483107.2014.898160 | User validation of personalized routing with wheelchair users on the Pitt campus. | 5 manual wheelchair users; 4 of 5 rated their most important parameters higher on the personalized route than on the shortest feasible route (snippet, [ResearchGate](https://www.researchgate.net/publication/260993502_Understanding_Route_Choices_for_Wheelchair_Navigation)) |
| 4 | Bolten & Caspi, "AccessMap Website Demonstration: Individualized, Accessible Pedestrian Trip Planning at Scale" | ASSETS 2019 (demo) | https://doi.org/10.1145/3308561.3354598 | Open-source, deployed, city-scale routing on OpenSidewalks data, with user-set limits (max incline, avoid missing curb ramps, avoid construction). | Launched 2017 (Seattle, later Bellingham and Mount Vernon); >35,000 routing requests; ~500-1,000 unique monthly users ([UW](https://urban.uw.edu/news/accessible-pedestrian-routing-tools-expand-to-three-washington-cities); usage figure from a secondary summary) |
| 5 | Bolten & Caspi, "Towards routine, city-scale accessibility metrics: Graph theoretic interpretations of pedestrian access using personalized pedestrian network analysis" | PLOS ONE, 2021 | https://doi.org/10.1371/journal.pone.0248399 | Formalizes Personalized Pedestrian Network Analysis (PPNA): per-profile weighted graphs plus equity metrics. | Metrics: Normalized Sidewalk Reach (NSR), Sidewalk Reach Quotient (SRQ); per-profile betweenness shows profiles disagree on which corridors matter |
| 6 | Kirkham & Tannert, "Using Computer Simulations to Investigate the Potential Performance of 'A to B' Routing Systems for People with Mobility Impairments" | MobileHCI 2021 | https://doi.org/10.1145/3447526.3472056 ; https://arxiv.org/abs/2107.01570 | Monte Carlo study showing that, since accessibility data are imperfect, routers should minimize barriers rather than promise to avoid them, and should present routes in terms of risk. | >460 million simulated journeys |
| 7 | Li, Pang, Labbé, Eisenberg, Hosseini, Froehlich, "Accessibility for Whom? Perceptions of Mobility Barriers Across Disability Groups and Implications for Designing Personalized Maps" | CHI 2025 | https://doi.org/10.1145/3706598.3713421 ; https://arxiv.org/abs/2502.19888 | Open dataset of barrier perception across 5 mobility-aid groups, used to drive personalized routing prototypes; the newest empirical basis for profile-specific costs. | N=190; 52 sidewalk-barrier images; cane, walker, scooter, manual WC, power WC |
| 8 | Karki, Han, Mahmud, Bhunia, Femiani, Raychoudhury, "OmniAcc: Personalized Accessibility Assistant Using Generative AI" | arXiv 2509.07220 (Sept 2025); arXiv comment: 1st Workshop on AI for Urban Planning at AAAI 2025 | https://arxiv.org/abs/2509.07220 | GPT-4-based assistant that combines satellite imagery and OSM to detect and map accessibility features, with personalized routing, hands-free navigation and Q&A. | 97.5% zero-shot crosswalk detection accuracy (Oxford, OH case study per snippet) |

Note: OmniAcc co-author Nadim Mahmud appears to match the GitHub owner of this repo (Nadim-Mahmud), so OmniAcc is likely this project's own prior work. Frame it as the baseline, not as independent literature.

Honorable mentions (verified at metadata or snippet level only):
- Neis & Zielstra, "Generation of a tailored routing network for disabled people based on collaboratively collected geodata," Applied Geography 47:70-77, 2014. Builds an OSM-based disability routing network, noting that official data lack the needed attributes ([Heidelberg record](https://heibib.ub.uni-heidelberg.de/search/Record/1735159158)).
- Mobasheri et al., 2017, Sustainability 9(6):997. OSM completeness for wheelchair routing in German cities (snippet).
- Anisha & Kirkham, "Investigating User Risk Attitudes in Navigation Systems to Support People with Mobility Impairments," OzCHI 2022, pp. 283-290, https://doi.org/10.1145/3572921.3572953 ([DBLP](https://dblp.dagstuhl.de/rec/conf/ozchi/AnishaK22.html)). Full text blocked. Per snippet, it argues that disclosing the risk of obstacles or missing data lets users avoid a route or prepare for it.
- Darko et al., "Adaptive personalized routing for vulnerable road users," IET Intelligent Transport Systems, 2022, https://doi.org/10.1049/itr2.12191. Q-learning with time-varying preferences and AHP weights; beats shortest-path and min-cost baselines (snippet).
- Xiong, Zong, Xue, Wu, "OPENPATH: A Supervisor-Specialist Agent System for Personalized, Accessible, and Multi-stop Urban Trip Planning," arXiv 2606.07486, June 2026. LLM agents parse intent and classical solvers route over curated accessibility data; applied to NYC ADA gaps. No quantitative results in the abstract.
- "MyPath: An AI-powered accessibility assistant for wheelchair navigation," Miami University thesis (OhioLINK ETD accession miami1783434731663158). An LLM conversational interface on an OSM wheelchair routing engine, apparently building on OmniAcc ([ETD](https://etd.ohiolink.edu/acprod/odb_etd/ws/send_file/send?accession=miami1783434731663158&disposition=inline)). PDF too large to fetch; author and year unverified.

## Classic and recent wheelchair routing systems

### Takeaway
The field runs from GIS barrier-mapping tools (Beale et al. 2006), to personalized multi-criteria cost functions (Kasemsuppakorn & Karimi 2009/2015), to deployed open city-scale routing on dedicated sidewalk graphs (AccessMap/OpenSidewalks 2017-2019; PPNA 2021).

### Cited Findings
- Beale et al. 2006 built MAGUS, a decision tool based on wheelchair users' situated knowledge, tested in Northampton, UK — [DOI](https://doi.org/10.1179/000870406X93517); [Kingston eprint](https://eprints.kingston.ac.uk/id/eprint/105)
- U-Access (2006) computes the shortest feasible route for three ability levels (unaided, aided mobility, wheelchair) (snippet) — [Springer PDF mirror](https://springerlink.bibliotecabuap.elogim.com/content/pdf/10.1007/s10109-006-0021-1.pdf)
- Kasemsuppakorn & Karimi 2009 used 6 ADA- and survey-based criteria; users set weights via 15 questions; the network is a 2008 Pitt-campus sidewalk database — [RESNA 2016](https://resna.org/sites/default/files/conference/2016/wheelchair_seating/karimi.html); [DOI](https://doi.org/10.1080/17489720902837936)
- AccessMap (Bolten & Caspi, UW) launched in 2017. Users set limits on hills, missing curb cuts and construction. It has served >35,000 routing requests across three WA cities — [UW Urban](https://urban.uw.edu/news/accessible-pedestrian-routing-tools-expand-to-three-washington-cities); [UW News 2017](https://www.washington.edu/news/2017/02/01/new-route-finding-map-lets-seattle-pedestrians-avoid-hills-construction-accessibility-barriers/); [demo DOI](https://doi.org/10.1145/3308561.3354598)
- AccessMap lacks real-time sidewalk closures and transit data (snippet) — [UW ECE](https://www.ece.uw.edu/spotlight/new-accessmap-offers-seattle-pedestrians-more-accessible-routes/)
- PPNA builds per-profile weighted pedestrian graphs and introduces the NSR/SRQ equity metrics — [PLOS ONE](https://doi.org/10.1371/journal.pone.0248399)

### Inferences
- For Cincinnati and Oxford, the OpenSidewalks data model plus a per-profile cost function is the de facto reference design. NSR/SRQ give a ready-made city-scale comparison across profiles.

### Gaps
- I could not access full texts of Beale 2006 or the AccessMap demo, so I have no algorithm details or figure URLs.

## Personalized cost functions and preference learning

### Takeaway
Most systems use explicit, hand-set preferences (questionnaire weights, incline thresholds, avoid flags). Preferences learned from behavior or feedback are rare, and none I found were wheelchair-specific with real-user validation.

### Cited Findings
- Three weighting methods (absolute restriction, relative restriction, path reduction) produce user-specific sidewalk parameter weights (snippet) — [ResearchGate](https://www.researchgate.net/publication/220232927_Personalised_routing_for_wheelchair_navigation)
- In the 2015 user study, 4 of 5 subjects rated their key parameters higher for the personalized route than for the shortest feasible route (snippet) — [ResearchGate](https://www.researchgate.net/publication/260993502_Understanding_Route_Choices_for_Wheelchair_Navigation)
- CHI 2025: N=190 across 5 mobility-aid groups rated their confidence on 52 barrier images. Perceptions differ by group, with some shared concerns. The authors built a personalized routing prototype and released an open dataset — [arXiv 2502.19888](https://arxiv.org/abs/2502.19888)
- A fuzzy approach aggregates user-reported confidence with obstacles into user-specific segment costs (snippet) — [ResearchGate](https://www.researchgate.net/publication/349031749_User-Specific_Route_Planning_for_People_with_Motor_Disabilities_A_Fuzzy_Approach)
- A collaborative system refines edge costs from user feedback (snippet) — [ResearchGate](https://www.researchgate.net/publication/327327987_A_Collaborative_System_for_Suitable_Wheelchair_Route_Planning)
- VRUPOD (IET ITS 2022): Q-learning with time-varying preferences and AHP weights, outperforming shortest and min-cost baselines on path cost (snippet) — [Wiley](https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/itr2.12191)

### Inferences
- The CHI 2025 dataset is the best available prior for profile-specific barrier costs. An LLM could elicit preferences conversationally and map them onto these priors, replacing the 2009 15-question form.

### Gaps
- I found no paper that learns wheelchair cost weights from route accept/reject or pairwise feedback and validates them with wheelchair users.

## Routing under uncertainty / missing accessibility data

### Takeaway
Missing and inaccurate data are widely acknowledged. The strongest evidence (Kirkham & Tannert 2021) says routers should minimize and communicate risk rather than claim barrier-free routes. Formal probabilistic or risk-aware wheelchair routing algorithms are underdeveloped.

### Cited Findings
- More than 460 million simulated journeys show routers should minimize rather than fully avoid barriers, given the limits of documentation — [arXiv 2107.01570](https://arxiv.org/abs/2107.01570); [DOI](https://doi.org/10.1145/3447526.3472056)
- The same authors know of no widely used accessible navigation system that presents routes in terms of risk (snippet) — [arXiv PDF](https://arxiv.org/pdf/2107.01570)
- OzCHI 2022 studies user risk attitudes and argues for disclosing the risk of obstacles or missing data (snippet; full text blocked) — [DBLP](https://dblp.dagstuhl.de/rec/conf/ozchi/AnishaK22.html)
- A cost-benefit study finds wheelchair routers regularly give unnecessary detours and/or inaccessible routes, and that data inaccuracy is always a risk (snippet) — [ResearchGate](https://www.researchgate.net/publication/335219833_Analyzing_Accessibility_Barriers_Using_Cost-Benefit_Analysis_to_Design_Reliable_Navigation_Services_for_Wheelchair_Users)
- OSM sidewalk data are largely missing. Heidelberg mined wheelchair GPS traces to add sidewalk geometry, and Neis & Zielstra 2014 built a tailored OSM network — [Heidelberg](https://heibib.ub.uni-heidelberg.de/search/Record/1572011440); [Heidelberg](https://heibib.ub.uni-heidelberg.de/search/Record/1735159158)
- PathAble (open-source Waterloo pilot, not peer-reviewed) treats "unknown" as a distinct state and labels its output as advice, not certification — [GitHub](https://github.com/s2002kumar/pathable)

### Inferences
- A practical design for the atlas: three-valued segment attributes (known-ok / known-barrier / unknown), a per-profile penalty on unknown segments, and risk disclosure to the user. This follows the Kirkham line of work, though that work specifies no algorithm.

### Gaps
- I found no peer-reviewed wheelchair-specific stochastic or robust shortest-path formulation with calibrated probabilities that a segment is inaccessible. It may exist in OR/transport venues my searches did not surface.

## Recent (2023-2026) LLM-based navigation assistants for people with disabilities

### Takeaway
LLM work on wheelchair routing is new and mostly preprints. OmniAcc (2025, likely this project's group) and OPENPATH (2026) are the closest. Both keep classical graph routing and use the LLM for perception, intent parsing or dialogue.

### Cited Findings
- OmniAcc: GPT-4 plus satellite imagery plus OSM; personalized routing, hands-free navigation, Q&A; 97.5% crosswalk detection — [arXiv 2509.07220](https://arxiv.org/abs/2509.07220)
- OPENPATH: a supervisor and specialist LLM agents with classical optimization; multi-stop trips; NYC ADA-gap and job-access analysis; no numbers in the abstract — [arXiv 2606.07486](https://arxiv.org/abs/2606.07486)
- MyPath (Miami University thesis): an LLM conversational interface on an OSM wheelchair routing engine — [OhioLINK ETD](https://etd.ohiolink.edu/acprod/odb_etd/ws/send_file/send?accession=miami1783434731663158&disposition=inline)
- Adjacent work for blind and low-vision users: NaviGPT (arXiv 2410.04005) — [arXiv](https://arxiv.org/html/2410.04005v1). Other titles from search that I did not read: Accessibility Scout (arXiv 2507.23190), CapNav (arXiv 2602.18424), "Position: Assistive Agents Need Accessibility Alignment" (arXiv 2605.13579), and "Do VLMs See What Sensors Feel?" (arXiv 2606.07642)

### Inferences
- The dominant architecture is "LLM as interface and orchestrator, graph router as solver." Neither OmniAcc nor OPENPATH reports real-user route-level evaluation in its abstract.

### Gaps
- I did not verify the contents of Accessibility Scout, CapNav, the position paper, the VLM street-view paper, or the MyPath author and year.

## What remains open

### Takeaway
The main open problems are principled handling of unknown segments, explainable and risk-aware route communication, learned or conversationally elicited personalization, and real-user evaluation (especially of LLM assistants).

### Cited Findings
- Routers should minimize and communicate risk, and no widely used system presents routes in terms of risk — [Kirkham & Tannert 2021](https://arxiv.org/abs/2107.01570)
- Perceptions differ by mobility-aid group, so one "wheelchair" profile is not enough — [Li et al. CHI 2025](https://arxiv.org/abs/2502.19888)
- AccessMap lacks real-time closures (snippet) — [UW ECE](https://www.ece.uw.edu/spotlight/new-accessmap-offers-seattle-pedestrians-more-accessible-routes/)
- User validation is small-N: 5 manual wheelchair users in 2015 — [DOI](https://doi.org/10.3109/17483107.2014.898160)
- LLM assistants report detection accuracy or no numbers, not route outcomes with users — [OmniAcc](https://arxiv.org/abs/2509.07220); [OPENPATH](https://arxiv.org/abs/2606.07486)

### Inferences
- Open items for the project: (1) an explicit unknown-segment policy with per-profile risk tolerance; (2) route explanations citing the source and recency of each attribute, which suits a multi-source map plus LLM; (3) conversational preference elicitation validated against the CHI 2025 data; (4) field studies with wheelchair users in Oxford and Cincinnati comparing personalized and shortest routes; (5) guardrails so the LLM never asserts accessibility that the graph does not support.

### Gaps
- I verified no representative figure-image URLs.
- I found no peer-reviewed (non-preprint) 2023-2026 LLM wheelchair-routing paper with a user study.
