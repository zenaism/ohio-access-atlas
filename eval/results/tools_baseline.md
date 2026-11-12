# Question bank: tools-only baseline

Run 2026-11-12 with `scripts/eval_tools.py` (no language model). **Hit rate at 5: 33/33 = 100%** of answerable questions; 11 questions need data we do not have (listed below).

Caveat: the expected places were written after looking at our data, so this is a regression baseline (it catches breakage when data or tools change), not an independent quality score. A real score needs expected answers written by people who know these places.

| id | category | verdict | top results |
|---|---|---|---|
| restroom-near-me | restrooms | hit | Fountain Square; Contemporary Arts Center; Aronoff Center for the Arts; National Underground Railroad Freedom Center; Cincinnati Reds Hall of Fame & Museum |
| changing-table-downtown | restrooms | hit | Cincinnati Art Museum; Cincinnati Museum Center |
| findlay-restroom | restrooms | unknown (gap) | Restroom near Findlay Market; Restroom near Jungle Jim’s International Market |
| smale-restroom | restrooms | hit | Smale Riverfront Park |
| oxford-restroom-late | restrooms | unknown (gap) | (none) |
| otr-coffee | food | hit | MECCA; Alice; Ché; Eli’s BBQ; Fifty Fifty Gin Club |
| oxford-restaurant-bathroom | food | unknown (gap) | (none) |
| northside-brewery | food | unknown (gap) | Streetside Brewery |
| skyline-ludlow | food | unknown (gap) | (none) |
| otr-birthday | food | hit | MECCA; Alice; Ché; Eli’s BBQ; Fifty Fifty Gin Club |
| union-terminal-sidewalk | getting there | hit | Cincinnati Museum Center |
| mt-adams-steep | getting there | unknown (gap) | Restroom near Mount Storm Shelter; 500 Lafayette at Mount Storm Park; Mount Airy Forest; Restroom near Mount Saint Joseph University Sports Complex |
| bus-to-zoo | getting there | hit | Cincinnati Zoo & Botanical Garden |
| gabp-parking | getting there | hit | Great American Ball Park |
| high-street-ramps | getting there | unknown (gap) | Spring Street Treats; Maplestreet Station; Bodega; Calendula and The Lounge; Chop Bento |
| fountain-square-closures | getting there | unknown (gap) | Restroom near Tyler Davidson Fountain; Fountain Square; Fifth Third Bank; Contemporary Arts Center; Government Square Transit Center |
| metro-access | getting there | hit | Metro Access (Cincinnati Metro paratransit); Greater Cincinnati buses (Metro, TANK, BCRTA) |
| paved-trails-cincinnati | trails | hit | Armleder Park Trail; Armleder-Lunken Connector Trail; Creekside Trail; Five Mile Trail; Lebanon Countryside YMCA Trail |
| oxford-flat-trail | trails | hit | Oxford Area Trails (OATS), Miami University portion; DeWitt Log Homestead; Helen S. Ruder Preserve; Leonard Howell Park; Peffer Park |
| sharon-woods-loop | trails | hit | Sharon Woods; Sharon Woods Loop Trail; MobilityWorks of Sharonville-Cincinnati, OH; Restroom near Sharonville Presbyterian Church; Sharonville Convention Center |
| waterfall | trails | unknown (gap) | Krohn Conservatory |
| treehouse | trails | hit | Everybody's Treehouse, Mt. Airy Forest |
| hueston-woods | trails | hit | Hueston Woods Marina; Hueston Woods Lodge; Restroom near Hueston Woods State Nature Preserve; Restroom near Hueston Woods Sugar House |
| all-terrain-chair | trails | hit | GRIT all-terrain chair pickup (MetroParks of Butler County); MetroParks of Butler County |
| museums-accessible | museums | hit | Cincinnati Museum Center; Music Hall; William Howard Taft National Historic Site; National Underground Railroad Freedom Center; Aronoff Center for the Arts |
| art-museum-wheelchairs | museums | hit | Cincinnati Art Museum |
| mcguffey | museums | hit | McGuffey House and Museum |
| sensory-hours | museums | hit | Cincinnati Playhouse in the Park; Cincinnati Shakespeare Company |
| aronoff-seats | museums | hit | Aronoff Center for the Arts |
| accessibility-events-month | events | hit | Cincinnati Shakespeare Company; Cincinnati Playhouse in the Park; Children's Theatre of Cincinnati (Emery Theater) |
| oxford-weekend | events | hit | Goggin Ice Center; Souers Recital Hall |
| disability-pride | events | unknown (gap) | (none) |
| blink | events | hit | BLINK 2026 festival |
| adaptive-sports | events | hit | Manuel D. & Rhoda Mayerson JCC |
| support-groups | events | unknown (gap) | (none) |
| wheelchair-repair | services | hit | Mobility Plus Cincinnati East; MobilityWorks of Sharonville-Cincinnati, OH; Superior Van & Mobility |
| report-ramp | services | hit | City of Cincinnati 311 (accessibility reports); William Howard Taft National Historic Site; Cincinnati Museum Center; Aronoff Center for the Arts; BB Riverboats |
| oxford-roll-in | services | hit | Hueston Woods Lodge |
| miami-entrances | services | hit | Hall Auditorium; Armstrong Student Center; Alumni Hall; Anderson Hall; Art Building |
| van-rental | services | hit | Superior Van & Mobility; Mobility Plus Cincinnati East; MobilityWorks of Sharonville-Cincinnati, OH |
| up-to-date | trust | hit | Cincinnati Museum Center |
| facebook-ramp | trust | hit | Taft Theatre |
| google-disagrees | trust | hit | Thomson Hall |
| ada-compliant | trust | hit | Music Hall |

## Data gaps (the assistant must say "not known")

- **Does Findlay Market have an accessible restroom?** Findlay Market's own accessibility page is not collected; OSM restroom near it has no wheelchair tag
- **Are there accessible restrooms in Uptown Oxford open after 9 pm?** no Uptown public restroom with wheelchair and opening-hours data; restaurant listings do not say
- **Which restaurants in Oxford have an accessible bathroom too?** Enjoy Oxford tags say "wheelchair accessible" with no restroom detail
- **Is there a brewery with a ramp and outdoor seating near Northside?** no ramp or patio data for breweries
- **Can I get my power chair into Skyline on Ludlow?** that Skyline is not in the data (the only Skyline is in Oxford); needs addresses or Google Places
- **Is Mt. Adams too steep to roll around?** slope data exists per path, but there is no neighborhood-level tool yet
- **Are there curb ramps on High Street in Oxford?** no curb-ramp inventory for Oxford (CAGIS covers Hamilton County only); 2025 city claim of "every curb" is not place-level
- **Any sidewalk closures or construction near Fountain Square this week?** no closure feed; 311 reports are counted per place but not listed
- **Where can I see a waterfall without stairs?** no waterfall viewpoints with access data
- **When is Disability Pride Cincinnati this year?** Disability Pride Cincinnati site did not respond; no dated record
- **Any support groups for new wheelchair users in Cincinnati?** CILO and similar organizations' calendars not readable
