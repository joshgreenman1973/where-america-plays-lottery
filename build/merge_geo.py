import json
data={d["zip"]:d for d in json.load(open("lottery_map.json"))}
def rnd(o):
    if isinstance(o,list):
        if o and isinstance(o[0],(int,float)): return [round(o[0],3),round(o[1],3)]
        return [rnd(x) for x in o]
    return o
def dedup(geom):
    # drop consecutive duplicate points after rounding
    def clean_ring(r):
        out=[r[0]]
        for p in r[1:]:
            if p!=out[-1]: out.append(p)
        return out if len(out)>=4 else r
    t=geom["type"]; c=geom["coordinates"]
    if t=="Polygon": geom["coordinates"]=[clean_ring(r) for r in c]
    elif t=="MultiPolygon": geom["coordinates"]=[[clean_ring(r) for r in poly] for poly in c]
    return geom
feats=[]
for fn,state in [("ny_zcta.json","NY"),("tx_zcta.json","TX")]:
    g=json.load(open(fn))
    for f in g["features"]:
        z=f["properties"].get("ZCTA5CE10")
        if z not in data: continue
        d=data[z]
        geom=dedup({"type":f["geometry"]["type"],"coordinates":rnd(f["geometry"]["coordinates"])})
        feats.append({"type":"Feature","geometry":geom,"properties":{
            "zip":z,"state":state,"sales":d["sales"],"per_cap":d["per_cap"],
            "pop":d["pop"],"city":d["city"],"retailers":d["retailers"]}})
    g=None
out={"type":"FeatureCollection","features":feats}
json.dump(out,open("zcta.json","w"),separators=(",",":"))
import os
print("features:",len(feats),"size MB:",round(os.path.getsize("zcta.json")/1e6,1))
