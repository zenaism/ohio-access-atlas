# Wheelchair Environment Sensing (IMU surface/roughness, slope, crowdsensing, radar/depth, map validation)

Note for the report writer: several of the closest prior works come from the Miami University (Oxford, OH) group of V. Raychoudhury and M. O. Gani, the same group whose members (e.g., N. Mahmud) appear on OmniPath. If SurfaceEncoder and mmRAMP come from that group, its own earlier papers (Yu et al. TAI 2022; Banerjee et al. MSN 2022; Mokrenko et al. COMPSAC 2021; Gani et al. BuildSys 2019; MyPath) are the prior work the novelty claims must be set against most directly. Source: [MyPath publications page](https://mypathweb.csi.miamioh.edu/publications.html).

## Shortlist: the 8 most important papers (verified)

| # | Paper | Main contribution (1 sentence) | Key numbers |
|---|---|---|---|
| 1 | Iwasawa, Yairi, Matsuo. "Combining Human Action Sensing of Wheelchair Users and Machine Learning for Autonomous Accessibility Data Collection." IEICE Trans. Inf. & Syst. E99.D(4):1153-1161, 2016. DOI [10.1587/transinf.2015EDP7278](https://www.jstage.jst.go.jp/article/transinf/E99.D/4/E99.D_2015EDP7278/_article/-char/en) | First to show that a wheelchair-mounted accelerometer (iPod touch) plus supervised ML can detect accessibility-relevant events (curbs, tactile paving, slopes) instead of manual surveys. | 9 wheelchair users, about 1 h each in Tokyo; F-scores: curb 0.63, tactile indicators 0.65, slope 0.50, stop 0.91 |
| 2 | Watanabe, Takahashi, Sato, Iwasawa, Matsuo, Yairi. "Wheelchair Behavior Recognition for Visualizing Sidewalk Accessibility by Deep Neural Networks." DL-HAR workshop at IJCAI-PRICAI 2020 (Springer CCIS); [arXiv:2101.03724](https://arxiv.org/abs/2101.03724) | Extends the Iwasawa/Yairi line to a supervised CNN, weakly supervised and self-supervised (VAE) representation learning of road surface and barriers from under-seat smartphone acceleration, and visualizes them on a map. | The abstract gives no headline metric. It is the closest prior work to SurfaceEncoder's "self/semi-supervised surface representation" idea. |
| 3 | Civitarese, Mascetti, Butifar, Bettini. "Automatic Detection of Urban Features from Wheelchair Users' Movements." IEEE PerCom 2019. DOI [10.1109/PERCOM.2019.8767422](https://air.unimi.it/handle/2434/664826); journal extension: Mascetti, Civitarese, El Malak, Bettini, "SmartWheels: Detecting urban features for wheelchair users' navigation," Pervasive and Mobile Computing, 2020 ([record](https://core.ac.uk/works/77629323), [PDF](https://air.unimi.it/retrieve/ff194397-befa-47b0-b348-cf2add2c3d65/2019_PMC_mobiwheel.pdf)) | Infers urban features (steps, ramps, etc.) from wheelchair inertial data, using activity recognition with confidence-based filtering. | PerCom: 10 users outdoors, precision about 0.9, weak on fine details such as step height. PMC: 17 users (10 controlled, 7 in the wild). |
| 4 | Yu, Raychoudhury, Saha, Edinger, Smith, Gani. "Automated Surface Classification System using Vibration Patterns: A Case Study with Wheelchairs." IEEE Trans. on Artificial Intelligence 4(4), 2023 (online 2022). DOI 10.1109/TAI.2022.3190828, [IEEE Xplore 9829917](https://ieeexplore.ieee.org/abstract/document/9829917/) | Supervised surface-type classification from wheelchair vibration (smartphone and wearable accel+gyro) across many countries, with a real-time prototype tested at unseen sites. | 32 surfaces, 32 subjects, 6 countries (AT, CN, FR, DE, IN, US); accuracy 97.5% (91.6% accelerometer only) ([index record](https://smartcity.efri.uniri.hr/article.php?id=11262)) |
| 5 | Edinger, Hofmann, Wachner, Becker, Raychoudhury, Krupitzer. "WheelShare: Crowd-sensed Surface Classification for Accessible Routing." IEEE PerCom Workshops (TSUM) 2019. [IEEE Xplore 8730849](https://ieeexplore.ieee.org/abstract/document/8730849/) | A system/vision paper: crowd-sensed vibration from wheelchair-mounted phones, classified into accessible and inaccessible surfaces, feeding an OSM-based personalized router. | No classification results. The paper says surface identification is "out of scope" (read from the full-text PDF). |
| 6 | Mobasheri, Huang, Degrossi, Zipf. "Enrichment of OpenStreetMap Data Completeness with Sidewalk Geometries Using Data Mining Techniques." Sensors 18(2):509, 2018. DOI [10.3390/s18020509](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5854971/) | Builds OSM sidewalk geometry from wheelchair users' GPS traces (CAP4Access) and checks it against an official reference dataset. This is the closest thing to "wheelchair data and OSM", but it concerns geometry, not accessibility attributes. | Heidelberg; 96% overlap with the reference; RMSE 0.93 m ([Sensors record](https://www.pubmed.gov/29419768/)) |
| 7 | Duvall, Sinagra, Cooper, Pearlman. "Proposed pedestrian pathway roughness thresholds to ensure safety and comfort for wheelchair users." Assistive Technology, 2016. [PubMed 27588607](https://webcf.waybackmachine.org/web/20220511191826/https://www.ncbi.nlm.nih.gov/pubmed/27588607) (plus the earlier Wolf, Pearlman, Cooper et al. 2005 sidewalk vibration study, [record](https://researchexperts.utmb.edu/en/publications/vibration-exposure-of-individuals-using-wheelchairs-over-sidewalk/)) | Links pathway roughness to wheelchair seat and footrest vibration and proposes the roughness thresholds behind ASTM E3028 (Wheelchair Pathway Roughness Index). This is the physical and standards basis for "roughness". | Thresholds: 50 mm/m (100 m window) and 100 mm/m (3 m window) per the abstract. An ICPI fact sheet states them differently ([ICPI](https://icpi.org/s/Fact-Sheet-16-Wheelchair-Pavement-Interaction-Site-Surveys-wlfm.pdf)), so check the original. Wolf 2005: 10 participants, 9 surfaces; recommends bevel under 6 mm. |
| 8 | Wang, Sun, Liu. "Self-Supervised Drivable Area and Road Anomaly Segmentation using RGB-D Data for Robotic Wheelchairs." IEEE RA-L 4(4), 2019. DOI 10.1109/LRA.2019.2932874, [arXiv:2007.05950](https://arxiv.org/abs/2007.05950), [dataset GMRPD](https://github.com/hlwang1124/GMRPD) | Wheelchair-mounted RGB-D (RealSense) with self-supervised labels for drivable area and road anomalies, plus a public dataset. It is the nearest public multimodal wheelchair-perception dataset to mmRAMP. | GMRPD: 3,896 hand-labeled RGB-D images, 30 scenes (sidewalks, squares) |

Honorable mentions:
- Fraunhofer IPA radar stair and curb detection for wheelchairs ([arXiv:1711.09206](https://arxiv.org/pdf/1711.09206)): this is the closest radar prior work.
- OmniPath, the closest "auditing" work (see Q5).

Figure URLs: I did not verify any figure image URLs, so none are given. The arXiv HTML pages (e.g., https://arxiv.org/html/2606.24129) host figures, but I did not check the individual image paths.

## Q1: Wheelchair IMU/accelerometer surface classification and vibration

### Takeaway
This is an established area. It has two main lineages: (a) the Iwasawa/Yairi group in Tokyo, 2012-2021, which moved from accelerometer event detection to CNN, weakly supervised and VAE representations; and (b) the WheelShare/MyPath line (Mannheim and Miami Univ.), 2019-2024, with supervised surface classification across 32 surfaces and 6 countries at 97.5%. Self- or weakly supervised surface representation from wheelchair IMU already exists (Watanabe et al. 2020/21), so SurfaceEncoder's novelty must rest on scale (52M points, 5 countries), the semi-supervised method, and cross-country generalization. It cannot claim to be the first non-supervised approach.

### Cited Findings
- Iwasawa & Yairi, PRICAI 2012: wheelchair life-logging with a single 3-axis accelerometer to map potential incidents such as curb falls. — [Springer PDF](https://springerlink.bibliotecabuap.elogim.com/content/pdf/10.1007/978-3-642-32695-0_16.pdf)
- IEICE 2016: 9 users, curb/tactile/slope/stop F = 0.63/0.65/0.50/0.91. — [J-STAGE](https://www.jstage.jst.go.jp/article/transinf/E99.D/4/E99.D_2015EDP7278/_article/-char/en)
- A 2019 MDPI *Information* paper (Iwasawa/Yairi line) applied a deep CNN to road surface states; a JSAI 2020 paper used ConvVAE reconstruction error as a per-user route "burden" proxy (14 wheelchair users). — [DOAJ](https://doaj.org/article/69461c699ac64829b8a7838fb301593d), [JSAI](https://www.jstage.jst.go.jp/article/pjsai/JSAI2020/0/JSAI2020_1G3ES502/_article/-char/en) (abstract level only)
- Watanabe et al. 2021: supervised CNN, weakly supervised and self-supervised VAE representations from an under-seat smartphone accelerometer. — [arXiv](https://arxiv.org/abs/2101.03724)
- SmartWheels / PerCom 2019: urban-feature detection, precision about 0.9 (10 users); PMC 2020 adds 17 users. — [UNIMI](https://air.unimi.it/handle/2434/664826), [CORE](https://core.ac.uk/works/77629323)
- Yu et al., IEEE TAI: 32 surfaces, 32 subjects, 6 countries, 97.5% (91.6% accelerometer only). — [index](https://smartcity.efri.uniri.hr/article.php?id=11262), [IEEE](https://ieeexplore.ieee.org/abstract/document/9829917/)
- Same group: Gani et al. BuildSys 2019 ([ACM](https://dl.acm.org/doi/abs/10.1145/3360322.3360863)); Mokrenko et al. COMPSAC 2021, transfer learning for surface detection ([IEEE](https://ieeexplore.ieee.org/abstract/document/9529616/)); Banerjee et al. MSN 2022, "Surface Recognition from Wheelchair-induced Noisy Vibration Data: A Tale of Many Cities" ([CSDL](https://www.computer.org/csdl/proceedings-article/msn/2022/645700a619/1LUtWSX7qEM)). — [publications list](https://mypathweb.csi.miamioh.edu/publications.html)
- Roughness and vibration physiology: Wolf et al. 2005 and Duvall et al. 2016 underpin ASTM E3028 WPRI. — [UTMB](https://researchexperts.utmb.edu/en/publications/vibration-exposure-of-individuals-using-wheelchairs-over-sidewalk/), [PubMed](https://webcf.waybackmachine.org/web/20220511191826/https://www.ncbi.nlm.nih.gov/pubmed/27588607), [ASTM E3028](https://standards.nimonik.com/products/astm/e3028/)
- A patent reports that mean RMS acceleration from a wheelchair-mounted phone sorted about 75% of surfaces as compliant or non-compliant with the roughness thresholds. — [USPTO 10101454](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10101454)

### Inferences
- There are two framings: surface type (categorical) and roughness (continuous, WPRI). Little prior work links learned IMU representations to standardized WPRI or RMS comfort values. This could be a differentiator.
- The sources do not report dataset sizes for prior work in raw IMU points. SurfaceEncoder's 52M points is plausibly the largest, but I could not verify this.

### Gaps
- I could not open the full text of Yu et al. TAI, Banerjee MSN 2022 or MyPath (MobiQuitous; Springer/EUDL returned 403) to get dataset sizes and whether any part was semi-supervised.
- Exact publication year of Yu et al.: online 2022, issue 4(4) 2023.

## Q2: Crowdsensing of sidewalk/road accessibility with smartphones or wheelchairs

### Takeaway
Several systems propose crowd-sensed wheelchair vibration feeding OSM routing (WheelShare 2019, MyPath 2023/24). CAP4Access mined wheelchair GPS traces into OSM sidewalk geometry. Most remain prototypes, and their evaluations measure classifier accuracy rather than map quality.

### Cited Findings
- WheelShare (PerCom-W 2019): crowd-sensed wheelchair-phone vibration and a GraphHopper/OSM router; surface identification is "out of scope" in that paper. — [PDF](https://sig-iss.work/percomworkshops2019/papers/p584-edinger.pdf)
- MyPath (EAI MobiQuitous; Nguyen, Islam, Banerjee, Noyce, Olejniczak, Smith, Gani): accessible routing from crowd-sensed surface vibration. The group proposes cross-referencing sensed surfaces with OSM tags so verified contributors can update OSM. — [Springer](https://link.springer.com/chapter/10.1007/978-3-031-63992-0_3), [RESNA 2022](https://resna.org/sites/default/files/conference/2022/PublicTransportation/80_Saha.html), [RESNA 2023 PAR feedback](https://www.resna.org/sites/default/files/conference/2023/PublicTransportation/91_Olejniczak.html)
- Mobasheri et al. 2018: wheelchair GPS traces gave sidewalk geometry with 96% overlap and RMSE 0.93 m (Heidelberg). — [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5854971/)
- Industry: Bolt "Wheels4Wheels" claims e-scooter telemetry gives surface quality at 95% accuracy, validated against manual mapping. This is a company claim and not peer reviewed. — [micromobility.io](https://micromobility.io/news/what-550-km-of-bolt-scooter-rides-reveal-about-accessible-streets)
- A stroller-mounted smartphone (about 100 Hz) was used for pedestrian space assessment (ISPRS 2024). — [ISPRS](https://isprs-archives.copernicus.org/articles/XLVIII-4-W10-2024/163/2024/isprs-archives-XLVIII-4-W10-2024-163-2024.pdf)

### Inferences
- The idea of crowdsensing for OSM is not new. What these sources do not show is any empirical, large-scale measurement of map quality using such data.

### Gaps
- MyPath's MobiQuitous publication year conflicts: the group page says 2023, while the EAI proceedings volume is 2024. Its quantitative results could not be retrieved.

## Q3: Slope / cross-slope estimation from IMU or a moving wheelchair/smartphone

### Takeaway
This area is thin and mostly gray literature: Japanese workshop and conference papers, patents and a thesis. I found no peer-reviewed paper with validated cross-slope accuracy (in degrees) from a wheelchair IMU, and the reported problems are vibration and GPS error. Iwasawa 2016's slope F = 0.50 shows how hard it is.

### Cited Findings
- 2014 IEICE technical report: IMU and GPS on an electric wheelchair to detect running and cross slope and steps. — [IEICE](https://www.ieice.org/ken/paper/20141211fBu7/eng/)
- ICCE 2019 (Nagasaki Univ.): "Slope information collection system using sensor information from general purpose wheelchair users"; smartphone slope angle logged every 0.05 s, averaged to 1 s, uploaded to the cloud. — [PDF](https://www.cis.nagasaki-u.ac.jp/~toru/src/wp-content/uploads/2019/01/Slope-information-collection-system-using-sensor-information-from-general-purpose-wheelchair-users-2019ICCE.pdf) (the server refused my connection, so details come from the search snippet; authors not verified)
- Univ. of Delaware 2023 thesis: smartphone slope measurement was inaccurate because of vibration on rough surfaces and GPS error near buildings; it could roughly flag non-compliant segments. — [UDSpace](https://udspace.udel.edu/handle/19716/33121)
- Patents describe rigid phone mounts that capture running and cross slope with an SVM. — [USPTO 10690774](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10690774)
- Non-sensor alternative: OmniPath computes running and cross slope from aerial LiDAR (USGS 3DEP) along OSM ways at 0.5 m steps. — [arXiv:2606.24129](https://arxiv.org/abs/2606.24129)

### Inferences
- Validated cross-slope estimation from a moving wheelchair IMU, against a digital level or LiDAR, looks open. mmRAMP (IMU + RGB-D + radar) could supply the ground truth for this.

### Gaps
- No peer-reviewed accuracy numbers found for IMU cross slope on wheelchairs.

## Q4: Radar or depth sensing on wheelchairs (obstacle, curb detection)

### Takeaway
Depth/RGB-D on wheelchairs is established for robotic navigation (ramp detection, drivable area). Radar is rare: there is Fraunhofer radar stair and curb detection for the MeBot stair-climbing chair, an mmWave ego-motion workshop paper, and commercial LUCI collision avoidance. I found no public raw mmWave + RGB-D + IMU wheelchair dataset, which supports mmRAMP's novelty claim, with the caveat that the search was not exhaustive.

### Cited Findings
- Fraunhofer IPA: mirror-based 2D FMCW radar scanner for stair detection on wheelchairs; radar is robust to weather. — [arXiv:1711.09206](https://arxiv.org/pdf/1711.09206), [MeBot article](https://www.computer-automation.de/robotics-en/wheelchair-robot--mebot--climbs-stairs-independently.htm)
- A MIMO mmWave radar was used for wheelchair ego-motion estimation (workshop). — [CEUR-WS Vol-4082 paper7](https://ceur-ws.org/Vol-4082/paper7.pdf)
- LUCI (commercial): mmWave radar, stereo vision and ultrasonic sensors for power-chair collision and drop-off avoidance, range over 6 m. — [Mobility Management 2021](https://digital.1105media.com/MMmag/2021/MM_2021_07/files/basic-html/page43.html)
- A review of curb negotiation for robotic wheelchairs: ultrasonic sensing is inaccurate, LiDAR is costly and struggles with wet or dark surfaces, and few automotive curb methods have been ported to wheelchairs. — [PMC8659845](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8659845/)
- RGB-D: Wang et al. RA-L 2019 (GMRPD, 3,896 images); Nejati & Argall, real-time ramp detection from RGB-D point clouds for power wheelchairs. — [arXiv](https://arxiv.org/abs/2007.05950), [Argall lab PDF](https://www.argallab.northwestern.edu/files/2016/09/16roman_nejati.pdf)
- Sidewalk datasets: SideGuide (stereo, for blind and low-vision users) and a virtual wheelchair sidewalk segmentation dataset (J. Imaging 2022). — [SideGuide](https://ytaek-oh.github.io/sideguide), [MDPI](https://mdpi.com/2313-433X/8/8/216)

### Gaps
- I did not check IEEE Xplore exhaustively for 2023-2026 mmWave curb or ramp papers. A targeted IEEE Sensors J / RA-L search is recommended before claiming "first mmWave wheelchair dataset".

## Q5: Has wheelchair-sensed data been used as ground truth to validate or score city/OSM accessibility maps?

### Takeaway
I found nothing that does this directly. No peer-reviewed study uses wheelchair-sensed IMU, radar or depth data as ground truth to measure the accuracy or completeness of OSM or municipal accessibility attributes (surface, smoothness, incline, kerb). The closest works are listed below.

### Cited Findings
- Mobasheri et al. 2018 validates wheelchair-trace-derived sidewalk *geometry* against an official dataset (the reverse direction: the map is the reference). — [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5854971/)
- The MyPath group proposes cross-referencing sensed surfaces with OSM surface tags to drive updates, but reports no tag-accuracy statistics. — [Miami senior design / MyPath](https://sites.miamioh.edu/cse-senior-design-expo/?p=735)
- OmniPath (Hossain, Mahmud, Raychoudhury, Gani; arXiv June 2026, IEEE COMPSAC 2026) audits OSM networks with aerial LiDAR against 200 human field surveys on the National Mall (F1 0.60 Severe, 0.58 Critical). It uses no wheelchair-sensed data. — [arXiv](https://arxiv.org/abs/2606.24129)
- Bolt Wheels4Wheels validated scooter-derived surface quality against manual mapping (industry, not peer reviewed). — [micromobility.io](https://micromobility.io/news/what-550-km-of-bolt-scooter-rides-reveal-about-accessible-streets)
- Imagery-based OSM accessibility checks rely on hand labels because OSM has too little curb ground truth. — [access-map GitHub](https://github.com/r671h/access-map), [ISPRS 2020 OSM accessibility mapping comparison](https://isprs-archives.copernicus.org/articles/XLIII-B4-2020/229/2020/isprs-archives-XLIII-B4-2020-229-2020.pdf)

### Inferences
- "Wheelchair-sensed ground truth for scoring OSM or city accessibility layers" appears to be an open, claimable contribution. Claim it as "to our knowledge", and note it is distinct from OmniPath (LiDAR, human audits) and Mobasheri (geometry only).

### Gaps
- The search covered the web, arXiv and publisher records, not Scopus, so a small chance of a missed workshop paper remains.

## Q6: What remains open

### Takeaway / list (inferences from the findings above)
- Cross-country and cross-device generalization of IMU surface models: Banerjee 2022 ("tale of many cities") and Mokrenko 2021 (transfer learning) show this is an acknowledged pain point, but there is no large standardized benchmark.
- A continuous roughness or comfort score (WPRI/RMS, ASTM E3028) learned from crowd IMU, rather than discrete surface classes.
- Validated running and cross-slope estimation from a moving wheelchair IMU (only gray literature exists; vibration and GPS error are unsolved).
- Public multimodal (mmWave + RGB-D + IMU) wheelchair datasets; radar curb/ramp height estimation has only a few prototypes.
- Using wheelchair-sensed data to score or validate OSM and municipal accessibility data at city scale (nothing found).
- Sparse labels: most prior work is fully supervised with video or hand labels. Weakly or self-supervised work exists (Watanabe 2021) but at small scale.
