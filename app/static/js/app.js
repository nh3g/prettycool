const state = {
  modules: [],
  categories: new Map(),
  config: {},
};

// Seletores centralizados para facilitar manutenção dos elementos da interface
const selectors = {
  statusArea: document.getElementById('status-area'),
  tabButtons: document.querySelectorAll('[data-tab-target]'),
  tabPanels: document.querySelectorAll('.tab-panel'),
  moduleCount: document.getElementById('module-count'),
  categoryCount: document.getElementById('category-count'),
  bundleCount: document.getElementById('bundle-count'),
  overviewCategoryList: document.getElementById('overview-category-list'),
  targetInput: document.getElementById('target-input'),
  runPrimary: document.getElementById('run-primary'),
  clearSelection: document.getElementById('clear-selection'),
  modeRadios: document.querySelectorAll('input[name="execution-mode"]'),
  modePanels: document.querySelectorAll('[data-mode-panel]'),
  bundleList: document.getElementById('bundle-list'),
  customModules: document.getElementById('custom-modules'),
  resultsContainer: document.getElementById('results-container'),
  reportLink: document.getElementById('report-link'),
  apiGrid: document.getElementById('api-key-grid'),
  apiForm: document.getElementById('api-form'),
  timeoutInput: document.getElementById('timeout-input'),
  resetApiForm: document.getElementById('reset-api-form'),
  consoleInput: document.getElementById('console-input'),
  consoleRun: document.getElementById('console-run'),
  consoleClear: document.getElementById('console-clear'),
  consoleOutput: document.getElementById('console-output'),
};

async function init() {
  setupTabNavigation();
  setupModeSelector();
  await loadModules();
  await loadConfig();
  attachEvents();
}

document.addEventListener('DOMContentLoaded', init);

function attachEvents() {
  selectors.runPrimary.addEventListener('click', handlePrimaryExecution);
  selectors.clearSelection.addEventListener('click', clearCustomSelection);
  selectors.apiForm.addEventListener('submit', handleApiSubmit);
  selectors.resetApiForm.addEventListener('click', () => selectors.apiForm.reset());
  selectors.consoleRun.addEventListener('click', handleConsoleRun);
  selectors.consoleClear.addEventListener('click', () => {
    selectors.consoleOutput.textContent = 'Console pronto.';
  });
}

function setupTabNavigation() {
  selectors.tabButtons.forEach((button) => {
    button.addEventListener('click', () => activateTab(button.dataset.tabTarget));
  });
}

function activateTab(tabName) {
  selectors.tabButtons.forEach((button) => {
    button.classList.toggle('active', button.dataset.tabTarget === tabName);
  });
  selectors.tabPanels.forEach((panel) => {
    panel.classList.toggle('active', panel.dataset.tab === tabName);
  });
}

function setupModeSelector() {
  selectors.modeRadios.forEach((radio) => {
    radio.addEventListener('change', () => toggleModePanels(radio.value));
  });
  toggleModePanels('all');
}

function toggleModePanels(mode) {
  selectors.modePanels.forEach((panel) => {
    const shouldShow = panel.dataset.modePanel === mode;
    panel.classList.toggle('visible', shouldShow);
  });
}

async function loadModules() {
  try {
    const response = await fetch('/api/modules');
    const data = await response.json();
    state.modules = data.modules || [];
    buildCategories();
    renderBundleOptions();
    renderModules();
    updateOverview();
  } catch (error) {
    updateStatus('Falha ao carregar módulos.', true);
  }
}

function buildCategories() {
  state.categories.clear();
  state.modules.forEach((module) => {
    const bucket = state.categories.get(module.category) || [];
    bucket.push(module);
    state.categories.set(module.category, bucket);
  });
}

function renderBundleOptions() {
  selectors.bundleList.innerHTML = '';
  const categories = [...state.categories.keys()];
  categories.forEach((category, index) => {
    const option = document.createElement('label');
    option.className = 'bundle-option';

    const input = document.createElement('input');
    input.type = 'radio';
    input.name = 'bundle-choice';
    input.value = category;
    if (index === 0) {
      input.checked = true;
    }
    input.addEventListener('change', highlightSelectedBundle);

    const info = document.createElement('div');
    info.innerHTML = `<strong>${category}</strong><span>${state.categories.get(category).length} módulo(s)</span>`;

    option.appendChild(input);
    option.appendChild(info);
    selectors.bundleList.appendChild(option);
  });
  highlightSelectedBundle();
}

