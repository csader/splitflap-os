// ============================================================
//  CONSTANTS
// ============================================================
// Position 48 is the physical " flap (addressed as 'q' in firmware)
const CHAR_MAP = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$&()-+=;\":%'.,/?*roygbpw";

// How to render characters from the live state string
const STATE_DISPLAY = {
  'r':'🟥','o':'🟧','y':'🟨','g':'🟩','b':'🟦','p':'🟪','w':'⬜','q':'"'
};

// Per-app quick-settings configuration
const APP_SETTINGS_CONFIG = {
  weather:    { title:'🌤️ Weather Settings', fields:[
    {key:'zip_code',            label:'Zip Code',              type:'text',     ph:'02118'},
    {key:'weather_api_key',     label:'OpenWeatherMap API Key', type:'password', ph:'...'},
    {key:'timezone',            label:'Timezone',              type:'text',     ph:'US/Eastern'},
  ]},
  metro:      { title:'🚇 Metro Settings', fields:[
    {key:'mbta_stop',  label:'Stop ID (e.g. place-NSTAT)',  type:'text', ph:'place-NSTAT'},
    {key:'mbta_route', label:'Route (e.g. Orange)',          type:'text', ph:'Orange'},
  ]},
  stocks:     { title:'📈 Stocks Settings', fields:[
    {key:'stocks_list', label:'Tickers (comma-separated)', type:'text', ph:'MSFT,GOOG,NVDA'},
  ]},
  sports:     { title:'🏆 Sports Settings', fields:[
    {key:'sports_nfl',    label:'NFL Teams (comma-sep, * for all)',  type:'text', ph:'NE,DAL'},
    {key:'sports_nba',    label:'NBA Teams',                         type:'text', ph:'BOS,LAL'},
    {key:'sports_mlb',    label:'MLB Teams',                         type:'text', ph:'BOS,NYY'},
    {key:'sports_nhl',    label:'NHL Teams',                         type:'text', ph:'BOS,DAL'},
    {key:'sports_ncaaf',  label:'College Football Teams',            type:'text', ph:'MICH,OSU'},
    {key:'sports_ncaab',  label:'College Basketball Teams',          type:'text', ph:'DUKE,UNC'},
    {key:'sports_mls',    label:'MLS Teams',                         type:'text', ph:'ATL,LAFC'},
    {key:'sports_epl',    label:'Premier League Teams',              type:'text', ph:'ARS,LIV'},
    {key:'sports_laliga', label:'La Liga Teams',                     type:'text', ph:'BAR,RMA'},
    {key:'sports_ucl',    label:'Champions League Teams',            type:'text', ph:'BAR,BAY'},
    {key:'sports_wnba',   label:'WNBA Teams',                       type:'text', ph:'NY,LA'},
    {key:'sports_pga',    label:'PGA (* to enable)',                 type:'text', ph:'*'},
    {key:'sports_ufc',    label:'UFC (* to enable)',                 type:'text', ph:'*'},
  ]},
  youtube:    { title:'▶️ YouTube Settings', fields:[
    {key:'yt_channel_id', label:'Channel ID', type:'text', ph:'UC...'},
  ]},
  yt_comments:{ title:'💬 YT Comments Settings', fields:[
    {key:'yt_video_id', label:'Video ID',   type:'text',     ph:'dQw4w9WgXcQ'},
    {key:'yt_api_key',  label:'API Key',    type:'password', ph:'...'},
  ]},
  countdown:  { title:'⏳ Countdown Settings', fields:[
    {key:'countdown_event',  label:'Event Name (15 chars)', type:'text',          ph:'NEW YEAR'},
    {key:'countdown_target', label:'Target Date & Time',    type:'datetime-local', ph:''},
  ]},
  world_clock:{ title:'🌍 World Clock Settings', fields:[
    {key:'world_clock_zones', label:'Timezones — comma-separated\n(e.g. US/Eastern, Europe/London, Asia/Tokyo)', type:'text', ph:'US/Eastern,US/Pacific,Europe/London'},
  ]},
  crypto:     { title:'₿ Crypto Settings', fields:[
    {key:'crypto_list', label:'CoinGecko IDs (comma-separated)', type:'text', ph:'bitcoin,ethereum,solana'},
  ]},
  iss:        { title:'🛸 ISS Tracker', fields:[] },
  demo:       { title:'🎬 Demo Mode', fields:[] },
  livestream: { title:'🔴 Livestream Settings', fields:[
    {key:'livestream_interval', label:'Rotation Interval (seconds)', type:'number', ph:'25', min:'5', max:'180', step:'1'},
    {key:'livestream_comments', label:'Comments — blank line separates slides, up to 3 lines each (use 🟥🟧🟨🟩🟦🟪⬜ for color tiles)', type:'textarea', ph:'JOHNDOE\nGreat video!\nSubscribed\n\nUSER_123\nLove the build\nVery cool'},
    {key:'yt_channel_id', label:'YouTube Channel ID (for subs)', type:'text', ph:'UC...'},
    {key:'yt_video_id',   label:'YouTube Video ID (live, for viewers)', type:'text', ph:'...'},
    {key:'yt_api_key',    label:'YouTube Data API Key', type:'password', ph:'...'},
    {key:'timezone',      label:'Timezone', type:'text', ph:'US/Eastern'},
  ]},
  anim_rainbow:{ title:'🌈 Rainbow Settings', fields:[
    {key:'anim_style', label:'Update Order', type:'select',
     opts:['ltr','rtl','center_out','outside_in','spiral','diagonal','anti_diagonal','random','rain','reverse_rain','columns','columns_rtl']},
    {key:'anim_speed', label:'Frame Speed (seconds)', type:'number', ph:'0.4', min:'0.1', max:'3', step:'0.1'},
  ]},
  anim_matrix:{ title:'💻 Matrix Settings', fields:[
    {key:'anim_text',  label:'Reveal Text (45 chars / 3×15)', type:'text', ph:'SPLIT  FLAP  DISPLAY'},
    {key:'anim_style', label:'Final Reveal Order', type:'select',
     opts:['ltr','rtl','center_out','outside_in','spiral','diagonal','anti_diagonal','random','rain','columns']},
    {key:'anim_speed', label:'Frame Speed (seconds)', type:'number', ph:'0.4', min:'0.1', max:'2', step:'0.1'},
  ]},
  anim_sweep: { title:'〰️ Sweep Settings', fields:[
    {key:'anim_style', label:'Update Order', type:'select',
     opts:['ltr','rtl','center_out','outside_in','spiral','diagonal','anti_diagonal','random','columns']},
    {key:'anim_speed', label:'Frame Speed (seconds)', type:'number', ph:'0.25', min:'0.05', max:'2', step:'0.05'},
  ]},
  anim_twinkle:{ title:'✨ Twinkle Settings', fields:[
    {key:'anim_speed', label:'Frame Speed (seconds)', type:'number', ph:'0.5', min:'0.1', max:'3', step:'0.1'},
  ]},
  anim_checker:{ title:'🎭 Checker Settings', fields:[
    {key:'anim_style', label:'Update Order', type:'select',
     opts:['ltr','rtl','center_out','outside_in','spiral','diagonal','random']},
    {key:'anim_speed', label:'Frame Speed (seconds)', type:'number', ph:'0.6', min:'0.1', max:'3', step:'0.1'},
  ]},
};

