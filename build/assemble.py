import urllib.request, urllib.parse, json, os
def get(u): return json.load(urllib.request.urlopen(u, timeout=300))
KEY=os.environ["CENSUS_API_KEY"]

# centroids
cent={}
for line in open("gaz/2023_Gaz_zcta_national.txt", encoding="latin-1"):
    p=line.rstrip("\n").split("\t")
    if p[0]=="GEOID": continue
    try: cent[p[0].strip()]=(round(float(p[5]),5), round(float(p[6]),5))
    except: pass

# population (cached)
if os.path.exists("pop.json"):
    POP=json.load(open("pop.json"))
else:
    cen=get(f"https://api.census.gov/data/2023/acs/acs5?get=B01003_001E,B09021_001E&for=zip%20code%20tabulation%20area:*&key={KEY}")
    i={h:k for k,h in enumerate(cen[0])}
    POP={r[i["zip code tabulation area"]]:{"pop":int(r[0]) if r[0] else 0,"adults":int(r[1]) if r[1] else 0} for r in cen[1:]}
    json.dump(POP,open("pop.json","w"))
print("pop ZCTAs:",len(POP),"centroids:",len(cent))

dc=["numbers_day","numbers_eve","numbers_iw","win4_day","win4_eve","win4_iw","t5_day","t5_eve","take5_iw","pick10","lotto","mega","megaplier","jtj","powerball","powerplay","doubleplay","c4l","m4l","quick_draw","qd_extra","money_dots"]
ds="+".join(f"coalesce(sum({c}),0)" for c in dc)
# NY: exclude non-geographic agent types (couriers, vendor)
nyq=(f"SELECT buszip AS zip, ({ds})+coalesce(sum(ig_settles),0) AS sales, count(distinct agtno) AS retailers "
     f"WHERE bus_day>='2025-06-01T00:00:00' AND buszip IS NOT NULL "
     f"AND bustype NOT IN ('COURIER','LOTTERY-VENDOR','CORPORATE HQ') GROUP BY buszip LIMIT 5000")
ny=get("https://data.ny.gov/resource/xyvi-fbb9.json?"+urllib.parse.urlencode({"$query":nyq}))
nymax=get("https://data.ny.gov/resource/xyvi-fbb9.json?"+urllib.parse.urlencode({"$query":"SELECT max(bus_day) AS d"}))[0]["d"][:10]
nyc=get("https://data.ny.gov/resource/xyvi-fbb9.json?"+urllib.parse.urlencode({"$query":"SELECT buszip AS zip, max(buscity) AS city WHERE buszip IS NOT NULL GROUP BY buszip LIMIT 5000"}))
NYCITY={r["zip"][:5]:r.get("city","") for r in nyc}

# TX
mm=get("https://data.texas.gov/resource/beka-uwfq.json?"+urllib.parse.urlencode({"$query":"SELECT max(cal_month) AS m WHERE cal_year=2026"}))
latest=int(mm[0]["m"])
txq=(f"SELECT location_zip AS zip, sum(net_sales_amount) AS sales, count(distinct retailer_number) AS retailers, "
     f"max(location_city) AS city, max(location_county_desc) AS county "
     f"WHERE ((cal_year=2025 AND cal_month>{latest}) OR (cal_year=2026 AND cal_month<={latest})) "
     f"AND location_zip IS NOT NULL AND location_state='TX' GROUP BY location_zip LIMIT 5000")
tx=get("https://data.texas.gov/resource/beka-uwfq.json?"+urllib.parse.urlencode({"$query":txq}))

def build(rows, state, cityfn):
    out=[]
    for r in rows:
        z=r["zip"][:5]
        if z not in cent or z not in POP: continue
        pop=POP[z]["pop"]
        if pop<1000: continue
        sales=float(r["sales"])
        if sales<=0: continue
        lat,lon=cent[z]
        out.append({"zip":z,"state":state,"sales":round(sales),"retailers":int(r["retailers"]),
            "pop":pop,"per_cap":round(sales/pop,1),"lat":lat,"lon":lon,"city":cityfn(r,z)})
    return out
data = build(ny,"NY", lambda r,z:(NYCITY.get(z,"") or "").title()) + build(tx,"TX", lambda r,z:(r.get("city","") or "").title())
data.sort(key=lambda d:d["sales"], reverse=True)
json.dump(data, open("lottery_map.json","w"))

mons=["","Jan","Feb","Mar","Apr","May","June","July","Aug","Sept","Oct","Nov","Dec"]
meta={"ny_window":"June 2025 through "+nymax,
      "tx_window":("%s 2025 through %s 2026"%(mons[latest+1] if latest<12 else "Jan", mons[latest])),
      "generated":nymax}
json.dump(meta, open("meta.json","w"))

for st in ("NY","TX"):
    s=[d for d in data if d["state"]==st]; tot=sum(d["sales"] for d in s)
    print(f"\n{st}: {len(s)} ZIPs, ${tot/1e9:.2f}B")
    for d in sorted(s,key=lambda d:d["sales"],reverse=True)[:4]:
        print(f"  TOTAL {d['zip']} {d['city'][:16]:16} ${d['sales']/1e6:6.1f}M  ${d['per_cap']:.0f}/cap pop{d['pop']}")
    for d in sorted([d for d in s if d['pop']>=5000],key=lambda d:d["per_cap"],reverse=True)[:4]:
        print(f"  PERCAP {d['zip']} {d['city'][:16]:16} ${d['per_cap']:.0f}/cap  (${d['sales']/1e6:.1f}M pop{d['pop']})")
print("\nmeta:",meta,"\nsaved",len(data),"rows")
