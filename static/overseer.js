/* Project 87 Overseer v5.2 — Frontend Logic */

'use strict';

const P87 = (() => {
  const STALE_THRESHOLD_MS = 120000;
  const POLL_INTERVAL_MS = 30000;
  const ACTIVITY_POLL_MS = 30000;

  let _state = {
    telemetry: null,
    activities: [],
    lastFetchTs: 0,
    consecutiveFails: 0,
    reduceMotion: false,
    selectedWallet: null,
    countdownInterval: null,
    nextCheckTs: null,
    overseerPowered: false,
    authToken: localStorage.getItem('authToken') || null,
    currentWallet: localStorage.getItem('walletAddress') || null,
  };

  // ── Init ─────────────────────────────────────────────────────────────────

  function init() {
    _state.reduceMotion = localStorage.getItem('p87_reduce_motion') === '1';
    _state.selectedWallet = localStorage.getItem('p87_selected_wallet') || null;

    if (_state.reduceMotion) document.body.classList.add('reduce-motion');

    _bindNav();
    _bindSettings();
    _bindWalletSelector();

    if (_state.authToken && _state.currentWallet) {
      // Already authenticated — check if wallet is activated before powering on
      _checkAuthAndPower();
    } else {
      _setPowered(false);
      _showModal();
    }

    setInterval(fetchTelemetry, POLL_INTERVAL_MS);
    setInterval(fetchActivity, ACTIVITY_POLL_MS);
    setInterval(_updateCountdowns, 1000);
  }

  // Check activation status then decide whether to power on automatically
  function _checkAuthAndPower() {
    fetch('/api/wallet/activation-status', {
      headers: { 'X-Auth-Token': _state.authToken || '', 'Content-Type': 'application/json' }
    })
      .then(function(r) {
        if (r.status === 401) { _setPowered(false); _showModal(); return null; }
        return r.json();
      })
      .then(function(data) {
        if (!data) return;
        if (data.activated) {
          _setPowered(true);
          _hideModal();
          fetchTelemetry();
          fetchActivity();
        } else {
          // Connected but not yet activated — show modal at signer phase
          _setPowered(false);
          _showModal();
          // Tell the modal UI to skip to signer phase
          if (typeof cmShowPhase === 'function') {
            cmShowPhase('signer');
            if (_state.currentWallet && typeof cmScanWbtcBalance === 'function') {
              cmScanWbtcBalance(_state.currentWallet);
            }
          }
        }
      })
      .catch(function() {
        _setPowered(false);
        _showModal();
      });
  }

  // ── Power state ──────────────────────────────────────────────────────────

  function _setPowered(on) {
    _state.overseerPowered = on;
    if (on) {
      document.body.classList.remove('overseer--awaiting-wallet');
    } else {
      document.body.classList.add('overseer--awaiting-wallet');
      _renderPoweredDownStrip();
    }
  }

  function _renderPoweredDownStrip() {
    _setText('strip-hf', 'HF: —');
    _setText('strip-eth', 'ETH: —');
    _setText('strip-countdown', 'T-MINUS: ----');
    _setText('strip-status', 'AWAITING CONNECT');
    _updateWalletBadge();
  }

  function _updateWalletBadge() {
    const badge = document.getElementById('strip-wallet-badge');
    if (!badge) return;
    if (_state.currentWallet) {
      badge.textContent = _state.currentWallet.slice(0,6) + '…' + _state.currentWallet.slice(-4);
    } else {
      badge.textContent = 'NO WALLET';
    }
  }

  function _showModal() {
    const modal = document.getElementById('connect-modal');
    if (modal) modal.classList.add('visible');
  }

  function _hideModal() {
    const modal = document.getElementById('connect-modal');
    if (modal) modal.classList.remove('visible');
  }

  // ── Navigation ───────────────────────────────────────────────────────────

  function _bindNav() {
    document.getElementById('nav-home')?.addEventListener('click', () => {
      _closeAllOverlays();
      _scrollToDome(0);
    });
    document.getElementById('nav-domes')?.addEventListener('click', () => {
      _closeAllOverlays();
      _toggleOverlay('hex-overlay');
    });
    document.getElementById('nav-activity')?.addEventListener('click', () => {
      _closeAllOverlays();
      _toggleOverlay('activity-overlay');
      _renderActivityOverlay();
    });
    document.getElementById('nav-settings')?.addEventListener('click', () => {
      _closeAllOverlays();
      _toggleOverlay('settings-overlay');
    });

    document.querySelectorAll('.dome-section').forEach((sec, i) => {
      sec.addEventListener('click', e => {
        if (e.target.closest('.dome-shell')) return;
      });
    });
  }

  function _scrollToDome(index) {
    const sections = document.querySelectorAll('.dome-section');
    if (sections[index]) {
      sections[index].scrollIntoView({ behavior: 'smooth' });
    }
    _updateNavActive(index);
  }

  function _updateNavActive(index) {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('nav-home')?.classList.add('active');
  }

  function _toggleOverlay(id) {
    const el = document.getElementById(id);
    if (!el) return;
    const isActive = el.classList.contains('active');
    _closeAllOverlays();
    if (!isActive) el.classList.add('active');
  }

  function _closeAllOverlays() {
    document.querySelectorAll('.overlay').forEach(o => o.classList.remove('active'));
  }

  // ── Settings ─────────────────────────────────────────────────────────────

  function _bindSettings() {
    const toggle = document.getElementById('reduce-motion-toggle');
    if (!toggle) return;
    toggle.classList.toggle('on', _state.reduceMotion);
    toggle.addEventListener('click', () => {
      _state.reduceMotion = !_state.reduceMotion;
      localStorage.setItem('p87_reduce_motion', _state.reduceMotion ? '1' : '0');
      toggle.classList.toggle('on', _state.reduceMotion);
      document.body.classList.toggle('reduce-motion', _state.reduceMotion);
    });
  }

  // ── Wallet selector ───────────────────────────────────────────────────────

  function _bindWalletSelector() {
    const sel = document.getElementById('wallet-selector');
    if (!sel) return;
    sel.addEventListener('change', () => {
      _state.selectedWallet = sel.value || null;
      localStorage.setItem('p87_selected_wallet', _state.selectedWallet || '');
      if (_state.overseerPowered) {
        fetchTelemetry();
        fetchActivity();
      }
    });
  }

  function _populateWalletSelector(wallets) {
    const sel = document.getElementById('wallet-selector');
    if (!sel || !wallets || !wallets.length) return;
    const current = _state.selectedWallet;
    sel.innerHTML = wallets.map(w =>
      `<option value="${w.wallet_address}" ${w.wallet_address === current ? 'selected' : ''}>
        ${w.wallet_address.slice(0,6)}…${w.wallet_address.slice(-4)}
       </option>`
    ).join('');
    if (!current) {
      _state.selectedWallet = wallets[0].wallet_address;
      localStorage.setItem('p87_selected_wallet', _state.selectedWallet);
    }
  }

  // ── Data fetching ─────────────────────────────────────────────────────────

  function fetchTelemetry() {
    if (!_state.overseerPowered) return;
    const qs = _state.selectedWallet ? `?wallet=${_state.selectedWallet}` : '';
    const headers = {};
    if (_state.authToken) headers['X-Auth-Token'] = _state.authToken;

    fetch(`/api/telemetry${qs}`, { headers })
      .then(r => r.json())
      .then(data => {
        _state.telemetry = data;
        _state.lastFetchTs = Date.now();
        _state.consecutiveFails = 0;
        _populateWalletSelector(data.wallets || []);
        const wallet = (data.wallets || [])[0] || {};
        _state.nextCheckTs = data.next_system_check_timestamp
          ? new Date(data.next_system_check_timestamp).getTime()
          : null;
        _render(wallet, data);
        _checkStale(data.last_updated_at);
      })
      .catch(() => {
        _state.consecutiveFails++;
        if (_state.consecutiveFails >= 2) _showStaleDomes();
      });
  }

  function fetchActivity() {
    if (!_state.overseerPowered) return;
    const qs = _state.selectedWallet
      ? `?wallet=${_state.selectedWallet}&limit=10`
      : '?limit=10';
    const headers = {};
    if (_state.authToken) headers['X-Auth-Token'] = _state.authToken;

    fetch(`/api/activity${qs}`, { headers })
      .then(r => r.json())
      .then(data => {
        _state.activities = data.activities || [];
        _renderActivityFeed();
      })
      .catch(() => {});
  }

  // ── Stale data ────────────────────────────────────────────────────────────

  function _checkStale(lastUpdatedAt) {
    if (!lastUpdatedAt) return;
    const ageMs = Date.now() - new Date(lastUpdatedAt).getTime();
    const banner = document.getElementById('stale-banner');
    if (ageMs > STALE_THRESHOLD_MS) {
      if (banner) banner.style.display = 'block';
      _showStaleDomes();
    } else {
      if (banner) banner.style.display = 'none';
      document.querySelectorAll('.dome-shell').forEach(d => d.classList.remove('dome-stale'));
    }
  }

  function _showStaleDomes() {
    document.getElementById('stale-banner').style.display = 'block';
    document.querySelectorAll('.dome-shell').forEach(d => d.classList.add('dome-stale'));
    _setText('d3-countdown', 'T-MINUS --:--');
  }

  // ── Main render ───────────────────────────────────────────────────────────

  function _render(wallet, fullData) {
    _renderDome1(wallet);
    _renderDome2(wallet);
    _renderDome3(fullData);
    _renderDome4(wallet);
    _renderDome5(fullData);
    _renderStripHeader(wallet, fullData);
    _renderHexOverlay(wallet, fullData);
    _checkBeamTriggers(wallet, fullData, _state.activities);
  }

  // ── Dome 1: Safety ────────────────────────────────────────────────────────

  function _renderDome1(w) {
    const hfNull = w.health_factor == null;
    const hf = hfNull ? 0 : w.health_factor;
    const shield = w.shield_status || 'DOWN';
    const strategy = (w.strategy_label || 'IDLE').toLowerCase();
    const pathMin = w.path_min_hf || 3.40;

    _setText('d1-hf', hfNull ? '--' : hf.toFixed(2));
    const collNull = w.collateral_usd == null || w.debt_usd == null;
    _setText('d1-collateral', collNull ? '$-- / $--' : `$${_fmt(w.collateral_usd)} / $${_fmt(w.debt_usd)}`);
    _setStrategyBadge('d1-strategy-badge', w.strategy_label || 'IDLE');
    _setShieldIndicator('d1-shield', shield);

    const ring = document.getElementById('d1-ring-fill');
    if (ring) {
      const pct = Math.min(hf / 6.0, 1.0);
      const circ = 2 * Math.PI * 90;
      ring.style.strokeDasharray = circ;
      ring.style.strokeDashoffset = circ * (1 - pct);

      const green_thresh = pathMin + 0.5;
      if (hf >= green_thresh) {
        ring.classList.remove('amber', 'red');
      } else if (hf >= pathMin) {
        ring.classList.remove('red');
        ring.classList.add('amber');
      } else {
        ring.classList.remove('amber');
        ring.classList.add('red');
        if (!_state.reduceMotion) ring.classList.add('pulse-red');
      }
    }

    const shell = document.getElementById('d1-shell');
    if (shell) {
      shell.className = 'dome-shell';
      if (shield === 'DOWN') shell.classList.add('shield-down');
      else if (shield === 'AWARE') shell.classList.add('shield-aware');
    }
  }

  function _setShieldIndicator(id, status) {
    const el = document.getElementById(id);
    if (!el) return;
    const cls = status === 'ACTIVE' ? 'active' : status === 'AWARE' ? 'aware' : 'down';
    el.className = `shield-indicator ${cls}`;
    const textEl = el.querySelector('.shield-text');
    if (textEl) textEl.textContent = `SHIELD: ${status}`;
  }

  function _setStrategyBadge(id, label) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = label;
    el.className = 'strategy-badge ' + (label || 'idle').toLowerCase();
  }

  // ── Dome 2: USDC Reactor ──────────────────────────────────────────────────

  function _renderDome2(w) {
    const usdc = w.user_usdc_balance || 0;
    const earned = w.usdc_earned_last_24h || 0;
    const repaid = w.usdc_repaid_last_24h || 0;

    _setText('d2-usdc', `$${usdc.toFixed(2)}`);
    _setText('d2-earned', `+$${earned.toFixed(2)} earned`);
    _setText('d2-repaid', `-$${repaid.toFixed(2)} repaid`);

    const tankFill = document.getElementById('d2-tank-fill');
    if (tankFill) {
      const pct = Math.min(usdc / 100.0, 1.0);
      const maxH = 80;
      const fillH = pct * maxH;
      const fillY = 8 + (maxH - fillH);
      tankFill.setAttribute('y', fillY);
      tankFill.setAttribute('height', fillH);
      tankFill.setAttribute('fill', usdc > 50 ? '#00e5ff' : usdc > 20 ? '#ffb000' : '#ff2020');
    }

    const earnedFill = document.getElementById('d2-earned-bar');
    if (earnedFill) earnedFill.style.width = `${Math.min(earned / 3.60 * 100, 100)}%`;

    const repaidFill = document.getElementById('d2-repaid-bar');
    if (repaidFill) repaidFill.style.width = `${Math.min(repaid / 3.60 * 100, 100)}%`;

    _renderYieldSpread(w);
  }

  function _renderYieldSpread(w) {
    const bc = w.borrow_cost_apy_pct;
    const ey = w.engine_yield_apy_pct_7d;
    const nev = w.net_economic_velocity_pct;
    const sep = '<span class="yield-spread-sep"> | </span>';

    const bcStr = bc != null ? `Borrow Cost: ${bc.toFixed(2)}%` : `Borrow Cost: N/A`;
    const eyStr = ey != null ? `Engine Yield: +${ey.toFixed(2)}%` : `Engine Yield: N/A`;

    let nevStr;
    if (nev === null || nev === undefined) {
      nevStr = `<span class="nev-null">NET PROFITABILITY: N/A</span>`;
    } else if (nev > 0) {
      nevStr = `<span class="nev-positive">NET PROFITABILITY: +${nev.toFixed(2)}%</span>`;
    } else {
      nevStr = `<span class="nev-negative">NON-PROFITABLE: ${nev.toFixed(2)}%</span>`;
    }

    const el = document.getElementById('d2-yield-spread');
    if (el) el.innerHTML = `${bcStr}${sep}${eyStr}${sep}${nevStr}`;
  }

  // ── Dome 3: Mission Time ──────────────────────────────────────────────────

  function _renderDome3(data) {
    if (!_state.nextCheckTs) {
      _setText('d3-countdown', 'T-MINUS --:--');
    }

    const nextRepay = data.next_repay_military_time;
    const nextNurse = data.next_nurse_timestamp;
    _setText('d3-next-repay', nextRepay ? `REPAY: ${nextRepay}` : 'REPAY: --');
    _setText('d3-next-nurse', nextNurse ? `NURSE: ${new Date(nextNurse).toLocaleTimeString('en-US', {hour:'2-digit', minute:'2-digit'})}` : 'NURSE: --');

    _renderMilestones(data.wallets && data.wallets[0] ? data.wallets[0].milestones : []);
    _renderArcs(data);
  }

  function _renderArcs(data) {
    const now = Date.now();
    const intervals = { core: 27 * 60000, repay: 240 * 60000, nurse: 70 * 60000 };
    const arcIds = { core: 'd3-arc-core', repay: 'd3-arc-repay', nurse: 'd3-arc-nurse' };
    const nextTimes = {
      core: data.next_system_check_timestamp ? new Date(data.next_system_check_timestamp).getTime() : null,
      repay: null,
      nurse: data.next_nurse_timestamp ? new Date(data.next_nurse_timestamp).getTime() : null,
    };

    Object.entries(arcIds).forEach(([key, arcId]) => {
      const arc = document.getElementById(arcId);
      if (!arc) return;
      const interval = intervals[key];
      const nextTime = nextTimes[key];
      let pct = 0;
      if (nextTime) {
        const elapsed = interval - (nextTime - now);
        pct = Math.max(0, Math.min(elapsed / interval, 1.0));
      }
      const r = parseInt(arc.getAttribute('data-r') || '70');
      const circ = 2 * Math.PI * r;
      arc.style.strokeDasharray = circ;
      arc.style.strokeDashoffset = circ * (1 - pct);
      const remaining = nextTime ? (nextTime - now) / 1000 : Infinity;
      arc.style.stroke = remaining < 30 && !_state.reduceMotion ? '#ffb000' : '';
    });
  }

  function _renderMilestones(milestones) {
    if (!milestones || !milestones.length) return;
    milestones.slice(0, 3).forEach((m, i) => {
      const el = document.getElementById(`d3-milestone-${i}`);
      if (!el) return;
      const pct = parseFloat(m.percentage_complete || 0).toFixed(1);
      const target = parseFloat(m.target_usdc || 0);
      el.innerHTML = `$${_formatK(target)} — <span class="milestone-pct">${pct}%</span> complete`;
    });
  }

  // ── Dome 4: Strategy Sentiment ────────────────────────────────────────────

  function _renderDome4(w) {
    const pct = w.growth_likelihood_pct || 50;
    const label = pct >= 70 ? 'BULLISH' : pct >= 30 ? 'NEUTRAL' : 'BEARISH';
    const cls = pct >= 70 ? 'bullish' : pct >= 30 ? 'neutral' : 'bearish';

    _setText('d4-likelihood-pct', `${pct.toFixed(0)}%`);
    _setText('d4-sentiment-label', label);

    const fill = document.getElementById('d4-likelihood-fill');
    if (fill) {
      fill.style.width = `${pct}%`;
      fill.className = `likelihood-fill ${cls}`;
    }

    _renderActivityFeed();
  }

  function _renderActivityFeed() {
    const feed = document.getElementById('d4-activity-feed');
    if (!feed) return;
    feed.innerHTML = _state.activities.slice(0, 10).map(a => {
      const ts = a.created_at ? new Date(a.created_at).toLocaleTimeString('en-US', {hour:'2-digit', minute:'2-digit', second:'2-digit'}) : '';
      const summary = a.details_summary || a.action_type || '';
      const severityCls = a.severity || 'info';
      const shieldTagged = summary.startsWith('[SHIELD DEPLOYED]')
        ? summary.replace('[SHIELD DEPLOYED]', `<span class="shield-tag">[SHIELD DEPLOYED]</span>`)
        : summary;
      return `<div class="feed-row ${severityCls}">[${ts}] ${a.action_type} — ${shieldTagged}</div>`;
    }).join('');
  }

  // ── Dome 5: Operator Bay ──────────────────────────────────────────────────

  function _renderDome5(data) {
    const op = data.operator_wallet || {};
    const ethBal = op.eth_balance || 0;
    const gasReserve = op.gas_reserve_eth || 1.0;
    const ratio = ethBal / gasReserve;

    const statusLabel = ratio >= 1.0 ? 'FUEL: OK' : ratio >= 0.5 ? 'FUEL: LOW' : 'FUEL: CRITICAL';
    const statusCls = ratio >= 1.0 ? 'ok' : ratio >= 0.5 ? 'low' : 'critical';

    _setText('d5-eth-balance', `${ethBal.toFixed(4)} ETH`);
    const statusEl = document.getElementById('d5-gauge-status');
    if (statusEl) { statusEl.textContent = statusLabel; statusEl.className = `gauge-status ${statusCls}`; }

    const pointer = document.getElementById('d5-gauge-pointer');
    if (pointer) {
      const angle = Math.min(ratio, 2.0) * 90;
      pointer.style.transform = `rotate(${angle}deg)`;
    }

    const arcFill = document.getElementById('d5-gauge-arc');
    if (arcFill) {
      const r = 60;
      const circ = Math.PI * r;
      arcFill.style.strokeDasharray = circ;
      arcFill.style.strokeDashoffset = circ * (1 - Math.min(ratio / 2.0, 1.0));
      arcFill.style.stroke = ratio >= 1.0 ? '#00ff88' : ratio >= 0.5 ? '#ffb000' : '#ff2020';
    }

    const lastNurse = op.last_nurse_at;
    const nurseEl = document.getElementById('d5-nurse-row');
    if (nurseEl && lastNurse) {
      const nurseTime = new Date(lastNurse).toLocaleTimeString('en-US', {hour:'2-digit', minute:'2-digit'});
      nurseEl.textContent = `Last sweep: ${nurseTime}`;
    }
  }

  // ── Countdowns ────────────────────────────────────────────────────────────

  function _updateCountdowns() {
    if (!_state.overseerPowered) return;

    const ageMs = Date.now() - _state.lastFetchTs;
    const isStale = _state.lastFetchTs > 0 && ageMs > STALE_THRESHOLD_MS;

    if (isStale) {
      _setText('d3-countdown', 'T-MINUS --:--');
      _setText('strip-countdown', 'T---:--');
      return;
    }

    if (!_state.nextCheckTs) return;

    const remaining = Math.max(0, Math.floor((_state.nextCheckTs - Date.now()) / 1000));
    const mm = String(Math.floor(remaining / 60)).padStart(2, '0');
    const ss = String(remaining % 60).padStart(2, '0');
    const countStr = `T-MINUS ${mm}:${ss}`;
    _setText('d3-countdown', countStr);
    _setText('strip-countdown', `T-${mm}:${ss}`);
  }

  // ── Top strip ─────────────────────────────────────────────────────────────

  function _renderStripHeader(wallet, data) {
    const hfNull = wallet.health_factor == null;
    const hf = hfNull ? 0 : wallet.health_factor;
    _setText('strip-hf', hfNull ? 'HF: --' : `HF: ${hf.toFixed(2)}`);
    const ethBal = data.operator_wallet ? data.operator_wallet.eth_balance || 0 : 0;
    const ethStatus = ethBal >= 1.0 ? 'ETH: OK' : ethBal >= 0.5 ? 'ETH: LOW' : 'ETH: CRIT';
    _setText('strip-eth', ethStatus);

    const shield = wallet.shield_status || 'DOWN';
    _setText('strip-status', `SHIELD: ${shield}`);
    const statusEl = document.getElementById('strip-status');
    if (statusEl) {
      statusEl.style.color = shield === 'ACTIVE' ? '#00ff88' : shield === 'AWARE' ? '#ffb000' : '#ff2020';
    }

    _updateWalletBadge();
  }

  // ── Hex overview ──────────────────────────────────────────────────────────

  function _renderHexOverlay(wallet, data) {
    const domes = [
      { name: 'SAFETY', metric: `HF ${(wallet.health_factor || 0).toFixed(2)}`, status: _hfStatus(wallet.health_factor || 0, wallet.path_min_hf || 3.40), dome: 0 },
      { name: 'REACTOR', metric: `$${(wallet.user_usdc_balance || 0).toFixed(2)}`, status: 'ok', dome: 1 },
      { name: 'MISSION', metric: 'T-TIME', status: 'ok', dome: 2 },
      { name: 'SENTIMENT', metric: `${(wallet.growth_likelihood_pct || 50).toFixed(0)}%`, status: _sentimentStatus(wallet.growth_likelihood_pct || 50), dome: 3 },
      { name: 'OPERATOR', metric: `${(data.operator_wallet?.eth_balance || 0).toFixed(3)}E`, status: _ethStatus(data.operator_wallet?.eth_balance || 0), dome: 4 },
    ];

    const row1 = document.getElementById('hex-row-1');
    const row2 = document.getElementById('hex-row-2');
    const row3 = document.getElementById('hex-row-3');
    if (!row1) return;

    const makeHex = (d) => `
      <div class="hex-cell" data-dome="${d.dome}">
        <div class="hex-name">${d.name}</div>
        <div class="hex-metric">${d.metric}</div>
        <div class="hex-dot ${d.status}"></div>
      </div>`;

    row1.innerHTML = makeHex(domes[0]) + makeHex(domes[1]);
    row2.innerHTML = makeHex(domes[2]);
    row3.innerHTML = makeHex(domes[3]) + makeHex(domes[4]);

    document.querySelectorAll('.hex-cell').forEach(cell => {
      cell.addEventListener('click', () => {
        const domeIdx = parseInt(cell.dataset.dome || 0);
        _closeAllOverlays();
        _scrollToDome(domeIdx);
      });
    });
  }

  // ── Activity overlay ──────────────────────────────────────────────────────

  function _renderActivityOverlay() {
    const qs = _state.selectedWallet ? `?wallet=${_state.selectedWallet}&limit=50` : '?limit=50';
    const headers = {};
    if (_state.authToken) headers['X-Auth-Token'] = _state.authToken;
    fetch(`/api/activity${qs}`, { headers })
      .then(r => r.json())
      .then(data => {
        const list = document.getElementById('activity-overlay-list');
        if (!list) return;
        const acts = data.activities || [];
        list.innerHTML = acts.map(a => {
          const ts = a.created_at ? new Date(a.created_at).toLocaleString() : '';
          const summary = a.details_summary || a.action_type || '';
          const shieldTagged = summary.startsWith('[SHIELD DEPLOYED]')
            ? summary.replace('[SHIELD DEPLOYED]', `<span class="shield-tag">[SHIELD DEPLOYED]</span>`)
            : summary;
          return `
            <div class="activity-item">
              <div class="activity-item-header">
                <span class="sev-dot ${a.severity || 'info'}"></span>
                <span class="action-type">${a.action_type}</span>
                <span class="timestamp">${ts}</span>
              </div>
              <div class="summary">${shieldTagged}</div>
            </div>`;
        }).join('');
      })
      .catch(() => {});
  }

  // ── T016: Cross-dome data beams ───────────────────────────────────────────

  let _beamSvg = null;
  let _prevActivities = [];
  let _prevLikelihoodPct = 50;
  let _prevMilestonePcts = [];

  function _getBeamSvg() {
    if (_beamSvg) return _beamSvg;
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('id', 'beam-overlay');
    svg.style.cssText = 'position:fixed;inset:0;width:100%;height:100%;pointer-events:none;z-index:90;overflow:visible;';
    document.body.appendChild(svg);
    _beamSvg = svg;
    return svg;
  }

  function _getDomeCollarCenter(domeId) {
    const scroll = document.getElementById('dome-scroll');
    const shell = document.querySelector(`#${domeId} .dome-shell`);
    if (!shell || !scroll) return null;
    const r = shell.getBoundingClientRect();
    return {
      x: r.left + r.width / 2,
      y: r.bottom - 6
    };
  }

  function _fireBeam(fromDomeId, toDomeId, strokeColor, duration) {
    if (_state.reduceMotion) return;
    const svg = _getBeamSvg();
    const from = _getDomeCollarCenter(fromDomeId);
    const to = _getDomeCollarCenter(toDomeId);
    if (!from || !to) return;

    const cx1 = from.x + (to.x - from.x) * 0.25;
    const cy1 = from.y + 40;
    const cx2 = from.x + (to.x - from.x) * 0.75;
    const cy2 = to.y + 40;
    const d = `M${from.x},${from.y} C${cx1},${cy1} ${cx2},${cy2} ${to.x},${to.y}`;

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', d);
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', strokeColor);
    path.setAttribute('stroke-width', '1.5');
    path.setAttribute('stroke-linecap', 'round');
    path.setAttribute('stroke-opacity', '0.7');

    const pathLen = 500;
    const dashLen = 8;
    const gapLen = 12;
    path.style.strokeDasharray = `${dashLen} ${gapLen}`;
    path.style.strokeDashoffset = pathLen;
    path.style.transition = `stroke-dashoffset ${duration}ms linear`;

    svg.appendChild(path);

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        path.style.strokeDashoffset = -pathLen;
      });
    });

    setTimeout(() => {
      if (svg.contains(path)) svg.removeChild(path);
    }, duration + 200);
  }

  function _checkBeamTriggers(wallet, data, activities) {
    if (_state.reduceMotion) return;

    if (!_prevActivities.length && activities.length) {
      _prevActivities = activities.map(a => a.id);
    }

    const newActivities = activities.filter(a => !_prevActivities.includes(a.id));
    _prevActivities = activities.map(a => a.id);

    for (const act of newActivities) {
      if (act.action_type === 'REPAY_EXECUTED') {
        _fireBeam('dome-2', 'dome-1', '#00e5ff', 800);
      }
      if (act.action_type === 'NURSE_SWEEP_COMPLETE' || act.action_type === 'NURSE_SWEEP') {
        _fireBeam('dome-5', 'dome-1', '#00ff88', 900);
      }
    }

    const milestones = wallet.milestones || [];
    const currentPcts = milestones.map(m => parseFloat(m.percentage_complete || 0));
    if (_prevMilestonePcts.length) {
      for (let i = 0; i < currentPcts.length; i++) {
        const prev = _prevMilestonePcts[i] || 0;
        const cur = currentPcts[i];
        if (Math.floor(cur / 10) > Math.floor(prev / 10)) {
          _fireBeam('dome-2', 'dome-3', '#ffb000', 700);
          break;
        }
      }
    }
    _prevMilestonePcts = currentPcts;

    const likelihood = wallet.growth_likelihood_pct || 50;
    if (_prevLikelihoodPct < 70 && likelihood >= 70) {
      _fireBeam('dome-4', 'dome-3', '#00ff88', 750);
    }
    _prevLikelihoodPct = likelihood;
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  function _setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function _fmt(val) {
    if (val == null) return '--';
    return parseFloat(val).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
  }

  function _formatK(val) {
    if (val >= 1000) return (val / 1000).toFixed(0) + 'K';
    return val.toFixed(0);
  }

  function _hfStatus(hf, pathMin) {
    if (hf < 3.20) return 'critical';
    if (hf < pathMin) return 'warning';
    return 'ok';
  }

  function _sentimentStatus(pct) {
    return pct >= 70 ? 'ok' : pct >= 30 ? 'warning' : 'critical';
  }

  function _ethStatus(eth) {
    return eth >= 1.0 ? 'ok' : eth >= 0.5 ? 'warning' : 'critical';
  }

  // ── Public API ────────────────────────────────────────────────────────────

  /**
   * Called by the auth bridge (overseer.html inline script) after a successful
   * /api/auth/wallet response. Stores credentials in state + localStorage.
   */
  function onWalletConnected(token, wallet) {
    _state.authToken = token;
    _state.currentWallet = wallet;
    _state.selectedWallet = wallet;
    localStorage.setItem('authToken', token);
    localStorage.setItem('walletAddress', wallet);
    localStorage.setItem('p87_selected_wallet', wallet);
    _updateWalletBadge();
  }

  /**
   * Called once the user clicks "LAUNCH OVERSEER" (after activation confirmed).
   * Powers on the domes, hides the modal, starts telemetry polling.
   */
  function powerOn() {
    _setPowered(true);
    _hideModal();
    fetchTelemetry();
    fetchActivity();
  }

  /**
   * Called by eject / hard-reset to wipe all auth state.
   */
  function onWalletEjected() {
    _state.authToken = null;
    _state.currentWallet = null;
    _state.overseerPowered = false;
    localStorage.removeItem('authToken');
    localStorage.removeItem('walletAddress');
    _setPowered(false);
    _showModal();
  }

  /**
   * Expose auth token to the inline auth script via a getter so the bridge
   * never needs to reach directly into _state.
   */
  function _getAuthToken() {
    return _state.authToken;
  }

  /**
   * Opens the connection modal (settings button, wallet badge).
   */
  function showModal() {
    _showModal();
  }

  return {
    init,
    showModal,
    powerOn,
    onWalletConnected,
    onWalletEjected,
    _getAuthToken,
  };
})();

document.addEventListener('DOMContentLoaded', P87.init);
