# Where America plays the lottery — New York and Texas

Interactive map of lottery ticket sales by ZIP code, with a toggle to control for
population (total dollars vs sales per resident). New York and Texas are the only two
states that publish current, machine-readable sales broken out by retailer location.

## Live
- Local preview: docs/ served as a static site.

## Data
- **New York**: NY State Gaming Commission, Lottery Daily Retailer Sales (xyvi-fbb9),
  data.ny.gov. Trailing 12 months. Sales = sum of all draw-game wagers + settled
  scratch-off value (ig_settles). Prize payouts (draw_paid, ig_paid) excluded.
- **Texas**: Texas Lottery Commission, sales by retailer (beka-uwfq), data.texas.gov.
  Trailing 12 months. Sales = sum of net_ticket_sales across all games, by ZIP.
- **Population**: U.S. Census ACS 2019–2023 5-year, total population by ZCTA (B01003).
- **ZIP centroids**: U.S. Census 2023 national gazetteer (ZCTA).

## Key methodology notes
- Sales are recorded at the **store**, not the buyer's home. Commercial / commuter /
  border ZIP codes look like heavy players for that reason; per-resident figures there
  are inflated. This is stated on the page.
- New York: excluded business types COURIER and LOTTERY-VENDOR — these are online /
  courier agents (e.g. one Newburgh courier booked $186M of statewide online sales to a
  single address) and are not tied to a neighborhood.
- ZIP codes under 1,000 residents dropped. Per-resident rankings use a 5,000-resident floor.

## Rebuild
    export CENSUS_API_KEY=<key>
    cd build && python3 assemble.py    # writes lottery_map.json + meta.json
    cp lottery_map.json meta.json ../docs/

Requires the Census 2023 gazetteer ZCTA file at build/gaz/2023_Gaz_zcta_national.txt.

## Map geometry
- ZIP boundaries: Census 2020 ZCTA cartographic files (via OpenDataDE State-zip-code-GeoJSON).
- build/merge_geo.py: keeps only ZIPs with data, rounds coords, attaches metrics → zcta.json.
- Simplified with mapshaper (`-simplify 12% keep-shapes`) to ~4.6 MB for the live map.
- The page renders a quantile choropleth (8 within-view bins), recoloured on each toggle.
