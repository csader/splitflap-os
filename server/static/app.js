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
const APP_SETTINGS_CONFIG = {};

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

let liveFlipSpeedMs = 28;
let liveGridRows = 3, liveGridCols = 15;
let simMode = false;

function updateSimModeUI() {
  const toggle = document.getElementById('simModeToggle');
  toggle.checked = !simMode;  // checked = LIVE, unchecked = SIM
  document.getElementById('simLabel').style.color = simMode ? '#f88' : '#555';
  document.getElementById('liveLabel').style.color = simMode ? '#555' : 'var(--green)';
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
  const grid = document.querySelector('.live-grid-control');
  if (!grid) return;
  grid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
  grid.innerHTML = '';
  liveFlaps['control'] = [];
  for (let i = 0; i < rows * cols; i++) {
    const el = document.createElement('div');
    el.className = 'live-flap';
    el.innerHTML = '<div class="fh ft"><span class="fc"></span></div><div class="fh fb"><span class="fc"></span></div><div class="fd"></div>';
    grid.appendChild(el);
    liveFlaps['control'].push(new LiveFlap(el));
  }
}

// Fetch initial grid config then init
(async function(){
  try {
    const cfg = await fetch('/grid_config').then(r=>r.json());
    initLiveGrids(cfg.rows || 3, cfg.cols || 15);
    initComposeGrid();
    simMode = cfg.sim_mode !== false;
    updateSimModeUI();
  } catch(e) { initLiveGrids(3, 15); initComposeGrid(); updateSimModeUI(); }
})();

async function applyGridConfig() {
  const rows = parseInt(document.getElementById('simRows').value) || 3;
  const cols = parseInt(document.getElementById('simCols').value) || 15;
  await fetch('/settings', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action:'save_global', sim_rows:rows, sim_cols:cols})
  });
  initLiveGrids(rows, cols);
  initComposeGrid();
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
      initComposeGrid();
    }

    // Homing overlay (single, hide in sim mode)
    const homingEl = document.getElementById('homing-control');
    if(homingEl){
      if(data.is_homed || data.sim_mode){ homingEl.style.display='none'; }
      else {
        homingEl.style.display='flex';
        homingEl.innerHTML = data.hardware_connected
          ? '<div style="text-align:center">HOMING REQUIRED<br><button class="btn btn-warning btn-sm" style="margin-top:8px" onclick="homeAll()">HOME ALL</button></div>'
          : '<div style="text-align:center">NO SPLITFLAP DEVICE DETECTED</div>';
      }
    }

    // Animated live display (single grid)
    const s = data.state || '';
    const fa = liveFlaps['control'];
    if(fa) for(let i=0; i<fa.length; i++){
      const ch = s[i] || ' ';
      const idx = CHAR_MAP.indexOf(ch);
      fa[i].setTarget(idx >= 0 ? idx : 0, i * 5);
    }

    // Active app banner (single)
    const app = data.active_app;
    const playlistRunning = data.active_app_playlist;
    const playlistName = data.app_playlist_name;
    currentActiveApp = app;
    const appLabel = playlistRunning ? (playlistName ? `Playlist: ${playlistName}` : 'Playlist') : (app ? (APP_LIST.find(a=>a.key===app)||{name:app}).name : null);
    const banner = document.getElementById('control-banner');
    const nameEl = document.getElementById('control-app-name');
    if(banner){
      banner.classList.toggle('visible', !!(app || playlistRunning));
      if((app || playlistRunning) && nameEl) nameEl.textContent = appLabel;
    }

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
  document.querySelectorAll('.bottom-tab').forEach(b=>b.classList.remove('active'));
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
  document.getElementById('page-'+name).classList.add('active');
  if(name==='apps') buildAppsGrid();
  if(name==='playlists'){ loadSavedAppPlaylists(); if(typeof lucide!=='undefined') lucide.createIcons(); }
}

// ── Hamburger ──
function toggleHamburger(){
  document.getElementById('hamburgerDrawer').classList.toggle('open');
  document.getElementById('hamburgerOverlay').classList.toggle('open');
}

function showHamburgerSection(name){
  // unused — replaced by openMenuPage
}

function hideHamburgerSection(){
  // unused — replaced by closeMenuPage
}

let _prevTab = 'apps';
function openMenuPage(name){
  // Close hamburger if open (don't toggle — callers outside the drawer would open it)
  const drawer = document.getElementById('hamburgerDrawer');
  if(drawer && drawer.classList.contains('open')) toggleHamburger();
  const active = document.querySelector('.bottom-tab.active');
  if(active) _prevTab = active.id.replace('tab-','');
  document.getElementById('bottomTabs').style.display='none';
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.getElementById('page-'+name).classList.add('active');
  if(name==='calibration') loadSettingsData();
  if(name==='settings') loadSettingsData();
  if(name==='library') loadAppLibrary();
  if(typeof lucide!=='undefined') lucide.createIcons();
}

function closeMenuPage(){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.getElementById('page-'+_prevTab).classList.add('active');
  document.getElementById('bottomTabs').style.display='flex';
}

function openAppLibrary(){
  const active = document.querySelector('.bottom-tab.active');
  if(active) _prevTab = active.id.replace('tab-','');
  document.getElementById('bottomTabs').style.display='none';
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.getElementById('page-library').classList.add('active');
  loadAppLibrary();
  if(typeof lucide!=='undefined') lucide.createIcons();
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
//  COMPOSE — REUSABLE GRID EDITOR
// ============================================================
let activeGridInstance = null; // tracks which grid has focus

function createComposeGrid(container, opts={}){
  const rows = opts.rows || get_rows();
  const cols = opts.cols || get_cols();
  const total = rows * cols;
  const compact = opts.compact || false;
  const onChange = opts.onChange || (()=>{});

  let buffer = Array(total).fill(' ');
  let cursor = -1;

  // Initialize from existing text
  if(opts.initialText){
    const chars = Array.from(opts.initialText);
    for(let i=0; i<Math.min(chars.length, total); i++) buffer[i] = chars[i] || ' ';
  }

  // Build DOM
  const wrapper = document.createElement('div');
  wrapper.className = 'compose-grid-editor' + (compact ? ' compact' : '');
  wrapper.style.position = 'relative';

  const gridWrap = document.createElement('div');
  gridWrap.className = 'preview-wrapper';
  gridWrap.style.cursor = 'text';
  const grid = document.createElement('div');
  grid.className = 'preview-grid';
  gridWrap.appendChild(grid);

  const capture = document.createElement('input');
  capture.type = 'text';
  capture.style.cssText = 'position:absolute;opacity:0;width:1px;height:1px;top:0;left:0;pointer-events:none';
  capture.autocomplete = 'off';
  capture.setAttribute('inputmode', 'text');
  capture.setAttribute('autocapitalize', 'characters');

  const controls = document.createElement('div');
  controls.className = 'control-panel';
  controls.style.cssText = 'display:flex;align-items:center;gap:8px;margin:6px 0';
  const centerLabel = document.createElement('label');
  centerLabel.style.cssText = 'cursor:pointer;font-size:.8rem;display:flex;align-items:center;gap:4px';
  const centerCb = document.createElement('input');
  centerCb.type = 'checkbox';
  centerCb.onchange = ()=> doCenter();
  centerLabel.appendChild(centerCb);
  centerLabel.appendChild(document.createTextNode(' Center'));
  const clearBtn = document.createElement('button');
  clearBtn.className = 'btn btn-secondary btn-sm';
  clearBtn.style.marginLeft = 'auto';
  clearBtn.textContent = 'Clear';
  clearBtn.onclick = ()=> doClear();
  controls.appendChild(centerLabel);
  controls.appendChild(clearBtn);

  const palette = document.createElement('div');
  palette.className = 'color-palette';
  ['🟥','🟧','🟨','🟩','🟦','🟪','⬜','⬛'].forEach(emoji=>{
    const btn = document.createElement('button');
    btn.className = 'color-btn';
    btn.textContent = emoji;
    btn.onclick = ()=> doInsertColor(emoji);
    palette.appendChild(btn);
  });

  wrapper.appendChild(gridWrap);
  wrapper.appendChild(capture);
  wrapper.appendChild(controls);
  wrapper.appendChild(palette);
  container.appendChild(wrapper);

  function render(){
    grid.innerHTML = '';
    grid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
    buffer.forEach((ch, i) => {
      const div = document.createElement('div');
      div.className = 'flap-unit' + (i === cursor ? ' cursor' : '');
      div.innerText = ch === ' ' ? '' : ch;
      div.onclick = ()=> setCursor(i);
      grid.appendChild(div);
    });
    onChange(getText());
  }

  function setCursor(i){
    cursor = i;
    activeGridInstance = instance;
    capture.focus();
    render();
  }

  function getText(){
    return buffer.join('');
  }

  function setText(text){
    buffer = Array(total).fill(' ');
    const chars = Array.from(text);
    for(let i=0; i<Math.min(chars.length, total); i++) buffer[i] = chars[i] || ' ';
    render();
  }

  function doClear(){
    buffer = Array(total).fill(' ');
    cursor = -1;
    centerCb.checked = false;
    render();
  }

  function doCenter(){
    for(let r=0; r<rows; r++){
      const start = r * cols;
      const row = buffer.slice(start, start + cols);
      let first = row.findIndex(c => c !== ' ');
      if(first === -1) continue;
      let last = row.length - 1;
      while(last > first && row[last] === ' ') last--;
      const content = row.slice(first, last + 1);
      const pad = Math.floor((cols - content.length) / 2);
      const centered = Array(cols).fill(' ');
      content.forEach((c, i) => centered[pad + i] = c);
      centered.forEach((c, i) => buffer[start + i] = c);
    }
    render();
  }

  function doInsertColor(emoji){
    if(cursor < 0) cursor = 0;
    activeGridInstance = instance;
    buffer[cursor] = emoji;
    if(cursor < total-1) cursor++;
    render();
    capture.focus();
  }

  function handleKey(e){
    if(activeGridInstance !== instance) return false;
    if(cursor < 0) return false;
    if(document.activeElement !== capture && !e.target.closest('.preview-grid')) return false;

    if(e.key === 'Backspace'){
      e.preventDefault();
      if(buffer[cursor] !== ' '){
        buffer[cursor] = ' ';
      } else if(cursor > 0){
        cursor--;
        buffer[cursor] = ' ';
      }
      render();
      return true;
    } else if(e.key === 'ArrowLeft'){
      e.preventDefault();
      if(cursor > 0) cursor--;
      render(); return true;
    } else if(e.key === 'ArrowRight'){
      e.preventDefault();
      if(cursor < total-1) cursor++;
      render(); return true;
    } else if(e.key === 'ArrowDown'){
      e.preventDefault();
      if(cursor + cols < total) cursor += cols;
      render(); return true;
    } else if(e.key === 'ArrowUp'){
      e.preventDefault();
      if(cursor - cols >= 0) cursor -= cols;
      render(); return true;
    } else if(e.key.length === 1 && !e.ctrlKey && !e.metaKey){
      e.preventDefault();
      buffer[cursor] = e.key.toUpperCase();
      if(cursor < total-1) cursor++;
      render();
      return true;
    }
    return false;
  }

  // Mobile input handler — keyboards don't always fire keydown
  capture.addEventListener('input', ()=>{
    if(activeGridInstance !== instance || cursor < 0) return;
    const val = capture.value;
    if(val.length > 0){
      const chars = Array.from(val);
      chars.forEach(ch => {
        if(cursor < total){
          buffer[cursor] = ch.toUpperCase();
          if(cursor < total-1) cursor++;
        }
      });
      capture.value = '';
      render();
    }
  });

  const instance = {
    render, getText, setText, handleKey, doClear,
    getBuffer(){ return buffer; },
    setBuffer(b){ buffer = b; render(); },
    getCursor(){ return cursor; },
    destroy(){ wrapper.remove(); }
  };

  render();
  return instance;
}

// Global keyboard router
document.addEventListener('keydown', e => {
  if(activeGridInstance && activeGridInstance.handleKey(e)) return;
});

// ── Compose tab (main) ──
let composeGrid = null;
let composeBuffer = []; // kept for compat
let composeCursor = -1;
const composeTotal = () => get_rows() * get_cols();
function get_rows(){ return liveGridRows || 3; }
function get_cols(){ return liveGridCols || 15; }

function initComposeGrid(){
  const container = document.getElementById('composeGridContainer');
  if(!container) return;
  container.innerHTML = '';
  let _grid = null;
  _grid = createComposeGrid(container, {
    rows: get_rows(), cols: get_cols(),
    onChange: (text) => {
      if(!_grid) return;
      composeGrid = _grid;
      composeBuffer = _grid.getBuffer();
      composeCursor = _grid.getCursor();
      const cols = get_cols();
      const l1 = document.getElementById('L1');
      const l2 = document.getElementById('L2');
      const l3 = document.getElementById('L3');
      if(l1) l1.value = composeBuffer.slice(0, cols).join('').trimEnd();
      if(l2) l2.value = composeBuffer.slice(cols, cols*2).join('').trimEnd();
      if(l3) l3.value = composeBuffer.slice(cols*2, cols*3).join('').trimEnd();
    }
  });
  composeGrid = _grid;
}

function initComposeBuffer(){ if(composeGrid) composeGrid.render(); }
function renderCompose(){ if(composeGrid) composeGrid.render(); }
function setCursor(i){ /* no-op, handled by grid instance */ }
function updatePreview(){ return composeGrid ? composeGrid.getText() : ''; }
function clearDisplay(){
  if(composeGrid) composeGrid.doClear();
  if(editingIndex!==null){
    editingIndex=null;
    document.getElementById('saveMsgBtn').textContent='+ Add to Playlist';
  }
}
function centerBuffer(){ /* handled by grid instance center checkbox */ }
function insertColor(emoji){ /* handled by grid instance color palette */ }

function toggleMultiMode(){
  document.getElementById('multiControls').style.display =
    document.getElementById('modeToggle').checked ? 'block':'none';
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
  const pages = [{
    text:  updatePreview(),
    delay: 5,
    style: 'ltr',
    speed: 15,
  }];
  fetch('/update_playlist',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({pages, delay: 5})});
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
  if(!list) return;
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
    // Merge plugin settings with hardcoded configs.
    // Prefer latest server definitions for matching keys so schema updates propagate live.
    for(const [key, cfg] of Object.entries(pluginConfigs)){
      if(APP_SETTINGS_CONFIG[key]){
        const existing = APP_SETTINGS_CONFIG[key].fields||[];
        const incoming = cfg.fields||[];
        const incomingByKey = new Map(incoming.map(f => [f.key, f]));
        const mergedExisting = existing.map(f => incomingByKey.get(f.key) || f);
        const existingKeys = new Set(existing.map(f => f.key));
        const appendedIncoming = incoming.filter(f => !existingKeys.has(f.key));
        APP_SETTINGS_CONFIG[key].fields = mergedExisting.concat(appendedIncoming);
      } else {
        APP_SETTINGS_CONFIG[key] = cfg;
      }
    }
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

  // Only show hardcoded apps if not already shown as a plugin
  APP_LIST.forEach(a => {
    if (!pluginKeys.has(a.key)) grid.appendChild(buildAppCard(a, false));
  });
  if(typeof lucide!=='undefined') lucide.createIcons();
}