// App registry for building the grid
const APP_LIST = [
  {key:'demo',         icon:'🎬', name:'Demo',          desc:'YouTube showcase'},
  {key:'livestream',   icon:'🔴', name:'Livestream',    desc:'Launch day rotate'},
  {key:'dashboard',    icon:'🏠', name:'Dashboard',     desc:'Time + weather'},
  {key:'time',         icon:'⏱️', name:'Time',          desc:'Live clock'},
  {key:'date',         icon:'📅', name:'Date',          desc:'Full date view'},
  {key:'weather',      icon:'🌤️', name:'Weather',       desc:'Current conditions'},
  {key:'metro',        icon:'🚇', name:'Metro',          desc:'MBTA arrivals'},
  {key:'stocks',       icon:'📈', name:'Stocks',         desc:'Live prices'},
  {key:'sports',       icon:'🏒', name:'Sports',         desc:'NHL scores'},
  {key:'youtube',      icon:'▶️', name:'YouTube',        desc:'Sub counter'},
  {key:'yt_comments',  icon:'💬', name:'Comments',       desc:'YT comments'},
  {key:'countdown',    icon:'⏳', name:'Countdown',      desc:'Timer to event'},
  {key:'world_clock',  icon:'🌍', name:'World Clock',    desc:'3 time zones'},
  {key:'crypto',       icon:'₿',  name:'Crypto',         desc:'Coin prices'},
  {key:'iss',          icon:'🛸', name:'ISS Tracker',    desc:'Space station'},
  {key:'anim_rainbow', icon:'🌈', name:'Rainbow',        desc:'Colour wave'},
  {key:'anim_sweep',   icon:'〰️', name:'Sweep',          desc:'Colour sweep'},
  {key:'anim_twinkle', icon:'✨', name:'Twinkle',        desc:'Sparkle effect'},
  {key:'anim_checker', icon:'🎭', name:'Checker',        desc:'Checkerboard'},
  {key:'anim_matrix',  icon:'💻', name:'Matrix',         desc:'Cascade reveal'},
];

// Transition style options for playlist pages
const TRANSITION_STYLES = [
  {v:'ltr',          l:'Left → Right'},
  {v:'rtl',          l:'Right → Left'},
  {v:'diagonal',     l:'Diagonal ↘'},
  {v:'anti_diagonal',l:'Diagonal ↙'},
  {v:'center_out',   l:'Center Out'},
  {v:'outside_in',   l:'Outside In'},
  {v:'random',       l:'Random'},
  {v:'rain',         l:'Rain (Top→Bot)'},
  {v:'reverse_rain', l:'Rain (Bot→Top)'},
  {v:'spiral',       l:'Spiral'},
  {v:'columns',      l:'Columns'},
  {v:'alternating',  l:'Alt (↔↔↔)'},
];

function buildStyleOptions(selected='ltr'){
  return TRANSITION_STYLES.map(s=>
    `<option value="${s.v}"${s.v===selected?' selected':''}>${s.l}</option>`
  ).join('');
}

// Update a single property on a playlist item in-place (called from rendered list)
function updatePlaylistItem(idx, key, value){
  if(!playlist[idx]) return;
  if(key==='delay'||key==='speed') playlist[idx][key]=parseFloat(value)||0;
  else playlist[idx][key]=value;
}

// ============================================================
//  GLOBAL STATE
// ============================================================
let globalSettings = null;
let selectedModule = 0;
let selectedCharIndex = 0;
let playlist = [];
let editingIndex = null;
let currentActiveApp = null;

let lastFocusedInput = null;
let lastCursorPos = 0;

// ============================================================
//  TOAST
// ============================================================
function showToast(msg, type='success'){
  const c = document.getElementById('toastContainer');
  const t = document.createElement('div');
  t.className = `toast${type==='error'?' error':type==='warn'?' warn':''}`;
  t.textContent = msg;
  c.appendChild(t);
  requestAnimationFrame(()=>{ requestAnimationFrame(()=>t.classList.add('show')); });
  setTimeout(()=>{
    t.classList.remove('show');
    setTimeout(()=>t.remove(), 400);
  }, 2800);
}

// ============================================================
//  ANIMATED LIVE FLAPS
// ============================================================
const liveFlaps = {control: [], apps: []};

class LiveFlap {
  constructor(el) {
    this.el = el;
    this.curIdx = 0;
    this.tgtIdx = 0;
    this.busy = false;
    this.queued = null;
  }
  setTarget(idx, delay) {
    this.tgtIdx = idx;
    if (this.curIdx === this.tgtIdx) return;
    if (this.busy) { this.queued = idx; return; }
    setTimeout(() => this._step(), delay);
  }
  _step() {
    if (this.curIdx === this.tgtIdx) {
      this.busy = false;
      if (this.queued !== null) { this.tgtIdx = this.queued; this.queued = null; if (this.curIdx !== this.tgtIdx) this._step(); }
      return;
    }
    this.busy = true;
    const next = (this.curIdx + 1) % 64;
    this._flip(CHAR_MAP[this.curIdx], CHAR_MAP[next], () => { this.curIdx = next; this._render(CHAR_MAP[next]); this._step(); });
  }
  _render(ch) {
    const d = STATE_DISPLAY[ch] || ch;
    const v = d === ' ' ? '' : d;
    this.el.querySelector('.ft .fc').textContent = v;
    this.el.querySelector('.fb .fc').textContent = v;
  }
  _flip(from, to, done) {
    const fd = STATE_DISPLAY[from] || from;
    const td = STATE_DISPLAY[to] || to;
    const fv = fd === ' ' ? '' : fd;
    const tv = td === ' ' ? '' : td;
    this.el.querySelectorAll('.ff').forEach(e => e.remove());
    const spd = liveFlipSpeedMs;
    const dn = document.createElement('div'); dn.className = 'ff ffd'; dn.style.animationDuration = spd+'ms';
    const dnc = document.createElement('span'); dnc.className = 'fc'; dnc.textContent = fv; dn.appendChild(dnc);
    const up = document.createElement('div'); up.className = 'ff ffu'; up.style.animationDuration = spd+'ms'; up.style.animationDelay = spd+'ms';
    const upc = document.createElement('span'); upc.className = 'fc'; upc.textContent = tv; up.appendChild(upc);
    this.el.querySelector('.fb .fc').textContent = tv;
    this.el.appendChild(dn); this.el.appendChild(up);
    setTimeout(() => { dn.remove(); up.remove(); this.el.querySelector('.ft .fc').textContent = tv; done(); }, spd * 2 + 10);
  }
}

let liveFlipSpeedMs = 62;
let liveGridRows = 3, liveGridCols = 15;
let simMode = true;

function updateSimModeUI() {
  const toggle = document.getElementById('simModeToggle');
  const label = document.getElementById('simModeLabel');
  toggle.checked = !simMode;  // checked = LIVE, unchecked = SIMULATION
  label.textContent = simMode ? 'SIMULATION' : 'LIVE';
  label.style.color = simMode ? '#f88' : '#8f8';
}

async function toggleSimMode() {
  const toggle = document.getElementById('simModeToggle');
  simMode = !toggle.checked;  // checked = LIVE (sim off), unchecked = SIM (sim on)
  updateSimModeUI();
  await fetch('/toggle_sim', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({enabled: simMode})
  });
  showToast(simMode ? 'Simulation mode — hardware output disabled' : 'Live mode — sending to hardware');
}

function initLiveGrids(rows, cols) {
  rows = rows || liveGridRows;
  cols = cols || liveGridCols;
  liveGridRows = rows;
  liveGridCols = cols;
  ['control', 'apps'].forEach(tab => {
    const grid = document.querySelector(`.live-grid-${tab}`);
    if (!grid) return;
    grid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
    grid.innerHTML = '';
    liveFlaps[tab] = [];
    for (let i = 0; i < rows * cols; i++) {
      const el = document.createElement('div');
      el.className = 'live-flap';
      el.innerHTML = '<div class="fh ft"><span class="fc"></span></div><div class="fh fb"><span class="fc"></span></div><div class="fd"></div>';
      grid.appendChild(el);
      liveFlaps[tab].push(new LiveFlap(el));
    }
  });
  document.getElementById('simRows').value = rows;
  document.getElementById('simCols').value = cols;
}

