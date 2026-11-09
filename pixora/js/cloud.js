'use strict';
/* PIXORA cloud: Supabase login + project sync */
const sb=(window.supabase&&SUPABASE_URL)?window.supabase.createClient(SUPABASE_URL,SUPABASE_KEY):null;let CU=null,syncT;
function cloudUI(){const el=$('#cloud');if(!sb){el.innerHTML='<p class="hint">Cloud library could not load (offline?).</p>';return}
el.innerHTML=CU?`<b>☁ ${CU.email}</b><button class="pri" onclick="syncNow()">Sync now</button><button onclick="sb.auth.signOut()">Sign out</button>`:`<input id="cem" type="email" placeholder="Email" autocomplete="email"><input id="cpw" type="password" placeholder="Password (6+ characters)" autocomplete="current-password"><button class="pri" onclick="cloudIn()">Sign in</button><button onclick="cloudUp()">Create account</button>`}
async function cloudIn(){const{error}=await sb.auth.signInWithPassword({email:$('#cem').value.trim(),password:$('#cpw').value});if(error)toast(error.message)}
async function cloudUp(){const{data,error}=await sb.auth.signUp({email:$('#cem').value.trim(),password:$('#cpw').value});if(error)return toast(error.message);toast(data.session?'Account created – you are signed in':'Check your email to confirm, then sign in')}
const toRow=p=>({id:p.id,name:p.name,type:p.type,thumb:p.th||null,fav:!!p.fav,deleted_at:p.del?new Date(p.del).toISOString():null,updated_at:new Date(p.date).toISOString(),data:{a:p.a,fx:p.fx,t:p.t,s:p.s}});
const fromRow=r=>({id:+r.id,name:r.name,type:r.type,th:r.thumb||undefined,fav:r.fav,del:r.deleted_at?Date.parse(r.deleted_at):undefined,date:Date.parse(r.updated_at),...r.data});
async function syncNow(){if(!CU)return;const{data,error}=await sb.from('projects').select('*');if(error)return toast('Sync failed: '+error.message);
const m=new Map(LS.g('proj',[]).map(p=>[String(p.id),p])),cl=new Map(data.map(r=>[+r.id,Date.parse(r.updated_at)]));
data.forEach(r=>{const c=fromRow(r),l=m.get(String(c.id));if(!l||c.date>l.date)m.set(String(c.id),{...l,...c})});
const up=[...m.values()].filter(p=>typeof p.id=='number'&&(!cl.has(p.id)||p.date>cl.get(p.id))).map(toRow);
if(up.length){const{error:e2}=await sb.from('projects').upsert(up);if(e2)return toast('Upload failed: '+e2.message)}
LS.s('proj',[...m.values()].sort((a,b)=>b.date-a.date));LS.s('lastbk',Date.now());if(!$('#projects').hidden)renderProjects();toast('☁ Synced')}
function cloudDel(id){id=Number(id);if(CU&&id)sb.from('projects').delete().eq('id',id).then(()=>{})}
const _sp=saveProj;saveProj=function(p){_sp(p);if(CU){clearTimeout(syncT);syncT=setTimeout(syncNow,1500)}};
if(sb){sb.auth.onAuthStateChange((_e,s)=>{CU=s?s.user:null;cloudUI();if(CU)syncNow()});setInterval(()=>CU&&syncNow(),60000)}
cloudUI();