function highlightSelectedBundle() {
  selectors.bundleList.querySelectorAll('.bundle-option').forEach((option) => {
    const input = option.querySelector('input');
    option.classList.toggle('active', input.checked);
  });
}

function renderModules() {
  selectors.customModules.innerHTML = '';
  state.categories.forEach((modules, category) => {
    const group = document.createElement('details');
    group.className = 'module-group';
    group.open = true;

    const summary = document.createElement('summary');
    summary.innerHTML = `<span>${category}</span><span class="badge">${modules.length}</span>`;
    group.appendChild(summary);

    const grid = document.createElement('div');
    grid.className = 'module-grid';

    modules.forEach((module) => {
      const card = document.createElement('div');
      card.className = 'module-card';

      const header = document.createElement('div');
      header.className = 'module-card-header';

      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.value = module.name;
      checkbox.id = `module-${module.name}`;

      const label = document.createElement('label');
      label.htmlFor = checkbox.id;
      label.innerHTML = `<strong>${module.display_name}</strong><span>${module.description}</span>`;

      header.appendChild(checkbox);
      header.appendChild(label);

      const actions = document.createElement('div');
      actions.className = 'module-card-actions';

      const quickRun = document.createElement('button');
      quickRun.type = 'button';
      quickRun.className = 'ghost';
      quickRun.textContent = 'Executar agora';
      quickRun.addEventListener('click', () => runExecution({ mode: 'module', modules: [module.name] }));

      actions.appendChild(quickRun);

      card.appendChild(header);
      card.appendChild(actions);
      grid.appendChild(card);
    });

    group.appendChild(grid);
    selectors.customModules.appendChild(group);
  });
}

function updateOverview() {
  selectors.moduleCount.textContent = state.modules.length;
  selectors.categoryCount.textContent = state.categories.size;
  selectors.bundleCount.textContent = state.categories.size;

  selectors.overviewCategoryList.innerHTML = '';
  state.categories.forEach((modules, category) => {
    const item = document.createElement('li');
    item.innerHTML = `<strong>${category}</strong><span>${modules.map((m) => m.display_name).join(', ')}</span>`;
    selectors.overviewCategoryList.appendChild(item);
  });
}

async function loadConfig() {
  try {
    const response = await fetch('/api/config/keys');
    const data = await response.json();
    state.config = data;
    renderApiKeys(data.keys || {});
    selectors.timeoutInput.value = data.timeout ?? '';
  } catch (error) {
    updateStatus('Não foi possível carregar as configurações.', true);
  }
}

function renderApiKeys(keys) {
  selectors.apiGrid.innerHTML = '';
  Object.entries(keys).forEach(([name, info]) => {
    const wrapper = document.createElement('label');
    wrapper.htmlFor = `api-${name}`;
    wrapper.innerHTML = `
      <span>${name}${info.set && info.value ? ` (****${info.value})` : ''}</span>
      <input type="password" id="api-${name}" name="api-${name}" placeholder="${info.set ? 'Atualizar chave' : 'Inserir chave'}" />
    `;
    selectors.apiGrid.appendChild(wrapper);
  });
}

function getSelectedMode() {
  const checked = Array.from(selectors.modeRadios).find((radio) => radio.checked);
  return checked ? checked.value : 'all';
}

function getSelectedBundle() {
  const checked = selectors.bundleList.querySelector('input[name="bundle-choice"]:checked');
  return checked ? checked.value : null;
}

function getSelectedModules() {
  const checked = selectors.customModules.querySelectorAll('input[type="checkbox"]:checked');
  return Array.from(checked).map((item) => item.value);
}

function clearCustomSelection() {
  selectors.customModules.querySelectorAll('input[type="checkbox"]').forEach((input) => {
    input.checked = false;
  });
}

