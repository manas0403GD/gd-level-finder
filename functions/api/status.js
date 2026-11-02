export async function onRequestGet({ env }) {
  const [levels, cached, tagged] = await Promise.all([
    env.DB.prepare("SELECT COUNT(*) AS n FROM levels").first(),
    env.DB.prepare("SELECT COUNT(*) AS n FROM levels WHERE tags_json IS NOT NULL").first(),
    env.DB.prepare("SELECT COUNT(*) AS n FROM levels WHERE tags_json NOT IN ('[]','')").first()
  ]);
  return Response.json({levels:levels.n,cached:cached.n,withTags:tagged.n,empty:levels.n-tagged.n,preloaded:true});
}