// Fetch initial grid config then init
(async function(){
  try {
    const cfg = await fetch('/grid_config').then(r=>r.json());
    initLiveGrids(cfg.rows || 3, cfg.cols || 15);
    simMode = cfg.sim_mode !== false;
    updateSimModeUI();
  } catch(e) { initLiveGrids(3, 15); updateSimModeUI(); }
})();

async function applyGridConfig() {
  const rows = parseInt(document.getElementById('simRows').value) || 3;
  const cols = parseInt(document.getElementById('simCols').value) || 15;
  await fetch('/settings', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action:'save_global', sim_rows:rows, sim_cols:cols})
  });
  initLiveGrids(rows, cols);
  showToast(`Grid set to ${rows}x${cols}`);
}

// ============================================================
//  LIVE VIEW POLLING
// ============================================================
setInterval(()=>{
  fetch('/current_state').then(r=>r.json()).then(data=>{
    // Rebuild grids if dimensions changed
    const rows = data.rows || 3, cols = data.cols || 15;
    if (rows !== liveGridRows || cols !== liveGridCols) {
      initLiveGrids(rows, cols);
    }

    // Homing overlays (hide in sim mode)
    ['control','apps'].forEach(tab=>{
      const el = document.getElementById(`homing-${tab}`);
      if(!el) return;
      if(data.is_homed || data.sim_mode){ el.style.display='none'; return; }
      el.style.display='flex';
      if(!data.hardware_connected){
        el.innerHTML='<div style="text-align:center">NO SPLITFLAP DEVICE DETECTED</div>';
      } else {
        el.innerHTML='<div style="text-align:center">HOMING REQUIRED<br><button class="btn btn-warning btn-sm" style="margin-top:8px" onclick="homeAll()">HOME ALL</button></div>';
      }
    });

    // Animated live display grids
    const s = data.state || '';
    ['control','apps'].forEach(tab=>{
      const fa = liveFlaps[tab];
      for(let i=0; i<fa.length; i++){
        const ch = s[i] || ' ';
        const idx = CHAR_MAP.indexOf(ch);
        fa[i].setTarget(idx >= 0 ? idx : 0, i * 5);
      }
    });

    // Active app banners
    const app = data.active_app;
    currentActiveApp = app;
    const appLabel = app ? (APP_LIST.find(a=>a.key===app)||{name:app}).name : null;
    ['control','apps'].forEach(tab=>{
      const banner = document.getElementById(`${tab}-banner`);
      const nameEl = document.getElementById(`${tab}-app-name`);
      if(banner){
        banner.classList.toggle('visible', !!app);
        if(app && nameEl) nameEl.textContent = appLabel;
      }
    });

    // Running highlight on app cards
    document.querySelectorAll('.app-card').forEach(c=>{
      c.classList.toggle('running', c.dataset.app === app);
    });
  }).catch(()=>{});
}, 1000);

// ============================================================
//  TAB SWITCHING
// ============================================================
function switchTab(name){
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
  document.getElementById('page-'+name).classList.add('active');
  if(name==='tuning') loadSettingsData();
  if(name==='apps'){ buildAppsGrid(); loadAppLibrary(); }
}

// ============================================================
//  CURSOR TRACKING
// ============================================================
document.querySelectorAll('.line-input').forEach(el=>{
  ['focus','keyup','click'].forEach(ev=>el.addEventListener(ev, e=>{
    lastFocusedInput = e.target;
    lastCursorPos = e.target.selectionStart||0;
  }));
});

// ============================================================
//  CONTROL TAB
// ============================================================
function updatePreview(){
  const grid = document.getElementById('preview');
  grid.innerHTML='';
  const centered = document.getElementById('centerToggle').checked;
  let full='';
  [1,2,3].forEach(n=>{
    const el = document.getElementById('L'+n);
    let chars = Array.from(el.value);
    if(chars.length>15){
      const s = el.selectionStart;
      chars = chars.slice(0,15);
      el.value = chars.join('');
      el.setSelectionRange(s,s);
    }
    let dc = chars.map(c=>c.toUpperCase());
    if(centered){
      const pad = Math.floor((15-dc.length)/2);
      for(let i=0;i<pad;i++) dc.unshift(' ');
    }
    while(dc.length<15) dc.push(' ');
    full += dc.join('');
  });
  for(let ch of Array.from(full)){
    const div = document.createElement('div');
    div.className='flap-unit';
    div.innerText = ch===' '?'':ch;
    grid.appendChild(div);
  }
  return full;
}

function clearDisplay(){
  ['L1','L2','L3'].forEach(id=>document.getElementById(id).value='');
  if(editingIndex!==null){
    editingIndex=null;
    document.getElementById('saveMsgBtn').textContent='+ Add to Playlist';
  }
  updatePreview();
}

function toggleMultiMode(){
  document.getElementById('multiControls').style.display =
    document.getElementById('modeToggle').checked ? 'block':'none';
}

function insertColor(emoji){
  const target = lastFocusedInput||document.getElementById('L1');
  let chars = Array.from(target.value);
  if(chars.length>=15) return;
  const text = target.value;
  const start = lastCursorPos;
  target.value = text.substring(0,start)+emoji+text.substring(start);
  lastCursorPos += emoji.length;
  target.focus();
  target.setSelectionRange(lastCursorPos,lastCursorPos);
  updatePreview();
}

function saveMessage(){
  const item={
    text: updatePreview(),
    rawL1: document.getElementById('L1').value,
    rawL2: document.getElementById('L2').value,
    rawL3: document.getElementById('L3').value,
    centered: document.getElementById('centerToggle').checked,
    delay: parseFloat(document.getElementById('delayInput').value)||5,
    style: document.getElementById('styleInput').value||'ltr',
    speed: parseInt(document.getElementById('speedInput').value)||15,
  };
  if(editingIndex!==null){
    // Preserve existing per-item settings if not explicitly changed
    item.delay = item.delay;
    item.style = item.style;
    item.speed = item.speed;
    playlist[editingIndex]=item;
    editingIndex=null;
    document.getElementById('saveMsgBtn').textContent='+ Add to Playlist';
    clearDisplay();
  } else {
    playlist.push(item);
  }
  renderPlaylist();
}

