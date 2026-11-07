# Topic 2: Computer vision for sidewalks, curb ramps and pedestrian accessibility features from aerial, satellite and street-view imagery

Verification note: DOIs for Tohme, Weld 2019, Liu 2024, and Hou & Ai 2020 were checked against the Crossref API (title, venue and year match). The Tile2Net DOI, the CVF and arXiv links, and the RampNet figure URLs all returned HTTP 200 (checked 2026-11-07). ACM doi.org links return 403 to scripts because ACM blocks bots. They are valid in a browser.

## Shortlist: the 8 most important papers (summary table)

| # | Paper | Year / Venue | Imagery | One-sentence contribution | Key numbers |
|---|---|---|---|---|---|
| 1 | Hara, Sun, Moore, Jacobs, Froehlich. "Tohme: Detecting Curb Ramps in Google Street View Using Crowdsourcing, Computer Vision, and Machine Learning" | 2014, ACM UIST. DOI [10.1145/2642918.2647403](https://doi.org/10.1145/2642918.2647403) | GSV | First system to detect curb ramps with CV in Street View. A learned controller sends each scene either to CV plus human verification or to manual crowd labeling. | 1,086 intersections in 4 North American cities, 403 crowd workers. CV alone found 67% of curb ramps. The hybrid matched manual accuracy at about 13% lower time cost. [PDF](https://makeabilitylab.cs.washington.edu/media/publications/Hara_TohmeDetectingCurbRampsInGoogleStreetViewUsingCrowdsourcingComputerVisionAndMachineLearning_UIST2014.pdf), [project](https://makeabilitylab.cs.washington.edu/project/tohme/) |
| 2 | Weld, Jang, Li, Zeng, Heimerl, Froehlich. "Deep Learning for Automatically Detecting Sidewalk Accessibility Problems Using Streetscape Imagery" | 2019, ACM ASSETS (Best Student Paper). DOI [10.1145/3308561.3353798](https://doi.org/10.1145/3308561.3353798) | GSV panoramas (Project Sidewalk) | First large-scale deep learning (ResNet-18) on crowdsourced Project Sidewalk labels, covering both auto-validation of labels and auto-labeling of new panoramas. | 300k+ labels from Washington DC. Auto-validation 81.3% precision / 77.2% recall. Auto-labeling 47.0% precision / 41.2% recall. [slides](https://makeabilitylab.cs.washington.edu/media/talks/Weld_DeepLearningForAutomaticallyDetectingSidewalkAccessibilityProblemsUsingStreetscapeImagery_2019.pdf), [SIGACCESS](https://www.sigaccess.org/2019/11/2019-best-student-paper/) |
| 3 | Hou, Ai. "A network-level sidewalk inventory method using mobile LiDAR and deep learning" | 2020, Transportation Research Part C 119:102772. DOI [10.1016/j.trc.2020.102772](https://doi.org/10.1016/j.trc.2020.102772) | Mobile LiDAR | PointNet++-based segmentation plus scan-pattern extraction for network-level sidewalk and curb ramp inventory, including geometry (ADA-style measures). | The related MassDOT report covered 85+ miles of sidewalk and 1,297 curb ramps on State Route 9, MA, at 7.0 min/mile (sidewalk) and 2.2 min/mile (ramps). [MassDOT/ROSAP report](https://rosap.ntl.bts.gov/view/dot/61618). Paper-level accuracy figures not verified. |
| 4 | Hosseini, Miranda, Lin, Silva. "CitySurfaces: City-scale semantic segmentation of sidewalk materials" | 2022, Sustainable Cities and Society 79:103630. DOI 10.1016/j.scs.2021.103630; [arXiv 2201.02260](https://arxiv.org/abs/2201.02260) | GSV / street-level | Active-learning semantic segmentation of sidewalk paving materials from street-level images at city scale. | 90.5% mIoU, trained on NYC and Boston and tested on 6 other cities. [arXiv](https://arxiv.org/abs/2201.02260), [EVL](https://www.evl.uic.edu/pubs/2620) |
| 5 | Hosseini, Sevtsuk, Miranda, Cesar Jr., Silva. "Mapping the walk: A scalable computer vision approach for generating sidewalk network datasets from aerial imagery" (Tile2Net) | 2023, Computers, Environment and Urban Systems 102:101950. DOI [10.1016/j.compenvurbsys.2023.101950](https://doi.org/10.1016/j.compenvurbsys.2023.101950) | Sub-meter orthorectified aerial tiles | Open-source end-to-end tool that segments sidewalks, crosswalks and footpaths from aerial tiles and converts them into routable pedestrian network centerlines. | About 20,000 training tiles. 84.51% mIoU (sidewalk IoU 82.67%, crosswalk 75.42%). Polygon match: Cambridge 98.92%, Boston 98.72% (unseen city), DC 84.40%, Manhattan 98.25%. Area overlap 85.9 / 77.9 / 73.8 / 87.5%. [NSF PAR full text](https://par.nsf.gov/servlets/purl/10493942), [code](https://github.com/VIDA-NYU/tile2net) |
| 6 | Liu, Wu, Kulkarni, Saugstad, Rapo, Freiburger, Hosseini, Li, Froehlich. "Towards Fine-Grained Sidewalk Accessibility Assessment with Deep Learning: Initial Benchmarks and an Open Dataset" | 2024, ACM ASSETS. DOI [10.1145/3663548.3688531](https://doi.org/10.1145/3663548.3688531) | GSV crops (Project Sidewalk) | First open benchmark for classifying 33 fine-grained condition tags (e.g., cracks, steep, narrow, missing tactile warning) with DINOv2 and CLIP-ViT. | Clean set of about 24k images (10 cities) and noisy set of about 87k (12 cities). DINOv2 beat CLIP-ViT. Only 13 of 33 tags reached weighted F1 of 0.7 or higher. Missing tactile warning F1=0.94, brick/cobblestone 0.91, "steep" curb ramp F1=0. The noisier data hurt performance (curb ramp F1 dropped from 0.62 to 0.3). [PDF](https://makeabilitylab.cs.washington.edu/media/publications/Liu_TowardsFineGrainedSidewalkAccessibilityAssessmentWithDeepLearningInitialBenchmarksAndAnOpenDataset_ASSETS2024.pdf) |
| 7 | O'Meara, Hwang, Wang, Saugstad, Froehlich. "RampNet: A Two-Stage Pipeline for Bootstrapping Curb Ramp Detection in Streetscape Images from Open Government Metadata" | 2025, ICCV 2025 Workshops (CV4A11y). [CVF open access](https://openaccess.thecvf.com/content/ICCV2025W/CV4A11y/html/OMeara_RampNet_A_Two-Stage_Pipeline_for_Bootstrapping_Curb_Ramp_Detection_in_ICCVW_2025_paper.html); [arXiv 2508.09415](https://arxiv.org/abs/2508.09415) | GSV panoramas | Converts open city curb-ramp lat/long inventories into pixel labels to build the largest curb ramp dataset, then trains a ConvNeXt V2 detector. | 214,376 panoramas and 849,895 ramp labels (NYC, Portland, Bend). Auto-labels 94.0% precision / 92.5% recall. Detector AP 0.9236 vs 0.380 for Weld et al. on the same ground truth. [arXiv HTML](https://arxiv.org/html/2508.09415v1) |
| 8 | Wang, Hagen, Gatmaitan, Zhou, Dong, Valipoor, Wong, Li. "Do VLMs See What Sensors Feel? A Scalable Expert-Guided Design for Wheelchair Accessibility Assessment from Street View" | 2026, accepted to WACV 2027 (arXiv v2 Nov 5, 2026). [arXiv 2606.07642](https://arxiv.org/abs/2606.07642) | GSV + wheelchair GPS traces | Expert-guided, ADA-informed retrieval-augmented VLM rating of GSV scenes, validated against real wheelchair dwell time. | 407 GSV locations on the University of Florida campus. Correlation with dwell time improved from r=-0.40 to r=-0.54 with expert guidance. Weak on subtle surface conditions and transient obstructions. |

Honorable mention (VLM evaluation, preprint): Lieu, Morra, Cadoni, Song, Mazzarello, Ratti. "Can VLMs Reliably Assess Sidewalk Accessibility Attributes from Pedestrian-Level Imagery?" arXiv [2609.17882](https://arxiv.org/abs/2609.17882), Sep 2026 (MIT Senseable City). The authors tested 4 VLMs on 514 Seoul images against field measurements, with conformal prediction. Width was the most informative attribute (about 1.0 m half-width). Cross slope intervals were too wide to resolve regulatory thresholds, and pavement-condition sets were uninformative for 3 of 4 models. Raw sampling intervals covered only 17-47% of field values at nominal 90%.

Bridging/position paper: Hosseini, Saugstad, Miranda, Sevtsuk, Silva, Froehlich. "Towards Global-Scale Crowd+AI Techniques to Map and Assess Sidewalks for People with Disabilities." CVPR 2022 AVA Workshop, [arXiv 2206.13677](https://arxiv.org/abs/2206.13677). It combines satellite-based network extraction, street-level material segmentation and Crowd+AI condition assessment, and calls for standardized benchmarks.

Representative figure images (verified HTTP 200):
- RampNet auto-translation pipeline: https://arxiv.org/html/2508.09415v1/figs/auto_translation.png
- RampNet panorama detection heatmap: https://arxiv.org/html/2508.09415v1/figs/full_pano.jpg
- RampNet PR curves (not checked individually): https://arxiv.org/html/2508.09415v1/figs/pvr.png
- No direct figure URL was verified for Tile2Net (the GitHub README images did not resolve via scraping), Liu 2024, or the VLM preprints (x1.png returned 404).

## Tile2Net (aerial imagery sidewalk networks)

### Takeaway
Tile2Net (Hosseini et al., CEUS 2023) is the reference open-source tool for turning aerial orthoimagery into sidewalk, crosswalk and footpath polygons and routable network centerlines. It reaches high polygon recall (98%+ in 3 of 4 cities), and area overlap is lower (74-88%), especially under tree canopy.

### Cited Findings
- Published in Computers, Environment and Urban Systems 2023 by Hosseini, Sevtsuk, Miranda, Cesar Jr. and Silva, with DOI 10.1016/j.compenvurbsys.2023.101950. — [architexturez](https://architexturez.net/node/230848); [EVL](https://www.evl.uic.edu/pubs/2703)
- Input is sub-meter orthorectified slippy-map tiles. The tool outputs sidewalk, crosswalk and footpath polygons, then centerlines and networks. — [NSF PAR full text](https://par.nsf.gov/servlets/purl/10493942)
- Training data was about 20,000 512x512 tiles (11k DC, 28k Cambridge and 8k NYC-park tiles before merging). The team manually corrected 2,500 of the 12,000 training tiles because of temporal mismatch with the GIS data. 1024x1024 input tiles worked best. — [NSF PAR](https://par.nsf.gov/servlets/purl/10493942)
- Segmentation reached 84.51% mIoU over 4 classes, with sidewalk IoU 82.67% and crosswalk IoU 75.42%. — [NSF PAR](https://par.nsf.gov/servlets/purl/10493942)
- The share of official GIS polygons matched by a detected polygon was 98.92% in Cambridge, 98.72% in Boston (no Boston training tiles), 84.40% in DC and 98.25% in Manhattan. Area-weighted overlap was 85.9%, 77.9%, 73.8% and 87.5%. The authors attribute the low DC figure to data/imagery mismatch and tree-covered footpaths. — [NSF PAR](https://par.nsf.gov/servlets/purl/10493942)
- Cambridge ground-truth centerlines changed 23% (crosswalks) and 9.2% (sidewalks) between 2011 and 2018, which shows that ground truth itself goes stale. — [NSF PAR](https://par.nsf.gov/servlets/purl/10493942)
- Code: [github.com/VIDA-NYU/tile2net](https://github.com/VIDA-NYU/tile2net)

### Inferences
- Tile2Net is the most direct candidate for generating Cincinnati and Oxford sidewalk networks. Ohio's statewide orthoimagery (OGRIP) would need checking for sub-meter resolution and leaf-off timing, given the paper's canopy sensitivity.
- Boston (an unseen city) still got 98.7% polygon matching, which suggests reasonable transfer within US Northeast urban form. Smaller college towns like Oxford, with more canopy and fewer sidewalks, may perform worse.

### Gaps
- The centerline/network-level precision and recall numbers (Table 5) were not extracted.
- I did not verify any independent evaluation of Tile2Net in Midwest cities.

## Curb ramp detection from street-view imagery

### Takeaway
Curb ramp detection has progressed from Tohme (2014, CV finds 67% of ramps, with crowd help) to Weld et al. (2019, deep learning on 300k Project Sidewalk labels) to RampNet (2025, AP 0.92 using auto-labels generated from open government inventories). Curb ramp presence is now close to solved in GSV-covered US cities. Ramp quality (steepness, etc.) is not.

### Cited Findings
- Tohme combined a CV pipeline with human verification and a manual crowd pipeline, scheduled by a learned controller. It used 1,086 intersections in 4 cities and 403 turkers, and CV alone found 67% of curb ramps. — [Tohme PDF](https://makeabilitylab.cs.washington.edu/media/publications/Hara_TohmeDetectingCurbRampsInGoogleStreetViewUsingCrowdsourcingComputerVisionAndMachineLearning_UIST2014.pdf); [project page](https://makeabilitylab.cs.washington.edu/project/tohme/)
- Weld et al. trained a modified ResNet-18 on 300k+ Project Sidewalk labels from DC. Auto-validation reached 81.3% precision and 77.2% recall, and auto-labeling 47.0% and 41.2%. It won Best Student Paper at ASSETS 2019. — [slides](https://makeabilitylab.cs.washington.edu/media/talks/Weld_DeepLearningForAutomaticallyDetectingSidewalkAccessibilityProblemsUsingStreetscapeImagery_2019.pdf); [SIGACCESS](https://www.sigaccess.org/2019/11/2019-best-student-paper/). Sources disagree on the award name (the lab page says Best Paper, SIGACCESS says Best Student Paper).
- RampNet: 214,376 panoramas and 849,895 auto-labels from NYC, Portland and Bend government data. Auto-labels had 94.0% precision and 92.5% recall. ConvNeXt V2 reached AP 0.9236, compared with 0.380 for Weld et al. on the same manual ground truth. Earlier precision was 33.7% (Weld) and 26% (Tohme). — [arXiv HTML](https://arxiv.org/html/2508.09415v1); [CVF](https://openaccess.thecvf.com/content/ICCV2025W/CV4A11y/html/OMeara_RampNet_A_Two-Stage_Pipeline_for_Bootstrapping_Curb_Ramp_Detection_in_ICCVW_2025_paper.html)
- RampNet limitations: each ramp appears in about 4.5 panoramas (duplicates), the data covers only 3 US cities (regional bias), and streetscape imagery is unavailable or outdated in rural areas and small towns. — [arXiv HTML](https://arxiv.org/html/2508.09415v1)
- RampNet code and data are open: GitHub ProjectSidewalk/RampNet and Hugging Face projectsidewalk/rampnet-dataset (MIT license). — [Makeability project page](https://makeabilitylab.cs.washington.edu/project/rampnet)

### Inferences
- RampNet's Stage 1 trick applies wherever a city publishes a curb ramp inventory. If Cincinnati has an ADA transition-plan ramp inventory, it could generate local training labels.
- The small-town imagery limitation is directly relevant to Oxford, Ohio.

### Gaps
- I found no verified Mapillary-specific curb ramp detection paper in this pass.

## Sidewalk segmentation/extraction from aerial imagery or LiDAR

### Takeaway
Aerial approaches (Tile2Net) give network topology at city scale. Mobile LiDAR (Hou & Ai 2020) gives geometry, including width and slopes, but needs costly data collection. Zero-shot foundation models (SAM) are being tested on LiDAR plus satellite fusion.

### Cited Findings
- Hou & Ai 2020 (TR Part C 119:102772) is a network-level sidewalk inventory method using mobile LiDAR and deep learning. — [Crossref-verified DOI](https://doi.org/10.1016/j.trc.2020.102772)
- The associated MassDOT report used PointNet++ segmentation. It inventoried 85+ miles of sidewalk and 1,297 curb ramps on MA Route 9 at 7.0 and 2.2 min/mile. — [ROSAP](https://rosap.ntl.bts.gov/view/dot/61618)
- Earlier work by Ai & Tsai (2016) measured ADA features (sidewalk width, cross slope, grade, curb ramp slope) from mobile LiDAR plus video logs. — [TRR 10.3141/2542-04](https://journals.sagepub.com/doi/full/10.3141/2542-04) (from search snippet, not fully read)
- A zero-shot SAM study on mobile LiDAR plus satellite imagery found that fusing the two lets SAM fully extract sidewalks in most cases. — [arXiv 2310.09918](https://arxiv.org/pdf/2310.09918); [MDPI J. Imaging](https://mdpi.com/2313-433X/10/3/52) (snippet only)
- The 2022 Crowd+AI CVPR workshop paper builds sidewalk topology from satellite imagery with hierarchical multi-scale attention. — [arXiv 2206.13677](https://arxiv.org/abs/2206.13677)

### Inferences
- For slope and cross slope, which matter most for wheelchair users, LiDAR (Ohio statewide aerial LiDAR, or mobile LiDAR) is the only verified imagery-adjacent source with real geometric fidelity. RGB imagery alone does not give it reliably (see VLM findings).

### Gaps
- Exact Hou & Ai accuracy numbers were not retrieved.

## Street-view sidewalk quality and obstacle detection

### Takeaway
Fine-grained condition classification is still immature. In the best open benchmark (Liu et al., ASSETS 2024), only 13 of 33 condition tags reach F1 of 0.7 or higher, and curb ramp "steep" scores F1=0. Material segmentation (CitySurfaces) works well, at 90.5% mIoU.

### Cited Findings
- Liu et al. 2024 compared DINOv2 and CLIP-ViT on 640x640 GSV crops for 33 tags. The clean set had about 24k images from 10 cities and the noisy set about 87k from 12 cities. DINOv2 was best. Top tags were missing tactile warning (0.94), parked car (0.93), brick/cobblestone (0.91) and paint fading (0.8). The worst were steep (0), utility panel (0) and narrow (0.3). Noisy data dropped curb ramp F1 from 0.62 to 0.3. — [PDF](https://makeabilitylab.cs.washington.edu/media/publications/Liu_TowardsFineGrainedSidewalkAccessibilityAssessmentWithDeepLearningInitialBenchmarksAndAnOpenDataset_ASSETS2024.pdf)
- Project Sidewalk is deployed in 21 cities across 8 countries, with over 1M labels and 693k validations across 11k street miles (as of 2024). — [Liu PDF](https://makeabilitylab.cs.washington.edu/media/publications/Liu_TowardsFineGrainedSidewalkAccessibilityAssessmentWithDeepLearningInitialBenchmarksAndAnOpenDataset_ASSETS2024.pdf)
- Liu et al.'s stated future work: a unified multi-label model, severity inference, and long-tail handling. — same PDF
- CitySurfaces reached 90.5% mIoU for sidewalk material segmentation (NYC and Boston training, 6 test cities). — [arXiv](https://arxiv.org/abs/2201.02260)
- Related datasets: SideSeeing, a multimodal sidewalk-assessment toolkit ([arXiv 2407.06464](https://arxiv.org/pdf/2407.06464)), and StreetSurfaceVis, 9,122 Mapillary images labeled for surface type and quality ([arXiv 2407.21454](https://arxiv.org/pdf/2407.21454v3.pdf)). Both are from search snippets only.

### Inferences
- The tags that matter most to wheelchair users (steep, narrow, uneven/slanted) are the ones current models handle worst.

### Gaps
- I did not verify a strong obstacle-detection paper aimed specifically at wheelchair users.

## Foundation-model / VLM approaches (2023-2026)

### Takeaway
VLMs are emerging as zero-shot accessibility screeners. They correlate moderately with real wheelchair friction (r up to -0.54) and handle salient features (curb ramps, crosswalks) well. They are not reliable for metric attributes like cross slope or for pavement condition without calibration.

### Cited Findings
- Wang et al. (WACV 2027) used expert-guided RAG VLMs on 407 UF-campus GSV locations, scored against wheelchair GPS dwell time. Correlation went from r=-0.40 to -0.54 with expert guidance, and agreement was weaker for subtle surfaces, transient obstructions and viewpoint-dependent barriers. — [arXiv 2606.07642](https://arxiv.org/abs/2606.07642)
- Lieu et al. (arXiv Sep 2026) tested 4 VLMs on 514 Seoul images against field measurements. No attribute reached compliance-grade precision. Cross slope intervals were too wide for regulatory thresholds, and uncalibrated sampling covered only 17-47% of field values. — [arXiv 2609.17882](https://arxiv.org/abs/2609.17882)
- A Feb 2026 Project Sidewalk paper uses a VLM to generate localized annotator guidance in Chandigarh, India. — [arXiv 2602.09216](https://arxiv.org/abs/2602.09216) (abstract-level only)
- Liu 2024 used foundation-model backbones (DINOv2, CLIP-ViT) for fine-tuned classification. — [Liu PDF](https://makeabilitylab.cs.washington.edu/media/publications/Liu_TowardsFineGrainedSidewalkAccessibilityAssessmentWithDeepLearningInitialBenchmarksAndAnOpenDataset_ASSETS2024.pdf)
- An ICCV 2025 workshop dedicated to this area exists: "Vision Foundation Models and Generative AI for Accessibility" (CV4A11y). — [arXiv 2508.09415](https://arxiv.org/abs/2508.09415)

### Inferences
- A practical design for Cincinnati and Oxford: use VLMs for triage (flag segments far from thresholds) and send borderline segments to field or LiDAR measurement. This mirrors the conformal-prediction screening idea in Lieu et al.

### Gaps
- Both key VLM papers are 2026 and very recent. Lieu et al. is not yet peer-reviewed.

## What remains open

### Takeaway
Detecting the presence of features (sidewalks, curb ramps, crosswalks) is mature. The open problems are condition and severity, metric geometry (slope, cross slope, width), generalization to new and smaller cities, imagery staleness, and validation against real wheelchair experience.

### Cited Findings
- Slope and cross slope: VLM cross slope intervals are too wide to resolve ADA thresholds ([Lieu et al.](https://arxiv.org/abs/2609.17882)), and the "steep" curb ramp tag scores F1=0 ([Liu et al.](https://makeabilitylab.cs.washington.edu/media/publications/Liu_TowardsFineGrainedSidewalkAccessibilityAssessmentWithDeepLearningInitialBenchmarksAndAnOpenDataset_ASSETS2024.pdf)).
- Condition and severity: only 13 of 33 tags reach F1 of 0.7, and severity inference is listed as future work. — [Liu et al.](https://makeabilitylab.cs.washington.edu/media/publications/Liu_TowardsFineGrainedSidewalkAccessibilityAssessmentWithDeepLearningInitialBenchmarksAndAnOpenDataset_ASSETS2024.pdf)
- Generalization: RampNet covers 3 US cities and flags regional bias and rural/small-town imagery gaps ([arXiv](https://arxiv.org/html/2508.09415v1)). Tile2Net is weaker under tree canopy and in DC ([NSF PAR](https://par.nsf.gov/servlets/purl/10493942)).
- Ground truth staleness: Cambridge GIS sidewalks changed 9.2% and crosswalks 23% over 2011-2018. — [NSF PAR](https://par.nsf.gov/servlets/purl/10493942)
- Validation against lived experience: only Wang et al. validate against actual wheelchair traces (n=407 locations, one campus). — [arXiv 2606.07642](https://arxiv.org/abs/2606.07642)
- Benchmarks: there is a stated need for standardized labeled satellite and streetscape benchmarks. — [arXiv 2206.13677](https://arxiv.org/abs/2206.13677)

### Inferences
- No verified study covers Ohio or Midwest cities. Cincinnati (hilly, so slope is critical) and Oxford (a small college town with possibly sparse or stale GSV) sit right in the documented gaps.

### Gaps
- I did not find a study that fuses aerial networks, street-view conditions and LiDAR slope into one routable accessibility graph with field validation.
