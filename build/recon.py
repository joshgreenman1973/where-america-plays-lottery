import urllib.request, urllib.parse, json
def get(u): return json.load(urllib.request.urlopen(u, timeout=180))

# TX game categories
txq="SELECT game_category, sum(net_sales_amount) AS s WHERE ((cal_year=2025 AND cal_month>6) OR (cal_year=2026 AND cal_month<=6)) AND location_state='TX' GROUP BY game_category ORDER BY s DESC"
print("=== TX game categories (trailing 12mo) ===")
tot=0; rows=get("https://data.texas.gov/resource/beka-uwfq.json?"+urllib.parse.urlencode({"$query":txq}))
for r in rows: tot+=float(r["s"])
for r in rows: print(f"  {r['game_category']:22} ${float(r['s'])/1e6:8.1f}M  ({100*float(r['s'])/tot:4.1f}%)")
print(f"  TOTAL ${tot/1e6:.0f}M")

# NY statewide game totals (trailing 12mo, excl couriers/vendor)
games=["numbers_day","numbers_eve","numbers_iw","win4_day","win4_eve","win4_iw","t5_day","t5_eve","take5_iw","pick10","lotto","mega","megaplier","jtj","powerball","powerplay","doubleplay","c4l","m4l","quick_draw","qd_extra","money_dots","ig_settles"]
sel=", ".join(f"coalesce(sum({g}),0) AS {g}" for g in games)
nyq=(f"SELECT {sel} WHERE bus_day>='2025-06-01T00:00:00' AND bustype NOT IN ('COURIER','LOTTERY-VENDOR','CORPORATE HQ')")
r=get("https://data.ny.gov/resource/xyvi-fbb9.json?"+urllib.parse.urlencode({"$query":nyq}))[0]
print("\n=== NY statewide game totals (trailing 12mo) ===")
ntot=sum(float(r[g]) for g in games)
for g in games:
    v=float(r[g]); 
    if v>1e6: print(f"  {g:13} ${v/1e6:8.1f}M  ({100*v/ntot:4.1f}%)")
print(f"  TOTAL ${ntot/1e6:.0f}M")
