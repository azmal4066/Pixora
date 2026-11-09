"use strict";
/* PIXORA extras: Spotify player everywhere + Save option everywhere */

/* ---------- Spotify ---------- */
const SP_RE=/open\.spotify\.com\/(?:intl-[a-z-]+\/)?(?:embed\/)?(track|album|playlist|episode|show|artist)\/([A-Za-z0-9]+)|spotify:(track|album|playlist|episode|show|artist):([A-Za-z0-9]+)/i;
function spUrl(s){const m=String(s).match(SP_RE);if(!m)return null;const k=(m[1]||m[3]).toLowerCase(),id=m[2]||m[4];return{u:`https://open.spotify.com/embed/${k}/${id}?utm_source=generator`,h:k=='track'||k=='episode'?152:352}}
const spBox=id=>`<div class="spbox"><h4>🎧 Spotify</h4><div class="row"><input id="spl_${id}" placeholder="Paste Spotify song / playlist link" style="flex:1;min-width:160px"><button class="pri" onclick="spLoad('${id}')">▶ Play</button><button onclick="spFind('${id}')">🔍 Find a song</button></div><div id="spf_${id}"></div><p class="hint" style="text-align:left;font-size:11px">Plays inside PIXORA for listening and timing reference. Spotify does not allow its audio to be captured, so for the exported video add the same song as an audio file (Import audio).</p></div>`;
function spLoad(id){const r=spUrl($('#spl_'+id).value);if(!r)return toast('Paste a valid Spotify link (Share → Copy link)');$('#spf_'+id).innerHTML=`<iframe src="${r.u}" height="${r.h}" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>`}
function spFind(id){const q=prompt('Song or artist to search on Spotify');if(!q)return;window.open('https://open.spotify.com/search/'+encodeURIComponent(q),'_blank','noopener');toast('On Spotify: Share → Copy song link, then paste it here')}
$('#audio .row').insertAdjacentHTML('afterend',spBox('au'));
$('#audio .row').insertAdjacentHTML('beforeend','<button class="pri" onclick="aSaveAll()">💾 Save ticked / all tracks</button>');
$('#vau').closest('.row').insertAdjacentHTML('afterend',spBox('vd'));
['mm','ly'].forEach(id=>$('#'+id+'au').closest('.row').insertAdjacentHTML('afterend',spBox(id)));

/* ---------- Save everywhere ---------- */
const EDS={photo:'Photo',video:'Video',music:'Music video',lyrics:'Lyrics video'},DIRTY={},CURP={};
const curSec=()=>(SEC.find(s=>!$('#'+s[0]).hidden)||[])[0];
function barUpdate(){const s=curSec(),b=$('#savebar');if(!b)return;b.hidden=['home','projects','settings'].includes(s);const one=(s in EDS)||s=='audio',d=one?DIRTY[s]:Object.values(DIRTY).some(Boolean);b.className='glass'+(d?' dirty':'');$('#sbs').textContent=d?'● Unsaved changes':'✓ All saved';$('#sbb').textContent=one?'💾 Save':'💾 Save all'}
const mark=s=>{DIRTY[s]=1;barUpdate()};
document.body.insertAdjacentHTML('beforeend','<div id="savebar" class="glass" hidden><span id="sbs"></span><button id="sbb" class="pri" onclick="saveCur()">💾 Save</button></div>');

function savePhoto(){if(!P.b.width){DIRTY.photo=0;barUpdate();return toast('Open a photo first')}const c=CURP.photo;if(c)pSave(c.id,c.name);else{const n=prompt('Project name','Photo '+new Date().toLocaleDateString());if(!n)return;const id=Date.now();pSave(id,n);CURP.photo={id,name:n}}DIRTY.photo=0;barUpdate();toast('💾 Project saved')}
function saveSect(s){const c=CURP[s];let n=c&&c.name;if(!n){n=prompt('Project name',EDS[s]+' '+new Date().toLocaleDateString());if(!n)return}const id=c?c.id:Date.now();saveProj({id,type:s,name:n,date:Date.now(),s:snap(s)});CURP[s]={id,name:n};DIRTY[s]=0;barUpdate();toast('💾 Project saved (media files stay on your device – re-add them when reopening)')}
function aSaveAll(){const ix=$$('#alist [data-i]:checked').map(e=>+e.dataset.i),L=ix.length?ix:AUD.map((_,i)=>i);if(!L.length)return toast('No tracks to save yet');L.forEach((i,k)=>setTimeout(()=>dl(AUD[i].blob,AUD[i].name),k*500));DIRTY.audio=0;barUpdate();toast(`💾 Saving ${L.length} track(s) to your device`)}
function saveAll(){let n=0;for(const s in EDS)if(DIRTY[s]){saveCur(s);n++}if(DIRTY.audio){aSaveAll();n++}if(!n)toast('Everything is already saved ✓')}
function saveCur(s){s=s||curSec();if(s=='photo')savePhoto();else if(s in EDS)saveSect(s);else if(s=='audio')aSaveAll();else saveAll()}

/* mark "unsaved" when something is edited */
const QUIET=/save|preview|stop|vPlay|exportDlg|pExport|start\(|spLoad|spFind|closeModal/i;
['input','change'].forEach(ev=>document.addEventListener(ev,e=>{const s=e.target.closest&&e.target.closest('main>section');if(s&&(s.id in EDS)&&!String(e.target.id).startsWith('spl_'))mark(s.id)},true));
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('button'),s=b&&b.closest('main>section');if(s&&((s.id in EDS)||s.id=='audio')&&!QUIET.test(b.getAttribute('onclick')||''))mark(s.id)},true);
const psig=()=>P.h.length+':'+P.f.length+':'+P.b.width;let lastP=psig();
setInterval(()=>{const s=psig();if(s!==lastP){lastP=s;mark('photo')}},700);

const _g2=go;go=function(s){_g2(s);barUpdate()};
const _aa=addAud;addAud=function(...a){_aa(...a);mark('audio')};
const _op=openProj;openProj=function(i){const p=LS.g('proj',[])[i];if(p&&p.type)CURP[p.type]={id:p.id,name:p.name};return Promise.resolve(_op(i)).then(()=>{lastP=psig();if(p&&p.type){DIRTY[p.type]=0}barUpdate()})};
const _pe=pExport;pExport=function(){_pe();if(P.b.width&&DIRTY.photo)setTimeout(()=>modal(`<h3>Exported ✓</h3><p>Your image was saved to your device. Save the project too, so you can keep editing later?</p><div class="row"><button onclick="closeModal()">Not now</button><button class="pri" onclick="closeModal();saveCur('photo')">💾 Save project</button></div>`),500)};

addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()=='s'){e.preventDefault();saveCur()}});
addEventListener('beforeunload',e=>{if(Object.values(DIRTY).some(Boolean)){e.preventDefault();e.returnValue=''}});
barUpdate();