function renderPlaylist(){
  const list = document.getElementById('playlistList');
  if(!playlist.length){
    list.innerHTML='<div style="color:#666;font-style:italic;font-size:.85rem">Queue is empty</div>';
    return;
  }
  list.innerHTML='';
  playlist.forEach((item,idx)=>{
    const arr=Array.from(item.text);
    const l1=arr.slice(0,15).join('').replace(/ /g,'&nbsp;');
    const l2=arr.slice(15,30).join('').replace(/ /g,'&nbsp;');
    const l3=arr.slice(30,45).join('').replace(/ /g,'&nbsp;');
    const div=document.createElement('div');
    div.className='playlist-item';
    div.style.cssText='flex-direction:column;align-items:stretch;gap:8px';
    div.innerHTML=`
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span style="color:var(--accent);font-weight:bold">Page ${idx+1}</span>
        <div style="display:flex;gap:4px">
          <button class="btn btn-secondary btn-sm" onclick="movePlaylist(${idx},-1)">▲</button>
          <button class="btn btn-secondary btn-sm" onclick="movePlaylist(${idx},1)">▼</button>
          <button class="btn btn-secondary btn-sm" onclick="editPlaylist(${idx})">EDIT</button>
          <button class="btn-del" onclick="removeFromPlaylist(${idx})">DEL</button>
        </div>
      </div>
      <div style="background:#111;padding:10px;border-radius:4px;font-family:'Courier New',monospace;font-size:1rem;line-height:1.5;text-align:center;letter-spacing:1px;border:1px solid #333">${l1}<br>${l2}<br>${l3}</div>
      <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:8px 10px;background:#1a1a1a;border-radius:5px;border-top:1px solid #2a2a2a">
        <label style="font-size:.78rem;color:#aaa;display:flex;align-items:center;gap:4px">
          ⏱
          <input type="number" value="${item.delay||5}" min="0.5" max="60" step="0.5"
            style="width:50px;background:#111;color:#fff;border:1px solid #444;border-radius:3px;padding:3px 5px;font-size:.8rem;text-align:center"
            onchange="updatePlaylistItem(${idx},'delay',this.value)">
          s
        </label>
        <label style="font-size:.78rem;color:#aaa;display:flex;align-items:center;gap:4px">
          ↔
          <select style="background:#111;color:#fff;border:1px solid #444;border-radius:3px;padding:3px 5px;font-size:.78rem"
            onchange="updatePlaylistItem(${idx},'style',this.value)">
            ${buildStyleOptions(item.style||'ltr')}
          </select>
        </label>
        <label style="font-size:.78rem;color:#aaa;display:flex;align-items:center;gap:4px">
          ⚡
          <input type="number" value="${item.speed||15}" min="0" max="500" step="5"
            style="width:50px;background:#111;color:#fff;border:1px solid #444;border-radius:3px;padding:3px 5px;font-size:.8rem;text-align:center"
            onchange="updatePlaylistItem(${idx},'speed',this.value)">
          ms
        </label>
      </div>`;
    list.appendChild(div);
  });
}

function editPlaylist(idx){
  editingIndex=idx;
  const item=playlist[idx];
  document.getElementById('L1').value=item.rawL1;
  document.getElementById('L2').value=item.rawL2;
  document.getElementById('L3').value=item.rawL3;
  document.getElementById('centerToggle').checked=item.centered;
  document.getElementById('delayInput').value=item.delay||5;
  document.getElementById('styleInput').value=item.style||'ltr';
  document.getElementById('speedInput').value=item.speed||15;
  document.getElementById('saveMsgBtn').textContent=`Save Changes to Page ${idx+1}`;
  updatePreview();
}

function movePlaylist(idx,dir){
  if(idx+dir<0||idx+dir>=playlist.length) return;
  [playlist[idx],playlist[idx+dir]]=[playlist[idx+dir],playlist[idx]];
  if(editingIndex===idx) editingIndex=idx+dir;
  else if(editingIndex===idx+dir) editingIndex=idx;
  renderPlaylist();
}

function removeFromPlaylist(idx){
  playlist.splice(idx,1);
  if(editingIndex===idx) clearDisplay();
  else if(editingIndex>idx) editingIndex--;
  renderPlaylist();
}

function sync(){
  let pages;
  const delay = document.getElementById('delayInput').value;
  if(document.getElementById('modeToggle').checked){
    // Rich objects — each page carries its own delay/style/speed
    pages = playlist.map(p=>({
      text:  p.text,
      delay: p.delay||5,
      style: p.style||'ltr',
      speed: p.speed||15,
    }));
  } else {
    // Single page — use compose-area defaults
    pages = [{
      text:  updatePreview(),
      delay: parseFloat(delay)||5,
      style: document.getElementById('styleInput').value||'ltr',
      speed: parseInt(document.getElementById('speedInput').value)||15,
    }];
  }
  fetch('/update_playlist',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({pages, delay})});
  showToast('Pushed to display');
}

function stopApp(){
  fetch('/stop_app',{method:'POST'}).then(()=>showToast('App stopped'));
}

// ── Saved Playlists ─────────────────────────────────────────
function loadSavedPlaylists(){
  fetch('/playlists').then(r=>r.json()).then(renderSavedPlaylists);
}

function renderSavedPlaylists(data){
  const list = document.getElementById('savedPlaylistList');
  const names = Object.keys(data||{});
  if(!names.length){
    list.innerHTML='<div style="color:#666;font-style:italic;font-size:.85rem">No saved playlists yet.</div>';
    return;
  }
  list.innerHTML='';
  names.forEach(name=>{
    const item = data[name];
    const div = document.createElement('div');
    div.className='saved-pl-item';
    div.innerHTML=`
      <span class="saved-pl-name">${name}</span>
      <span style="color:#666;font-size:.8rem">${item.pages.length}p·${item.delay}s</span>
      <button class="btn btn-secondary btn-sm" onclick="loadSavedPlaylist('${encodeURIComponent(name)}')">Load</button>
      <button class="btn btn-success btn-sm" onclick="runSavedPlaylist('${encodeURIComponent(name)}')">Run</button>
      <button class="btn-del" onclick="deleteSavedPlaylist('${encodeURIComponent(name)}')">✕</button>`;
    list.appendChild(div);
  });
}

function saveCurrentPlaylist(){
  const name = document.getElementById('savePlaylistName').value.trim();
  if(!name){ showToast('Enter a name first','warn'); return; }
  let pages;
  const delay = document.getElementById('delayInput').value;
  if(document.getElementById('modeToggle').checked){
    pages = playlist.map(p=>({text:p.text,delay:p.delay||5,style:p.style||'ltr',speed:p.speed||15}));
  } else {
    pages = [{text:updatePreview(),delay:parseFloat(delay)||5,
              style:document.getElementById('styleInput').value||'ltr',
              speed:parseInt(document.getElementById('speedInput').value)||15}];
  }
  fetch('/playlists',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({name,pages,delay})})
  .then(r=>r.json()).then(()=>{
    showToast(`Saved "${name}"`);
    document.getElementById('savePlaylistName').value='';
    loadSavedPlaylists();
  });
}

function loadSavedPlaylist(encodedName){
  const name = decodeURIComponent(encodedName);
  fetch('/playlists').then(r=>r.json()).then(data=>{
    const item = data[name];
    if(!item) return;
    playlist = item.pages.map(p=>{
      const text   = typeof p==='object' ? p.text   : p;
      const delay  = typeof p==='object' ? (p.delay||5) : 5;
      const style  = typeof p==='object' ? (p.style||'ltr') : 'ltr';
      const speed  = typeof p==='object' ? (p.speed||15) : 15;
      return { text, delay, style, speed,
               rawL1:text.slice(0,15).trim(), rawL2:text.slice(15,30).trim(),
               rawL3:text.slice(30,45).trim(), centered:false };
    });
    document.getElementById('delayInput').value = item.delay;
    document.getElementById('modeToggle').checked = true;
    toggleMultiMode();
    renderPlaylist();
    showToast(`Loaded "${name}"`);
  });
}

function runSavedPlaylist(encodedName){
  const name = decodeURIComponent(encodedName);
  fetch('/playlists').then(r=>r.json()).then(data=>{
    const item = data[name];
    if(!item) return;
    fetch('/update_playlist',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({pages:item.pages, delay:item.delay})});
    showToast(`Running "${name}"`);
  });
}

function deleteSavedPlaylist(encodedName){
  const name = decodeURIComponent(encodedName);
  if(!confirm(`Delete playlist "${name}"?`)) return;
  fetch(`/playlists/${encodeURIComponent(name)}`,{method:'DELETE'})
  .then(()=>{ showToast(`Deleted "${name}"`,'warn'); loadSavedPlaylists(); });
}

