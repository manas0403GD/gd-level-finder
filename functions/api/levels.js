export async function onRequestGet({ request, env }) {
  const q = new URL(request.url).searchParams.get("q")?.trim() || "";
  let result;
  if (q) {
    const like = `%${q}%`;
    result = await env.DB.prepare(`SELECT id,name,creator,song,difficulty,rating,side_rating,enjoyment_avg,enjoyment_votes,tags_json,tier,side_tier FROM levels WHERE name LIKE ?1 OR creator LIKE ?1 OR song LIKE ?1 OR id LIKE ?1 ORDER BY name COLLATE NOCASE`).bind(like).all();
  } else {
    result = await env.DB.prepare(`SELECT id,name,creator,song,difficulty,rating,side_rating,enjoyment_avg,enjoyment_votes,tags_json,tier,side_tier FROM levels ORDER BY name COLLATE NOCASE`).all();
  }
  return Response.json(result.results || []);
}