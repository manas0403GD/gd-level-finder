export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const page = Math.max(1, Number.parseInt(url.searchParams.get("page") || "1",10) || 1);
  const perPage = Math.min(20, Math.max(1, Number.parseInt(url.searchParams.get("per_page") || "8",10) || 8));
  const total = (await env.DB.prepare("SELECT COUNT(*) AS n FROM community_ideas").first()).n;
  const {results=[]} = await env.DB.prepare("SELECT id,title,description,author,created_at FROM community_ideas ORDER BY id DESC LIMIT ? OFFSET ?").bind(perPage,(page-1)*perPage).all();
  return Response.json({items:results,page,per_page:perPage,total,pages:Math.max(1,Math.ceil(total/perPage))});
}
export async function onRequestPost({ request, env }) {
  let data; try { data = await request.json(); } catch { return Response.json({error:"Invalid JSON."},{status:400}); }
  const title=String(data.title||"").trim(), description=String(data.description||"").trim(), author=String(data.author||"").trim()||"Anonymous";
  if(!title||!description) return Response.json({error:"Please add both a title and a description."},{status:400});
  if(title.length>90||description.length>1200||author.length>35) return Response.json({error:"Please shorten your idea or display name."},{status:400});
  if(title.length<4||description.length<10) return Response.json({error:"Please provide a little more detail."},{status:400});
  const result=await env.DB.prepare("INSERT INTO community_ideas(title,description,author) VALUES(?,?,?)").bind(title,description,author).run();
  const row=await env.DB.prepare("SELECT id,title,description,author,created_at FROM community_ideas WHERE id=?").bind(result.meta.last_row_id).first();
  return Response.json(row,{status:201});
}