// ============================================================
//  APPS TAB
// ============================================================
async function buildAppsGrid(){
  const grid = document.getElementById('appsGrid');
  grid.innerHTML = '';

  const pluginKeys = new Set();
  try {
    const res = await fetch('/installed_apps');
    const data = await res.json();
    const pluginConfigs = data.settings_config || {};
    Object.assign(APP_SETTINGS_CONFIG, pluginConfigs);
    (data.apps || []).forEach(a => pluginKeys.add(a.key.replace('plugin_','')));
    (data.apps || []).forEach(a => grid.appendChild(buildAppCard(a, true)));
  } catch(e) { console.error('Failed to load plugins:', e); }

  // Also fetch library to know which hardcoded apps are library-managed
  const libraryKeys = new Set();
  try {
    const lr = await fetch('/app_library');
    const ld = await lr.json();
    (ld.apps || []).forEach(a => libraryKeys.add(a.id));
  } catch(e) {}

  // Only show hardcoded apps if not a plugin AND not in the library
  APP_LIST.forEach(a => {
    if (!pluginKeys.has(a.key) && !libraryKeys.has(a.key)) grid.appendChild(buildAppCard(a, false));
  });
}

function buildAppCard(a, isPlugin) {
  const div = document.createElement('div');
  div.className = 'app-card';
  div.dataset.app = a.key;
  div.onclick = () => runApp(a.key);
  const hasCfg = APP_SETTINGS_CONFIG[a.key] && (APP_SETTINGS_CONFIG[a.key].fields||[]).length > 0;
  const removable = isPlugin;
  div.innerHTML = `
    ${hasCfg ? `<button class="app-gear" style="right:${removable?'28':'8'}px" title="Settings" onclick="event.stopPropagation();openAppSettings('${a.key}')">⚙️</button>` : ''}
    ${removable ? `<button class="app-gear" title="Remove" onclick="event.stopPropagation();removeApp('${a.plugin_id||a.key.replace('plugin_','')}')">✕</button>` : ''}
    <span class="app-icon">${a.icon}</span>
    <span class="app-name">${a.name}</span>
    <span class="app-desc">${a.desc}</span>`;
  return div;
}

async function removeApp(appId){
  if(!confirm('Remove '+appId+'?')) return;
  try {
    const res = await fetch('/app_library/uninstall',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({id:appId})
    });
    const d = await res.json();
    if(d.status==='success'){
      showToast(appId+' removed','warn');
      buildAppsGrid();
    } else { showToast(d.message||'Error','error'); }
  } catch(e){ showToast('Remove failed','error'); }
}

function runApp(appKey){
  fetch('/run_app',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({app:appKey})});
  const label = (APP_LIST.find(a=>a.key===appKey)||{name:appKey.replace('plugin_','').replace(/-/g,' ')}).name;
  showToast(`▶ ${label} started`);
}

// ── App Library ──────────────────────────────────────────────
function openAppLibrary(){
  document.getElementById('appLibraryModal').style.display='flex';
  loadAppLibrary();
}
function closeAppLibrary(){
  document.getElementById('appLibraryModal').style.display='none';
}

async function loadAppLibrary(){
  const grid = document.getElementById('appLibraryGrid');
  grid.innerHTML = '<div style="color:#888;grid-column:1/-1;text-align:center;padding:20px">Loading...</div>';
  try {
    const res = await fetch('/app_library');
    const data = await res.json();
    const apps = data.apps || [];
    if(!apps.length){
      grid.innerHTML = '<div style="color:#666;grid-column:1/-1;text-align:center;padding:20px">No apps available</div>';
      return;
    }
    grid.innerHTML = '';
    apps.sort((a,b) => (a.installed===b.installed) ? (a.name||'').localeCompare(b.name||'') : a.installed ? 1 : -1);
    apps.forEach(a => {
      const div = document.createElement('div');
      div.className = 'app-card';
      div.style.cursor = 'default';
      div.innerHTML = `
        <span class="app-icon">${a.icon||'🧩'}</span>
        <span class="app-name">${a.name}</span>
        <span class="app-desc">${a.description||''}</span>
        <span style="display:inline-block;font-size:.65rem;color:#888;background:#222;padding:2px 6px;border-radius:4px;margin-top:4px">${a.type}${a.version?' · v'+a.version:''}</span>
        <div style="margin-top:8px">
          ${a.installed
            ? '<button class="btn-del" style="width:100%;padding:8px;border-radius:6px;font-size:.8rem" onclick="event.stopPropagation();uninstallApp(\''+a.id+'\')">Uninstall</button>'
            : '<button class="btn btn-success btn-sm" style="width:100%" onclick="event.stopPropagation();installApp(\''+a.id+'\')">Install</button>'
          }
        </div>`;
      grid.appendChild(div);
    });
  } catch(e){
    grid.innerHTML = '<div style="color:var(--red);grid-column:1/-1;text-align:center;padding:20px">Failed to load library</div>';
  }
}

async function installApp(appId){
  showToast('Installing '+appId+'...');
  try {
    const res = await fetch('/app_library/install',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({id:appId})
    });
    const data = await res.json();
    if(data.status==='success'){
      showToast(appId+' installed');
      await buildAppsGrid();
      loadAppLibrary();
    } else {
      showToast(data.message||'Install failed','error');
    }
  } catch(e){ showToast('Install failed','error'); }
}

async function uninstallApp(appId){
  if(!confirm('Uninstall "'+appId+'"?')) return;
  try {
    const res = await fetch('/app_library/uninstall',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({id:appId})
    });
    const data = await res.json();
    if(data.status==='success'){
      showToast(appId+' uninstalled','warn');
      await buildAppsGrid();
      loadAppLibrary();
    } else {
      showToast(data.message||'Uninstall failed','error');
    }
  } catch(e){ showToast('Uninstall failed','error'); }
}

// ── Per-app settings modal ──────────────────────────────────
let currentAppSettingsKey = null;

async function openAppSettings(appKey){
  currentAppSettingsKey = appKey;
  const cfg = APP_SETTINGS_CONFIG[appKey];
  if(!cfg) return;

  // Always fetch fresh settings
  const res = await fetch('/settings');
  globalSettings = await res.json();

  document.getElementById('appSettingsTitle').textContent = cfg.title;
  const fields = document.getElementById('appSettingsFields');
  fields.innerHTML='';

  if(!cfg.fields.length){
    fields.innerHTML='<p style="color:#888;text-align:center">No configurable settings for this app.</p>';
  } else {
    cfg.fields.forEach(f=>{
      const div = document.createElement('div');
      div.className = 'modal-field';
      const label = document.createElement('label');
      label.textContent = f.label;
      div.appendChild(label);

      let input;
      if(f.type==='select'){
        input = document.createElement('select');
        (f.opts||[]).forEach(opt=>{
          const o = document.createElement('option');
          o.value = opt; o.textContent = opt;
          if((globalSettings[f.key]||'')===opt) o.selected=true;
          input.appendChild(o);
        });
      } else if(f.type==='textarea'){
        input = document.createElement('textarea');
        input.rows = 8;
        if(f.ph) input.placeholder = f.ph;
        input.value = globalSettings[f.key]||'';
      } else {
        input = document.createElement('input');
        input.type = f.type||'text';
        if(f.min)  input.min  = f.min;
        if(f.max)  input.max  = f.max;
        if(f.step) input.step = f.step;
        if(f.ph)   input.placeholder = f.ph;
        // Special: datetime-local needs T stripped to 16 chars
        let val = globalSettings[f.key]||'';
        if(f.type==='datetime-local' && val.length>16) val=val.slice(0,16);
        input.value = val;
      }
      input.id = `asf_${f.key}`;
      div.appendChild(input);
      fields.appendChild(div);
    });
  }

  document.getElementById('appSettingsModal').style.display='flex';
}

