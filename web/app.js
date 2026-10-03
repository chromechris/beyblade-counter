/* Beytelligence (Beyblade X Counter Picker) - browser UI.
 * Same data and the same matchup model as beycounter/engine.py (kept in sync by hand). */
(() => {
  'use strict';

  const DATA_URLS = ['data/beyblade_x.json', '../beycounter/data/beyblade_x.json'];
  const LS_KEY = 'beycounter.collection';
  const SLOT_ORDER = ['blade', 'lock_chip', 'main_blade', 'assist_blade', 'assist_blade_2', 'ratchet', 'bit'];
  const BEATS = { Attack: 'Stamina', Stamina: 'Defense', Defense: 'Attack' };
  const K = { KO_SCALE: 25, BURST_SCALE: 30, SPIN_SCALE: 20, DASH_WEIGHT: 0.25, WEIGHT_PER_GRAM: 2.0, TYPE_BONUS: 1.1, MARGIN_GAIN: 3.0 };
  const PLACEHOLDER = 'data:image/svg+xml;utf8,' + encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="#f3f4f6"/>' +
    '<circle cx="50" cy="50" r="36" fill="none" stroke="#c7cad3" stroke-width="7"/><circle cx="50" cy="50" r="12" fill="#c7cad3"/></svg>');

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const norm = s => String(s ?? '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const sig = x => 1 / (1 + Math.exp(-x));
  const localImage = n => n ? n.replace(/[^A-Za-z0-9._-]/g, '_') : null;
  const fileCode = m => m.product_code || (m.custom ? 'CUSTOM' : (m.line || 'N/A'));
  const lineOf = m => m.line || 'Hasbro';

  let DB = null;
  let collection = loadCollection();
  const state = { opponent: null, pool: 'all', line: '', type: '', top: 8 };

  // ------------------------------------------------------------------ data
  function buildDb(data) {
    const parts = new Map(data.parts.map(p => [p.id, p]));
    const models = new Map(data.models.map(m => [m.id, { ...m, custom: false }]));
    const db = { meta: data.meta, parts, models, partsList: data.parts, modelsList: [...models.values()], avgs: {} };
    const sums = {};
    for (const p of data.parts) {
      if (p.attack == null) continue;
      for (const key of [`${p.classification}|${p.type || ''}`, `${p.classification}|`]) {
        const a = (sums[key] ||= [0, 0, 0, 0, 0, 0, 0]);
        a[0]++; a[1] += p.attack || 0; a[2] += p.defense || 0; a[3] += p.stamina || 0;
        a[4] += p.dash || 0; a[5] += p.burst_resistance || 0; a[6] += p.weight_g || 0;
      }
    }
    for (const [k, a] of Object.entries(sums)) db.avgs[k] = a.slice(1).map(v => v / a[0]);
    db.max = { attack: 1, defense: 1, stamina: 1, dash: 1, burst_resistance: 1 };
    for (const m of db.modelsList) {
      const t = totals(m, db);
      for (const k of Object.keys(db.max)) db.max[k] = Math.max(db.max[k], t[k]);
    }
    return db;
  }

  function akas(p) {
    return (p.aka || '').split(/<br\s*\/?>|,|\//).map(a => a.replace(/\(.*?\)/g, '').trim()).filter(Boolean);
  }

  function partStats(p, db = DB) {
    if (p.classification === 'Lock Chip') return { a: 0, d: 0, s: 0, da: 0, b: 0, w: p.weight_g ?? 1.7, est: p.weight_g == null };
    const avg = db.avgs[`${p.classification}|${p.type || ''}`] || db.avgs[`${p.classification}|`] || [0, 0, 0, 0, 0, 0];
    const raw = [p.attack, p.defense, p.stamina, p.dash, p.burst_resistance, p.weight_g];
    let est = !!p.estimated;
    const v = raw.map((x, i) => {
      if (x != null) return x;
      if ((i === 3 || i === 4) && p.classification !== 'Bit') return 0;
      est = true;
      return avg[i];
    });
    return { a: v[0], d: v[1], s: v[2], da: v[3], b: v[4], w: v[5], est };
  }

  function totals(m, db = DB) {
    const t = { attack: 0, defense: 0, stamina: 0, dash: 0, burst_resistance: 0, weight_g: 0, estimated: false };
    for (const [slot, pid] of Object.entries(m.parts)) {
      const p = db.parts.get(pid);
      if (!p) continue;
      const s = partStats(p, db);
      t.attack += s.a; t.defense += s.d; t.stamina += s.s; t.weight_g += s.w;
      t.estimated = t.estimated || s.est;
      if (slot === 'bit') { t.dash = s.da; t.burst_resistance = s.b; }
    }
    return t;
  }

  // ---------------------------------------------------------------- engine
  function typeAdvantage(mine, theirs) {
    if (BEATS[mine] === theirs) return 1;
    if (BEATS[theirs] === mine) return -1;
    return 0;
  }

  function pressure(me, them) {
    const ko = (me.attack + K.DASH_WEIGHT * me.dash) - them.defense + K.WEIGHT_PER_GRAM * (me.weight_g - them.weight_g) - 15;
    const burst = me.attack - them.burst_resistance - 25;
    const spin = me.stamina - them.stamina;
    const p = { ko: sig(ko / K.KO_SCALE), burst: sig(burst / K.BURST_SCALE), spin: sig(spin / K.SPIN_SCALE) };
    p.best = Math.max(p.ko, p.burst, p.spin);
    p.bestPath = p.best === p.ko ? 'knock-out' : p.best === p.burst ? 'burst' : 'spin finish';
    p.combined = 0.65 * p.best + 0.35 * (p.ko + p.burst + p.spin) / 3;
    return p;
  }

  function verdictOf(score) {
    if (score >= 70) return 'strong counter';
    if (score >= 55) return 'favourable';
    if (score >= 45) return 'even';
    if (score >= 30) return 'unfavourable';
    return 'bad matchup';
  }

  function evaluate(cand, opp) {
    const ct = totals(cand), ot = totals(opp);
    const off = pressure(ct, ot), thr = pressure(ot, ct);
    const adv = typeAdvantage(cand.type, opp.type);
    const score = Math.round(1000 * sig(K.MARGIN_GAIN * (off.combined - thr.combined) + K.TYPE_BONUS * adv)) / 10;
    const r = { candidate: cand, opponent: opp, ct, ot, off, thr, adv, score, verdict: verdictOf(score) };
    r.explain = explain(r);
    return r;
  }

  const pct = x => `${Math.round(x * 100)}%`;
  const f0 = x => Math.round(x).toString();
  function explain(r) {
    const { ct: c, ot: o, candidate: cm, opponent: om } = r;
    const notes = [];
    if (r.adv > 0) notes.push(`Type advantage: ${cm.type} beats ${om.type} (official type triangle).`);
    else if (r.adv < 0) notes.push(`Type liability: ${om.type} beats ${cm.type} (official type triangle).`);
    else notes.push(`Neutral typing: ${cm.type} vs ${om.type}.`);
    const p = r.off.bestPath;
    if (p === 'knock-out') notes.push(`Attack vector: knock-out - attack ${f0(c.attack)} (+dash ${f0(c.dash)}) vs their defense ${f0(o.defense)}, ${c.weight_g.toFixed(1)} g vs ${o.weight_g.toFixed(1)} g (${pct(r.off.ko)} pressure).`);
    else if (p === 'burst') notes.push(`Attack vector: burst - attack ${f0(c.attack)} vs their burst resistance ${f0(o.burst_resistance)} (${pct(r.off.burst)} pressure).`);
    else notes.push(`Attack vector: spin finish - stamina ${f0(c.stamina)} vs their ${f0(o.stamina)} (${pct(r.off.spin)} pressure).`);
    const t = r.thr.bestPath;
    if (t === 'knock-out') notes.push(`Threat: knock-out - their attack ${f0(o.attack)} vs your defense ${f0(c.defense)} (${pct(r.thr.ko)}).`);
    else if (t === 'burst') notes.push(`Threat: burst - their attack ${f0(o.attack)} vs your burst resistance ${f0(c.burst_resistance)} (${pct(r.thr.burst)}).`);
    else notes.push(`Threat: outspin - their stamina ${f0(o.stamina)} vs your ${f0(c.stamina)} (${pct(r.thr.spin)}).`);
    if (c.estimated || o.estimated) notes.push('Some component stats are unpublished and were estimated from type averages.');
    return notes;
  }

  function rank(opp, pool, top) {
    const out = [];
    for (const c of pool) {
      if (!c.custom && c.id === opp.id) continue;
      out.push(evaluate(c, opp));
    }
    out.sort((a, b) => b.score - a.score || a.candidate.name.localeCompare(b.candidate.name));
    return top ? out.slice(0, top) : out;
  }

  // ------------------------------------------------------------ collection
  function loadCollection() {
    try { const raw = localStorage.getItem(LS_KEY); if (raw) return JSON.parse(raw); } catch (e) { /* private mode */ }
    return { entries: [] };
  }
  function saveCollection() {
    try { localStorage.setItem(LS_KEY, JSON.stringify(collection)); } catch (e) { toast('Could not save (browser storage blocked).'); }
    $('#colCount').textContent = collection.entries.length;
  }
  function collectionModels() {
    return collection.entries
      .map(e => e.model ? DB.models.get(e.model) : (e.custom ? { ...e.custom, custom: true } : null))
      .filter(Boolean);
  }
  const inCollection = id => collectionModels().some(m => m.id === id);
  function addToCollection(m) {
    if (inCollection(m.id)) return false;
    collection.entries.push(m.custom ? { custom: { ...m } } : { model: m.id });
    saveCollection();
    return true;
  }
  function removeFromCollection(id) {
    collection.entries = collection.entries.filter(e => (e.model || (e.custom && e.custom.id)) !== id);
    saveCollection();
  }

  // ---------------------------------------------------------------- search
  function searchModels(text, pool, limit = 12) {
    const t = norm(text);
    if (!t) return [];
    const words = text.toLowerCase().split(/\s+/).map(norm).filter(Boolean);
    const scored = [];
    for (const m of pool) {
      let best = 0;
      for (const n of [m.name, m.hasbro_name || '', ...(m.aliases || []), m.product_code || '']) {
        const nn = norm(n);
        if (!nn) continue;
        if (nn === t) best = Math.max(best, 100);
        else if (nn.startsWith(t)) best = Math.max(best, 80);
        else if (nn.includes(t)) best = Math.max(best, 60);
        else if (words.length && words.every(w => nn.includes(w))) best = Math.max(best, 50);
      }
      if (best) scored.push([best, m]);
    }
    scored.sort((a, b) => b[0] - a[0] || a[1].name.localeCompare(b[1].name));
    return scored.slice(0, limit).map(x => x[1]);
  }

  function attachSearch(input, drop, getPool, onPick) {
    let items = [], sel = -1;
    const render = () => {
      if (!items.length) {
        drop.innerHTML = input.value.trim() ? '<div class="drop-empty">No match. Try part of the name, e.g. "wizard".</div>' : '';
        drop.classList.toggle('hidden', !input.value.trim());
        return;
      }
      drop.innerHTML = items.map((m, i) => `
        <div class="drop-item ${i === sel ? 'sel' : ''}" data-i="${i}">
          <img src="${modelImage(m)}" alt="" loading="lazy" onerror="this.src='${PLACEHOLDER}'">
          <div><div class="n">${esc(m.name)}</div><div class="s">${esc(subtitle(m))}</div></div>
          <span class="type-badge ${m.type.toLowerCase()}" style="margin-left:auto">${m.type}</span>
        </div>`).join('');
      drop.classList.remove('hidden');
    };
    const pick = m => { onPick(m); input.value = ''; items = []; drop.classList.add('hidden'); };
    input.addEventListener('input', () => { items = searchModels(input.value, getPool()); sel = items.length ? 0 : -1; render(); });
    input.addEventListener('focus', () => { if (items.length) drop.classList.remove('hidden'); });
    input.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown') { sel = Math.min(sel + 1, items.length - 1); render(); e.preventDefault(); }
      else if (e.key === 'ArrowUp') { sel = Math.max(sel - 1, 0); render(); e.preventDefault(); }
      else if (e.key === 'Enter') { if (items[sel]) pick(items[sel]); }
      else if (e.key === 'Escape') { drop.classList.add('hidden'); }
    });
    drop.addEventListener('mousedown', e => {
      const it = e.target.closest('.drop-item');
      if (it) { e.preventDefault(); pick(items[+it.dataset.i]); }
    });
    document.addEventListener('click', e => { if (!drop.contains(e.target) && e.target !== input) drop.classList.add('hidden'); });
  }

  // ------------------------------------------------------------- rendering
  function modelImage(m) {
    if (m.image) return 'img/models/' + localImage(m.image);
    for (const slot of ['blade', 'main_blade']) {
      const p = m.parts[slot] && DB.parts.get(m.parts[slot]);
      if (p && p.image) return 'img/parts/' + localImage(p.image);
    }
    return PLACEHOLDER;
  }
  function partImage(p) { return p.image ? 'img/parts/' + localImage(p.image) : PLACEHOLDER; }

  function subtitle(m) {
    const bits = [];
    if (m.hasbro_name && m.hasbro_name !== m.name) bits.push(m.hasbro_name);
    if (m.product_code) bits.push(m.product_code);
    else if (m.custom) bits.push('custom combo');
    return bits.join(' · ');
  }

  function statBars(t, compact = false) {
    const row = (lbl, key, val, max) => `
      <span class="lbl">${lbl}</span>
      <span class="bar ${key}"><i style="width:${Math.min(100, 100 * val / max)}%"></i></span>
      <span class="val">${f0(val)}</span>`;
    return `<div class="stats ${compact ? 'compact' : ''}">
      ${row('Attack', 'attack', t.attack, DB.max.attack)}
      ${row('Defense', 'defense', t.defense, DB.max.defense)}
      ${row('Stamina', 'stamina', t.stamina, DB.max.stamina)}
      ${row('Dash', 'dash', t.dash, DB.max.dash)}
      ${row('Burst', 'burst', t.burst_resistance, DB.max.burst_resistance)}
    </div>
    <div class="weight">${t.weight_g.toFixed(1)} g${t.estimated ? ' <span class="est">· partly estimated</span>' : ''}</div>`;
  }

  const ringColor = v => ({ 'strong counter': 'var(--good)', 'favourable': 'var(--ok)', 'even': 'var(--even)', 'unfavourable': 'var(--poor)', 'bad matchup': 'var(--bad)' }[v]);

  function modelCard(m, opts = {}) {
    const t = totals(m);
    const kind = opts.result ? 'Asset' : m.custom ? 'Custom asset' : 'File';
    return `
      <article class="card" data-id="${esc(m.id)}">
        <div class="file"><span>${kind} // ${esc(lineOf(m))}</span><b>${esc(fileCode(m))}</b></div>
        <div class="photo">
          ${opts.rank ? `<div class="rank">#${opts.rank}</div>` : ''}
          ${opts.removable ? `<button class="remove" data-remove="${esc(m.id)}" title="Remove from arsenal">×</button>`
            : (inCollection(m.id) ? '<span class="owned">In arsenal</span>' : '')}
          <img class="thumb" src="${modelImage(m)}" alt="" loading="lazy" onerror="this.src='${PLACEHOLDER}'">
        </div>
        <div class="body">
          <div class="name">${esc(m.name)}</div>
          <div class="sub">${esc(subtitle(m))}</div>
          <div><span class="type-badge ${m.type.toLowerCase()}">${m.type}</span></div>
          ${opts.result ? `
            <div class="scorebox" style="--c:${ringColor(opts.result.verdict)}">
              <div class="ring" style="--p:${opts.result.score}"><span>${Math.round(opts.result.score)}</span></div>
              <div class="verdict"><span class="stamp">${opts.result.verdict}</span><small>assessment / 100</small></div>
            </div>
            <ul class="why">${opts.result.explain.map(n => `<li>${esc(n)}</li>`).join('')}</ul>`
          : statBars(t, true)}
        </div>
      </article>`;
  }

  function renderOpponent() {
    const box = $('#oppCard');
    const m = state.opponent;
    if (!m) { box.className = 'opp-card empty'; box.innerHTML = '<p><b>Awaiting target.</b> Search for the Beyblade you are facing, or open its file under <b>Dossiers</b>.</p>'; return; }
    const t = totals(m);
    box.className = 'opp-card';
    box.innerHTML = `
      <div class="file"><span>Subject file // ${esc(lineOf(m))}</span><b>${esc(fileCode(m))}</b></div>
      <div class="photo"><img class="hero" src="${modelImage(m)}" alt="" onerror="this.src='${PLACEHOLDER}'"><span class="cls">Classified</span></div>
      <div class="body">
        <div class="name">${esc(m.name)}</div>
        <div class="sub">${esc(subtitle(m))}</div>
        <div style="margin-top:6px"><span class="type-badge ${m.type.toLowerCase()}">${m.type}</span></div>
        <div class="label">Threat profile</div>
        ${statBars(t)}
        <div class="modal-actions">
          <button class="btn" data-detail="${esc(m.id)}">Full dossier</button>
          <button class="btn" id="oppClear">New target</button>
        </div>
      </div>`;
  }

  function renderResults() {
    const box = $('#results');
    if (!state.opponent) { box.innerHTML = '<p class="hint">Identify a target first.</p>'; return; }
    let pool = state.pool === 'mine' ? collectionModels() : DB.modelsList;
    if (state.pool === 'mine' && !pool.length) {
      box.innerHTML = '<p class="hint">Your arsenal is empty. Log the Beyblades you own under <b>My arsenal</b>.</p>';
      return;
    }
    if (state.line) pool = pool.filter(m => (m.line || '') === state.line);
    if (state.type) pool = pool.filter(m => m.type === state.type);
    const ranked = rank(state.opponent, pool, state.pool === 'mine' ? 0 : state.top);
    box.innerHTML = ranked.length ? ranked.map((r, i) => modelCard(r.candidate, { rank: i + 1, result: r })).join('')
      : '<p class="hint">Nothing on file matches these filters.</p>';
  }

  function renderCollection() {
    const ms = collectionModels();
    $('#colCards').innerHTML = ms.length ? ms.map(m => modelCard(m, { removable: true })).join('')
      : '<p class="hint">No assets on file. Use the search box above to log the Beyblades you own, or assemble a custom combo below.</p>';
    $('#colCount').textContent = ms.length;
  }

  function renderBrowse() {
    const q = $('#browseSearch').value, line = $('#browseLine').value, type = $('#browseType').value;
    let ms = q.trim() ? searchModels(q, DB.modelsList, 500)
      : [...DB.modelsList].sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));
    if (line) ms = ms.filter(m => (m.line || '') === line);
    if (type) ms = ms.filter(m => m.type === type);
    $('#browseCount').textContent = `${ms.length} files`;
    $('#browseCards').innerHTML = ms.map(m => modelCard(m)).join('');
  }

  function showModel(m) {
    const t = totals(m);
    const parts = SLOT_ORDER.filter(s => m.parts[s]).map(s => DB.parts.get(m.parts[s])).filter(Boolean);
    const partLine = p => {
      const s = partStats(p);
      if (p.classification === 'Lock Chip') return `${p.weight_g != null ? p.weight_g + ' g' : ''}`;
      const core = `atk ${f0(s.a)} · def ${f0(s.d)} · sta ${f0(s.s)}`;
      const bit = p.classification === 'Bit' ? ` · dash ${f0(s.da)} · burst ${f0(s.b)}` : '';
      return `${core}${bit} · ${s.w.toFixed(1)} g${s.est ? ' (estimated)' : ''}`;
    };
    $('#modalBody').innerHTML = `
      <div class="modal-head"><span>Dossier // ${esc(lineOf(m))}</span><span>${esc(fileCode(m))} · ${esc(m.type)}</span></div>
      <div class="modal-inner">
      <div class="detail">
        <div class="photo"><img class="hero" src="${modelImage(m)}" alt="" onerror="this.src='${PLACEHOLDER}'"></div>
        <div>
          <div class="name">${esc(m.name)}</div>
          <div class="meta">${esc([m.hasbro_name && m.hasbro_name !== m.name ? 'Hasbro: ' + m.hasbro_name : '', m.product_code, m.system, m.spin, m.release_jp ? 'JP release ' + m.release_jp : ''].filter(Boolean).join(' · '))}</div>
          <span class="type-badge ${m.type.toLowerCase()}">${m.type}</span>
          ${m.aliases && m.aliases.length ? `<div class="meta">Also known as: ${esc(m.aliases.join(', '))}</div>` : ''}
          ${statBars(t)}
          <div class="label">Components</div>
          <div class="parts">
            ${parts.map(p => `<div class="part"><img src="${partImage(p)}" alt="" onerror="this.src='${PLACEHOLDER}'">
              <div><div class="pn">${esc(p.classification)}: ${esc(p.name)}${p.type ? ` <span class="type-badge ${p.type.toLowerCase()}">${p.type}</span>` : ''}</div>
              <div class="ps">${esc(partLine(p))}</div></div></div>`).join('')}
          </div>
          <div class="modal-actions">
            <button class="btn primary" data-opponent="${esc(m.id)}">Set as target</button>
            ${inCollection(m.id) ? `<button class="btn danger" data-remove="${esc(m.id)}">Remove from arsenal</button>`
                                 : `<button class="btn" data-add="${esc(m.id)}">Add to arsenal</button>`}
          </div>
        </div>
      </div>
      </div>`;
    $('#modal').classList.remove('hidden');
    $('#modal').dataset.id = m.id;
  }

  function findModel(id) { return DB.models.get(id) || collectionModels().find(m => m.id === id) || null; }

  let toastTimer = null;
  function toast(msg) {
    const t = $('#toast');
    t.textContent = msg; t.classList.remove('hidden');
    clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.add('hidden'), 2200);
  }

  function setOpponent(m) {
    state.opponent = m;
    renderOpponent(); renderResults();
    switchTab('finder');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function switchTab(name) {
    $$('.tab').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
    $$('.tab-panel').forEach(p => p.classList.toggle('active', p.id === 'tab-' + name));
    if (name === 'collection') renderCollection();
    if (name === 'browse') renderBrowse();
    if (name === 'finder') { renderOpponent(); renderResults(); }
  }

  // ------------------------------------------------------- custom builder
  function fillBuilder() {
    const opt = (p, label) => `<option value="${esc(p.id)}">${esc(label || p.name)}</option>`;
    const blades = DB.partsList.filter(p => p.classification === 'Blade').sort((a, b) => a.name.localeCompare(b.name));
    const mains = DB.partsList.filter(p => p.classification === 'Main Blade').sort((a, b) => a.name.localeCompare(b.name));
    $('#cbBlade').innerHTML = `<optgroup label="Blades (BX / UX)">${blades.map(p => opt(p, `${p.name}${p.type ? ' (' + p.type + ')' : ''}`)).join('')}</optgroup>` +
      `<optgroup label="Custom Line main blades (CX)">${mains.map(p => opt(p, `${p.name}${p.type ? ' (' + p.type + ')' : ''}`)).join('')}</optgroup>`;
    const sortedOf = cls => DB.partsList.filter(p => p.classification === cls).sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));
    $('#cbLock').innerHTML = '<option value="">(none)</option>' + sortedOf('Lock Chip').map(p => opt(p)).join('');
    $('#cbAssist').innerHTML = sortedOf('Assist Blade').map(p => opt(p, `${p.name}${p.type ? ' (' + p.type + ')' : ''}`)).join('');
    $('#cbAssist2').innerHTML = '<option value="">(none)</option>' + sortedOf('Assist Blade').map(p => opt(p)).join('');
    $('#cbRatchet').innerHTML = sortedOf('Ratchet').map(p => opt(p)).join('');
    $('#cbBit').innerHTML = sortedOf('Bit').map(p => opt(p, `${p.name} (${akas(p)[0] || '?'}${p.type ? ', ' + p.type : ''})`)).join('');
    $$('#builder select').forEach(s => s.addEventListener('change', previewCustom));
    previewCustom();
  }

  function makeCustom() {
    const head = DB.parts.get($('#cbBlade').value);
    const ratchet = DB.parts.get($('#cbRatchet').value);
    const bit = DB.parts.get($('#cbBit').value);
    if (!head || !ratchet || !bit) return null;
    const parts = {};
    let base;
    if (head.classification === 'Blade') {
      parts.blade = head.id; base = head.name;
    } else {
      const assist = DB.parts.get($('#cbAssist').value);
      const assist2 = DB.parts.get($('#cbAssist2').value);
      const lock = DB.parts.get($('#cbLock').value);
      if (!assist) return null;
      parts.main_blade = head.id; parts.assist_blade = assist.id;
      if (assist2 && assist2.id !== assist.id) parts.assist_blade_2 = assist2.id;
      if (lock) parts.lock_chip = lock.id;
      base = `${lock ? lock.name : ''}${head.name} ${assist.name[0]}${assist2 && assist2.id !== assist.id ? assist2.name[0] : ''}`;
    }
    parts.ratchet = ratchet.id; parts.bit = bit.id;
    let type = bit.type || head.type || 'Balance';
    if (bit.type === 'Balance' && head.type) type = head.type;
    const name = `${base}${base.endsWith(' ') ? '' : ' '}${ratchet.name}${akas(bit)[0] || bit.name}`.replace(/\s+/g, ' ').trim();
    return { id: name, name, type, spin: head.spin, system: head.system, line: 'Custom', product_code: null,
             hasbro_name: null, release_jp: null, parts, aliases: [], source: 'custom combo', image: null, custom: true };
  }

  function previewCustom() {
    const head = DB.parts.get($('#cbBlade').value);
    const cx = head && head.classification === 'Main Blade';
    $('#cbLockWrap').classList.toggle('hidden', !cx);
    $('#cbAssistWrap').classList.toggle('hidden', !cx);
    $('#cbAssist2Wrap').classList.toggle('hidden', !cx);
    const m = makeCustom();
    if (!m) { $('#cbPreview').innerHTML = ''; return; }
    const t = totals(m);
    $('#cbPreview').innerHTML = `<div class="name" style="font-weight:800">${esc(m.name)} <span class="type-badge ${m.type.toLowerCase()}">${m.type}</span></div>${statBars(t)}`;
  }

  // --------------------------------------------------------- import/export
  function exportCollection() {
    const blob = new Blob([JSON.stringify(collection, null, 1)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = 'beytelligence_arsenal.json'; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  function importCollection(file) {
    const rd = new FileReader();
    rd.onload = () => {
      try {
        const data = JSON.parse(rd.result);
        if (!data || !Array.isArray(data.entries)) throw new Error('bad format');
        let added = 0;
        for (const e of data.entries) {
          if (e.model && DB.models.has(e.model) && !inCollection(e.model)) { collection.entries.push({ model: e.model }); added++; }
          else if (e.custom && e.custom.id && !inCollection(e.custom.id)) { collection.entries.push({ custom: e.custom }); added++; }
        }
        saveCollection(); renderCollection();
        toast(`Imported ${added} asset${added === 1 ? '' : 's'}.`);
      } catch (err) { toast('That file is not an arsenal export.'); }
    };
    rd.readAsText(file);
  }

  // ------------------------------------------------------------------ init
  async function loadData() {
    for (const url of DATA_URLS) {
      try {
        const res = await fetch(url);
        if (res.ok) return await res.json();
      } catch (e) { /* try the next location */ }
    }
    throw new Error('database not found');
  }

  // Installable web app: register the service worker (HTTPS, or localhost for testing).
  // Inside the Capacitor app the files are already local, so it is skipped there.
  function setupOffline() {
    const secure = location.protocol === 'https:' || ['localhost', '127.0.0.1'].includes(location.hostname);
    if (!('serviceWorker' in navigator) || !secure || window.Capacitor) return;
    navigator.serviceWorker.addEventListener('message', e => {
      const m = e.data || {};
      if (m.type === 'precache-done' && m.added) toast(`Offline cache secured: ${m.added} photos saved on this device.`);
    });
    navigator.serviceWorker.register('sw.js').then(() => navigator.serviceWorker.ready).then(reg => {
      if (!reg.active || !DB) return;
      const urls = new Set();
      for (const m of DB.modelsList) if (m.image) urls.add(new URL(modelImage(m), location.href).href);
      for (const p of DB.partsList) if (p.image) urls.add(new URL(partImage(p), location.href).href);
      reg.active.postMessage({ type: 'precache-images', urls: [...urls] });
    }).catch(() => {});
  }

  async function init() {
    DB = buildDb(await loadData());
    setupOffline();
    $('#tagline').innerHTML = `<span class="dot"></span>online · ${DB.modelsList.length} subject files · ${DB.partsList.length} component records · source: Takara Tomy / Hasbro`;
    $('#colCount').textContent = collection.entries.length;

    $('#tabs').addEventListener('click', e => { const b = e.target.closest('.tab'); if (b) switchTab(b.dataset.tab); });

    attachSearch($('#oppSearch'), $('#oppDrop'), () => DB.modelsList, setOpponent);
    attachSearch($('#colSearch'), $('#colDrop'), () => DB.modelsList, m => {
      toast(addToCollection(m) ? `Asset logged: ${m.name}` : `${m.name} is already in your arsenal`);
      renderCollection();
    });

    $('#poolSeg').addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return;
      state.pool = b.dataset.pool;
      $$('#poolSeg button').forEach(x => x.classList.toggle('active', x === b));
      renderResults();
    });
    $('#lineFilter').addEventListener('change', e => { state.line = e.target.value; renderResults(); });
    $('#typeFilter').addEventListener('change', e => { state.type = e.target.value; renderResults(); });
    $('#topN').addEventListener('change', e => { state.top = +e.target.value; renderResults(); });

    ['browseSearch', 'browseLine', 'browseType'].forEach(id => $('#' + id).addEventListener('input', renderBrowse));

    // one delegated click handler for cards and buttons everywhere
    document.addEventListener('click', e => {
      const rm = e.target.closest('[data-remove]');
      if (rm) { e.stopPropagation(); const m = findModel(rm.dataset.remove); removeFromCollection(rm.dataset.remove); toast(`Asset removed: ${m ? m.name : ''}`); renderCollection(); renderResults(); $('#modal').classList.add('hidden'); return; }
      const add = e.target.closest('[data-add]');
      if (add) { const m = findModel(add.dataset.add); if (m) { addToCollection(m); toast(`Asset logged: ${m.name}`); showModel(m); renderCollection(); } return; }
      const opp = e.target.closest('[data-opponent]');
      if (opp) { const m = findModel(opp.dataset.opponent); $('#modal').classList.add('hidden'); if (m) setOpponent(m); return; }
      const det = e.target.closest('[data-detail]');
      if (det) { const m = findModel(det.dataset.detail); if (m) showModel(m); return; }
      if (e.target.id === 'oppClear') { state.opponent = null; renderOpponent(); renderResults(); $('#oppSearch').focus(); return; }
      const card = e.target.closest('.card');
      if (card) { const m = findModel(card.dataset.id); if (m) showModel(m); }
    });
    $('#modalClose').addEventListener('click', () => $('#modal').classList.add('hidden'));
    $('#modal').addEventListener('click', e => { if (e.target.id === 'modal') $('#modal').classList.add('hidden'); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') $('#modal').classList.add('hidden'); });

    fillBuilder();
    $('#cbAdd').addEventListener('click', () => {
      const m = makeCustom();
      if (!m) { toast('Pick a blade, ratchet and bit (and an assist blade for Custom Line).'); return; }
      toast(addToCollection(m) ? `Custom asset logged: ${m.name}` : `${m.name} is already in your arsenal`);
      renderCollection();
    });
    $('#exportBtn').addEventListener('click', exportCollection);
    $('#importFile').addEventListener('change', e => { if (e.target.files[0]) importCollection(e.target.files[0]); e.target.value = ''; });
    $('#clearBtn').addEventListener('click', () => {
      if (collection.entries.length && confirm('Wipe every asset from your arsenal?')) { collection.entries = []; saveCollection(); renderCollection(); renderResults(); }
    });

    renderOpponent(); renderResults(); renderCollection();
  }

  init().catch(err => {
    $('#tagline').textContent = 'Uplink failed: could not load the database. Serve the project folder over HTTP (python serve.py) rather than opening the file directly.';
    console.error(err);
  });
})();