async function handlePrimaryExecution() {
  const mode = getSelectedMode();
  const payload = { mode };

  if (mode === 'bundle') {
    const category = getSelectedBundle();
    if (!category) {
      updateStatus('Selecione uma categoria para o bundle.', true);
      return;
    }
    payload.category = category;
  }

  if (mode === 'custom') {
    const modules = getSelectedModules();
    if (!modules.length) {
      updateStatus('Selecione ao menos um módulo.', true);
      return;
    }
    payload.mode = modules.length === 1 ? 'module' : 'modules';
    payload.modules = modules;
  }

  await runExecution(payload);
}

async function runExecution({ mode, modules = [], category = null }) {
  const target = selectors.targetInput.value.trim();
  if (!target) {
    updateStatus('Informe um alvo válido.', true);
    return;
  }

  updateStatus('Executando...');
  try {
    const payload = {
      target,
      mode,
      modules,
      category,
      options: {},
    };

    const response = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Falha na execução.');
    }

    const data = await response.json();
    displayResults(data.results || []);
    updateReportLink(data.report_path);
    updateStatus('Execução concluída.');
    activateTab('results');
  } catch (error) {
    updateStatus(error.message, true);
  }
}

function displayResults(results) {
  selectors.resultsContainer.innerHTML = '';
  if (!results.length) {
    selectors.resultsContainer.innerHTML = '<p class="empty-state">Nenhum dado retornado pelos módulos.</p>';
    return;
  }

  results.forEach((result) => {
    const card = document.createElement('article');
    card.className = 'result-card';

    const title = document.createElement('h3');
    title.textContent = result.display_name;
    card.appendChild(title);

    const status = document.createElement('div');
    status.className = 'status-pill';
    status.textContent = result.success ? 'Sucesso' : 'Falha';
    if (!result.success) {
      status.classList.add('error');
    }
    card.appendChild(status);

    const summary = document.createElement('p');
    summary.textContent = result.summary;
    card.appendChild(summary);

    if (result.errors && result.errors.length) {
      const errorBlock = document.createElement('pre');
      errorBlock.textContent = result.errors.join('\n');
      card.appendChild(errorBlock);
    }

    if (result.records && result.records.length) {
      const records = document.createElement('pre');
      records.textContent = JSON.stringify(result.records, null, 2);
      card.appendChild(records);
    }

    selectors.resultsContainer.appendChild(card);
  });
}

function updateStatus(message, isError = false) {
  selectors.statusArea.textContent = message;
  selectors.statusArea.classList.toggle('error', isError);
}

function updateReportLink(path) {
  if (path) {
    selectors.reportLink.innerHTML = `Relatório salvo em <code>${path}</code>`;
  } else {
    selectors.reportLink.textContent = '';
  }
}

async function handleApiSubmit(event) {
  event.preventDefault();
  const formData = new FormData(selectors.apiForm);
  const payload = { keys: {} };
  formData.forEach((value, key) => {
    if (key.startsWith('api-') && value) {
      const name = key.replace('api-', '');
      payload.keys[name] = value;
    }
  });

  const timeoutValue = selectors.timeoutInput.value.trim();
  if (timeoutValue) {
    payload.timeout = Number(timeoutValue);
  }

  try {
    const response = await fetch('/api/config/keys', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error('Não foi possível atualizar as chaves.');
    }
    const data = await response.json();
    renderApiKeys(data.keys || {});
    updateStatus('Configurações atualizadas.');
  } catch (error) {
    updateStatus(error.message, true);
  }
}

async function handleConsoleRun() {
  const command = selectors.consoleInput.value.trim();
  if (!command) {
    updateStatus('Informe um comando para o console.', true);
    return;
  }
  try {
    const response = await fetch('/api/console', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command }),
    });
    const data = await response.json();
    const prefix = data.success ? '✅' : '⚠️';
    selectors.consoleOutput.textContent = `${prefix} ${data.output}`;
    if (data.report_path) {
      updateReportLink(data.report_path);
    }
  } catch (error) {
    selectors.consoleOutput.textContent = `⚠️ Erro ao executar comando: ${error.message}`;
  }
}
