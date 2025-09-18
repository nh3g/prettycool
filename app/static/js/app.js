const state = {
  modules: [],
  categories: new Map(),
  config: {},
};

const selectors = {
  modulesList: document.getElementById('modules-list'),
  bundleButtons: document.getElementById('bundle-buttons'),
  targetInput: document.getElementById('target-input'),
  runSelected: document.getElementById('run-selected'),
  runAll: document.getElementById('run-all'),
  resultsContainer: document.getElementById('results-container'),
  statusArea: document.getElementById('status-area'),
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
  await loadModules();
  await loadConfig();
  attachEvents();
}

document.addEventListener('DOMContentLoaded', init);

function attachEvents() {
  selectors.runSelected.addEventListener('click', handleRunSelected);
  selectors.runAll.addEventListener('click', () => runExecution({ mode: 'all' }));
  selectors.apiForm.addEventListener('submit', handleApiSubmit);
  selectors.resetApiForm.addEventListener('click', () => selectors.apiForm.reset());
  selectors.consoleRun.addEventListener('click', handleConsoleRun);
  selectors.consoleClear.addEventListener('click', () => {
    selectors.consoleOutput.textContent = 'Console pronto.';
  });
}

async function loadModules() {
  try {
    const response = await fetch('/api/modules');
    const data = await response.json();
    state.modules = data.modules || [];
    renderModules();
    renderBundleButtons();
  } catch (error) {
    updateStatus('Falha ao carregar módulos.', true);
  }
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

function renderModules() {
  selectors.modulesList.innerHTML = '';
  state.categories.clear();

  state.modules.forEach((module) => {
    const bucket = state.categories.get(module.category) || [];
    bucket.push(module);
    state.categories.set(module.category, bucket);
  });

  [...state.categories.entries()].forEach(([category, modules]) => {
    const header = document.createElement('h2');
    header.textContent = category;
    selectors.modulesList.appendChild(header);

    modules.forEach((module) => {
      const wrapper = document.createElement('div');
      wrapper.className = 'module-item';

      const label = document.createElement('label');
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.value = module.name;
      checkbox.id = `module-${module.name}`;

      const text = document.createElement('span');
      text.innerHTML = `<strong>${module.display_name}</strong><br /><small>${module.description}</small>`;

      label.appendChild(checkbox);
      label.appendChild(text);

      const runButton = document.createElement('button');
      runButton.type = 'button';
      runButton.textContent = 'Executar';
      runButton.addEventListener('click', () => runExecution({ mode: 'module', modules: [module.name] }));

      wrapper.appendChild(label);
      wrapper.appendChild(runButton);
      selectors.modulesList.appendChild(wrapper);
    });
  });
}

function renderBundleButtons() {
  selectors.bundleButtons.innerHTML = '';
  state.categories.forEach((_modules, category) => {
    const button = document.createElement('button');
    button.textContent = `Executar ${category}`;
    button.addEventListener('click', () => runExecution({ mode: 'bundle', category }));
    selectors.bundleButtons.appendChild(button);
  });
}

function renderApiKeys(keys) {
  selectors.apiGrid.innerHTML = '';
  Object.entries(keys).forEach(([name, info]) => {
    const label = document.createElement('label');
    label.htmlFor = `api-${name}`;
    const title = document.createElement('span');
    const suffix = info.set && info.value ? ` (****${info.value})` : '';
    title.textContent = `${name}${suffix}`;
    const input = document.createElement('input');
    input.type = 'password';
    input.id = `api-${name}`;
    input.name = name;
    input.placeholder = info.set ? 'Atualizar chave' : 'Inserir chave';
    label.appendChild(title);
    label.appendChild(input);
    selectors.apiGrid.appendChild(label);
  });
}

function getSelectedModules() {
  const checked = selectors.modulesList.querySelectorAll('input[type="checkbox"]:checked');
  return Array.from(checked).map((item) => item.value);
}

async function handleRunSelected() {
  const modules = getSelectedModules();
  if (modules.length === 0) {
    updateStatus('Selecione pelo menos um módulo.', true);
    return;
  }
  const mode = modules.length === 1 ? 'module' : 'modules';
  await runExecution({ mode, modules });
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
  } catch (error) {
    updateStatus(error.message, true);
  }
}

function displayResults(results) {
  selectors.resultsContainer.innerHTML = '';
  if (!results.length) {
    selectors.resultsContainer.innerHTML = '<p>Nenhum dado retornado pelos módulos.</p>';
    return;
  }

  results.forEach((result) => {
    const card = document.createElement('div');
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
  selectors.statusArea.style.color = isError ? '#ff566b' : '#9aa0c6';
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
    if (key.startsWith('api-')) {
      const name = key.replace('api-', '');
      if (value) payload.keys[name] = value;
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
