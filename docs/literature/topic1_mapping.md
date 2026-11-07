# Mapping sidewalk accessibility for wheelchair users: crowdsourced and open-data approaches

Verification note: every DOI below was resolved against the Crossref API (api.crossref.org/works/<doi>) on 2026-11-07, and title, authors, year and venue were confirmed, unless marked "not checked on Crossref". Figure URLs marked "(HTTP 200)" were checked with curl and returned an image. Preprints are flagged.

## Shortlist: the 8 most important papers

| # | Paper | Main contribution (one sentence) | Key numbers / figure |
|---|---|---|---|
| 1 | Saha, Saugstad, Maddali, Zeng, Holland, Bower, Dash, Chen, Li, Hara, Froehlich. "Project Sidewalk: A Web-based Crowdsourcing Tool for Collecting Sidewalk Accessibility Data at Scale." CHI 2019 (Best Paper). [doi:10.1145/3290605.3300292](https://doi.org/10.1145/3290605.3300292) | Showed that remote volunteers and paid crowdworkers "virtually walking" in Google Street View can audit a whole city's sidewalks (curb ramps, missing ramps, obstacles, surface problems, no sidewalk). | 18-month DC deployment; 797 users; 205,385 labels; 2,941 miles ([UW News](https://washington.edu/news/2019/04/18/project-sidewalk)). Recall about 68% (paid) vs 61% (registered) and 49% (anonymous); precision about 70% ([PDF](https://makeabilitylab.cs.washington.edu/media/publications/Saha_ProjectSidewalkAWebBasedCrowdsourcingToolForCollectingSidewalkAccessibilityDataAtScale_CHI2019.pdf)). Figure (HTTP 200): https://makeabilitylab.cs.washington.edu/media/publications/images/Saha_ProjectSidewalkAWebBasedCrowdsourcingToolForCollectingSidewalkAccessibilityDataAtScale_CHI2019.jpg.300x0_q85_detail.jpg |
| 2 | Hara, Le, Froehlich. "Combining Crowdsourcing and Google Street View to Identify Street-level Accessibility Problems." CHI 2013. [doi:10.1145/2470654.2470744](https://doi.org/10.1145/2470654.2470744) | Foundational paper: established Street View imagery plus crowd labeling as a valid way to find sidewalk accessibility problems. Its follow-up, Tohme (UIST 2014, [doi:10.1145/2642918.2647403](https://doi.org/10.1145/2642918.2647403)), added computer vision for curb-ramp detection. | Accuracy numbers not extracted (see Gaps). |
| 3 | Duan, Kiami, Milandin, Kuang, Saugstad, Hosseini, Froehlich. "Scaling Crowd+AI Sidewalk Accessibility Assessments: Initial Experiments Examining Label Quality and Cross-city Training on Performance." ASSETS 2022. [doi:10.1145/3517428.3550381](https://doi.org/10.1145/3517428.3550381) | Measured how crowd label quality affects deep-learning classifiers trained on Project Sidewalk labels, and whether models transfer across cities. | Companion CVPR 2022 AVA workshop paper (Hosseini et al., [arXiv:2206.13677](https://arxiv.org/abs/2206.13677)): more than 700k labels and 400k validations; 10+ cities including Mexico and the Netherlands; DC-pretrained models tested on Seattle and Newberg, OR. Figure (HTTP 200): https://makeabilitylab.cs.washington.edu/media/publications/images/Duan_ScalingCrowdAiSidewalkAccessibilityAssessmentsInitialExperimentsExaminingLabelQualityAndCrossCityTrainingOnPerformance_ASSETS222022.jpg.300x0_q85_detail.jpg |
| 4 | Askari, Snyder, Li, Saugstad, Froehlich, Eisenberg. "Validating Pedestrian Infrastructure Data: How Well Do Street-View Imagery Audits Compare to Government Field Data?" Urban Science 9(4):130, 2025. [doi:10.3390/urbansci9040130](https://doi.org/10.3390/urbansci9040130) | The most direct comparison of crowdsourced data with official city inventories: high agreement on whether a feature exists, much lower agreement on how severe its condition is. | Seattle (open-data portal) and DuPage County, IL (data-sharing agreement); 18 census block groups; agreement from about 75% (pedestrian signals) to 100% (missing sidewalks); 431 surface/obstacle labels compared against 87 Seattle segments; severity scales had to be recoded (Project Sidewalk's 1-5 vs the government's 3 levels). Figure (HTTP 200): https://makeabilitylab.cs.washington.edu/media/publications/images/Askari_ValidatingPedestrianInfrastructureDataHowWellDoStreetViewImageryAuditsCompareToGovernmentFieldData_UrbanSci2025.jpg.300x0_q85_detail.jpg |
| 5 | Bolten, Caspi. "Towards routine, city-scale accessibility metrics: Graph theoretic interpretations of pedestrian access using personalized pedestrian network analysis." PLOS ONE 16(3):e0248399, 2021. [doi:10.1371/journal.pone.0248399](https://doi.org/10.1371/journal.pone.0248399) | The main peer-reviewed AccessMap/OpenSidewalks paper: personalized pedestrian network analysis (PPNA) weights the sidewalk graph (incline, curbs and so on) by a user profile, such as a powered wheelchair. | About one-third of the downtown Seattle walkshed is inaccessible to a powered-wheelchair profile; introduces a "normalized sidewalk reach" metric ([UW CSE News](https://news.cs.washington.edu/2021/04/02/taskar-center-researchers-offer-a-roadmap-for-more-robust-modeling-of-pedestrian-mobility-on-a-city-wide-scale/)). Figure (HTTP 200): https://journals.plos.org/plosone/article/figure/image?size=large&id=10.1371/journal.pone.0248399.g001 |
| 6 | Bolten, Caspi. "Towards operationalizing the communal production and management of public (open) data: a pedestrian network case study." ACM COMPASS 2022. [doi:10.1145/3530190.3534821](https://doi.org/10.1145/3530190.3534821) | Describes how OpenSidewalks pedestrian-network data (OpenSidewalks Schema, OSM-compatible) can be produced and maintained jointly by communities and agencies. | Cites the [OpenSidewalks-Schema GitHub repository](https://github.com/OpenSidewalks/OpenSidewalks-Schema) and the AccessMap demo at ASSETS 2019 ([doi:10.1145/3308561.3354598](https://doi.org/10.1145/3308561.3354598)). |
| 7 | Omar, Moreira, Hodczak, Hosseini, Miranda. "Crowdsourcing and Sidewalk Data: A Preliminary Study on the Trustworthiness of OpenStreetMap Data in the US." arXiv:2210.02350, 2022. **PREPRINT (no venue stated)**. [arXiv](https://arxiv.org/abs/2210.02350) | Clearest measurement of how sparse OSM sidewalk data is across US cities, plus a trustworthiness index built from edit history. | 54 US cities; 80% have under 5% of roads with sidewalk tags; only Seattle and Detroit have a sidewalk-to-road ratio above 0.4; Chicago has 0.55% of roads tagged; kerb, smoothness and width "nearly absent"; surface is the most common attribute (about 40% of Seattle sidewalks). Figure (HTTP 200): https://ar5iv.labs.arxiv.org/html/2210.02350/assets/Fig2.png |
| 8 | Nichols, Groth, Quinn. "Assessing the Accuracy and Completeness of OpenStreetMap Sidewalks: A Comparative Study With Google Street View." Preventing Chronic Disease 23, Oct 2026. doi:10.5888/pcd23.260255 ([CDC page](https://www.cdc.gov/pcd/issues/2026/26_0255.htm)) | Statewide Maryland check: OSM sidewalks are accurate where present but very incomplete, worst in low-density areas. This is directly relevant to Oxford, OH. | 6,103 points in 141 tracts; sensitivity 30.2%, PPV 99.2%; sidewalk-present agreement 19.7% (low density) vs 35.4% (high density); 72.8% of points without Street View imagery were in low-density tracts. DOI not checked on Crossref. |

Strong alternates: Mobasheri et al. 2018 (Sensors) on OSM sidewalk completeness; Hosseini et al. 2023 Tile2Net (CEUS); Deitz et al. 2021 "Squeaky wheels" (Big Data & Society); Li et al. CHI 2024 LabelAId; Mobasheri et al. 2017 Wheelmap.

## Q1: Project Sidewalk: the original paper, multi-city deployments, label validation and quality, newer work

### Takeaway
Project Sidewalk grew from feasibility studies (ASSETS 2012, CHI 2013, UIST 2014 Tohme) to the CHI 2019 Best Paper. Later work covers multi-city deployments (now dozens of cities) and Crowd+AI label quality (ASSETS 2022, CHI 2024 LabelAId, ASSETS 2024 dataset). A 2025 study validated its data against government inventories.

### Cited Findings
- CHI 2019 paper metadata verified (Saha et al., doi:10.1145/3290605.3300292) — [Crossref](https://api.crossref.org/works/10.1145/3290605.3300292)
- DC deployment: 797 users, 205,385 labels, 2,941 miles over 18 months — [UW News](https://washington.edu/news/2019/04/18/project-sidewalk)
- Recall 68% for paid workers vs 61% registered and 49% anonymous volunteers, with precision about 70% — [CHI 2019 PDF](https://makeabilitylab.cs.washington.edu/media/publications/Saha_ProjectSidewalkAWebBasedCrowdsourcingToolForCollectingSidewalkAccessibilityDataAtScale_CHI2019.pdf). Per-label-type figures from the talk slides (search snippet only): missing curb ramp about 20.5% precision / 69.3% recall; surface problem about 72.6% / 27.1%; obstacle about 47.5% / 39.9% — [slides](https://makeabilitylab.cs.washington.edu/media/talks/Saha_ProjectSidewalkAWebBasedCrowdsourcingToolForCollectingSidewalkAccessibilityDataAtScale_2019.pdf)
- Earlier work in the line: Hara et al. CHI 2013 (doi:10.1145/2470654.2470744); Tohme UIST 2014 (doi:10.1145/2642918.2647403); ASSETS 2012 poster (doi:10.1145/2384916.2384989) — [Makeability project page](https://makeabilitylab.cs.washington.edu/project/sidewalk/)
- Multi-city: more than 700,000 labels and 400,000 validations; deployed in 10 additional cities including Mexico and the Netherlands — [Hosseini et al. 2022, arXiv:2206.13677](https://arxiv.org/abs/2206.13677)
- Other multi-city and context papers (workshop or preprint level): Froehlich et al., "Sidewalk Accessibility in the US and Mexico" (Civic Tech 2020, arXiv:2012.00515); Froehlich et al., "Towards Mapping and Assessing Sidewalk Accessibility Across Socio-cultural and Geographic Contexts" (Data4Good 2020, arXiv:2207.13626); Li et al., "A Pilot Study of Sidewalk Equity in Seattle" (UrbanAccess 2022, arXiv:2211.11545) — [project page](https://makeabilitylab.cs.washington.edu/project/sidewalk/)
- Scale today, which differs by source and date: 35 cities in 8 countries per a 2025 PacTrans article; 50+ cities in 10 countries and 3.4M+ labels per the GitHub README — [PacTrans](https://depts.washington.edu/pactrans/?p=8749); [GitHub](https://github.com/ProjectSidewalk/SidewalkWebpage)
- LabelAId (Li et al., CHI 2024, doi:10.1145/3613904.3642089): 36.7% better mistake inference than ML baselines; 34-participant between-subjects study; higher precision with no loss of efficiency; draws on 757,730 labels from 15 cities — [arXiv:2403.09810](https://arxiv.org/abs/2403.09810)
- Community audit case study, Oradell NJ (Li et al., CHI 2024, doi:10.1145/3613904.3642003) — [Crossref](https://api.crossref.org/works/10.1145/3613904.3642003)
- Open dataset and deep-learning benchmarks (Liu et al., ASSETS 2024 poster, doi:10.1145/3663548.3688531); perceptions across disability groups (Li et al., "Accessibility for Whom?", CHI 2025, doi:10.1145/3706598.3713421) — [Crossref](https://api.crossref.org/works/10.1145/3706598.3713421)
- Weld et al., ASSETS 2019 Best Paper: deep learning on streetscape imagery (doi:10.1145/3308561.3353798, DOI not checked on Crossref); Lalwani et al. 2026, VLM-guided annotation in Chandigarh (AI4UP workshop, arXiv:2602.09216, not checked independently) — [project page](https://makeabilitylab.cs.washington.edu/project/sidewalk/)

### Inferences
- Core set for the review: CHI 2013 (origin), CHI 2019 (deployment), ASSETS 2022 or LabelAId (quality), Urban Science 2025 (validation against official data).
- Precision on some label types is low (missing curb ramps about 20%), so crowd validation and AI filtering are needed before the data supports ADA decisions.

### Gaps
- Accuracy numbers for CHI 2013 and Tohme were not extracted.
- I did not check whether Project Sidewalk has a deployment in Cincinnati or elsewhere in Ohio (see the projectsidewalk.org city list).

## Q2: AccessMap and OpenSidewalks (UW Taskar Center) and the OpenSidewalks schema

### Takeaway
The peer-reviewed record is small: PLOS ONE 2021 (PPNA), COMPASS 2022 (communal open data) and an ASSETS 2019 demo. The OpenSidewalks Schema is documented on GitHub and the OSM wiki, not in a standalone peer-reviewed paper.

### Cited Findings
- PLOS ONE 2021: the PPNA framework; about one-third of the downtown Seattle walkshed is inaccessible for a powered-wheelchair profile; "normalized sidewalk reach" — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7978374); [UW CSE News](https://news.cs.washington.edu/2021/04/02/taskar-center-researchers-offer-a-roadmap-for-more-robust-modeling-of-pedestrian-mobility-on-a-city-wide-scale/)
- COMPASS 2022 (doi:10.1145/3530190.3534821) cites the OpenSidewalks-Schema repository and the AccessMap ASSETS 2019 demo (doi:10.1145/3308561.3354598, pp. 676-678) — [Crossref](https://api.crossref.org/works/10.1145%2F3530190.3534821)
- Earliest AccessMap description: Bolten, Caspi et al., "Urban sidewalks: visualization and routing for individuals with limited mobility," arXiv:1602.04281, 2016 (preprint) — [arXiv](https://www.arxiv.org/pdf/1602.04281)
- The OpenSidewalks Schema is "an open pedestrian transportation network data standard which draws from and is intended to be largely compatible with OpenStreetMap data." It is led by TCAT and funded by USDOT ITS4US through the TDEI — [sidewalks.washington.edu/about](https://sidewalks.washington.edu/about); [OSM wiki](https://wiki.openstreetmap.org/wiki/OpenSidewalks)
- The project began in UW eScience Data Science for Social Good (2015-2016), led by Caspi and Bolten — [eScience DSSG 2016](https://escience.washington.edu/dssg-2016-global-opensidewalks)
- The OSM tagging proposal has been in draft since 2016 and was never voted on — [OSM accessibility list, Jan 2021](https://lists.openstreetmap.org/pipermail/accessibility/2021-January/000446.html)
- Bolten's 2020 PhD dissertation documents building and studying AccessMap — [UW ResearchWorks](https://digital.lib.washington.edu/researchworks/items/63c791bd-8aa9-436c-864f-185b290a3a64/full)

### Inferences
- For the Ohio project, the OpenSidewalks schema is a natural target data model (sidewalk, crossing and curb features with incline and surface). AccessMap/PPNA supplies the routing and metric method.

### Gaps
- I found no peer-reviewed paper from 2023-2026 on the OpenSidewalks Schema or the TDEI tooling, only project pages and data.gov listings.

## Q3: Completeness and quality of OSM accessibility tags (wheelchair, kerb, incline, surface; Wheelmap; sidewalks)

### Takeaway
The studies agree that OSM sidewalk and accessibility data is accurate where present but very incomplete. Kerb, width, smoothness and incline tags are almost absent, and coverage is worst in low-density areas.

### Cited Findings
- Wheelmap: Mobasheri, Deister, Dieterich, Open Geospatial Data, Software and Standards 2:27, 2017 (doi:10.1186/s40965-017-0040-5). Traffic-light wheelchair=* ratings stored in OSM, with a REST API — [SpringerOpen](https://opengeospatialdata.springeropen.com/articles/10.1186/s40965-017-0040-5)
- Mobasheri, Huang, Degrossi, Zipf, Sensors 18(2):509, 2018 (doi:10.3390/s18020509). Sidewalk geometries mined from wheelchair users' GPS traces in Heidelberg overlap 96% of the official reference network. The paper says sidewalk detail is largely absent from OSM — [Heidelberg catalog](https://heibib.ub.uni-heidelberg.de/search/Record/1572011440); [CORE PDF](https://core.ac.uk/download/211678226.pdf)
- Mobasheri, Zipf, Francis, Geo-spatial Information Science 2018 (doi:10.1080/10095020.2018.1493817). In the CAP4Access EU project, incomplete OSM sidewalk and kerb data was a basic challenge, addressed with mapping parties and awareness tools — [Crossref](https://api.crossref.org/works/10.1080/10095020.2018.1493817); [DOAJ](https://doaj.org/article/7e16447df533469fb6cf843e692cc7bb)
- Omar et al. 2022 (preprint): across 54 US cities, 80% have under 5% of roads with sidewalk tags; kerb, smoothness and width are nearly absent — [ar5iv](https://ar5iv.labs.arxiv.org/html/2210.02350)
- Nichols et al. 2026: OSM sidewalk sensitivity 30.2% against Street View in Maryland, PPV 99.2%; lowest in low-density tracts — [CDC PCD](https://www.cdc.gov/pcd/issues/2026/26_0255.htm)
- Rhoads et al., "Sidewalk networks: Review and outlook," CEUS 106:102031, 2023 (doi:10.1016/j.compenvurbsys.2023.102031). A review of sidewalk network data, including OSM. Metadata verified on Crossref; content not read — [Crossref](https://api.crossref.org/works/10.1016/j.compenvurbsys.2023.102031)
- POI wheelchair tags in European capitals (2021, Intercontinental Geoinformation Days, a lower-tier venue): London 2.0%, Ankara 0.6%, Warsaw 0.5% (figures from a search snippet only) — [publisher page](https://publish.mersin.edu.tr/index.php/igd/article/view/444)
- UNVERIFIED, do not cite: "98.44% of 421k UK Wheelmap nodes unknown" comes from a secondary review site only — [secondary](https://a11y-paradise.onrender.com/reviews/69c04e87392b06b0ce6ff7e6)

### Inferences
- In Cincinnati, and especially Oxford (a small, low-density town), treat OSM sidewalk presence as high-precision but low-recall. Incline and kerb values will need to come from the DEM and the city curb-ramp inventory.

### Gaps
- I found no peer-reviewed study of the completeness of wheelchair=*, kerb=* or incline=* tags on sidewalk ways specifically. The existing work looks at POIs or sidewalk geometry.

## Q4: Comparisons of official city sidewalk and curb-ramp inventories with crowdsourced or OSM data

### Takeaway
Direct comparisons are rare. Askari et al. 2025 is the main one. Related work includes Deitz's comparison of ML-detected curb ramps with government data, Mobasheri 2018's comparison with an official network, and evidence that official data is itself often missing.

### Cited Findings
- Askari et al. 2025: high agreement on presence but "varying agreement for the severity." Barriers to comparison include location mismatches, different topology (points vs segments), different condition criteria, and errors in the reference data — [PDF](https://makeabilitylab.cs.washington.edu/media/publications/Askari_ValidatingPedestrianInfrastructureDataHowWellDoStreetViewImageryAuditsCompareToGovernmentFieldData_UrbanSci2025.pdf)
- Deitz, Lobben, Alferez, "Squeaky wheels," Big Data & Society 2021 (doi:10.1177/20539517211047735). Of 178 US cities, about 60% have open-data portals; sidewalk data appears in 34%, sidewalk condition in 18%, curb ramps in 17%. These figures are as summarized in Askari et al.; the DOI is verified on [Crossref](https://api.crossref.org/works/10.1177/20539517211047735)
- Deitz 2023, "Outlier Bias: AI Classification of Curb Ramps, Outliers, and Context," Big Data & Society 10 (doi:10.1177/20539517231203669, not checked on Crossref). Compares ML curb-ramp predictions with government data in 9 US cities; random forest 88% accurate (as summarized in [Askari et al.](https://makeabilitylab.cs.washington.edu/media/publications/Askari_ValidatingPedestrianInfrastructureDataHowWellDoStreetViewImageryAuditsCompareToGovernmentFieldData_UrbanSci2025.pdf))
- Eisenberg et al. (cited in Askari): only 13% of 401 government entities had published ADA transition plans; on average 65% of curb ramps and 50% of sidewalks were inaccessible — [Askari et al.](https://makeabilitylab.cs.washington.edu/media/publications/Askari_ValidatingPedestrianInfrastructureDataHowWellDoStreetViewImageryAuditsCompareToGovernmentFieldData_UrbanSci2025.pdf)
- Hosseini, Sevtsuk, Miranda, Cesar, Silva, "Mapping the walk" (Tile2Net), CEUS 101:101950, 2023 (doi:10.1016/j.compenvurbsys.2023.101950). Open-source extraction of sidewalk, crosswalk and footpath polygons and networks from aerial imagery, trained on Cambridge, DC and NYC. The authors note most US towns have no sidewalk maps — [EVL](https://www.evl.uic.edu/pubs/2703); [code](https://github.com/VIDA-NYU/tile2net)

### Inferences
- Fusing city inventories, OSM and 311 data addresses the gap Askari et al. identify: matching condition and severity scales across sources is harder than matching presence.

### Gaps
- I found no study that compares OSM itself with a city curb-ramp inventory, and none that uses 311 reports as a sidewalk condition or validation source. Both look like real gaps, but my searches were limited.

## Q5: What remains open

### Takeaway
The open problems are: condition and severity rather than presence, standard severity scales, validation, coverage in small or low-density towns, keeping data current over time, and fusing many different sources.

### Cited Findings
- There is "a lack of standardized formats for auditing the severity of pedestrian infrastructure issues," and AI handles subjective severity poorly — [Askari et al. 2025](https://makeabilitylab.cs.washington.edu/media/publications/Askari_ValidatingPedestrianInfrastructureDataHowWellDoStreetViewImageryAuditsCompareToGovernmentFieldData_UrbanSci2025.pdf)
- Low-density areas have the weakest OSM coverage and also lack Street View imagery — [Nichols et al. 2026](https://www.cdc.gov/pcd/issues/2026/26_0255.htm)
- Coverage within a city is uneven, and edit-history trust is a problem — [Omar et al. 2022 (preprint)](https://ar5iv.labs.arxiv.org/html/2210.02350)
- Crowd precision varies by label type, which motivates AI-assisted validation — [LabelAId](https://arxiv.org/abs/2403.09810)
- Barriers should be personalized by disability group — [Li et al. CHI 2025](https://doi.org/10.1145/3706598.3713421); [Bolten & Caspi 2021](https://doi.org/10.1371/journal.pone.0248399)
- The OSM sidewalk tagging standard has been in draft since 2016 — [OSM list](https://lists.openstreetmap.org/pipermail/accessibility/2021-January/000446.html)

### Inferences
- Openings for the Cincinnati and Oxford project: (1) fusing several sources (GIS, OSM, 311, DEM incline) with condition scales mapped onto each other; (2) a small college-town case where OSM and Street View coverage is thin; (3) 311 as a time-stamped condition signal; (4) validating OSM, not only Project Sidewalk, against official inventories.

### Gaps
- I found no published work fusing 311 data with sidewalk inventories for wheelchair routing. This is inferred from absence in limited searches.
