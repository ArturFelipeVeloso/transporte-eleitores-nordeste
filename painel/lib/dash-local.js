/*
 * dash-local.js — versão local da API "dash" usada pelo painel.
 * Cada conjunto de dados fica em dados/<id>.js e só é carregado quando o
 * painel precisa dele (por exemplo, as localidades de um estado quando
 * esse estado é escolhido). Os filtros ficam em memória.
 */
(function () {
  window.DADOS = window.DADOS || {};
  const DADOS = window.DADOS;
  const calcs = new Map();
  const calcCache = new Map();
  const listeners = [];
  const loading = new Map(); // id -> 'loading' | 'error'
  const DEFAULT_PARAMS = { uf: null, mun: null, sit: null, q: null, aba: null };
  let params = Object.assign({}, DEFAULT_PARAMS);

  let pending = false;
  function emit() {
    if (pending) return;
    pending = true;
    requestAnimationFrame(() => {
      pending = false;
      for (const fn of listeners) {
        try { fn(); } catch (e) { console.error(e); }
      }
    });
  }

  window.__dadosCarregados = function (id) {
    loading.delete(id);
    calcCache.clear();
    emit();
  };

  function load(id) {
    if (loading.has(id)) return;
    loading.set(id, 'loading');
    const s = document.createElement('script');
    s.src = 'dados/' + id + '.js';
    s.onerror = () => { loading.set(id, 'error'); emit(); };
    document.head.appendChild(s);
  }

  // Retorna as linhas, ou undefined enquanto carrega, ou null se não existe.
  function rowsOf(id) {
    if (Object.prototype.hasOwnProperty.call(DADOS, id)) return DADOS[id];
    if (calcs.has(id)) {
      if (!calcCache.has(id)) {
        const c = calcs.get(id);
        const inputs = c.inputs.map(rowsOf);
        if (inputs.some((x) => x === undefined || x === null)) return undefined;
        calcCache.set(id, c.fn(...inputs));
      }
      return calcCache.get(id);
    }
    if (loading.get(id) === 'error') return null;
    load(id);
    return undefined;
  }

  window.dash = {
    colors: [
      'var(--serie-1)', 'var(--serie-2)', 'var(--serie-3)', 'var(--serie-4)',
      'var(--serie-5)', 'var(--serie-6)', 'var(--serie-7)', 'var(--serie-8)',
    ],
    data(id) {
      const d = rowsOf(id);
      if (d === undefined) return { status: 'loading', data: [], columns: [], meta: [], refreshing: false };
      if (d === null) return { status: 'error', data: [], columns: [], meta: [], refreshing: false, message: 'Arquivo dados/' + id + '.js não encontrado' };
      const columns = Array.isArray(d) && d.length ? Object.keys(d[0]) : [];
      return { status: 'ok', data: d, rows: d, columns, meta: [], refreshing: false };
    },
    onData(fn) {
      listeners.push(fn);
      try { fn(); } catch (e) { console.error(e); }
    },
    calc(id, spec) { calcs.set(id, spec); calcCache.delete(id); },
    loader() {},
    params() { return Object.assign({}, params); },
    setParams(obj) { params = Object.assign({}, params, obj); emit(); },
    resetParams() { params = Object.assign({}, DEFAULT_PARAMS); emit(); },
    refresh() { emit(); },
    setLink(name) { if (name) history.replaceState(null, '', '#' + name); },
  };

  let lastW = window.innerWidth;
  window.addEventListener('resize', () => {
    if (Math.abs(window.innerWidth - lastW) < 4) return;
    lastW = window.innerWidth;
    emit();
  });
})();
