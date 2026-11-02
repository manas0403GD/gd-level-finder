const extract = p => Array.isArray(p) ? p : (p && typeof p==="object" ? ["data","levels","demons","results","items"].map(k=>p[k]).find(Array.isArray)||[] : []);
async function getJson(url, headers={}) { const r=await fetch(url,{headers:{Accept:"application/json",...headers}}); if(!r.ok) throw new Error(`${url}: HTTP ${r.status}`); return r.json(); }
export async function onRequestGet() {
  const result={pointercrate:[],aredl:[],errors:{}};
  try {
    let after=null;
    for(let i=0;i<3;i++){
      const url="https://pointercrate.com/api/v2/demons/listed/?limit=100"+(after!==null?"&after="+after:"");
      const rows=extract(await getJson(url));
      if(!rows.length) break;
      result.pointercrate.push(...rows.filter(v=>v&&v.level_id!=null));
      const positions=rows.map(v=>v?.position).filter(v=>v!=null);
      if(rows.length<100||!positions.length) break;
      after=Math.max(...positions);
    }
  } catch(e) { result.errors.pointercrate=String(e); }
  try {
    const url="https://api.aredl.net/v2/api/aredl/levels?exclude_legacy=false&exclude_pending=false&exclude_removed=false";
    const payload=await getJson(url,{Origin:"https://aredl.net",Referer:"https://aredl.net/"});
    result.aredl=extract(payload).filter(v=>v&&v.level_id!=null);
    if(!result.aredl.length) throw new Error("No recognizable AREDL records");
  } catch(e) { result.errors.aredl=String(e); }
  return Response.json(result,{headers:{"Cache-Control":"public, max-age=900"}});
}