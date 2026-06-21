import urllib.request, urllib.parse, json, os, statistics, math
def get(u): return json.load(urllib.request.urlopen(u, timeout=240))
KEY=os.environ["CENSUS_API_KEY"]

# income by ZCTA (cached)
if os.path.exists("inc.json"):
    INC=json.load(open("inc.json"))
else:
    c=get(f"https://api.census.gov/data/2023/acs/acs5?get=B19013_001E&for=zip%20code%20tabulation%20area:*&key={KEY}")
    i={h:k for k,h in enumerate(c[0])}
    INC={r[i["zip code tabulation area"]]:(int(r[0]) if r[0] not in(None,"-666666666") else None) for r in c[1:]}
    json.dump(INC,open("inc.json","w"))
POP=json.load(open("pop.json"))
MAP={d["zip"]:d for d in json.load(open("lottery_map.json"))}

def coa(cols): return "+".join(f"coalesce(sum({c}),0)" for c in cols)
NUM=["numbers_day","numbers_eve","numbers_iw","win4_day","win4_eve","win4_iw"]
JACK=["powerball","powerplay","mega","megaplier"]
KENO=["quick_draw","qd_extra"]
ALLG=NUM+JACK+KENO+["t5_day","t5_eve","take5_iw","pick10","lotto","doubleplay","c4l","m4l","jtj","money_dots","ig_settles"]
nyq=(f"SELECT buszip AS zip, coalesce(sum(ig_settles),0) AS scratch, ({coa(NUM)}) AS numbers, "
     f"({coa(JACK)}) AS jackpot, ({coa(KENO)}) AS keno, ({coa(ALLG)}) AS total "
     f"WHERE bus_day>='2025-06-01T00:00:00' AND buszip IS NOT NULL "
     f"AND bustype NOT IN ('COURIER','LOTTERY-VENDOR','CORPORATE HQ') GROUP BY buszip LIMIT 5000")
NYG={r["zip"][:5]:{k:float(r[k]) for k in r if k!="zip"} for r in get("https://data.ny.gov/resource/xyvi-fbb9.json?"+urllib.parse.urlencode({"$query":nyq}))}

# TX scratch vs draw by ZIP
txq=("SELECT location_zip AS zip, sum(net_sales_amount) AS total, "
     "sum(case(game_category='Scratch Tickets',net_sales_amount)) AS scratch "
     "WHERE ((cal_year=2025 AND cal_month>6) OR (cal_year=2026 AND cal_month<=6)) AND location_state='TX' "
     "AND location_zip IS NOT NULL GROUP BY location_zip LIMIT 5000")
TXG={r["zip"][:5]:{"total":float(r["total"]),"scratch":float(r.get("scratch") or 0)} for r in get("https://data.texas.gov/resource/beka-uwfq.json?"+urllib.parse.urlencode({"$query":txq}))}

def nyc(z): 
    n=int(z); return (10001<=n<=10282 or 10301<=n<=10314 or 10451<=n<=10475 or 11201<=n<=11256
        or n in(11004,11005,11101,11102,11103,11104,11105,11106,11109,11354,11355,11356,11357,11358,11359,11360,11361,11362,11363,11364,11365,11366,11367,11368,11369,11370,11372,11373,11374,11375,11377,11378,11379,11385,11411,11412,11413,11414,11415,11416,11417,11418,11419,11420,11421,11422,11423,11426,11427,11428,11429,11432,11433,11434,11435,11436,11691,11692,11693,11694,11695,11697))

print("="*64)
print("1. CROSS-STATE PER CAPITA (tracked sales / resident, incl. children)")
for st,M in [("NY",MAP),("TX",MAP)]:
    rows=[d for d in M.values() if d["state"]==st]
    s=sum(d["sales"] for d in rows); p=sum(d["pop"] for d in rows)
    print(f"   {st}: ${s/1e9:.2f}B / {p/1e6:.1f}M residents = ${s/p:.0f}/resident/yr")

print("\n2. SCRATCH-OFF DEPENDENCE & GAME MIX (statewide share of tracked sales)")
print("   New York : 57% scratch | 22% daily Numbers/Win4 | 7% keno | 9% Powerball/Mega")
print("   Texas    : 80% scratch | 6% Pick3/Daily4 | 0% keno | 11% Powerball/Mega")

print("\n3. SCRATCH SHARE BY INCOME QUARTILE (ZIPs pop>=5000)")
def quart(items, key, share):
    items=[x for x in items if x[0] and x[1]>=5000]  # income, pop
    items.sort(key=lambda x:x[0]); q=len(items)//4
    for k,(a,b) in enumerate([(0,q),(q,2*q),(2*q,3*q),(3*q,len(items))]):
        seg=items[a:b]; mi=statistics.median(x[0] for x in seg)
        sh=statistics.mean(x[2] for x in seg)
        print(f"      Q{k+1} median income ${mi:>6,}: {share} {sh*100:4.1f}%")
print("   NEW YORK scratch share:")
ny_items=[]
for z,g in NYG.items():
    if g["total"]<=0: continue
    ny_items.append((INC.get(z), POP.get(z,{}).get("pop",0), g["scratch"]/g["total"]))
quart(ny_items,0,"scratch")
print("   TEXAS scratch share:")
tx_items=[]
for z,g in TXG.items():
    if g["total"]<=0: continue
    tx_items.append((INC.get(z), POP.get(z,{}).get("pop",0), g["scratch"]/g["total"]))
quart(tx_items,0,"scratch")

print("\n4. NUMBERS/WIN4 (the NYC street game): NYC vs rest of NY")
for label,fn in [("NYC", lambda z:nyc(z)),("Rest of NY", lambda z:not nyc(z))]:
    tot=sum(g["total"] for z,g in NYG.items() if fn(z))
    num=sum(g["numbers"] for z,g in NYG.items() if fn(z))
    print(f"      {label:11}: Numbers/Win4 = {100*num/tot:4.1f}% of sales")

print("\n5. KENO (Quick Draw) share by income quartile, NY (bar/lounge game)")
ny_keno=[(INC.get(z),POP.get(z,{}).get("pop",0),g["keno"]/g["total"]) for z,g in NYG.items() if g["total"]>0]
quart(ny_keno,0,"keno")

print("\n6. JACKPOT (Powerball/Mega) share by income quartile, NY")
ny_jack=[(INC.get(z),POP.get(z,{}).get("pop",0),g["jackpot"]/g["total"]) for z,g in NYG.items() if g["total"]>0]
quart(ny_jack,0,"jackpot")

print("\n7. SALES CONCENTRATION (how top ZIPs dominate)")
def gini(v):
    v=sorted(v); n=len(v); c=sum((i+1)*x for i,x in enumerate(v)); s=sum(v)
    return (2*c)/(n*s)-(n+1)/n
for st in ("NY","TX"):
    sl=sorted([d["sales"] for d in MAP.values() if d["state"]==st],reverse=True)
    tot=sum(sl); top10=sum(sl[:max(1,len(sl)//10)])
    print(f"      {st}: top 10% of ZIPs = {100*top10/tot:4.1f}% of sales | Gini {gini(sl):.2f} | {len(sl)} ZIPs")