function closeAppSettings(){
  document.getElementById('appSettingsModal').style.display='none';
}

function saveAppSettings(){
  const cfg = APP_SETTINGS_CONFIG[currentAppSettingsKey];
  if(!cfg) return;
  const payload = {action:'save_global'};
  cfg.fields.forEach(f=>{
    const el = document.getElementById(`asf_${f.key}`);
    if(el) payload[f.key] = el.value;
  });
  fetch('/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
  .then(()=>{ showToast('Settings saved'); closeAppSettings(); });
}

// ============================================================
//  TUNING TAB
// ============================================================
function loadSettingsData(){
  document.getElementById('modMatrix').innerHTML='<div style="color:#888;grid-column:span 15;text-align:center;padding:8px">Loading…</div>';
  fetch('/settings').then(r=>r.json()).then(data=>{
    globalSettings=data;
    document.getElementById('zipInput').value    = data.zip_code||'';
    document.getElementById('tzInput').value     = data.timezone||'';
    document.getElementById('keyInput').value    = data.weather_api_key||'';
    document.getElementById('stopInput').value   = data.mbta_stop||'';
    document.getElementById('routeInput').value  = data.mbta_route||'';
    document.getElementById('stockInput').value  = data.stocks_list||'';
    document.getElementById('nhlInput').value    = data.nhl_teams||'';
    document.getElementById('ytInput').value     = data.yt_channel_id||'';
    document.getElementById('ytApiInput').value  = data.yt_api_key||'';
    document.getElementById('ytVideoInput').value= data.yt_video_id||'';
    document.getElementById('autoHomeToggle').checked = data.auto_home;
    document.getElementById('simRows').value = data.sim_rows||3;
    document.getElementById('simCols').value = data.sim_cols||15;
    renderModuleGrid();
    selectModule(selectedModule);
  });
}

function renderModuleGrid(){
  const grid = document.getElementById('modMatrix');
  grid.innerHTML='';
  for(let i=0;i<45;i++){
    const cell=document.createElement('div');
    cell.className=`mod-cell${i===selectedModule?' active':''}`;
    cell.textContent=i.toString().padStart(2,'0');
    cell.onclick=()=>selectModule(i);
    grid.appendChild(cell);
  }
}

function selectModule(id){
  selectedModule=id;
  renderModuleGrid();
  document.getElementById('inspectorPanel').style.display='flex';
  document.getElementById('inspectTitle').textContent=`MODULE ${id.toString().padStart(2,'0')}`;
  document.getElementById('inspectOffset').textContent=globalSettings.offsets[id.toString()]||2832;
  document.getElementById('inspectCalib').textContent=globalSettings.calibrations[id.toString()]||4096;
  renderCharGrid();
}

function renderCharGrid(){
  const grid=document.getElementById('charMatrix');
  grid.innerHTML='';
  const COLOR_DISP={'r':'🟥','o':'🟧','y':'🟨','g':'🟩','b':'🟦','p':'🟪','w':'⬜',' ':'⬛'};
  const tuned=globalSettings.tuned_chars[selectedModule.toString()]||{};
  for(let i=0;i<64;i++){
    const ch=CHAR_MAP[i];
    // " is shown as " (it's position 48, was 'q')
    const disp=COLOR_DISP[ch]||ch;
    const expected=i*64;
    const isTuned=tuned[i.toString()]!==undefined;
    const actual=isTuned?tuned[i.toString()]:expected;
    const cell=document.createElement('div');
    cell.className=`char-cell${isTuned?' tuned':''}`;
    cell.innerHTML=`<div class="char-id">${disp}</div><div class="char-step">${actual}</div>`;
    cell.onclick=()=>openCharModal(i,disp,expected,actual);
    grid.appendChild(cell);
  }
}

function adjustOffset(delta){
  fetch('/settings',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id:selectedModule,action:'adjust',delta})})
  .then(r=>r.json()).then(d=>{
    globalSettings.offsets[selectedModule.toString()]=d.new_offset;
    document.getElementById('inspectOffset').textContent=d.new_offset;
  });
}

function homeSelected(){
  fetch('/settings',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id:selectedModule,action:'home_one'})});
  showToast(`Homing module ${selectedModule.toString().padStart(2,'0')}`);
}

function homeAll(){
  if(!confirm('Re-home all 45 modules via broadcast?')) return;
  fetch('/home_all').then(()=>showToast('Homing all modules','warn'));
}

function calibrateSelected(){
  if(!confirm(`Calibrate Module ${selectedModule}? It will spin 360° to measure steps.`)) return;
  document.getElementById('inspectCalib').textContent='Measuring…';
  fetch('/settings',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id:selectedModule,action:'calibrate'})})
  .then(r=>r.json()).then(d=>{
    if(d.status==='success'){
      globalSettings.calibrations[selectedModule.toString()]=d.steps;
      document.getElementById('inspectCalib').textContent=d.steps;
      showToast(`Module ${selectedModule}: ${d.steps} steps`);
    } else {
      showToast('Calibration timeout','error');
    }
  });
}

function syncOneFromHardware(){
  document.getElementById('inspectOffset').textContent='Syncing…';
  fetch('/sync_module',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id:selectedModule})})
  .then(r=>r.json()).then(d=>{
    if(d.status==='success'){ globalSettings=d.settings; selectModule(selectedModule); showToast('Synced'); }
    else showToast('Sync failed','error');
  });
}

function syncAllFromHardware(){
  if(!confirm('Poll all 45 modules to rebuild settings.json? (~15 seconds)')) return;
  document.body.style.cursor='wait';
  fetch('/sync_all',{method:'POST'}).then(r=>r.json()).then(d=>{
    document.body.style.cursor='default';
    globalSettings=d.settings;
    selectModule(selectedModule);
    showToast('All modules synced');
  });
}

function openCharModal(index,displayChar,expected,current){
  selectedCharIndex=index;
  document.getElementById('modalTitle').textContent=`Tune: ${displayChar}`;
  document.getElementById('modalExpected').textContent=expected;
  document.getElementById('modalInput').value=current;
  document.getElementById('charModal').style.display='flex';
}

function closeModal(){ document.getElementById('charModal').style.display='none'; }

function modalAction(action){
  const step=document.getElementById('modalInput').value;
  fetch('/custom_tune',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({action,id:selectedModule,index:selectedCharIndex,step})})
  .then(r=>r.json()).then(()=>{
    if(action==='save'){
      if(!globalSettings.tuned_chars[selectedModule]) globalSettings.tuned_chars[selectedModule]={};
      globalSettings.tuned_chars[selectedModule][selectedCharIndex]=parseInt(step);
      showToast('Step saved to EEPROM');
    } else if(action==='erase'){
      delete globalSettings.tuned_chars[selectedModule][selectedCharIndex];
      showToast('Reverted to expected','warn');
    } else {
      return; // goto: don't close
    }
    renderCharGrid();
    closeModal();
  });
}

function saveGlobal(){
  const rows = parseInt(document.getElementById('simRows').value) || 3;
  const cols = parseInt(document.getElementById('simCols').value) || 15;
  fetch('/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
    action:'save_global',
    sim_rows:rows, sim_cols:cols,
    zip_code:       document.getElementById('zipInput').value,
    timezone:       document.getElementById('tzInput').value,
    weather_api_key:document.getElementById('keyInput').value,
    mbta_stop:      document.getElementById('stopInput').value,
    mbta_route:     document.getElementById('routeInput').value,
    stocks_list:    document.getElementById('stockInput').value,
    nhl_teams:      document.getElementById('nhlInput').value,
    yt_channel_id:  document.getElementById('ytInput').value,
    yt_api_key:     document.getElementById('ytApiInput').value,
    yt_video_id:    document.getElementById('ytVideoInput').value,
  })}).then(()=>{
    initLiveGrids(rows, cols);
    showToast('Settings saved');
  });
}

