'use strict';
(function () {

  const POLL_INTERVAL_MS = 30000;
  let fetchInFlight = false;
  let openCard = null;
  let animating = false;
  let telemetryData = null;

  const $ = id => document.getElementById(id);

  function setCls(el, cls) {
    if (!el) return;
    el.className = cls;
  }

  function setText(id, value, cls) {
    const el = $(id);
    if (!el) return;
    el.textContent = (value === null || value === undefined) ? '—' : String(value);
    if (cls) el.className = cls;
  }

  function fmt(v, decimals, prefix, suffix) {
    if (v === null || v === undefined) return null;
    const n = parseFloat(v);
    if (isNaN(n)) return null;
    return (prefix || '') + n.toFixed(decimals) + (suffix || '');
  }

  function fmtUsd(v) { return fmt(v, 2, '$'); }
  function fmtHf(v)  { return fmt(v, 4, ''); }
  function fmtPct(v) {
    if (v === null || v === undefined) return null;
    const n = parseFloat(v);
    if (isNaN(n)) return null;
    return (n >= 0 ? '+' : '') + n.toFixed(2) + '%';
  }
  function fmtMin(v) {
    if (v === null || v === undefined) return null;
    const m = parseInt(v, 10);
    if (isNaN(m)) return null;
    if (m < 60) return m + 'm ago';
    return Math.floor(m / 60) + 'h ' + (m % 60) + 'm ago';
  }
  function fmtCountdown(v) {
    if (v === null || v === undefined) return null;
    const m = parseInt(v, 10);
    if (isNaN(m)) return null;
    if (m < 60) return m + 'm';
    return Math.floor(m / 60) + 'h ' + (m % 60) + 'm';
  }

  function shieldClass(status) {
    if (!status) return 'telem-value shield-DOWN';
    return 'telem-value shield-' + status;
  }

  function apyClass(v) {
    if (v === null || v === undefined) return 'metric-value val-dim';
    return parseFloat(v) >= 0 ? 'metric-value apy-positive' : 'metric-value apy-negative';
  }

  function showToast(msg, isError) {
    const el = $('toast');
    if (!el) return;
    el.textContent = msg;
    el.className = 'toast-visible' + (isError ? ' toast-error' : '');
    clearTimeout(el._tid);
    el._tid = setTimeout(() => { el.className = ''; }, 3500);
  }

  function checkSessionOverlay() {
    const hasCookie = document.cookie.split(';').some(c => c.trim().startsWith('session_token='));
    const overlay = $('connect-overlay');
    if (!overlay) return;
    if (!hasCookie) {
      overlay.classList.remove('hidden');
    } else {
      overlay.classList.add('hidden');
    }
  }

  function populateTelemetry(d) {
    if (!d) return;
    telemetryData = d;

    const w = (d.wallets && d.wallets.length > 0) ? d.wallets[0] : null;

    const engineYield = w ? w.engine_yield_apy_pct_7d : null;
    const spread = d.net_apy_spread;
    const shield = w ? w.shield_status_enum : null;
    const usdc = w ? w.user_usdc_balance : null;

    const spreadStr = fmtPct(spread);
    const apyEl = $('bh-apy-value');
    if (apyEl) {
      apyEl.textContent = spreadStr || '—';
      apyEl.className = apyClass(spread);
    }

    const shieldEl = $('bh-shield-value');
    if (shieldEl) {
      shieldEl.textContent = shield || 'DOWN';
      shieldEl.className = 'metric-value ' + (shield ? 'shield-' + shield : 'shield-DOWN');
    }

    const usdcEl = $('bh-usdc-value');
    if (usdcEl) {
      usdcEl.textContent = fmtUsd(usdc) || '—';
    }

    const hf = w ? w.health_factor : null;
    const hfStr = fmtHf(hf);
    let hfClass = 'telem-value val-dim';
    if (hf !== null && hf !== undefined) {
      hfClass = hf >= 3.60 ? 'telem-value val-green' : hf >= 3.20 ? 'telem-value val-amber' : 'telem-value val-red';
    }
    setText('green-hf', hfStr, hfClass);
    setText('green-wbtc', fmtUsd(w ? w.wbtc_collateral_usd : null));
    const dai = w ? w.total_debt_usd : null;
    setText('green-dai', fmtUsd(dai), 'telem-value val-amber');

    setText('cyan-balance', fmtUsd(usdc), 'telem-value val-cyan');
    setText('cyan-lifetime', fmtUsd(w ? w.lifetime_usdc_generated : null), 'telem-value val-green');

    const amberSpreadEl = $('amber-spread');
    if (amberSpreadEl) {
      amberSpreadEl.textContent = spreadStr || '—';
      amberSpreadEl.className = spread !== null ? ('telem-value ' + (parseFloat(spread) >= 0 ? 'val-green' : 'val-red')) : 'telem-value val-dim';
    }
    setText('amber-m100', d.milestone_100_hhmm || '—', 'telem-value val-amber');
    setText('amber-m1k', d.milestone_1000_hhmm || '—', 'telem-value val-amber');

    const magShieldEl = $('magenta-shield');
    if (magShieldEl) {
      magShieldEl.textContent = shield || 'DOWN';
      magShieldEl.className = shieldClass(shield);
    }
    setText('magenta-elapsed', fmtMin(d.last_repay_elapsed_min), 'telem-value val-dim');
    setText('magenta-countdown', fmtCountdown(d.next_repay_countdown_min), 'telem-value val-magenta');
  }

  async function syncTelemetry() {
    if (fetchInFlight) return;
    fetchInFlight = true;
    try {
      const res = await fetch('/api/telemetry', { credentials: 'same-origin' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      populateTelemetry(data);
    } catch (e) {
      const hdrIds = ['bh-apy-value', 'bh-shield-value', 'bh-usdc-value'];
      hdrIds.forEach(id => setText(id, 'ERR', 'metric-value val-red'));
    } finally {
      fetchInFlight = false;
    }
  }

  function openDomeCard(card) {
    if (animating) return;
    animating = true;
    card.classList.add('pulse-emit');
    setTimeout(() => {
      card.classList.add('card-flipped');
      setTimeout(() => {
        card.classList.remove('pulse-emit');
        animating = false;
        openCard = card;
      }, 200);
    }, 300);
  }

  function closeDomeCard(card, cb) {
    if (!card) { if (cb) cb(); return; }
    card.classList.add('power-down');
    setTimeout(() => {
      card.classList.remove('card-flipped', 'power-down');
      openCard = null;
      if (cb) cb();
    }, 400);
  }

  function handleCardTap(card) {
    if (animating) return;
    if (openCard === card) {
      closeDomeCard(card);
      return;
    }
    if (openCard) {
      animating = true;
      closeDomeCard(openCard, () => {
        setTimeout(() => {
          animating = false;
          openDomeCard(card);
        }, 80);
      });
      return;
    }
    openDomeCard(card);
  }

  function initCardFlip() {
    const grid = $('dome-grid');
    if (!grid) return;
    grid.addEventListener('click', e => {
      const card = e.target.closest('.dome-card');
      if (!card) return;
      handleCardTap(card);
    });
  }

  async function handleWithdraw() {
    const btn = $('btn-withdraw');
    if (!btn || btn.disabled) return;
    btn.disabled = true;
    const orig = btn.textContent;
    btn.textContent = '[ PROCESSING… ]';
    try {
      const res = await fetch('/api/usdc/withdraw', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json().catch(() => ({}));
      if (data.success) {
        showToast('WITHDRAW OK — TX: ' + (data.tx_hash ? data.tx_hash.slice(0, 18) + '…' : 'confirmed'));
        setTimeout(syncTelemetry, 2000);
      } else {
        showToast('[' + (data.code || 'ERROR') + '] ' + (data.message || 'withdrawal failed'), true);
      }
    } catch (e) {
      showToast('NETWORK ERROR — withdraw aborted', true);
    } finally {
      btn.disabled = false;
      btn.textContent = orig;
    }
  }

  async function handleEmergency(endpoint, btnId, actionLabel) {
    const btn = $(btnId);
    if (!btn || btn.disabled) return;
    btn.disabled = true;
    const orig = btn.textContent;
    btn.textContent = '[ PROCESSING… ]';
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json().catch(() => ({}));
      if (data.success) {
        const wrapper = $('app-wrapper');
        if (wrapper) {
          wrapper.classList.add('emergency-shake');
          setTimeout(() => wrapper.classList.remove('emergency-shake'), 600);
        }
        showToast(actionLabel.toUpperCase() + ' CONFIRMED — ' + (data.timestamp || ''));
      } else {
        showToast('[' + (data.code || 'ERROR') + '] ' + (data.message || actionLabel + ' failed'), true);
      }
    } catch (e) {
      showToast('NETWORK ERROR — ' + actionLabel + ' aborted', true);
    } finally {
      btn.disabled = false;
      btn.textContent = orig;
    }
  }

  function initButtons() {
    const wBtn = $('btn-withdraw');
    if (wBtn) wBtn.addEventListener('click', handleWithdraw);

    const eBtn = $('btn-eject');
    if (eBtn) eBtn.addEventListener('click', () => handleEmergency('/api/emergency/eject', 'btn-eject', 'EJECT'));

    const rBtn = $('btn-hard-reset');
    if (rBtn) rBtn.addEventListener('click', () => handleEmergency('/api/emergency/hard_reset', 'btn-hard-reset', 'HARD RESET'));
  }

  function init() {
    checkSessionOverlay();
    initCardFlip();
    initButtons();
    syncTelemetry();
    setInterval(syncTelemetry, POLL_INTERVAL_MS);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