const LUCIDE_APP_ICONS = {
  demo:'clapperboard', livestream:'radio', dashboard:'layout-dashboard',
  time:'clock', date:'calendar', weather:'cloud-sun', metro:'train-front',
  stocks:'trending-up', sports:'trophy', youtube:'play-circle',
  yt_comments:'message-circle', countdown:'timer', world_clock:'globe',
  crypto:'coins', iss:'rocket', anim_rainbow:'rainbow', anim_sweep:'waves',
  anim_twinkle:'sparkles', anim_checker:'grid-3x3', anim_matrix:'binary',
  'dad-jokes':'smile', 'motivational-quotes':'quote', 'word-of-the-day':'book-open',
  'bitcoin-fear-greed':'gauge',
  'fortune-cookie':'cookie', 'magic-8-ball':'circle-help', 'shower-thoughts':'cloud-drizzle',
  'funny-one-liners':'laugh', 'stoic-quotes':'landmark', 'office-quotes':'briefcase',
  'star-wars-quotes':'sword', 'harry-potter-quotes':'wand-sparkles',
  'good-morning':'sunrise', 'good-night':'moon-star',
  'word-clock':'type', 'time-since':'hourglass', 'moon-phase':'moon',
  'art-clock':'palette', 'chuck-norris':'shield', 'trivia':'brain',
  'on-this-day':'scroll-text', 'national-today':'party-popper',
  'news-headlines':'newspaper', 'planes_overhead':'plane', 'birdnet':'bird',
};
function appLucideIcon(key){
  const id = key.replace('plugin_','');
  const name = LUCIDE_APP_ICONS[id];
  return name ? `<i data-lucide="${name}" style="width:28px;height:28px"></i>` : null;
}

function buildAppCard(a, isPlugin) {
  const div = document.createElement('div');
  const bareKey = a.key.replace('plugin_','');
  const cfgKey = a.key in APP_SETTINGS_CONFIG ? a.key : (bareKey in APP_SETTINGS_CONFIG ? bareKey : a.key);
  const hasCfg = (APP_SETTINGS_CONFIG[cfgKey] && (APP_SETTINGS_CONFIG[cfgKey].fields||[]).length > 0) || bareKey === 'sports';
  const removable = isPlugin;

  // Check grid compatibility
  const minRows = a.min_rows || 0;
  const minCols = a.min_cols || 0;
  const compatible = liveGridRows >= minRows && liveGridCols >= minCols;
  const incompatibleReason = !compatible
    ? `Requires ${minRows > liveGridRows ? minRows+'+ rows' : ''}${minRows > liveGridRows && minCols > liveGridCols ? ' and ' : ''}${minCols > liveGridCols ? minCols+'+ cols' : ''}`
    : '';

  div.className = 'app-card has-app-actions' + (compatible ? '' : ' incompatible');
  div.dataset.app = a.key;
  div.onclick = compatible ? () => runApp(a.key) : null;
  if(!compatible) div.title = incompatibleReason;

  const icon = appLucideIcon(a.key) || appLucideIcon(a.plugin_id||'') || `<span style="font-size:2.2rem">${a.icon}</span>`;
  div.innerHTML = `
    ${hasCfg && compatible ? `<button class="app-gear" style="right:${removable?'28':'8'}px" title="Settings" onclick="event.stopPropagation();openAppSettings('${cfgKey}')"><i data-lucide="settings" style="width:14px;height:14px"></i></button>` : ''}
    ${removable ? `<button class="app-gear" title="Remove" onclick="event.stopPropagation();removeApp('${a.plugin_id||a.key.replace('plugin_','')}')"><i data-lucide="x" style="width:14px;height:14px"></i></button>` : ''}
    <span class="app-icon">${icon}</span>
    <span class="app-name">${a.name}</span>
    <span class="app-desc">${compatible ? a.desc : incompatibleReason}</span>`;
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
  if(currentActiveApp === appKey || currentActiveApp === appKey.replace('plugin_','')){
    fetch('/stop_app',{method:'POST'}).then(()=>showToast('App stopped'));
    return;
  }
  fetch('/run_app',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({app:appKey})});
  const label = (APP_LIST.find(a=>a.key===appKey)||{name:appKey.replace('plugin_','').replace(/-/g,' ')}).name;
  showToast(`▶ ${label} started`);
}

// ── App Library ──────────────────────────────────────────────