function toggleAutoHome(){
  fetch('/toggle_autohome',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({enabled:document.getElementById('autoHomeToggle').checked})});
}

// ── Backup / Restore ─────────────────────────────────────────
function downloadBackup(){
  fetch('/backup_settings').then(r=>r.json()).then(data=>{
    const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
    const a=document.createElement('a');
    a.href=URL.createObjectURL(blob);
    a.download=`splitflap_backup_${new Date().toISOString().slice(0,10)}.json`;
    a.click();
    showToast('Backup downloaded');
  });
}

function uploadBackup(input){
  if(!input.files.length) return;
  const reader=new FileReader();
  reader.onload=e=>{
    try{
      const data=JSON.parse(e.target.result);
      if(!confirm(`Restore calibration data and push to all 45 modules? This takes ~30 seconds.`)) return;
      document.getElementById('restoreStatus').textContent='Restoring…';
      fetch('/restore_settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})
      .then(r=>r.json()).then(d=>{
        document.getElementById('restoreStatus').textContent=d.status==='success'?'✓ Done':'✗ Error';
        if(d.status==='success'){ showToast('Restore complete'); loadSettingsData(); }
        else showToast('Restore error','error');
      });
    }catch(err){
      showToast('Invalid JSON file','error');
    }
    input.value='';
  };
  reader.readAsText(input.files[0]);
}


// ============================================================
//  AUTO FINE-TUNE
// ============================================================
const at = {
  active: false,
  charIndex: 63,
  phase: 'ahead',     // 'ahead' | 'behind' | 'verify'
  selected: new Set(),
  positions: {},       // module positions from server
};

const COLOR_DISP_AT = {'r':'🟥','o':'🟧','y':'🟨','g':'🟩','b':'🟦','p':'🟪','w':'⬜',' ':'⬛'};

function charDisplay(idx) {
  const ch = CHAR_MAP[idx];
  return COLOR_DISP_AT[ch] || ch;
}

function openAutoTune(){
  document.getElementById('autoTuneOverlay').style.display='flex';
  document.getElementById('atStart').style.display='block';
  document.getElementById('atHoming').style.display='none';
  document.getElementById('atActive').style.display='none';
  document.getElementById('atDone').style.display='none';
}

function closeAutoTune(){
  document.getElementById('autoTuneOverlay').style.display='none';
  // Refresh tuning page data after changes
  if(globalSettings) loadSettingsData();
}

async function atBegin(){
  const startIdx = parseInt(document.getElementById('atStartIdx').value) || 63;
  const stepSize = parseInt(document.getElementById('atStepSize').value) || 25;
  at.charIndex = Math.max(1, Math.min(63, startIdx));

  // Show homing screen
  document.getElementById('atStart').style.display='none';
  document.getElementById('atHoming').style.display='block';

  // Stop any running app first
  await fetch('/stop_app', {method:'POST'});

  // Home all modules
  await fetch('/auto_tune', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action:'home'})
  });

  // Countdown
  const cdEl = document.getElementById('atHomingCountdown');
  for(let i=12; i>0; i--){
    cdEl.textContent = `${i} seconds remaining…`;
    await new Promise(r=>setTimeout(r, 1000));
  }

  // Set step size in active screen
  document.getElementById('atStepSizeActive').value = stepSize;

  // Transition to active tuning
  document.getElementById('atHoming').style.display='none';
  document.getElementById('atActive').style.display='block';
  document.getElementById('atJumpIdx').value = at.charIndex;

  atGoToChar(at.charIndex);
}

async function atGoToChar(idx){
  at.charIndex = idx;
  at.phase = 'ahead';
  at.selected.clear();

  document.getElementById('atJumpIdx').value = idx;

  // Update header
  const ch = charDisplay(idx);
  document.getElementById('atCharBox').textContent = ch;
  document.getElementById('atCharBox').title = `Index ${idx}: "${CHAR_MAP[idx]}"`;
  document.getElementById('atProgressText').textContent =
    `Character ${idx} of 63 — Index ${idx} — "${CHAR_MAP[idx]}"`;

  // Send all modules to this character
  await fetch('/auto_tune', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action:'goto_char', char_index: idx})
  });

  // Get position data
  const res = await fetch('/auto_tune', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action:'get_positions', char_index: idx})
  });
  const data = await res.json();
  at.positions = data.positions || {};

  atRenderPhase();
}

function atRenderPhase(){
  const grid = document.getElementById('atGrid');
  const instrEl = document.getElementById('atInstructions');
  const btnRow = document.getElementById('atPhaseButtons');

  // Grid
  grid.innerHTML = '';
  for(let i=0;i<45;i++){
    const cell = document.createElement('div');
    cell.className = 'at-cell';
    cell.textContent = i.toString().padStart(2,'0');

    // Show tuned indicator
    const pos = at.positions[i.toString()];
    if(pos && pos.tuned !== null){
      cell.classList.add('tuned-indicator');
    }

    // Selection state
    if(at.selected.has(i)){
      cell.classList.add(at.phase === 'ahead' ? 'sel-ahead' : 'sel-behind');
    }

    cell.onclick = () => {
      if(at.phase === 'verify') return;
      if(at.selected.has(i)) at.selected.delete(i);
      else at.selected.add(i);
      atRenderPhase();
    };

    grid.appendChild(cell);
  }

  // Get neighboring char names for instructions
  const prevChar = at.charIndex > 0 ? charDisplay(at.charIndex - 1) : '?';
  const nextChar = at.charIndex < 63 ? charDisplay(at.charIndex + 1) : '?';
  const curChar = charDisplay(at.charIndex);

  if(at.phase === 'ahead'){
    instrEl.innerHTML = `All modules should show <strong>${curChar}</strong>.<br>` +
      `Click any module showing <strong style="color:#f55">${nextChar}</strong> (one ahead / overshot).` +
      `<br><span style="color:#666;font-size:.8rem">Then press "Apply" or "Skip" if none are wrong.</span>`;
    btnRow.innerHTML = `
      <button class="btn" style="background:#633;color:#fff;min-width:140px" onclick="atApplyAhead()">
        Apply −${document.getElementById('atStepSizeActive').value} to ${at.selected.size} selected
      </button>
      <button class="btn btn-secondary" onclick="atSkipToPhase('behind')">None Ahead → Check Behind</button>
    `;
  } else if(at.phase === 'behind'){
    instrEl.innerHTML = `All modules should show <strong>${curChar}</strong>.<br>` +
      `Click any module showing <strong style="color:#5f5">${prevChar}</strong> (one behind / undershot).` +
      `<br><span style="color:#666;font-size:.8rem">Then press "Apply" or "All Good" to advance.</span>`;
    btnRow.innerHTML = `
      <button class="btn" style="background:#363;color:#fff;min-width:140px" onclick="atApplyBehind()">
        Apply +${document.getElementById('atStepSizeActive').value} to ${at.selected.size} selected
      </button>
      <button class="btn btn-success" onclick="atNextChar()">All Good → Next Character</button>
      <button class="btn btn-secondary btn-sm" onclick="atSkipToPhase('ahead')">Re-check Ahead</button>
    `;
  } else { // verify
    instrEl.innerHTML = `Corrections applied. Modules are re-displaying <strong>${curChar}</strong>.<br>` +
      `<span style="color:#888">Check the physical display. Still wrong? Go back. All good? Advance.</span>`;
    btnRow.innerHTML = `
      <button class="btn btn-success" onclick="atNextChar()">All Good → Next Character</button>
      <button class="btn btn-warning" onclick="atSkipToPhase('ahead')">Still Wrong → Re-check</button>
    `;
  }
}

