import urllib.request, urllib.parse, json
def get(u): return json.load(urllib.request.urlopen(u, timeout=180))
q=("SELECT cal_year AS y, cal_month AS m, "
   "sum(case(game_category='Powerball®' OR game_category='Mega Millions®',net_sales_amount)) AS jackpot, "
   "sum(case(game_category='Scratch Tickets',net_sales_amount)) AS scratch "
   "WHERE cal_year>=2024 AND location_state='TX' GROUP BY cal_year,cal_month ORDER BY cal_year,cal_month")
rows=get("https://data.texas.gov/resource/beka-uwfq.json?"+urllib.parse.urlencode({"$query":q}))
mn=["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
print("TX monthly: Powerball+Mega (jackpot-driven) vs Scratch")
js=[]
for r in rows:
    j=float(r.get("jackpot") or 0); s=float(r.get("scratch") or 0)
    js.append((f"{mn[int(r['m'])]} {r['y']}", j, s))
    bar="#"*int(j/3e6)
    print(f"  {mn[int(r['m'])]} {r['y']}: Powerball+Mega ${j/1e6:6.1f}M {bar}")
jv=[x[1] for x in js]
hi=max(js,key=lambda x:x[1]); lo=min(js,key=lambda x:x[1])
print(f"\n  Peak jackpot month: {hi[0]} ${hi[1]/1e6:.0f}M  |  Quietest: {lo[0]} ${lo[1]/1e6:.0f}M  |  ratio {hi[1]/lo[1]:.1f}x")
sv=[x[2] for x in js]
print(f"  Scratch range: ${min(sv)/1e6:.0f}M - ${max(sv)/1e6:.0f}M  (ratio {max(sv)/min(sv):.2f}x) -- far steadier than jackpot games")