async function loadAppLibrary(){
  const grid = document.getElementById('appLibraryGrid');
  const filterBar = document.getElementById('appLibraryCategoryFilter');
  grid.innerHTML = '<div style="color:#888;grid-column:1/-1;text-align:center;padding:20px">Loading...</div>';
  if(filterBar) filterBar.innerHTML = '';
  try {
    const res = await fetch('/app_library');
    const data = await res.json();
    const apps = data.apps || [];
    if(!apps.length){
      grid.innerHTML = '<div style="color:#666;grid-column:1/-1;text-align:center;padding:20px">No apps available</div>';
      return;
    }
    apps.sort((a,b) => (a.installed===b.installed) ? (a.name||'').localeCompare(b.name||'') : a.installed ? 1 : -1);

    // Build category filter pills
    const cats = [...new Set(apps.map(a=>a.category).filter(Boolean))].sort();
    let activeFilter = 'all';
    function renderFilter(){
      if(!filterBar) return;
      const allCats = ['all', ...cats];
      const labels = {all:'All',time:'Time',entertainment:'Entertainment',news:'News',lifestyle:'Lifestyle',education:'Education',finance:'Finance',sports:'Sports',animation:'Animation',data:'Data'};
      filterBar.innerHTML = allCats.map(c=>{
        const active = c===activeFilter;
        return `<button data-cat="${c}" style="white-space:nowrap;padding:4px 12px;border-radius:16px;border:1px solid ${active?'var(--accent)':'var(--border)'};background:${active?'var(--accent)':'transparent'};color:${active?'#000':'var(--text)'};font-size:.78rem;cursor:pointer;transition:all .15s">${labels[c]||c}</button>`;
      }).join('');
      filterBar.querySelectorAll('button').forEach(btn=>{
        btn.onclick = ()=>{ activeFilter=btn.dataset.cat; renderFilter(); renderGrid(); };
      });
    }

    function renderGrid(){
      grid.innerHTML = '';
      const filtered = activeFilter==='all' ? apps : apps.filter(a=>a.category===activeFilter);
      filtered.forEach(a => {
        const div = document.createElement('div');
        div.className = 'app-card app-library-card';
        div.style.cursor = 'default';
        const icon = appLucideIcon(a.id) || `<span style="font-size:2.2rem">${a.icon||'🧩'}</span>`;
        const catBadge = a.category ? `<span style="display:inline-block;font-size:.6rem;color:#aaa;background:#1a1a1a;padding:1px 5px;border-radius:3px;margin-left:4px">${a.category}</span>` : '';
        div.innerHTML = `
          <span class="app-icon">${icon}</span>
          <span class="app-name">${a.name}</span>
          <span class="app-desc">${a.description||''}</span>
          <span style="display:inline-block;font-size:.65rem;color:#888;background:#222;padding:2px 6px;border-radius:4px;margin-top:4px">${a.type}${a.version?' · v'+a.version:''}${catBadge}</span>
          <div class="app-library-action">
            ${a.installed
              ? '<button class="btn-del" style="width:100%;padding:8px;border-radius:6px;font-size:.8rem;text-align:center" onclick="event.stopPropagation();uninstallApp(\''+a.id+'\')">Uninstall</button>'
              : '<button class="btn btn-success btn-sm" style="width:100%;justify-content:center" onclick="event.stopPropagation();installApp(\''+a.id+'\')">Install</button>'
            }
          </div>`;
        grid.appendChild(div);
      });
      if(!filtered.length) grid.innerHTML = '<div style="color:#666;grid-column:1/-1;text-align:center;padding:20px">No apps in this category</div>';
      if(typeof lucide!=='undefined') lucide.createIcons();
    }

    renderFilter();
    renderGrid();
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

function getSettingsValue(key, fallback=''){
  const value = globalSettings ? globalSettings[key] : undefined;
  if(value === undefined || value === null || value === '') return fallback;
  return value;
}

function normalizeSettingOption(opt){
  if(opt && typeof opt === 'object'){
    return {
      value: String(opt.value ?? ''),
      label: String(opt.label ?? opt.value ?? '')
    };
  }
  return { value: String(opt ?? ''), label: String(opt ?? '') };
}

function normalizeToggleSize(rawSize){
  const size = String(rawSize || 'md').toLowerCase();
  if(size === 'small' || size === 'sm') return 'sm';
  if(size === 'large' || size === 'lg') return 'lg';
  return 'md';
}

function createSegmentedToggleControl({id, options, value, size='md'}){
  const normalized = (options || []).map(normalizeSettingOption).filter(o=>o.value!=='' || o.label!=='');
  const fallback = normalized[0] ? normalized[0].value : '';
  const current = String(value ?? fallback);
  const sizeClass = normalizeToggleSize(size);
  const changeListeners = [];

  const wrapper = document.createElement('div');
  wrapper.className = `sf-segmented-toggle ${sizeClass}`;

  const hidden = document.createElement('input');
  hidden.type = 'hidden';
  hidden.id = id;
  hidden.value = normalized.some(o=>o.value===current) ? current : fallback;
  wrapper.appendChild(hidden);

  const setActive = (newValue, notify=false)=>{
    const nextValue = String(newValue ?? fallback);
    const resolved = normalized.some(o=>o.value===nextValue) ? nextValue : fallback;
    const changed = hidden.value !== resolved;
    hidden.value = resolved;
    wrapper.querySelectorAll('button').forEach(btn=>{
      btn.classList.toggle('active', btn.dataset.value===resolved);
    });
    if(notify && changed) changeListeners.forEach(cb=>cb(resolved));
  };

  normalized.forEach(opt=>{
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'sf-segmented-toggle-btn';
    btn.dataset.value = opt.value;
    btn.textContent = opt.label;
    btn.onclick = ()=> setActive(opt.value, true);
    wrapper.appendChild(btn);
  });

  wrapper._setValue = (newValue)=> setActive(newValue, false);
  wrapper._addChangeListener = (cb)=>{
    if(typeof cb === 'function') changeListeners.push(cb);
  };

  setActive(hidden.value);
  return wrapper;
}

function getModalFieldValue(key){
  const el = document.getElementById(`asf_${key}`);
  return el ? String(el.value ?? '') : '';
}

// Set a modal field value without triggering change listeners.
// Works for plain inputs/selects and segmented toggle controls.
function setModalFieldValue(key, value){
  const el = document.getElementById(`asf_${key}`);
  if(!el) return;
  const wrapper = el.parentElement && el.parentElement.classList.contains('sf-segmented-toggle')
    ? el.parentElement
    : null;
  if(wrapper && typeof wrapper._setValue === 'function'){
    wrapper._setValue(value);
    return;
  }
  el.value = value ?? '';
}

// Bind a change callback for either native form controls or segmented toggle wrappers.
function bindModalFieldChange(key, onChange){
  const el = document.getElementById(`asf_${key}`);
  if(!el || typeof onChange !== 'function') return;
  const wrapper = el.parentElement && el.parentElement.classList.contains('sf-segmented-toggle')
    ? el.parentElement
    : null;
  if(wrapper && typeof wrapper._addChangeListener === 'function'){
    wrapper._addChangeListener(onChange);
    return;
  }
  el.addEventListener('change', ()=> onChange(String(el.value ?? '')));
}

function appendInputWithInlineToggle(div, input, field){
  const inlineToggle = field.inline_toggle;
  if(!(inlineToggle && (inlineToggle.key || '').trim())){
    div.appendChild(input);
    return;
  }

  const inlineKey = inlineToggle.key.trim();
  const inlineValue = getSettingsValue(inlineKey, inlineToggle.default ?? '');
  const inlineSize = normalizeToggleSize(inlineToggle.size);
  const inlineControl = createSegmentedToggleControl({
    id: `asf_${inlineKey}`,
    options: inlineToggle.options || [],
    value: inlineValue,
    size: inlineSize
  });
  inlineControl.classList.add('sf-inline-toggle');

  const row = document.createElement('div');
  row.className = 'sf-inline-field-row';
  const position = inlineToggle.position === 'before' ? 'before' : 'after';
  if(position === 'before'){
    row.appendChild(inlineControl);
    row.appendChild(input);
  } else {
    row.appendChild(input);
    row.appendChild(inlineControl);
  }
  div.appendChild(row);
}

function setFieldDisabledState(fieldKey, disabled){
  const row = document.getElementById(`asf_row_${fieldKey}`);
  if(!row) return;
  row.classList.toggle('is-disabled', !!disabled);
  row.querySelectorAll('input, select, textarea, button').forEach(el=>{
    el.disabled = !!disabled;
  });
}

// ── Number stepper ──────────────────────────────────────────
function createNumberStepper(input){
  const wrap = document.createElement('div');
  wrap.className = 'sf-num-stepper';
  const min  = input.min  !== '' ? parseFloat(input.min)  : -Infinity;
  const max  = input.max  !== '' ? parseFloat(input.max)  :  Infinity;
  const step = input.step !== '' ? parseFloat(input.step) : 1;
  function clamp(v){ return Math.min(max, Math.max(min, v)); }
  const dec = document.createElement('button');
  dec.type = 'button'; dec.className = 'sf-num-btn'; dec.textContent = '−';
  dec.addEventListener('click', ()=>{
    input.value = clamp((parseFloat(input.value)||0) - step);
    input.dispatchEvent(new Event('change', {bubbles:true}));
  });
  const inc = document.createElement('button');
  inc.type = 'button'; inc.className = 'sf-num-btn'; inc.textContent = '+';
  inc.addEventListener('click', ()=>{
    input.value = clamp((parseFloat(input.value)||0) + step);
    input.dispatchEvent(new Event('change', {bubbles:true}));
  });
  wrap.appendChild(dec);
  wrap.appendChild(input);
  wrap.appendChild(inc);
  return wrap;
}

// ── Computed field functions registry ────────────────────────
// Each function receives an ordered array of watched field values
// matching the "watches" array declared in the manifest.
// Return a string, or { text, warn } for warning state.
const FIELD_COMPUTE_FUNCTIONS = {};

function formatCompactCount(n){
  if(n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if(n >= 10000) return Math.round(n / 1000) + 'k';
  if(n >= 1000) return (n / 1000).toFixed(1) + 'k';
  return String(n);
}

function isTruthySetting(value, truthyValues){
  const actual = String(value ?? '').toLowerCase();
  return truthyValues.includes(actual);
}

function resolveCallsPerPoll(profile, vals, truthyValues){
  if(!profile || typeof profile !== 'object') return 1;
  if(profile.call_formula && typeof profile.call_formula === 'object'){
    const formula = profile.call_formula;
    const indices = Array.isArray(formula.flag_indices) ? formula.flag_indices : [];
    const baseCalls = Number(formula.base_calls ?? 1);
    const perTrueCalls = Number(formula.per_true_calls ?? 1);
    const trueCount = indices.reduce((count, idx)=>{
      return count + (isTruthySetting(vals[idx], truthyValues) ? 1 : 0);
    }, 0);
    if(formula.type === 'base_plus_any_true'){
      return baseCalls + (trueCount > 0 ? perTrueCalls : 0);
    }
    if(formula.type === 'base_plus_true_count'){
      return baseCalls + (trueCount * perTrueCalls);
    }
    return Math.max(1, Number(profile.calls_per_poll ?? 1));
  }
  return Math.max(1, Number(profile.calls_per_poll ?? 1));
}

function applyTemplate(template, data){
  return String(template || '').replace(/\{(\w+)\}/g, (_, key)=> {
    const value = data[key];
    return value == null ? '' : String(value);
  });
}

FIELD_COMPUTE_FUNCTIONS['polling_usage_estimate'] = function(vals, field){
  const cfg = (field && field.compute_config && typeof field.compute_config === 'object')
    ? field.compute_config
    : {};

  const minRate = Math.max(1, Number(cfg.min_rate ?? 1));
  const defaultRate = Math.max(minRate, Number(cfg.default_rate ?? 60));
  const rateIndex = Number(cfg.rate_index ?? 0);
  const rate = Math.max(minRate, parseInt(vals[rateIndex]) || defaultRate);
  const truthyValues = (Array.isArray(cfg.truthy_values) ? cfg.truthy_values : ['yes', 'true', '1', 'on'])
    .map(v => String(v).toLowerCase());

  const selectorIndex = cfg.selector_index == null ? null : Number(cfg.selector_index);
  let selector = selectorIndex == null
    ? null
    : String(vals[selectorIndex] ?? cfg.selector_default ?? '').toLowerCase();

  const profiles = (cfg.profiles && typeof cfg.profiles === 'object') ? cfg.profiles : {};
  const profileKeys = Object.keys(profiles);
  if(!selector){
    const matched = vals.map(v => String(v ?? '').toLowerCase()).find(v => profileKeys.includes(v));
    selector = matched || String(cfg.selector_default ?? '').toLowerCase() || (profileKeys.length === 1 ? profileKeys[0] : null);
  }
  const selectedProfile = selector && profiles[selector] && typeof profiles[selector] === 'object'
    ? profiles[selector]
    : (!selector && profileKeys.length === 1 ? profiles[profileKeys[0]] : {});

  const callsPerPoll = resolveCallsPerPoll(selectedProfile, vals, truthyValues);
  const limitPerDay = selectedProfile.limit_per_day == null ? null : Number(selectedProfile.limit_per_day);
  const limitPerMonth = selectedProfile.limit_per_month == null ? null : Number(selectedProfile.limit_per_month);
  const warnPrefix = String(selectedProfile.warn_prefix || 'Estimated usage exceeds configured limits.');
  const limitText = String(selectedProfile.limit_text || cfg.default_limit_text || 'Plan dependent');

  const pollsPerDay = Math.ceil(86400 / rate);
  const reqPerDay = pollsPerDay * callsPerPoll;
  const reqPerMonth = reqPerDay * 30;

  let warn = null;
  if(limitPerDay && reqPerDay > limitPerDay){
    warn = `${warnPrefix} ${formatCompactCount(reqPerDay)}/day exceeds ${formatCompactCount(limitPerDay)}/day.`;
  } else if(limitPerMonth && reqPerMonth > limitPerMonth){
    warn = `${warnPrefix} ${formatCompactCount(reqPerMonth)}/month exceeds ${formatCompactCount(limitPerMonth)}/month.`;
  }

  const textTemplate = String(cfg.text_template || '~{reqPerDay} req/day · ~{reqPerMonth}/month');
  const text = applyTemplate(textTemplate, {
    selector,
    reqPerDay: formatCompactCount(reqPerDay),
    reqPerMonth: formatCompactCount(reqPerMonth),
    callsPerPoll,
    limitText,
  });

  return { text, warn };
};

function renderComputedInfo(el, result){
  if(typeof result === 'string'){
    el.className = 'sf-computed-info';
    el.innerHTML = '';
    el.appendChild(document.createTextNode(result));
  } else {
    el.className = 'sf-computed-info' + (result.warn ? ' warn' : '');
    el.innerHTML = '';
    const t = document.createElement('span');
    t.textContent = result.text || '';
    el.appendChild(t);
    if(result.warn){
      const w = document.createElement('span');
      w.className = 'sf-computed-warn';
      w.textContent = '⚠ ' + result.warn;
      el.appendChild(w);
    }
  }
}

function renderNoticeField(div, field){
  const box = document.createElement('div');
  const variant = String(field.variant || 'info').toLowerCase();
  box.className = `sf-notice sf-notice-${variant}`;

  if(field.icon){
    const icon = document.createElement('div');
    icon.className = 'sf-notice-icon';
    icon.textContent = String(field.icon);
    box.appendChild(icon);
  }

  const body = document.createElement('div');
  body.className = 'sf-notice-body';

  if(field.title){
    const title = document.createElement('div');
    title.className = 'sf-notice-title';
    title.textContent = String(field.title);
    body.appendChild(title);
  }

  if(field.text){
    const text = document.createElement('div');
    text.className = 'sf-notice-text';
    text.textContent = String(field.text);
    body.appendChild(text);
  }

  if(Array.isArray(field.items) && field.items.length){
    const list = document.createElement('ul');
    list.className = 'sf-notice-list';
    field.items.forEach(item=>{
      const li = document.createElement('li');
      li.textContent = String(item);
      list.appendChild(li);
    });
    body.appendChild(list);
  }

  if(field.linkHref){
    const link = document.createElement('a');
    link.className = 'sf-notice-link';
    link.href = String(field.linkHref);
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = String(field.linkText || field.linkHref);
    body.appendChild(link);
  }

  box.appendChild(body);
  div.appendChild(box);
}

function renderAppSettingsField(fieldsContainer, field){
  const div = document.createElement('div');
  div.className = 'modal-field';
  div.id = `asf_row_${field.key}`;
  if(field.type === 'notice'){
    if(field.label){
      const label = document.createElement('label');
      label.textContent = field.label;
      div.appendChild(label);
    }
    renderNoticeField(div, field);
    fieldsContainer.appendChild(div);
    return;
  }
  const label = document.createElement('label');
  label.textContent = field.label;
  div.appendChild(label);

  const fieldValue = getSettingsValue(field.key, field.ph ?? '');

  if(field.type==='toggle'){
    const toggleSize = normalizeToggleSize(field.size || field.toggle_size);
    const toggle = createSegmentedToggleControl({
      id: `asf_${field.key}`,
      options: field.opts || [],
      value: fieldValue,
      size: toggleSize
    });
    div.appendChild(toggle);
    fieldsContainer.appendChild(div);
    return;
  }

  let input;
  if(field.type==='select'){
    input = document.createElement('select');
    (field.opts||[]).forEach(rawOpt=>{
      const opt = normalizeSettingOption(rawOpt);
      const optionEl = document.createElement('option');
      optionEl.value = opt.value;
      optionEl.textContent = opt.label;
      if(String(fieldValue)===opt.value) optionEl.selected=true;
      input.appendChild(optionEl);
    });
  } else if(field.type==='textarea'){
    input = document.createElement('textarea');
    input.rows = 8;
    if(field.ph) input.placeholder = field.ph;
    input.value = fieldValue;
  } else if(field.type==='search_chips' && field.maxItems===1){
    const wrapper = document.createElement('div');
    div.appendChild(wrapper);
    fieldsContainer.appendChild(div);
    createSingleSearchPicker({
      container: wrapper,
      hiddenId: `asf_${field.key}`,
      searchUrl: field.searchUrl,
      resultKey: field.resultKey,
      currentValue: fieldValue
    });
    return;
  } else if(field.type==='search_chips'){
    const wrapper = document.createElement('div');
    wrapper.className = 'chip-picker';
    div.appendChild(wrapper);
    fieldsContainer.appendChild(div);
    createSearchChipPicker({
      container: wrapper,
      hiddenId: `asf_${field.key}`,
      searchUrl: field.searchUrl,
      resultKey: field.resultKey,
      maxItems: field.maxItems||null,
      currentValues: fieldValue
    });
    return;
  } else if(field.type === 'computed'){
    const infoBox = document.createElement('div');
    infoBox.className = 'sf-computed-info';
    infoBox.dataset.computeKey = field.key;
    div.appendChild(infoBox);
    fieldsContainer.appendChild(div);
    return;
  } else if(field.type === 'number'){
    input = document.createElement('input');
    input.type = 'number';
    if(field.min != null) input.min = field.min;
    if(field.max != null) input.max = field.max;
    if(field.step)        input.step = field.step;
    input.value = String(fieldValue ?? '');
  } else {
    input = document.createElement('input');
    input.type = field.type||'text';
    if(field.min)  input.min  = field.min;
    if(field.max)  input.max  = field.max;
    if(field.step) input.step = field.step;
    if(field.ph)   input.placeholder = field.ph;
    let val = String(fieldValue ?? '');
    if(field.type==='datetime-local' && val.length>16) val=val.slice(0,16);
    input.value = val;
  }

  input.id = `asf_${field.key}`;
  if(field.type === 'password'){
    const wrap = document.createElement('div');
    wrap.className = 'password-reveal-wrap';
    wrap.appendChild(input);
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'password-reveal-btn';
    btn.title = 'Show/hide';
    btn.innerHTML = '&#128065;';
    btn.addEventListener('click', ()=>{
      input.type = input.type === 'password' ? 'text' : 'password';
      btn.style.opacity = input.type === 'text' ? '1' : '';
    });
    wrap.appendChild(btn);
    div.appendChild(wrap);
  } else if(field.type === 'number'){
    appendInputWithInlineToggle(div, field.stepper ? createNumberStepper(input) : input, field);
  } else {
    appendInputWithInlineToggle(div, input, field);
  }
  fieldsContainer.appendChild(div);
}

function wireAppSettingsSyncRules(fields){
  const fieldsByKey = new Map(fields.map(f=>[f.key, f]));
  let syncInProgress = false;

  function conditionMatches(actualValue, expected){
    const actual = String(actualValue ?? '');
    if(Array.isArray(expected)) return expected.map(v => String(v)).includes(actual);
    return actual === String(expected);
  }

  function applySyncValues(sourceKey){
    const source = fieldsByKey.get(sourceKey);
    if(!source || !source.sync_values) return;
    const selected = getModalFieldValue(sourceKey);
    const mapping = source.sync_values[selected];
    if(!mapping || typeof mapping !== 'object') return;
    syncInProgress = true;
    Object.entries(mapping).forEach(([targetKey, targetValue])=>{
      if(fieldsByKey.has(targetKey)) setModalFieldValue(targetKey, targetValue);
    });
    syncInProgress = false;
  }

  function applyVisibility(){
    fields.forEach(f=>{
      if(!f.visible_when) return;
      const row = document.getElementById(`asf_row_${f.key}`);
      if(!row) return;
      const visible = Object.entries(f.visible_when).every(
        ([parentKey, expected]) => conditionMatches(getModalFieldValue(parentKey), expected)
      );
      row.style.display = visible ? '' : 'none';
    });
  }

  function applyDisabledState(){
    fields.forEach(f=>{
      const disabled = !!f.disabled_when && Object.entries(f.disabled_when).every(
        ([parentKey, expected]) => conditionMatches(getModalFieldValue(parentKey), expected)
      );
      setFieldDisabledState(f.key, disabled);
    });
  }

  function onFieldChanged(fieldKey){
    const field = fieldsByKey.get(fieldKey);
    if(!field) return;

    if(!syncInProgress && field.sync_parent){
      const parentKey = field.sync_parent;
      const customValue = field.sync_parent_custom_value || 'custom';
      if(fieldsByKey.has(parentKey) && getModalFieldValue(parentKey) !== String(customValue)){
        setModalFieldValue(parentKey, customValue);
      }
    }

    applySyncValues(fieldKey);
    applyVisibility();
    applyDisabledState();
  }

  function recomputeFields(){
    fields.forEach(f=>{
      if(f.type !== 'computed' || !f.compute) return;
      const infoBox = document.querySelector(`[data-compute-key="${f.key}"]`);
      if(!infoBox) return;
      const fn = FIELD_COMPUTE_FUNCTIONS[f.compute];
      if(!fn) return;
      const vals = (f.watches || []).map(wk => getModalFieldValue(wk));
      renderComputedInfo(infoBox, fn(vals, f));
    });
  }

  fields.forEach(f=> bindModalFieldChange(f.key, ()=> onFieldChanged(f.key)));
  fields.forEach(f=> applySyncValues(f.key));
  applyVisibility();
  applyDisabledState();
  recomputeFields();

  // Re-run computed fields whenever any watched field changes
  fields.forEach(f=>{
    if(f.type !== 'computed' || !f.watches) return;
    f.watches.forEach(wk=> bindModalFieldChange(wk, ()=> recomputeFields()));
  });
}

async function openAppSettings(appKey){
  if(appKey==='sports'||appKey==='plugin_sports'){ openSportsSettings(); return; }
  currentAppSettingsKey = appKey;
  const cfg = APP_SETTINGS_CONFIG[appKey];
  if(!cfg) return;

  // Always fetch fresh settings
  const res = await fetch('/settings');
  globalSettings = await res.json();

  // Set title with Lucide icon if available, stripping emoji prefix from cfg.title
  const titleEl = document.getElementById('appSettingsTitle');
  const bareKey = appKey.replace('plugin_','');
  const lucideIconName = LUCIDE_APP_ICONS[bareKey];
  // Strip leading emoji + space from title (e.g. "🌤️ Weather Settings" → "Weather Settings")
  const titleText = cfg.title.replace(/^[\p{Emoji}\s]+/u, '').trim();
  if(lucideIconName){
    titleEl.innerHTML = `<i data-lucide="${lucideIconName}" style="width:20px;height:20px;vertical-align:middle;margin-right:6px"></i>${titleText}`;
    if(typeof lucide!=='undefined') lucide.createIcons();
  } else {
    titleEl.textContent = cfg.title;
  }
  const fields = document.getElementById('appSettingsFields');
  fields.innerHTML='';

  if(!cfg.fields.length){
    fields.innerHTML='<p style="color:#888;text-align:center">No configurable settings for this app.</p>';
  } else {
    cfg.fields.forEach(f=> renderAppSettingsField(fields, f));
    wireAppSettingsSyncRules(cfg.fields);
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
    if(el) payload[f.key] = el.type === 'checkbox' ? el.checked : el.value;
    const inlineKey = f.inline_toggle && (f.inline_toggle.key || '').trim();
    if(inlineKey){
      const inlineEl = document.getElementById(`asf_${inlineKey}`);
      if(inlineEl) payload[inlineKey] = inlineEl.value;
    }
  });
  fetch('/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
  .then(()=>{ showToast('Settings saved'); closeAppSettings(); });
}

// ============================================================
//  SINGLE TIMEZONE PICKER
// ============================================================
function createTimezonePicker(container, currentValue){
  const hidden = document.createElement('input');
  hidden.type='hidden'; hidden.id='globalTzValue'; hidden.value=currentValue;
  container.appendChild(hidden);

  const input = document.createElement('input');
  input.type='text'; input.className='line-input';
  input.style.cssText='font-size:.9rem;margin:0;text-transform:none';
  input.value=currentValue;
  input.placeholder='Search timezone…';
  container.appendChild(input);

  const resultsEl = document.createElement('div');
  resultsEl.className='chip-picker-results';
  container.appendChild(resultsEl);

  let debounce=null;
  input.onfocus=()=>{ if(!input.value) doSearch(''); };
  input.oninput=()=>{
    clearTimeout(debounce);
    debounce=setTimeout(()=>doSearch(input.value.trim()),300);
  };

  async function doSearch(q){
    try{
      const res = await fetch(`/timezones?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      resultsEl.innerHTML='';
      (data.zones||[]).forEach(z=>{
        const el = document.createElement('div');
        el.className='chip-picker-result'+(z.value===hidden.value?' selected':'');
        el.textContent=z.label;
        el.onclick=()=>{
          hidden.value=z.value;
          input.value=z.value;
          resultsEl.innerHTML='';
          setSettingsDirty(true);
        };
        resultsEl.appendChild(el);
      });
    }catch(e){}
  }

  // Close results on outside click
  document.addEventListener('click',(e)=>{
    if(!container.contains(e.target)) resultsEl.innerHTML='';
  });
}

// ============================================================
//  SINGLE SEARCH PICKER (for maxItems:1 fields in app settings)
// ============================================================
function createSingleSearchPicker({container, hiddenId, searchUrl, resultKey, currentValue}){
  const hidden = document.createElement('input');
  hidden.type='hidden'; hidden.id=hiddenId; hidden.value=currentValue;
  container.appendChild(hidden);

  const input = document.createElement('input');
  input.type='text'; input.className='line-input';
  input.style.cssText='font-size:.85rem;margin:0;text-transform:none';
  input.value=currentValue;
  input.placeholder='Search…';
  container.appendChild(input);

  const resultsEl = document.createElement('div');
  resultsEl.className='chip-picker-results';
  container.appendChild(resultsEl);

  let debounce=null;
  input.onfocus=()=>{ if(!input.value) doSearch(''); };
  input.oninput=()=>{
    clearTimeout(debounce);
    debounce=setTimeout(()=>doSearch(input.value.trim()),300);
  };

  async function doSearch(q){
    try{
      const res = await fetch(`${searchUrl}?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      resultsEl.innerHTML='';
      (data[resultKey]||[]).forEach(item=>{
        const el = document.createElement('div');
        el.className='chip-picker-result'+(item.value===hidden.value?' selected':'');
        el.textContent=item.label;
        el.onclick=()=>{
          hidden.value=item.value;
          input.value=item.value;
          resultsEl.innerHTML='';
        };
        resultsEl.appendChild(el);
      });
    }catch(e){}
  }

  document.addEventListener('click',(e)=>{
    if(!container.contains(e.target)) resultsEl.innerHTML='';
  });
}

// ============================================================
//  SEARCH + CHIP PICKER COMPONENT
// ============================================================
function createSearchChipPicker({container, hiddenId, searchUrl, resultKey, maxItems, currentValues}){
  const values = currentValues ? currentValues.split(',').map(v=>v.trim()).filter(Boolean) : [];
  const hidden = document.createElement('input');
  hidden.type='hidden'; hidden.id=hiddenId; hidden.value=values.join(',');
  container.appendChild(hidden);

  const chipsEl = document.createElement('div');
  chipsEl.className='chip-picker-chips';
  container.appendChild(chipsEl);

  const searchInput = document.createElement('input');
  searchInput.type='text'; searchInput.className='line-input';
  searchInput.style.cssText='font-size:.85rem;margin:6px 0 0 0;text-transform:none';
  searchInput.placeholder='Search…';
  container.appendChild(searchInput);

  const resultsEl = document.createElement('div');
  resultsEl.className='chip-picker-results';
  container.appendChild(resultsEl);

  function renderChips(){
    chipsEl.innerHTML='';
    values.forEach((v,i)=>{
      const chip = document.createElement('span');
      chip.className='team-chip selected';
      chip.style.cssText='display:inline-flex;align-items:center;gap:4px;margin:2px;padding:4px 8px';
      chip.innerHTML=`${v} <span style="cursor:pointer;opacity:.6" data-idx="${i}">✕</span>`;
      chip.querySelector('span').onclick=(e)=>{ e.stopPropagation(); values.splice(i,1); sync(); };
      chipsEl.appendChild(chip);
    });
  }

  function sync(){
    hidden.value = values.join(',');
    renderChips();
  }

  let debounce=null;
  searchInput.oninput=()=>{
    clearTimeout(debounce);
    const q = searchInput.value.trim();
    if(q.length<1){ resultsEl.innerHTML=''; return; }
    debounce=setTimeout(async()=>{
      try{
        const res = await fetch(`${searchUrl}?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        const items = data[resultKey]||[];
        resultsEl.innerHTML='';
        items.forEach(item=>{
          const already = values.includes(item.value);
          const el = document.createElement('div');
          el.className='chip-picker-result'+(already?' selected':'');
          el.textContent=item.label;
          el.onclick=()=>{
            if(already) return;
            if(maxItems && values.length>=maxItems) values.shift();
            values.push(item.value);
            sync();
            el.classList.add('selected');
          };
          resultsEl.appendChild(el);
        });
      }catch(e){ resultsEl.innerHTML='<span style="color:var(--red);font-size:.8rem">Search failed</span>'; }
    },300);
  };

  renderChips();
}

// ============================================================
//  TUNING TAB
// ============================================================
function loadSettingsData(){
  document.getElementById('modMatrix').innerHTML='<div style="color:#888;grid-column:span 15;text-align:center;padding:8px">Loading…</div>';
  fetch('/settings').then(r=>r.json()).then(data=>{
    globalSettings=data;
    document.getElementById('autoHomeToggle').checked = data.auto_home;
    document.getElementById('simRows').value = data.sim_rows||3;
    document.getElementById('simCols').value = data.sim_cols||15;
    document.getElementById('globalLoopDelay').value = data.global_loop_delay||5;
    // MQTT settings
    document.getElementById('mqttEnabled').checked = data.mqtt_enabled !== false;
    document.getElementById('mqttBroker').value = data.mqtt_broker || '';
    document.getElementById('mqttPort').value = data.mqtt_port || 1883;
    document.getElementById('mqttUser').value = data.mqtt_user || '';
    document.getElementById('mqttPassword').value = data.mqtt_password || '';
    // Notification settings
    const notifyEnabled = !!data.notify_enabled;
    document.getElementById('notifyEnabled').checked = notifyEnabled;
    document.getElementById('notifyConfig').style.display = notifyEnabled ? 'block' : 'none';
    document.getElementById('notifyDisplaySeconds').value = data.notify_display_seconds || 10;
    renderNotifySources(data.notify_sources || {});
    // Global timezone picker
    const tzEl = document.getElementById('globalTzPicker');
    if(tzEl){
      tzEl.innerHTML='';
      createTimezonePicker(tzEl, data.timezone||'');
    }
    renderModuleGrid();
    selectModule(selectedModule);
    setSettingsDirty(false);
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

function setOffsetDirect(){
  const input = document.getElementById('offsetDirectInput');
  const target = parseInt(input.value);
  if(isNaN(target)){ showToast('Enter a valid number','warn'); return; }
  const current = parseInt(globalSettings.offsets?.[selectedModule.toString()] ?? 2832);
  const delta = target - current;
  if(delta === 0){ showToast('Already at '+target); input.value=''; return; }
  adjustOffset(delta);
  input.value='';
}

function resetOffset(){
  const current = parseInt(globalSettings.offsets?.[selectedModule.toString()] ?? 2832);
  const delta = 2832 - current;
  if(delta === 0){ showToast('Already at 2832'); return; }
  adjustOffset(delta);
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

function setSettingsDirty(isDirty){
  const fab = document.getElementById('settingsFab');
  if(!fab) return;
  fab.classList.toggle('visible', !!isDirty);
}

// ============================================================
//  NOTIFICATION SETTINGS
// ============================================================
let _notifySources = {};

function renderNotifySources(sources){
  _notifySources = Object.assign({}, sources);
  const el = document.getElementById('notifySourceList');
  if(!el) return;
  el.innerHTML='';
  const names = Object.keys(_notifySources);
  if(!names.length){
    el.innerHTML='<div style="color:#666;font-size:.85rem;margin-bottom:8px">No sources configured.</div>';
    return;
  }
  names.forEach(name=>{
    const key = _notifySources[name];
    const row = document.createElement('div');
    row.style.cssText='display:flex;align-items:center;gap:8px;padding:8px 10px;background:#1a1a1a;border:1px solid var(--border);border-radius:6px;margin-bottom:6px';
    row.innerHTML=`
      <span style="flex:1;font-size:.88rem;font-weight:600;font-family:monospace">${name}</span>
      <code style="font-size:.75rem;color:#888;background:#111;padding:2px 6px;border-radius:4px;cursor:pointer" title="Click to copy" onclick="navigator.clipboard.writeText('${key}');showToast('Key copied')">${key.slice(0,8)}…</code>
      <button class="ap-entry-btn" onclick="deleteNotifySource('${name}')" title="Remove">✕</button>`;
    el.appendChild(row);
  });
}

function addNotifySource(){
  const name = prompt('Source name (e.g. frigate, openclaw, n8n):');
  if(!name || !name.trim()) return;
  const key = (Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2)).slice(0,20);
  _notifySources[name.trim()] = key;
  renderNotifySources(_notifySources);
  saveNotifySources();
  setTimeout(()=>{ confirm(`Key for "${name}":\n\n${key}\n\nCopy it now — it won't be shown again in full.`); }, 100);
}

function deleteNotifySource(name){
  if(!confirm(`Remove source "${name}"? Its key will stop working immediately.`)) return;
  delete _notifySources[name];
  renderNotifySources(_notifySources);
  saveNotifySources();
}

function saveNotifySources(){
  fetch('/settings',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({action:'save_global', notify_sources: _notifySources})});
}

document.addEventListener('DOMContentLoaded', ()=>{
  const toggle = document.getElementById('notifyEnabled');
  if(toggle) toggle.addEventListener('change', ()=>{
    document.getElementById('notifyConfig').style.display = toggle.checked ? 'block' : 'none';
  });
});

function saveGlobal(){
  const rows = parseInt(document.getElementById('simRows').value) || 3;
  const cols = parseInt(document.getElementById('simCols').value) || 15;
  const globalDelay = parseInt(document.getElementById('globalLoopDelay').value) || 5;
  const tzEl = document.getElementById('globalTzValue');
  const tz = tzEl ? tzEl.value : '';
  fetch('/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
    action:'save_global',
    sim_rows:rows, sim_cols:cols,
    global_loop_delay: globalDelay,
    timezone: tz,
    mqtt_enabled: document.getElementById('mqttEnabled').checked,
    mqtt_broker: document.getElementById('mqttBroker').value,
    mqtt_port: parseInt(document.getElementById('mqttPort').value) || 1883,
    mqtt_user: document.getElementById('mqttUser').value,
    mqtt_password: document.getElementById('mqttPassword').value,
    notify_enabled: document.getElementById('notifyEnabled').checked,
    notify_display_seconds: parseInt(document.getElementById('notifyDisplaySeconds').value) || 10,
  })}).then(()=>{
    initLiveGrids(rows, cols);
    buildAppsGrid(); // re-check compatibility after grid change
    initComposeGrid(); // resize compose grid to match new dimensions
    showToast('Settings saved');
    setSettingsDirty(false);
    // Reconnect MQTT if credentials changed
    if(document.getElementById('mqttEnabled').checked){
      fetch('/mqtt_reconnect',{method:'POST'});
    }
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
  const startIdx = parseInt(document.getElementById('atStartIdx').value) || 1;
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
  const next = at.charIndex + 1;
  if(next > 63){
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

document.querySelectorAll('button[onclick="saveGlobal()"]:not(#settingsFab)').forEach(el => el.remove());

const settingsPage = document.getElementById('page-settings');
if(settingsPage){
  settingsPage.addEventListener('input', (e) => {
    if(e.target.closest('.settings-grid')) setSettingsDirty(true);
  });
}

// ============================================================
//  SPORTS TEAM PICKER
// ============================================================
let _sportsState = {};

async function openSportsSettings(){
  document.getElementById('sportsModal').style.display='flex';
  const list = document.getElementById('sportsLeagueList');
  list.innerHTML='<div style="text-align:center;color:#888;padding:20px">Loading leagues…</div>';

  // Fetch fresh settings for display options
  const settingsRes = await fetch('/settings');
  const allSettings = await settingsRes.json();

  try {
    const res = await fetch('/sports_leagues');
    const data = await res.json();
    _sportsState = {};
    list.innerHTML='';

    const filterVal = allSettings.plugin_sports_sports_filter || allSettings.sports_filter || 'all';
    const leagueVal = allSettings.plugin_sports_sports_show_league || allSettings.sports_show_league || 'yes';
    const compactVal = allSettings.plugin_sports_sports_compact || allSettings.sports_compact || 'no';
    const delayVal = allSettings.plugin_sports_loop_delay || allSettings.sports_loop_delay || '5';

    // Display settings at top
    const opts = document.createElement('div');
    opts.style.cssText='display:flex;flex-direction:column;gap:12px;margin-bottom:16px;padding:12px 14px;background:#1a1a1a;border:1px solid var(--border);border-radius:8px';

    // Show filter
    const filterRow = document.createElement('div');
    filterRow.style.cssText='display:flex;align-items:center;gap:8px;font-size:.85rem;color:#ccc';
    filterRow.innerHTML='<span style="min-width:90px">Show</span>';
    filterRow.appendChild(createSegmentedToggleControl({
      id:'sportsFilterSelect',
      options:[
        {value:'all',label:'All'},
        {value:'live',label:'Live'},
        {value:'live+upcoming',label:'Live+Next'},
        {value:'live+final',label:'Live+Final'},
      ],
      value: filterVal, size:'sm'
    }));
    opts.appendChild(filterRow);

    // League name
    const leagueRow = document.createElement('div');
    leagueRow.style.cssText='display:flex;align-items:center;gap:8px;font-size:.85rem;color:#ccc';
    leagueRow.innerHTML='<span style="min-width:90px">League Name</span>';
    leagueRow.appendChild(createSegmentedToggleControl({
      id:'sportsLeagueToggle',
      options:[{value:'yes',label:'Show'},{value:'no',label:'Hide'}],
      value: leagueVal, size:'sm'
    }));
    opts.appendChild(leagueRow);

    // Layout
    const layoutRow = document.createElement('div');
    layoutRow.style.cssText='display:flex;align-items:center;gap:8px;font-size:.85rem;color:#ccc';
    layoutRow.innerHTML='<span style="min-width:90px">Games per page</span>';
    layoutRow.appendChild(createSegmentedToggleControl({
      id:'sportsCompactToggle',
      options:[{value:'no',label:'1'},{value:'yes',label:'2'}],
      value: compactVal, size:'sm'
    }));
    opts.appendChild(layoutRow);

    // Delay stepper
    const delayRow = document.createElement('div');
    delayRow.style.cssText='display:flex;align-items:center;gap:8px;font-size:.85rem;color:#ccc';
    delayRow.innerHTML='<span style="min-width:90px">Delay</span>';
    const delayWrap = document.createElement('span');
    delayWrap.id='sportsDelayStepperWrap';
    delayRow.appendChild(delayWrap);
    delayRow.appendChild(Object.assign(document.createElement('span'),{textContent:' s'}));
    opts.appendChild(delayRow);
    list.appendChild(opts);
    // Build stepper for delay
    const delayInput = document.createElement('input');
    delayInput.type='number'; delayInput.id='sportsDelayInput';
    delayInput.value=delayVal; delayInput.min='2'; delayInput.max='30'; delayInput.step='1';
    delayInput.style.cssText='width:50px;padding:4px;background:#111;color:#fff;border:1px solid #555;border-radius:4px;text-align:center;font-size:.82rem';
    document.getElementById('sportsDelayStepperWrap').appendChild(createNumberStepper(delayInput));

    for(const lg of data.leagues){
      const followed = lg.followed || '';
      _sportsState[lg.key] = {follow_all: followed==='*', teams: new Set(followed==='*'?[]:followed.split(',').filter(t=>t.trim()).map(t=>t.trim().toUpperCase()))};
      const section = document.createElement('div');
      section.className='league-section';
      const count = _sportsState[lg.key].follow_all ? 'ALL' : (_sportsState[lg.key].teams.size || '');
      section.innerHTML=`
        <div class="league-header" onclick="toggleLeague('${lg.key}')">
          <span class="league-name">${lg.name}</span>
          <span class="league-count" id="lcount-${lg.key}">${count}</span>
        </div>
        <div class="league-body" id="lbody-${lg.key}">
          <div class="league-controls">
            <label style="cursor:pointer;display:flex;align-items:center;gap:6px">
              <input type="checkbox" ${_sportsState[lg.key].follow_all?'checked':''} onchange="toggleFollowAll('${lg.key}',this.checked)"> Follow All
            </label>
          </div>
          <div class="team-grid" id="tgrid-${lg.key}"><div style="color:#888;font-size:.8rem">Loading teams…</div></div>
        </div>`;
      list.appendChild(section);
    }
  } catch(e){ list.innerHTML='<div style="color:var(--red);padding:20px">Failed to load</div>'; }
}

function closeSportsSettings(){
  // Save display options
  const filter = document.getElementById('sportsFilterSelect');
  const league = document.getElementById('sportsLeagueToggle');
  const compact = document.getElementById('sportsCompactToggle');
  const delay = document.getElementById('sportsDelayInput');
  if(filter && league && compact){
    const payload = {action:'save_global', sports_filter:filter.value, sports_show_league:league.value, sports_compact:compact.value};
    if(delay) payload.plugin_sports_loop_delay = delay.value;
    fetch('/settings',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)});
  }
  document.getElementById('sportsModal').style.display='none';
}

async function toggleLeague(key){
  const body = document.getElementById(`lbody-${key}`);
  body.classList.toggle('open');
  if(!body.classList.contains('open') || body.dataset.loaded) return;
  const grid = document.getElementById(`tgrid-${key}`);
  const st = _sportsState[key];
  if(key==='pga'||key==='ufc'){
    grid.innerHTML=`<label style="cursor:pointer;display:flex;align-items:center;gap:6px;grid-column:1/-1;font-size:.85rem"><input type="checkbox" ${st.follow_all?'checked':''} onchange="toggleFollowAll('${key}',this.checked)"> Enable ${key.toUpperCase()}</label>`;
  } else {
    grid.innerHTML=`
      <div style="grid-column:1/-1">
        <input type="text" class="line-input" style="font-size:.85rem;margin:0 0 8px 0;text-transform:none" placeholder="Search teams…" oninput="searchTeams('${key}',this.value)" id="tsearch-${key}">
        <div id="tresults-${key}"></div>
        <div id="tfollowed-${key}" style="margin-top:8px"></div>
      </div>`;
    renderFollowedChips(key);
  }
  body.dataset.loaded='1';
}

let _searchTimeout = null;
function searchTeams(league, query){
  clearTimeout(_searchTimeout);
  const results = document.getElementById(`tresults-${league}`);
  if(query.length < 2){ results.innerHTML=''; return; }
  _searchTimeout = setTimeout(async()=>{
    try {
      const res = await fetch(`/sports_teams/${league}?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      results.innerHTML='';
      data.teams.slice(0,12).forEach(t=>{
        const st = _sportsState[league];
        const already = st.follow_all || st.teams.has(t.abbr);
        const chip = document.createElement('div');
        chip.className='team-chip'+(already?' selected':'');
        chip.innerHTML=`<strong>${t.abbr}</strong><br><span style="font-size:.65rem;font-weight:normal">${t.short}</span>`;
        chip.style.padding='8px 4px';
        chip.onclick=()=>{
          if(!already){ st.teams.add(t.abbr); saveSportsFollow(league); updateLeagueCount(league); renderFollowedChips(league); }
          chip.classList.add('selected');
        };
        results.appendChild(chip);
      });
    } catch(e){ results.innerHTML='<span style="color:var(--red);font-size:.8rem">Search failed</span>'; }
  }, 300);
}

function renderFollowedChips(league){
  const el = document.getElementById(`tfollowed-${league}`);
  if(!el) return;
  const st = _sportsState[league];
  if(!st.teams.size && !st.follow_all){ el.innerHTML='<span style="color:#666;font-size:.8rem">No teams followed</span>'; return; }
  el.innerHTML='';
  st.teams.forEach(abbr=>{
    const chip = document.createElement('div');
    chip.className='team-chip selected';
    chip.style.display='inline-flex';chip.style.alignItems='center';chip.style.gap='4px';chip.style.margin='2px';
    chip.innerHTML=`${abbr} <span style="cursor:pointer;opacity:.6" onclick="event.stopPropagation();unfollowTeam('${league}','${abbr}')">✕</span>`;
    el.appendChild(chip);
  });
}

function unfollowTeam(league, abbr){
  _sportsState[league].teams.delete(abbr);
  saveSportsFollow(league);
  updateLeagueCount(league);
  renderFollowedChips(league);
}

function toggleFollowAll(league, checked){
  _sportsState[league].follow_all = checked;
  document.querySelectorAll(`#tgrid-${league} .team-chip`).forEach(c=>c.classList.toggle('selected', checked));
  updateLeagueCount(league);
  saveSportsFollow(league);
}

function updateLeagueCount(league){
  const st = _sportsState[league];
  const el = document.getElementById(`lcount-${league}`);
  if(el) el.textContent = st.follow_all ? 'ALL' : (st.teams.size || '');
}

function saveSportsFollow(league){
  const st = _sportsState[league];
  const teams = st.follow_all ? '*' : Array.from(st.teams).join(',');
  fetch('/sports_follow',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({league, teams})});
}

// ============================================================
//  APP PLAYLISTS
// ============================================================
let appPlaylistEntries = [];
let playlistGridInstances = [];

function renderAppPlaylistEntries(){
  const el = document.getElementById('appPlaylistEntries');
  // Destroy old grid instances
  playlistGridInstances.forEach(g => { if(g) g.destroy(); });
  playlistGridInstances = [];
  if(!appPlaylistEntries.length){
    el.innerHTML='<div style="color:#666;font-style:italic;font-size:.85rem">No entries yet. Add apps or messages below.</div>';
    return;
  }
  el.innerHTML='';
  appPlaylistEntries.forEach((entry,i)=>{
    const row = document.createElement('div');
    row.className='ap-entry';
    const label = entry.type==='app'
      ? `${(APP_LIST.find(a=>a.key===entry.app)||{icon:'📦'}).icon} ${(APP_LIST.find(a=>a.key===entry.app)||{name:entry.app}).name}`
      : null;
    if(entry.type==='compose'){
      row.style.flexDirection='column';
      row.style.alignItems='stretch';
      const header = document.createElement('div');
      header.style.cssText='display:flex;align-items:center;gap:6px;margin-bottom:6px';
      header.innerHTML=`
        <span style="font-size:.75rem;color:#888">📝</span>
        <span style="font-size:.8rem;color:#aaa;flex:1">Message ${i+1}</span>
        <input type="number" class="ap-entry-dur" value="${entry.duration||10}" min="1" max="600" step="1"
          onchange="appPlaylistEntries[${i}].duration=parseInt(this.value)||10" title="Duration (seconds)">
        <span style="font-size:.75rem;color:#888">s</span>
        <button class="ap-entry-btn" onclick="moveAppEntry(${i},-1)" title="Move up">↑</button>
        <button class="ap-entry-btn" onclick="moveAppEntry(${i},1)" title="Move down">↓</button>
        <button class="ap-entry-btn" onclick="removeAppEntry(${i})" title="Remove">✕</button>`;
      row.appendChild(header);
      const gridContainer = document.createElement('div');
      row.appendChild(gridContainer);
      el.appendChild(row);
      const gridInst = createComposeGrid(gridContainer, {
        rows: get_rows(), cols: get_cols(), compact: true,
        initialText: entry.text || '',
        onChange: (text) => { appPlaylistEntries[i].text = text; }
      });
      playlistGridInstances[i] = gridInst;
    } else {
      row.innerHTML=`
        <span class="ap-entry-label">${label}</span>
        <input type="number" class="ap-entry-dur" value="${entry.duration||30}" min="5" max="600" step="5"
          onchange="appPlaylistEntries[${i}].duration=parseInt(this.value)||30" title="Duration (seconds)">
        <span style="font-size:.75rem;color:#888">s</span>
        <button class="ap-entry-btn" onclick="moveAppEntry(${i},-1)" title="Move up">↑</button>
        <button class="ap-entry-btn" onclick="moveAppEntry(${i},1)" title="Move down">↓</button>
        <button class="ap-entry-btn" onclick="removeAppEntry(${i})" title="Remove">✕</button>`;
      el.appendChild(row);
    }
  });
}

function addAppPlaylistEntry(type){
  if(type==='app'){
    // Show a picker
    const modal = document.createElement('div');
    modal.className='modal-overlay';
    modal.style.display='flex';
    modal.innerHTML=`
      <div class="modal-content" style="max-width:400px">
        <h3 style="color:var(--accent);margin-bottom:12px">Add App to Playlist</h3>
        <select id="apPickerSelect" style="width:100%;background:#111;color:#fff;border:1px solid #555;padding:8px;border-radius:4px;font-size:.9rem;margin-bottom:12px">
          ${APP_LIST.map(a=>`<option value="${a.key}">${a.icon} ${a.name}</option>`).join('')}
        </select>
        <label style="font-size:.85rem;color:#aaa;display:flex;align-items:center;gap:6px;margin-bottom:14px">
          Duration <input type="number" id="apPickerDur" value="30" min="5" max="600" step="5"
            style="width:70px;padding:5px;background:#111;color:#fff;border:1px solid #555;border-radius:4px;text-align:center"> seconds
        </label>
        <div style="display:flex;gap:8px">
          <button class="btn btn-success" style="flex:1" onclick="confirmAddApp(this)">Add</button>
          <button class="btn" style="background:#333;color:#aaa;border:1px solid #555" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
        </div>
      </div>`;
    document.body.appendChild(modal);
  } else {
    // Compose entry — add empty and focus
    appPlaylistEntries.push({type:'compose', text:'', duration:10, style:'ltr', speed:15});
    renderAppPlaylistEntries();
  }
}

function confirmAddApp(btn){
  const modal = btn.closest('.modal-overlay');
  const app = document.getElementById('apPickerSelect').value;
  const dur = parseInt(document.getElementById('apPickerDur').value)||30;
  appPlaylistEntries.push({type:'app', app, duration:dur});
  modal.remove();
  renderAppPlaylistEntries();
}

function moveAppEntry(i, dir){
  const j = i+dir;
  if(j<0||j>=appPlaylistEntries.length) return;
  [appPlaylistEntries[i], appPlaylistEntries[j]] = [appPlaylistEntries[j], appPlaylistEntries[i]];
  renderAppPlaylistEntries();
}

function removeAppEntry(i){
  appPlaylistEntries.splice(i,1);
  renderAppPlaylistEntries();
}

function runAppPlaylist(){
  if(!appPlaylistEntries.length){ showToast('Add entries first','warn'); return; }
  const loop = document.getElementById('appPlaylistLoop').checked;
  fetch('/run_app_playlist',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({entries:appPlaylistEntries, loop})});
  showToast('▶ Playlist started');
}

function openSaveAppPlaylist(){
  if(!appPlaylistEntries.length){ showToast('Add entries first','warn'); return; }
  const modal = document.createElement('div');
  modal.className='modal-overlay';
  modal.style.display='flex';
  modal.innerHTML=`
    <div class="modal-content" style="max-width:360px">
      <h3 style="color:var(--accent);margin-bottom:12px">Save Playlist</h3>
      <input type="text" id="saveAppPlaylistName" placeholder="Playlist name…" class="line-input" style="font-size:.9rem;margin-bottom:14px;text-transform:none">
      <div style="display:flex;gap:8px">
        <button class="btn btn-success" style="flex:1" onclick="saveAppPlaylist();this.closest('.modal-overlay').remove()">Save</button>
        <button class="btn" style="background:#333;color:#aaa;border:1px solid #555" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
      </div>
    </div>`;
  document.body.appendChild(modal);
  setTimeout(()=>document.getElementById('saveAppPlaylistName').focus(),50);
}

function saveAppPlaylist(){
  const name = document.getElementById('saveAppPlaylistName').value.trim();
  if(!name){ showToast('Enter a name','warn'); return; }
  if(!appPlaylistEntries.length){ showToast('Add entries first','warn'); return; }
  const loop = document.getElementById('appPlaylistLoop').checked;
  fetch('/app_playlists',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({name, entries:appPlaylistEntries, loop})})
  .then(()=>{ showToast('Playlist saved'); loadSavedAppPlaylists(); });
}

function loadSavedAppPlaylists(){
  fetch('/app_playlists').then(r=>r.json()).then(data=>{
    const el = document.getElementById('savedAppPlaylistList');
    const names = Object.keys(data);
    if(!names.length){ el.innerHTML='<div style="color:#666;font-style:italic;font-size:.85rem">No saved playlists yet.</div>'; return; }
    el.innerHTML='';
    names.forEach(name=>{
      const pl = data[name];
      const count = (pl.entries||[]).length;
      const row = document.createElement('div');
      row.style.cssText='display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid #333';
      row.innerHTML=`
        <span style="flex:1;font-size:.9rem">${name} <span style="color:#888;font-size:.75rem">(${count} items${pl.loop?' · loop':''})</span></span>
        <button class="btn btn-sm" style="background:#333;color:#ccc;border:1px solid #555" onclick="loadAppPlaylist('${name.replace(/'/g,"\\'")}')">Load</button>
        <button class="btn btn-success btn-sm" onclick="runSavedAppPlaylist('${name.replace(/'/g,"\\'")}')">▶ Run</button>
        <button class="btn-del btn-sm" style="padding:4px 8px;border-radius:4px" onclick="deleteAppPlaylist('${name.replace(/'/g,"\\'")}')">✕</button>`;
      el.appendChild(row);
    });
  });
}

function loadAppPlaylist(name){
  fetch('/app_playlists').then(r=>r.json()).then(data=>{
    const pl = data[name];
    if(!pl) return;
    appPlaylistEntries = pl.entries||[];
    document.getElementById('appPlaylistLoop').checked = pl.loop!==false;
    renderAppPlaylistEntries();
    showToast(`Loaded "${name}"`);
  });
}

function runSavedAppPlaylist(name){
  fetch('/app_playlists').then(r=>r.json()).then(data=>{
    const pl = data[name];
    if(!pl) return;
    appPlaylistEntries = pl.entries||[];
    document.getElementById('appPlaylistLoop').checked = pl.loop!==false;
    renderAppPlaylistEntries();
    fetch('/run_app_playlist',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({entries:pl.entries, loop:pl.loop!==false, name})});
    showToast(`▶ "${name}" started`);
  });
}

function deleteAppPlaylist(name){
  if(!confirm(`Delete "${name}"?`)) return;
  fetch(`/app_playlists/${encodeURIComponent(name)}`,{method:'DELETE'})
  .then(()=>{ showToast(`Deleted "${name}"`,'warn'); loadSavedAppPlaylists(); });
}

// ============================================================
//  NETWORK STATUS
// ============================================================
let _networkOnline = true;

function updateNetworkStatus(){
  fetch('/network_status').then(r=>r.json()).then(data=>{
    _networkOnline = data.online;
    const el = document.getElementById('networkIndicator');
    if(!el) return;
    const icon = data.mode==='hotspot' ? 'radio' : (data.online ? 'wifi' : 'wifi-off');
    const color = data.online ? 'var(--green)' : (data.mode==='hotspot' ? 'var(--orange)' : '#555');
    el.innerHTML=`<i data-lucide="${icon}" style="width:14px;height:14px;color:${color}"></i>`;
    el.title = data.mode==='hotspot' ? `Hotspot: ${data.ssid} (${data.ip})` : (data.online ? `WiFi: ${data.ssid} (${data.ip})` : 'Offline');
    // Update settings page network info
    const info = document.getElementById('networkInfo');
    if(info){
      if(data.mode==='hotspot') info.innerHTML=`<strong style="color:var(--orange)">Hotspot mode</strong> — ${data.ssid} @ ${data.ip}`;
      else if(data.online) info.innerHTML=`<strong style="color:var(--green)">Connected</strong> — ${data.ssid} @ ${data.ip}`;
      else info.innerHTML=`<strong style="color:#888">Offline</strong> — no internet`;
    }
    if(typeof lucide!=='undefined') lucide.createIcons();
  }).catch(()=>{});
}
updateNetworkStatus();
setInterval(updateNetworkStatus, 30000);

function scanWifi(){
  const btn = document.getElementById('wifiScanBtn');
  const list = document.getElementById('wifiList');
  btn.disabled=true; btn.textContent='Scanning...';
  list.innerHTML='<div style="color:#888;font-size:.85rem">Scanning...</div>';
  fetch('/wifi_scan').then(r=>r.json()).then(data=>{
    btn.disabled=false; btn.textContent='Scan for Networks';
    if(!data.networks||!data.networks.length){
      list.innerHTML='<div style="color:#888;font-size:.85rem">No networks found</div>';
      return;
    }
    list.innerHTML='';
    data.networks.forEach(n=>{
      const row = document.createElement('div');
      row.style.cssText='display:flex;align-items:center;gap:8px;padding:8px 10px;background:#1a1a1a;border:1px solid var(--border);border-radius:6px;margin-bottom:6px;cursor:pointer';
      const bars = n.signal>75?'▂▄▆█':n.signal>50?'▂▄▆░':n.signal>25?'▂▄░░':'▂░░░';
      row.innerHTML=`
        <span style="flex:1;font-size:.88rem;font-weight:600">${n.ssid}</span>
        <span style="font-size:.7rem;color:#888;font-family:monospace">${bars}</span>
        <span style="font-size:.7rem;color:#666">${n.security?'🔒':''}</span>`;
      row.onclick=()=>connectWifi(n.ssid, !!n.security);
      list.appendChild(row);
    });
  }).catch(()=>{
    btn.disabled=false; btn.textContent='Scan for Networks';
    list.innerHTML='<div style="color:var(--red);font-size:.85rem">Scan failed (requires Pi)</div>';
  });
}

function connectWifi(ssid, needsPassword){
  let password = '';
  if(needsPassword){
    password = prompt(`Enter password for "${ssid}":`);
    if(password===null) return;
  }
  const list = document.getElementById('wifiList');
  list.innerHTML=`<div style="color:#888;font-size:.85rem">Connecting to ${ssid}...</div>`;
  fetch('/wifi_connect',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({ssid, password})})
  .then(r=>r.json()).then(data=>{
    if(data.status==='success'){
      showToast(`Connected to ${ssid}`);
      list.innerHTML=`<div style="color:var(--green);font-size:.85rem">Connected to ${ssid}! Reboot to use this network.</div>`;
      updateNetworkStatus();
    } else {
      showToast(data.message||'Connection failed','error');
      list.innerHTML=`<div style="color:var(--red);font-size:.85rem">${data.message||'Connection failed'}</div>`;
    }
  }).catch(()=>{
    list.innerHTML='<div style="color:var(--red);font-size:.85rem">Connection failed</div>';
  });
}

function saveHotspotConfig(){
  const ssid = document.getElementById('hotspotSsid').value.trim();
  const pass = document.getElementById('hotspotPass').value.trim();
  if(!ssid||!pass||pass.length<8){ showToast('SSID required, password min 8 chars','warn'); return; }
  fetch('/network_config',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({hotspot_ssid:ssid, hotspot_password:pass})})
  .then(()=>showToast('Hotspot config saved'));
}

// ============================================================
//  SOFTWARE UPDATE
// ============================================================
function checkForUpdate(force=false){
  fetch(`/check_update${force?'?force=1':''}`).then(r=>r.json()).then(data=>{
    const badge = document.getElementById('versionBadge');
    const statusEl = document.getElementById('updateStatus');
    const actionsEl = document.getElementById('updateActions');
    const releaseLink = document.getElementById('releaseLink');

    if(badge) badge.textContent = `v${data.current}`;

    if(!statusEl) return;
    if(data.error){
      statusEl.textContent = `v${data.current} — update check failed`;
      return;
    }
    if(data.has_update){
      statusEl.innerHTML = `<strong style="color:var(--green)">Update available: v${data.latest}</strong>${data.release_name ? ` — ${data.release_name}` : ''}`;
      if(actionsEl){ actionsEl.style.display='flex'; }
      if(releaseLink && data.release_url) releaseLink.href = data.release_url;
      if(badge){
        badge.textContent = 'update available';
        badge.style.color='var(--green)';
        badge.onclick = ()=>{ openMenuPage('settings'); setTimeout(()=>{ const el=document.getElementById('softwareUpdateSection'); if(el) el.scrollIntoView({behavior:'smooth'}); },200); };
      }
      if(typeof lucide!=='undefined') lucide.createIcons();
    } else {
      statusEl.textContent = `v${data.current} — up to date`;
      if(actionsEl) actionsEl.style.display='none';
    }
  }).catch(()=>{
    const statusEl = document.getElementById('updateStatus');
    if(statusEl) statusEl.textContent = 'Update check unavailable (offline?)';
  });
}

function applyUpdate(){
  // Show update modal
  const modal = document.getElementById('updateModal');
  const icon = document.getElementById('updateModalIcon');
  const title = document.getElementById('updateModalTitle');
  const msg = document.getElementById('updateModalMsg');
  const spinner = document.getElementById('updateModalSpinner');
  const reloadBtn = document.getElementById('updateModalReloadBtn');
  const closeBtn = document.getElementById('updateModalCloseBtn');
  if(modal){ modal.style.display='flex'; }

  function setStep(iconStr, titleStr, msgStr, showSpinner, showReload, showClose){
    if(icon) icon.textContent=iconStr;
    if(title) title.textContent=titleStr;
    if(msg) msg.textContent=msgStr;
    if(spinner) spinner.style.display=showSpinner?'block':'none';
    if(reloadBtn) reloadBtn.style.display=showReload?'block':'none';
    if(closeBtn) closeBtn.style.display=showClose?'block':'none';
  }

  setStep('⬇️','Downloading update…','Pulling latest from GitHub, please wait.',true,false,false);

  let done = false;

  fetch('/apply_update',{method:'POST'}).then(r=>r.json()).then(data=>{
    if(done) return;
    if(data.status === 'error'){
      setStep('❌','Update failed',data.message||'Unknown error',false,false,true);
      const btn = document.getElementById('applyUpdateBtn');
      if(btn){ btn.disabled=false; btn.innerHTML='<i data-lucide="download" style="width:14px;height:14px"></i> Update Now'; if(typeof lucide!=='undefined') lucide.createIcons(); }
      return;
    }
    const restartMsg = data.needs_install
      ? 'Installing dependencies and restarting… this may take a minute.'
      : 'Restarting server…';
    setStep('🔄','Restarting…',restartMsg,true,false,false);
  }).catch(()=>{
    if(done) return; // poll already completed, don't overwrite
    setStep('🔄','Restarting…','Server is restarting…',true,false,false);
  });

  // Poll until server comes back
  let attempts = 0;
  const poll = setInterval(()=>{
    attempts++;
    fetch('/version').then(r=>r.json()).then(data=>{
      clearInterval(poll);
      done = true;
      setStep('✅','Update complete!',`v${data.version} installed successfully.`,false,true,false);
    }).catch(()=>{
      if(attempts > 90){
        clearInterval(poll);
        setStep('⚠️','Taking longer than expected','The server may still be restarting. Try reloading manually.',false,true,true);
      }
    });
  }, 2000);
}

checkForUpdate();

buildAppsGrid();
loadSavedPlaylists();
loadSavedAppPlaylists();
updatePreview();
if(typeof lucide!=='undefined') lucide.createIcons();