async function atApplyAhead(){
  if(!at.selected.size){
    showToast('No modules selected','warn');
    return;
  }
  const step = parseInt(document.getElementById('atStepSizeActive').value) || 25;
  const modules = Array.from(at.selected);

  await fetch('/auto_tune', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      action: 'adjust',
      modules: modules,
      char_index: at.charIndex,
      delta: -step  // ahead = overshot = reduce steps
    })
  });

  showToast(`Applied −${step} to ${modules.length} modules`);
  at.selected.clear();

  // Re-send all to this char to verify
  await fetch('/auto_tune', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action:'goto_char', char_index: at.charIndex})
  });

  // Refresh positions
  const res = await fetch('/auto_tune', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action:'get_positions', char_index: at.charIndex})
  });
  const data = await res.json();
  at.positions = data.positions || {};

  at.phase = 'verify';
  atRenderPhase();
}

async function atApplyBehind(){
  if(!at.selected.size){
    showToast('No modules selected','warn');
    return;
  }
  const step = parseInt(document.getElementById('atStepSizeActive').value) || 25;
  const modules = Array.from(at.selected);

  await fetch('/auto_tune', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      action: 'adjust',
      modules: modules,
      char_index: at.charIndex,
      delta: +step  // behind = undershot = increase steps
    })
  });

  showToast(`Applied +${step} to ${modules.length} modules`);
  at.selected.clear();

  // Re-send to verify
  await fetch('/auto_tune', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action:'goto_char', char_index: at.charIndex})
  });

  // Refresh positions
  const res = await fetch('/auto_tune', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action:'get_positions', char_index: at.charIndex})
  });
  const data = await res.json();
  at.positions = data.positions || {};

  at.phase = 'verify';
  atRenderPhase();
}

function atSkipToPhase(phase){
  at.phase = phase;
  at.selected.clear();
  atRenderPhase();
}

function atNextChar(){
  const next = at.charIndex - 1;
  if(next < 1){
    // Done!
    document.getElementById('atActive').style.display='none';
    document.getElementById('atDone').style.display='block';
    return;
  }
  atGoToChar(next);
}

function atJumpTo(val){
  const idx = parseInt(val);
  if(idx >= 1 && idx <= 63){
    atGoToChar(idx);
  }
}

function atFinish(){
  if(!confirm('End fine-tuning? All corrections so far are already saved.')) return;
  document.getElementById('atActive').style.display='none';
  document.getElementById('atDone').style.display='block';
}


// ============================================================
//  TEACH MODE
// ============================================================
const tm = { charIdx:0, stepSize:3, selected:new Set(), positions:{}, screen:'start', adjustedChars:new Set() };

function openTeachMode(){
  document.getElementById('teachModeOverlay').style.display='flex';
  document.getElementById('tmStart').style.display='block';
  document.getElementById('tmHoming').style.display='none';
  document.getElementById('tmActive').style.display='none';
  document.getElementById('tmDone').style.display='none';
}

function closeTeachMode(){
  document.getElementById('teachModeOverlay').style.display='none';
  if(globalSettings) loadSettingsData();
}

async function tmBegin(){
  tm.stepSize = parseInt(document.getElementById('tmStepSize').value) || 3;
  tm.charIdx = 0;
  tm.adjustedChars.clear();

  document.getElementById('tmStart').style.display='none';
  document.getElementById('tmHoming').style.display='block';

  await fetch('/stop_app', {method:'POST'});
  await fetch('/auto_tune', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action:'home'})
  });

  const cdEl = document.getElementById('tmHomingCountdown');
  for(let i=12; i>0; i--){
    cdEl.textContent = `${i} seconds remaining…`;
    await new Promise(r=>setTimeout(r, 1000));
  }

  document.getElementById('tmStepSizeActive').value = tm.stepSize;
  document.getElementById('tmHoming').style.display='none';
  document.getElementById('tmActive').style.display='block';

  tmGoToChar(0);
}

async function tmGoToChar(idx){
  tm.charIdx = idx;
  tm.selected.clear();

  document.getElementById('tmPrevBtn').disabled = (idx === 0);

  const pct = ((idx / 63) * 100).toFixed(0);
  document.getElementById('tmProgressFill').style.width = pct + '%';
  document.getElementById('tmProgressText').textContent = `Character ${idx} of 63`;

  const ch = charDisplay(idx);
  document.getElementById('tmCharBox').textContent = ch;
  document.getElementById('tmCharBox').title = `Index ${idx}: "${CHAR_MAP[idx]}"`;

  await fetch('/auto_tune', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action:'goto_char', char_index: idx})
  });

  const res = await fetch('/auto_tune', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action:'get_positions', char_index: idx})
  });
  const data = await res.json();
  tm.positions = data.positions || {};

  tmRenderGrid();
}

function tmRenderGrid(){
  const grid = document.getElementById('tmGrid');
  grid.innerHTML = '';
  for(let i=0; i<45; i++){
    const cell = document.createElement('div');
    cell.className = 'at-cell';
    cell.textContent = i.toString().padStart(2,'0');
    const pos = tm.positions[i.toString()];
    if(pos && pos.tuned !== null) cell.classList.add('tuned-indicator');
    if(tm.selected.has(i)) cell.classList.add('sel-ahead');
    cell.onclick = () => {
      if(tm.selected.has(i)) tm.selected.delete(i);
      else tm.selected.add(i);
      tmRenderGrid();
    };
    grid.appendChild(cell);
  }
}

function tmSelectNone(){ tm.selected.clear(); tmRenderGrid(); }

async function tmNudge(multiplier){
  if(!tm.selected.size){ showToast('No modules selected','warn'); return; }
  const step = parseInt(document.getElementById('tmStepSizeActive').value) || tm.stepSize;
  const delta = step * multiplier;
  const modules = Array.from(tm.selected);

  await fetch('/auto_tune', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ action:'adjust', modules:modules, char_index:tm.charIdx, delta:delta })
  });

  tm.adjustedChars.add(tm.charIdx);
  showToast(`Applied ${delta>0?'+':''}${delta} to ${modules.length} modules`);

  await fetch('/auto_tune', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action:'goto_char', char_index: tm.charIdx})
  });

  const res = await fetch('/auto_tune', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action:'get_positions', char_index: tm.charIdx})
  });
  const data = await res.json();
  tm.positions = data.positions || {};
  tmRenderGrid();
}

function tmNext(){
  if(tm.charIdx >= 63){
    document.getElementById('tmActive').style.display='none';
    document.getElementById('tmDone').style.display='block';
    document.getElementById('tmSummary').textContent =
      `Adjusted ${tm.adjustedChars.size} of 64 characters.`;
    return;
  }
  tmGoToChar(tm.charIdx + 1);
}

function tmPrev(){
  if(tm.charIdx > 0) tmGoToChar(tm.charIdx - 1);
}

function tmFinishEarly(){
  if(!confirm('End teach mode? All corrections so far are already saved.')) return;
  document.getElementById('tmActive').style.display='none';
  document.getElementById('tmDone').style.display='block';
  document.getElementById('tmSummary').textContent =
    `Adjusted ${tm.adjustedChars.size} characters (stopped at index ${tm.charIdx}).`;
}


// ============================================================
//  INIT
// ============================================================
// Populate default transition style select
(function(){
  const sel = document.getElementById('styleInput');
  if(sel) sel.innerHTML = buildStyleOptions('ltr');
})();

buildAppsGrid();
loadSavedPlaylists();
updatePreview();
