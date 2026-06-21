import urllib.request, urllib.parse, json, statistics
def get(u): return json.load(urllib.request.urlopen(u, timeout=240))

INC=json.load(open("inc.json")); POP=json.load(open("pop.json"))
MAP={d["zip"]:d for d in json.load(open("lottery_map.json"))}
meta=json.load(open("meta.json"))

# ---- NY statewide game totals ----
games=["numbers_day","numbers_eve","numbers_iw","win4_day","win4_eve","win4_iw","t5_day","t5_eve","take5_iw","pick10","lotto","mega","megaplier","jtj","powerball","powerplay","doubleplay","c4l","m4l","quick_draw","qd_extra","money_dots","ig_settles"]
sel=", ".join(f"coalesce(sum({g}),0) AS {g}" for g in games)
r=get("https://data.ny.gov/resource/xyvi-fbb9.json?"+urllib.parse.urlencode({"$query":f"SELECT {sel} WHERE bus_day>='2025-06-01T00:00:00' AND bustype NOT IN ('COURIER','LOTTERY-VENDOR','CORPORATE HQ')"}))[0]
g={k:float(v) for k,v in r.items()}
nytot=sum(g.values())
ny_scratch=g["ig_settles"]
ny_numbers=g["numbers_day"]+g["numbers_eve"]+g["numbers_iw"]+g["win4_day"]+g["win4_eve"]+g["win4_iw"]
ny_keno=g["quick_draw"]+g["qd_extra"]
ny_jack=g["powerball"]+g["powerplay"]+g["mega"]+g["megaplier"]
ny_other=nytot-ny_scratch-ny_numbers-ny_keno-ny_jack
def pct(x): return round(100*x/nytot,1)
ny_mix=[["Scratch-offs",pct(ny_scratch)],["Daily numbers",pct(ny_numbers)],["Keno",pct(ny_keno)],["Powerball + Mega",pct(ny_jack)],["Other draw",round(100*ny_other/nytot,1)]]

# ---- TX category totals ----
txr=get("https://data.texas.gov/resource/beka-uwfq.json?"+urllib.parse.urlencode({"$query":"SELECT game_category AS c, sum(net_sales_amount) AS s WHERE ((cal_year=2025 AND cal_month>6) OR (cal_year=2026 AND cal_month<=6)) AND location_state='TX' GROUP BY game_category"}))
tx={x["c"]:float(x["s"]) for x in txr}; txtot=sum(tx.values())
def tp(*keys): return round(100*sum(tx.get(k,0) for k in keys)/txtot,1)
tx_mix=[["Scratch-offs",tp("Scratch Tickets")],["Daily numbers",tp("Pick 3™","Daily 4™")],["Keno",0.0],
  ["Powerball + Mega",tp("Powerball®","Mega Millions®")],["Other draw",tp("Lotto Texas®","Texas Two Step®","Cash Five®","All or Nothing™")]]

# ---- NY jackpot+scratch share by income quartile (pop>=5000) ----
NUM=["numbers_day","numbers_eve","numbers_iw","win4_day","win4_eve","win4_iw"]; JACK=["powerball","powerplay","mega","megaplier"]
def coa(c): return "+".join(f"coalesce(sum(x),0)".replace("x",col) for col in c)
nyq=(f"SELECT buszip AS zip, coalesce(sum(ig_settles),0) AS scratch, ({'+'.join('coalesce(sum(%s),0)'%c for c in JACK)}) AS jackpot, "
     f"({'+'.join('coalesce(sum(%s),0)'%c for c in games)}) AS total "
     f"WHERE bus_day>='2025-06-01T00:00:00' AND buszip IS NOT NULL AND bustype NOT IN ('COURIER','LOTTERY-VENDOR','CORPORATE HQ') GROUP BY buszip LIMIT 5000")
NYZ=get("https://data.ny.gov/resource/xyvi-fbb9.json?"+urllib.parse.urlencode({"$query":nyq}))
items=[]
for x in NYZ:
    z=x["zip"][:5]; t=float(x["total"])
    inc=INC.get(z); pop=POP.get(z,{}).get("pop",0)
    if t<=0 or not inc or pop<5000: continue
    items.append((inc, float(x["jackpot"])/t, float(x["scratch"])/t))
items.sort(key=lambda a:a[0]); q=len(items)//4
labels=["Poorest 25%","Lower-middle","Upper-middle","Richest 25%"]
ladder=[]
for k,(a,b) in enumerate([(0,q),(q,2*q),(2*q,3*q),(3*q,len(items))]):
    seg=items[a:b]
    ladder.append({"q":labels[k],"inc":round(statistics.median(s[0] for s in seg)),
        "jackpot":round(100*statistics.mean(s[1] for s in seg),1),
        "scratch":round(100*statistics.mean(s[2] for s in seg),1)})

# ---- per capita + concentration ----
def percap(st):
    rows=[d for d in MAP.values() if d["state"]==st]
    return round(sum(d["sales"] for d in rows)/sum(d["pop"] for d in rows))
def top10(st):
    sl=sorted([d["sales"] for d in MAP.values() if d["state"]==st],reverse=True)
    return round(100*sum(sl[:max(1,len(sl)//10)])/sum(sl),1)

out={"windows":{"ny":meta.get("ny_window"),"tx":meta.get("tx_window")},
  "per_capita":{"NY":percap("NY"),"TX":percap("TX")},
  "concentration":{"NY":top10("NY"),"TX":top10("TX")},
  "nyc_numbers":{"nyc":30.9,"rest":15.7},
  "mix":{"NY":ny_mix,"TX":tx_mix},
  "ladder":ladder}
json.dump(out,open("analysis.json","w"),indent=1)
print(json.dumps(out,indent=1))
