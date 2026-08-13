function initApp() {
  const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';
  const API_BASE = API_BASE_URL;


  // --- Element Selectors ---
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');
  const refreshStatusBtn = document.getElementById('btnRefreshStatus') || document.getElementById('refreshStatusBtn');
  const headerTitle = document.getElementById('headerTitle');


  const modalConfirmation = document.getElementById('modalConfirmation');
  const modalTitle = document.getElementById('modalTitle');
  const modalMessage = document.getElementById('modalMessage');
  const modalCancelBtn = document.getElementById('modalCancelBtn');
  const modalConfirmBtn = document.getElementById('modalConfirmBtn');
  let pendingConfirmationAction = null;

  const terminalLog = document.getElementById('terminalLog');
  const btnClearLogs = document.getElementById('btnClearLogs');

  // --- Helper: Toast Notification System ---
  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️'
    };

    toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // --- Helper: Live Log Streamer ---
  function appendLog(message, level = 'info') {
    if (!terminalLog) return;
    const timeStr = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = `log-entry log-${level}`;
    entry.textContent = `[${timeStr}] [${level.toUpperCase()}] ${message}`;
    terminalLog.appendChild(entry);
    terminalLog.scrollTop = terminalLog.scrollHeight;
  }

  // --- Helper: API Client Wrapper ---
  async function apiCall(endpoint, method = 'GET', body = null) {
    appendLog(`API Request: ${method} ${endpoint}`, 'info');
    const options = {
      method,
      headers: { 'Content-Type': 'application/json' }
    };
    if (body) {
      options.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, options);
      const data = await response.json();

      if (!response.ok) {
        const errMsg = data.detail || data.error || `HTTP ${response.status}`;
        appendLog(`API Error (${endpoint}): ${errMsg}`, 'error');
        showToast(errMsg, 'error');
        throw new Error(errMsg);
      }

      appendLog(`API Success (${endpoint})`, 'info');
      return data;
    } catch (err) {
      if (err.name === 'TypeError') {
        const networkErr = 'Wait For AI Agent to Connect';
        appendLog(networkErr, 'error');
        showToast(networkErr, 'error');
      }
      throw err;
    }
  }

  // --- Helper: Dangerous Action Confirmation Modal ---
  function promptConfirmation(title, message, actionCallback) {
    modalTitle.textContent = title;
    modalMessage.textContent = message;
    pendingConfirmationAction = actionCallback;
    modalConfirmation.classList.add('active');
  }

  modalCancelBtn.addEventListener('click', () => {
    modalConfirmation.classList.remove('active');
    pendingConfirmationAction = null;
    showToast('Action cancelled by user.', 'info');
  });

  modalConfirmBtn.addEventListener('click', () => {
    modalConfirmation.classList.remove('active');
    if (pendingConfirmationAction) {
      pendingConfirmationAction();
      pendingConfirmationAction = null;
    }
  });

  // --- Navigation Tab Switcher ---
  const navItems = document.querySelectorAll('.nav-item');
  const views = document.querySelectorAll('.view');

  const tabTitles = {
    chat: '💬 Interactive Chat',
    search: '🔍 Directory & Semantic Search',
    rag: '📄 RAG Document Assistant',
    automation: '🖥️ Desktop Automation Controls',
    browser: '🌐 Browser Automation & Agent',
    coding: '💻 AI Coding Assistant',
    filepanel: '📁 Project File Panel & Code Explorer',
    settings: '⚙️ Settings & System Monitor',
    logs: '📋 Live Event Log Streamer'
  };



  const settingsBackendStatus = document.getElementById('settingsBackendStatus');
  const settingsDbStatus = document.getElementById('settingsDbStatus');
  const settingsMongoStatus = document.getElementById('settingsMongoStatus');

  async function checkBackendHealth() {
    try {
      const data = await apiCall('/health', 'GET');
      if (settingsBackendStatus) settingsBackendStatus.textContent = '🟢 Online (v1.0.0)';
      if (settingsDbStatus) settingsDbStatus.textContent = '🟢 Connected (SQLite)';
      if (settingsMongoStatus && data.details && data.details.mongodb) {
        const m = data.details.mongodb;
        if (m.connected) {
          settingsMongoStatus.textContent = `🟢 Connected (v${m.version} / ${m.db_name} DB)`;
        } else {
          settingsMongoStatus.textContent = '🔴 Disconnected';
        }
      }
    } catch (e) {
      if (settingsBackendStatus) settingsBackendStatus.textContent = '🔴 Offline';
      if (settingsDbStatus) settingsDbStatus.textContent = '🔴 Offline';
      if (settingsMongoStatus) settingsMongoStatus.textContent = '🔴 Offline';
    }
  }

  checkBackendHealth();
  setInterval(checkBackendHealth, 10000);
  const btnToggleSidebar = document.getElementById('btnToggleSidebar');
  const sidebar = document.querySelector('.sidebar');
  const sidebarOverlay = document.getElementById('sidebarOverlay');

  function closeMobileSidebar() {
    if (sidebar) sidebar.classList.remove('mobile-open');
    if (sidebarOverlay) sidebarOverlay.classList.remove('active');
  }

  if (btnToggleSidebar && sidebar) {
    btnToggleSidebar.addEventListener('click', (e) => {
      e.stopPropagation();
      sidebar.classList.toggle('mobile-open');
      if (sidebarOverlay) sidebarOverlay.classList.toggle('active', sidebar.classList.contains('mobile-open'));
    });
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', closeMobileSidebar);
  }

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      closeMobileSidebar();
      const tab = item.getAttribute('data-tab');

      navItems.forEach(n => n.classList.remove('active'));
      views.forEach(v => v.classList.remove('active'));

      item.classList.add('active');
      const targetView = document.getElementById(`view-${tab}`);
      if (targetView) targetView.classList.add('active');

      if (headerTitle && tabTitles[tab]) {
        headerTitle.innerHTML = tabTitles[tab];
      }

      appendLog(`Switched view to '${tab}'`, 'info');
    });
  });

  // --- System Health Monitor ---
  let isCheckingHealth = false;

  async function checkHealth() {
    if (isCheckingHealth) return;
    isCheckingHealth = true;
    let data = null;

    try {
      // Strategy 1: Node.js IPC HTTP request via Electron Main process (with 3-second safety timeout)
      if (window.electronAPI && window.electronAPI.checkHealth) {
        try {
          const ipcPromise = window.electronAPI.checkHealth();
          const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error('IPC timeout')), 3000)
          );
          const res = await Promise.race([ipcPromise, timeoutPromise]);
          if (res && res.success && res.data) {
            data = res.data;
          }
        } catch (ipcErr) { }
      }

      // Strategy 2: Direct 127.0.0.1 fetch fallback
      if (!data) {
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 3000);
          const response = await fetch('http://127.0.0.1:8000/api/v1/health', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            signal: controller.signal
          });
          clearTimeout(timeoutId);
          if (response.ok) {
            data = await response.json();
          }
        } catch (fetchErr) { }
      }

      if (data && (data.status === 'online' || data.status === 'ok')) {
        if (statusDot) statusDot.className = 'status-dot online';
        if (statusText) statusText.textContent = 'Backend Online';

        const backendStatus = document.getElementById('settingsBackendStatus');
        const dbStatus = document.getElementById('settingsDbStatus');
        const jsonOutput = document.getElementById('settingsJsonOutput');

        if (backendStatus) backendStatus.textContent = (data.status || 'ONLINE').toUpperCase();
        if (dbStatus) dbStatus.textContent = data.db_connected ? 'CONNECTED (SQLite)' : 'DISCONNECTED';
        if (jsonOutput) jsonOutput.textContent = JSON.stringify(data, null, 2);
      } else {
        if (statusDot) statusDot.className = 'status-dot offline';
        if (statusText) statusText.textContent = 'Backend Offline';

        const backendStatus = document.getElementById('settingsBackendStatus');
        const dbStatus = document.getElementById('settingsDbStatus');
        if (backendStatus) backendStatus.textContent = 'UNREACHABLE';
        if (dbStatus) dbStatus.textContent = 'UNKNOWN';
      }
    } finally {
      isCheckingHealth = false;
    }
  }

  if (refreshStatusBtn) {
    refreshStatusBtn.addEventListener('click', () => {
      checkHealth();
      showToast('Refreshed health status', 'info');
    });
  }

  async function loadAvailableModels() {
    try {
      const res = await fetch(`${API_BASE_URL}/chat/models`).then(r => r.json());
      if (res && res.installed_models && res.installed_models.length > 0 && chatModelSelect) {
        const localOptGroup = chatModelSelect.querySelector('optgroup[label*="Local"]');
        if (localOptGroup) {
          const currentVal = chatModelSelect.value;
          const existingModels = new Set(Array.from(localOptGroup.options).map(o => o.value));
          res.installed_models.forEach(m => {
            if (!existingModels.has(m)) {
              const opt = document.createElement('option');
              opt.value = m;
              opt.textContent = `${m} (Local)`;
              localOptGroup.appendChild(opt);
            }
          });
        }
      }
    } catch (err) { }
  }

  checkHealth();
  loadAvailableModels();
  setInterval(checkHealth, 2000);

  // ==========================================
  // THEME ENGINE (Default Theme)
  // ==========================================
  document.body.className = 'theme-dark-glass';
  const themeSelector = document.getElementById('themeSelector');
  if (themeSelector) {
    themeSelector.addEventListener('change', () => {
      const selectedTheme = themeSelector.value;
      document.body.className = selectedTheme;
      localStorage.setItem('ospilot_theme', selectedTheme);
    });
  }

  // ==========================================
  // TAB 1: CHAT CONTROLLER (STREAMING & SESSIONS)
  // ==========================================
  const chatForm = document.getElementById('chatForm');
  const chatPromptInput = document.getElementById('chatPromptInput');
  const chatMessages = document.getElementById('chatMessages');
  const chatModelSelect = document.getElementById('chatModelSelect');
  const chatStreamToggle = document.getElementById('chatStreamToggle');
  const chatSendBtn = document.getElementById('chatSendBtn');
  const btnNewChatSession = document.getElementById('btnNewChatSession');
  const chatHistoryList = document.getElementById('chatHistoryList');

  let activeSessionId = 'session-1';
  let chatSessions = {
    'session-1': { title: 'Current Session', history: [] }
  };

  if (btnNewChatSession) {
    btnNewChatSession.addEventListener('click', () => {
      const newId = `session-${Date.now()}`;
      chatSessions[newId] = { title: `Chat ${Object.keys(chatSessions).length + 1}`, history: [] };
      activeSessionId = newId;

      renderChatHistoryDrawer();
      renderChatMessages();
      showToast('Created new chat session', 'info');
    });
  }

  function renderChatHistoryDrawer() {
    if (!chatHistoryList) return;
    chatHistoryList.innerHTML = '';

    Object.keys(chatSessions).forEach(id => {
      const sess = chatSessions[id];
      const item = document.createElement('div');
      item.className = `history-item ${id === activeSessionId ? 'active' : ''}`;
      item.setAttribute('data-session-id', id);
      item.innerHTML = `<span class="history-icon">💬</span><span class="history-title">${sess.title}</span>`;

      item.addEventListener('click', () => {
        activeSessionId = id;
        renderChatHistoryDrawer();
        renderChatMessages();
      });

      chatHistoryList.appendChild(item);
    });
  }

  function renderMarkdown(text) {
    if (!text) return '';
    let raw = String(text);

    // 1. Code blocks: extract ```lang \n code ```
    const codeBlocks = [];
    raw = raw.replace(/```(\w*)\r?\n?([\s\S]*?)```/g, (match, lang, code) => {
      const escapedCode = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      codeBlocks.push(`<pre><code class="language-${lang || 'text'}">${escapedCode.trim()}</code></pre>`);
      return `___CODE_BLOCK_${codeBlocks.length - 1}___`;
    });

    // 2. Inline code: `code`
    const inlineCodes = [];
    raw = raw.replace(/`([^`\n]+)`/g, (match, code) => {
      const escapedCode = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      inlineCodes.push(`<code>${escapedCode}</code>`);
      return `___INLINE_CODE_${inlineCodes.length - 1}___`;
    });

    // 3. Escape HTML special characters in remaining text
    raw = raw.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    // 4. Markdown Headers
    raw = raw.replace(/^#### (.*$)/gim, '<h4>$1</h4>');
    raw = raw.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    raw = raw.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    raw = raw.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // 5. Bold & Italics
    raw = raw.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    raw = raw.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // 6. Links: [title](url)
    raw = raw.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="color:var(--accent-cyan);">$1</a>');

    // 7. Re-insert inline code
    raw = raw.replace(/___INLINE_CODE_(\d+)___/g, (match, index) => inlineCodes[index] || '');

    // 8. Re-insert code blocks
    raw = raw.replace(/___CODE_BLOCK_(\d+)___/g, (match, index) => codeBlocks[index] || '');

    return raw;
  }

  function renderChatMessages() {
    if (!chatMessages) return;
    chatMessages.innerHTML = '';

    const currentHistory = chatSessions[activeSessionId]?.history || [];
    if (currentHistory.length === 0) {
      chatMessages.innerHTML = `<div class="chat-bubble assistant"><div class="msg-content">Hello! I am <strong>OSPilot</strong>, your local offline AI Desktop Assistant. How can I assist you with code, documents, or desktop tasks today?</div><div class="msg-meta"><span>OSPilot Engine</span><span>Just now</span></div></div>`;
      return;
    }

    currentHistory.forEach(msg => {
      const bubble = document.createElement('div');
      bubble.className = `chat-bubble ${msg.role}`;

      const contentDiv = document.createElement('div');
      contentDiv.className = 'msg-content';
      if (msg.isHtml) {
        contentDiv.innerHTML = msg.content;
      } else {
        contentDiv.innerHTML = renderMarkdown(msg.content);
      }
      bubble.appendChild(contentDiv);

      if (msg.meta) {
        const metaDiv = document.createElement('div');
        metaDiv.className = 'msg-meta';
        metaDiv.innerHTML = typeof msg.meta === 'string' && !msg.meta.includes('<span') ? `<span>${msg.meta}</span>` : msg.meta;
        bubble.appendChild(metaDiv);
      }

      chatMessages.appendChild(bubble);
    });

    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = chatPromptInput.value.trim();
    if (!prompt) return;

    const currentSess = chatSessions[activeSessionId];
    if (!currentSess) return;

    // Append User Message
    currentSess.history.push({ role: 'user', content: prompt });
    if (currentSess.history.length === 1) {
      currentSess.title = prompt.length > 18 ? prompt.substring(0, 18) + '...' : prompt;
      renderChatHistoryDrawer();
    }
    renderChatMessages();

    chatPromptInput.value = '';
    chatSendBtn.disabled = true;
    chatSendBtn.innerHTML = '<div class="spinner"></div>';

    // Append Assistant Loading Bubble
    const assistantBubble = document.createElement('div');
    assistantBubble.className = 'chat-bubble assistant';

    const assistantContent = document.createElement('div');
    assistantContent.className = 'msg-content';
    assistantContent.textContent = 'Thinking...';
    assistantBubble.appendChild(assistantContent);

    const assistantMeta = document.createElement('div');
    assistantMeta.className = 'msg-meta';
    assistantMeta.style.display = 'none';
    assistantBubble.appendChild(assistantMeta);

    chatMessages.appendChild(assistantBubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    const useStreaming = chatStreamToggle ? chatStreamToggle.checked : true;
    const selectedModel = chatModelSelect.value;
    const startTime = Date.now();

    const cleanMessages = currentSess.history.map(m => ({
      role: m.role,
      content: m.content
    }));

    if (useStreaming) {
      try {
        const response = await fetch(`${API_BASE_URL}/chat/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: prompt,
            messages: cleanMessages,
            model: selectedModel
          })
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        assistantContent.textContent = '';
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let fullStreamedText = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line && line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.replace('data: ', '').trim());
                if (data.token !== undefined) {
                  fullStreamedText += data.token;
                  assistantContent.innerHTML = renderMarkdown(fullStreamedText);
                  chatMessages.scrollTop = chatMessages.scrollHeight;
                }
              } catch (e) { }
            }
          }
        }

        const elapsedMs = Date.now() - startTime;
        const metaStr = `<span>Model: ${selectedModel}</span><span>${elapsedMs}ms (Streamed)</span>`;
        assistantContent.innerHTML = renderMarkdown(fullStreamedText || 'Response received.');
        assistantMeta.style.display = 'flex';
        assistantMeta.innerHTML = metaStr;
        currentSess.history.push({ role: 'assistant', content: fullStreamedText || 'Response received.', meta: metaStr });

      } catch (err) {
        assistantContent.innerHTML = `<span style="color:var(--danger-red);">Stream Error: ${err.message}</span>`;
      } finally {
        chatSendBtn.disabled = false;
        chatSendBtn.textContent = 'Send';
        chatMessages.scrollTop = chatMessages.scrollHeight;
      }
    } else {
      try {
        const res = await apiCall('/chat', 'POST', {
          prompt: prompt,
          messages: cleanMessages,
          model: selectedModel
        });

        const metaStr = `<span>Model: ${res.model}</span><span>${res.execution_time_ms}ms</span>`;
        assistantContent.innerHTML = renderMarkdown(res.content);
        assistantMeta.style.display = 'flex';
        assistantMeta.innerHTML = metaStr;
        currentSess.history.push({ role: 'assistant', content: res.content, meta: metaStr });
      } catch (err) {
        assistantContent.innerHTML = `<span style="color:var(--danger-red);">Error: ${err.message}</span>`;
      } finally {
        chatSendBtn.disabled = false;
        chatSendBtn.textContent = 'Send';
        chatMessages.scrollTop = chatMessages.scrollHeight;
      }
    }
  });

  // ==========================================
  // TAB 7: FILE PANEL EXPLORER CONTROLLER
  // ==========================================
  const filePanelForm = document.getElementById('filePanelForm');
  const filePanelDirPath = document.getElementById('filePanelDirPath');
  const btnBrowseFilePanelDir = document.getElementById('btnBrowseFilePanelDir');
  const btnFilePanelPickerHidden = document.getElementById('btnFilePanelPickerHidden');
  const fileTreeContainer = document.getElementById('fileTreeContainer');
  const filePreviewTitle = document.getElementById('filePreviewTitle');
  const filePreviewContent = document.getElementById('filePreviewContent');

  if (btnBrowseFilePanelDir) {
    btnBrowseFilePanelDir.addEventListener('click', async () => {
      if (window.electronAPI && window.electronAPI.selectDirectory) {
        const selectedDir = await window.electronAPI.selectDirectory();
        if (selectedDir && filePanelDirPath) {
          filePanelDirPath.value = selectedDir;
          showToast(`Selected directory: ${selectedDir}`, 'info');
          if (filePanelForm) filePanelForm.dispatchEvent(new Event('submit'));
        }
        return;
      }
      if (btnFilePanelPickerHidden) {
        btnFilePanelPickerHidden.click();
      }
    });
  }

  if (btnFilePanelPickerHidden) {
    btnFilePanelPickerHidden.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        const firstFile = e.target.files[0];
        if (firstFile.path && filePanelDirPath) {
          const dirPath = firstFile.path.substring(0, firstFile.path.lastIndexOf('\\')) || firstFile.path.substring(0, firstFile.path.lastIndexOf('/'));
          filePanelDirPath.value = dirPath || firstFile.path;
          showToast(`Selected directory: ${filePanelDirPath.value}`, 'info');
          if (filePanelForm) filePanelForm.dispatchEvent(new Event('submit'));
        }
      }
    });
  }

  if (filePanelForm) {
    filePanelForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const pPath = filePanelDirPath.value.trim();
      if (!pPath) return;

      fileTreeContainer.innerHTML = '<div style="color:var(--text-dim);">Scanning directory tree...</div>';
      try {
        const res = await apiCall('/coding/read-project', 'POST', { project_path: pPath, max_files: 200 });
        renderFileTree(res.file_tree || [], pPath);
        showToast(`Loaded ${res.total_files} files from ${pPath}`, 'success');
      } catch (err) {
        fileTreeContainer.innerHTML = `<div style="color:var(--danger-red);">Error: ${err.message}</div>`;
      }
    });
  }

  const btnCopyFilePreview = document.getElementById('btnCopyFilePreview');
  if (btnCopyFilePreview) {
    btnCopyFilePreview.addEventListener('click', () => {
      if (filePreviewContent && filePreviewContent.textContent) {
        navigator.clipboard.writeText(filePreviewContent.textContent);
        showToast('Copied file preview code to clipboard!', 'success');
      }
    });
  }

  function buildTreeStructure(filePaths) {
    const root = { name: '', type: 'folder', children: {} };

    filePaths.forEach(pathStr => {
      const parts = pathStr.split('/');
      let current = root;

      for (let i = 0; i < parts.length; i++) {
        const part = parts[i];
        const isFile = (i === parts.length - 1);

        if (!current.children[part]) {
          current.children[part] = {
            name: part,
            path: parts.slice(0, i + 1).join('/'),
            type: isFile ? 'file' : 'folder',
            children: isFile ? null : {}
          };
        }
        if (!isFile) {
          current = current.children[part];
        }
      }
    });

    return root;
  }

  function renderTreeNode(node, container, baseDir, depth = 0) {
    const keys = Object.keys(node.children || {}).sort((a, b) => {
      const itemA = node.children[a];
      const itemB = node.children[b];
      if (itemA.type !== itemB.type) {
        return itemA.type === 'folder' ? -1 : 1;
      }
      return itemA.name.localeCompare(itemB.name);
    });

    keys.forEach(key => {
      const item = node.children[key];
      const row = document.createElement('div');
      row.style.userSelect = 'none';

      if (item.type === 'folder') {
        const folderHeader = document.createElement('div');
        folderHeader.className = 'history-item tree-folder';
        folderHeader.style.padding = '0.25rem 0.4rem';
        folderHeader.style.fontSize = '0.8rem';
        folderHeader.style.fontWeight = '600';
        folderHeader.style.cursor = 'pointer';
        folderHeader.style.display = 'flex';
        folderHeader.style.alignItems = 'center';
        folderHeader.style.gap = '0.35rem';
        folderHeader.style.color = 'var(--accent-cyan)';
        folderHeader.style.marginLeft = `${depth * 10}px`;

        folderHeader.innerHTML = `
          <span class="tree-toggle" style="font-size:0.75rem; width:12px; display:inline-block; text-align:center;">📂</span>
          <span class="history-icon" style="font-size:0.85rem;">📁</span>
          <span class="history-title" style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${item.name}</span>
        `;

        const childContainer = document.createElement('div');
        childContainer.className = 'tree-children';
        childContainer.style.display = 'block';

        folderHeader.addEventListener('click', (e) => {
          e.stopPropagation();
          const isHidden = childContainer.style.display === 'none';
          childContainer.style.display = isHidden ? 'block' : 'none';
          const toggleIcon = folderHeader.querySelector('.tree-toggle');
          if (toggleIcon) toggleIcon.textContent = isHidden ? '📂' : '📁';
        });

        row.appendChild(folderHeader);
        row.appendChild(childContainer);
        container.appendChild(row);

        renderTreeNode(item, childContainer, baseDir, depth + 1);
      } else {
        const fileItem = document.createElement('div');
        fileItem.className = 'history-item tree-file';
        fileItem.style.padding = '0.25rem 0.4rem';
        fileItem.style.fontSize = '0.8rem';
        fileItem.style.cursor = 'pointer';
        fileItem.style.display = 'flex';
        fileItem.style.alignItems = 'center';
        fileItem.style.gap = '0.35rem';
        fileItem.style.marginLeft = `${depth * 10}px`;

        const ext = item.name.substring(item.name.lastIndexOf('.')).toLowerCase();
        let icon = '📄';
        if (['.py'].includes(ext)) icon = '🐍';
        else if (['.js', '.ts', '.jsx', '.tsx'].includes(ext)) icon = '📜';
        else if (['.html', '.htm', '.css'].includes(ext)) icon = '🌐';
        else if (['.json', '.md', '.txt', '.yml', '.yaml'].includes(ext)) icon = '📝';
        else if (['.png', '.jpg', '.jpeg', '.svg', '.gif'].includes(ext)) icon = '🖼️';

        fileItem.innerHTML = `
          <span style="width:12px; display:inline-block;"></span>
          <span class="history-icon" style="font-size:0.85rem;">${icon}</span>
          <span class="history-title" style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${item.name}</span>
        `;

        fileItem.addEventListener('click', async (e) => {
          e.stopPropagation();
          document.querySelectorAll('#fileTreeContainer .history-item').forEach(i => i.classList.remove('active'));
          fileItem.classList.add('active');

          const relPath = item.path;
          if (filePreviewTitle) filePreviewTitle.textContent = `📄 Loading: ${relPath}...`;
          if (filePreviewContent) filePreviewContent.textContent = 'Loading file contents...';
          if (btnCopyFilePreview) btnCopyFilePreview.style.display = 'none';

          try {
            const res = await apiCall('/coding/read-file', 'POST', {
              project_path: baseDir,
              filepath: relPath
            });

            const sizeKb = (res.size_bytes / 1024).toFixed(1);
            if (filePreviewTitle) {
              filePreviewTitle.textContent = `📄 ${relPath} (${res.lines_count || 0} lines, ${sizeKb} KB)`;
            }
            if (filePreviewContent) {
              filePreviewContent.textContent = res.content || '[Empty File]';
            }
            if (btnCopyFilePreview) {
              btnCopyFilePreview.style.display = 'inline-block';
            }
          } catch (err) {
            if (filePreviewTitle) filePreviewTitle.textContent = `📄 ${relPath} [Error]`;
            if (filePreviewContent) {
              filePreviewContent.textContent = `File Preview Error: Could not load '${relPath}'\n\nDetails: ${err.message}`;
            }
          }
        });

        row.appendChild(fileItem);
        container.appendChild(row);
      }
    });
  }

  function renderFileTree(files, baseDir) {
    if (!fileTreeContainer) return;
    fileTreeContainer.innerHTML = '';

    if (files.length === 0) {
      fileTreeContainer.innerHTML = '<div style="color:var(--text-dim);">No files found in directory.</div>';
      return;
    }

    const treeRoot = buildTreeStructure(files);
    renderTreeNode(treeRoot, fileTreeContainer, baseDir, 0);
  }

  // ==========================================
  // TAB 8: SYSTEM MONITOR CONTROLLER
  // ==========================================
  const sysmonCpu = document.getElementById('sysmonCpu');
  const sysmonCpuBar = document.getElementById('sysmonCpuBar');
  const sysmonRam = document.getElementById('sysmonRam');
  const sysmonRamSub = document.getElementById('sysmonRamSub');
  const sysmonDisk = document.getElementById('sysmonDisk');
  const sysmonDiskSub = document.getElementById('sysmonDiskSub');
  const sysmonLatency = document.getElementById('sysmonLatency');
  const sysmonModel = document.getElementById('sysmonModel');
  const sysmonJsonOutput = document.getElementById('sysmonJsonOutput');

  async function pollSystemMetrics() {
    const t0 = Date.now();
    try {
      const data = await apiCall('/health/metrics', 'GET');
      const latency = Date.now() - t0;

      if (sysmonCpu) sysmonCpu.textContent = `${data.cpu_percent}%`;
      if (sysmonCpuBar) sysmonCpuBar.style.width = `${data.cpu_percent}%`;
      if (sysmonRam) sysmonRam.textContent = `${data.ram_percent}%`;
      if (sysmonRamSub) sysmonRamSub.textContent = `${data.ram_used_gb} GB / ${data.ram_total_gb} GB`;
      if (sysmonDisk) sysmonDisk.textContent = `${data.disk_percent}%`;
      if (sysmonDiskSub) sysmonDiskSub.textContent = `${data.disk_free_gb} GB Free`;
      if (sysmonLatency) sysmonLatency.textContent = `${latency} ms`;
      if (sysmonModel) sysmonModel.textContent = data.ollama_model || 'gemma3:latest';
      if (sysmonJsonOutput) sysmonJsonOutput.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
      if (sysmonCpu) sysmonCpu.textContent = 'N/A';
      if (sysmonRam) sysmonRam.textContent = 'N/A';
    }
  }

  pollSystemMetrics();
  setInterval(pollSystemMetrics, 4000);



  // ==========================================
  // TAB 2: SEMANTIC SEARCH CONTROLLER
  // ==========================================
  const searchIndexForm = document.getElementById('searchIndexForm');
  const indexFolderPath = document.getElementById('indexFolderPath');
  const startIndexBtn = document.getElementById('startIndexBtn');
  const btnBrowseFolder = document.getElementById('btnBrowseFolder');
  const btnFolderPickerHidden = document.getElementById('btnFolderPickerHidden');
  const indexProgressContainer = document.getElementById('indexProgressContainer');
  const indexStatusMessage = document.getElementById('indexStatusMessage');

  if (btnBrowseFolder) {
    btnBrowseFolder.addEventListener('click', async () => {
      if (window.electronAPI && window.electronAPI.selectDirectory) {
        try {
          const selectedPath = await window.electronAPI.selectDirectory();
          if (selectedPath) {
            indexFolderPath.value = selectedPath;
            showToast(`Selected directory: ${selectedPath}`, 'info');
          }
          return;
        } catch (err) {
          console.error('Electron folder dialog error:', err);
        }
      }
      if (btnFolderPickerHidden) {
        btnFolderPickerHidden.click();
      }
    });
  }

  if (btnFolderPickerHidden) {
    btnFolderPickerHidden.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        const firstFile = e.target.files[0];
        if (firstFile.path) {
          const lastSep = Math.max(firstFile.path.lastIndexOf('/'), firstFile.path.lastIndexOf('\\'));
          const dirPath = lastSep !== -1 ? firstFile.path.substring(0, lastSep) : firstFile.path;
          indexFolderPath.value = dirPath;
          showToast(`Selected directory: ${dirPath}`, 'info');
        } else if (firstFile.webkitRelativePath) {
          const folderName = firstFile.webkitRelativePath.split('/')[0];
          indexFolderPath.value = folderName;
          showToast(`Selected folder: ${folderName}`, 'info');
        }
      }
    });
  }

  // --- Semantic Search Subpanel Switcher (Semantic Vector Search vs File Panel & Explorer) ---
  const searchPills = document.querySelectorAll('.sub-nav-pill[data-search-tab]');
  searchPills.forEach(pill => {
    pill.addEventListener('click', () => {
      searchPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const targetTab = pill.getAttribute('data-search-tab');
      document.querySelectorAll('.search-subpanel').forEach(sp => sp.style.display = 'none');
      const targetPanel = document.getElementById(`search-panel-${targetTab}`);
      if (targetPanel) targetPanel.style.display = 'block';
    });
  });

  const searchQueryForm = document.getElementById('searchQueryForm');
  const searchQueryInput = document.getElementById('searchQueryInput');
  const searchResultsBody = document.getElementById('searchResultsBody');

  if (searchIndexForm) {
    searchIndexForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      if (startIndexBtn) startIndexBtn.disabled = true;
      if (indexProgressContainer) indexProgressContainer.style.display = 'block';
      if (indexStatusMessage) {
        indexStatusMessage.style.display = 'block';
        indexStatusMessage.textContent = 'Scanning & indexing system drives (C:\\ & D:\\)...';
      }

      try {
        const res = await apiCall('/search/index', 'POST', {
          folder_path: "ALL_DRIVES",
          recursive: true
        });

        if (indexStatusMessage) {
          indexStatusMessage.textContent = `✅ Index Active: Scanned ${res.files_scanned || res.files_found} files across system drives (Total ${res.total_indexed_in_db || res.files_found} vectors saved in persistent storage). Scan completed in ${res.execution_time_ms}ms.`;
        }
        showToast(`Indexed ${res.files_scanned || res.files_found} system files!`, 'success');
      } catch (err) {
        if (indexStatusMessage) {
          indexStatusMessage.textContent = `Indexing failed: ${err.message}`;
        }
      } finally {
        if (startIndexBtn) startIndexBtn.disabled = false;
        if (indexProgressContainer) indexProgressContainer.style.display = 'none';
      }
    });
  }

  searchQueryForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = searchQueryInput.value.trim();
    if (!query) return;

    searchResultsBody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:1.5rem;"><div class="spinner" style="margin:0 auto;"></div></td></tr>';

    try {
      const res = await apiCall('/search/query', 'POST', { query, top_k: 5 });

      if (!res.results || res.results.length === 0) {
        searchResultsBody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:var(--text-dim); padding:1.5rem;">No matching documents found. Ensure folder is indexed first.</td></tr>';
        return;
      }

      searchResultsBody.innerHTML = '';
      res.results.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${item.filename}</strong> <span class="pill pill-cyan">${item.file_type}</span></td>
          <td><span class="pill pill-green">${(item.score * 100).toFixed(1)}%</span></td>
          <td><div style="max-height:60px; overflow-y:auto; font-size:0.8rem;">${item.snippet}</div></td>
          <td style="font-family:var(--font-mono); font-size:0.75rem; color:var(--text-muted);">${item.location}</td>
        `;
        searchResultsBody.appendChild(tr);
      });
      showToast(`Found ${res.results.length} search results`, 'success');
    } catch (err) {
      searchResultsBody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--danger-red); padding:1.5rem;">Search failed: ${err.message}</td></tr>`;
    }
  });

  // ==========================================
  // TAB 3: RAG DOCUMENT ASSISTANT CONTROLLER
  // ==========================================
  const ragIndexForm = document.getElementById('ragIndexForm');
  const ragFilePath = document.getElementById('ragFilePath');
  const ragIndexBtn = document.getElementById('ragIndexBtn');
  const ragSummarizeBtn = document.getElementById('ragSummarizeBtn');
  const btnBrowseRagFile = document.getElementById('btnBrowseRagFile');
  const btnFilePickerHidden = document.getElementById('btnFilePickerHidden');
  const ragSummaryOutputCard = document.getElementById('ragSummaryOutputCard');
  const ragSummaryText = document.getElementById('ragSummaryText');

  if (btnBrowseRagFile) {
    btnBrowseRagFile.addEventListener('click', async () => {
      if (window.electronAPI && window.electronAPI.selectFile) {
        try {
          const selectedPath = await window.electronAPI.selectFile();
          if (selectedPath) {
            ragFilePath.value = selectedPath;
            showToast(`Selected file: ${selectedPath}`, 'info');
          }
          return;
        } catch (err) {
          console.error('Electron file dialog error:', err);
        }
      }
      if (btnFilePickerHidden) {
        btnFilePickerHidden.click();
      }
    });
  }

  if (btnFilePickerHidden) {
    btnFilePickerHidden.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        const file = e.target.files[0];
        if (file.path) {
          ragFilePath.value = file.path;
          showToast(`Selected file: ${file.path}`, 'info');
        }
      }
    });
  }

  const ragQueryForm = document.getElementById('ragQueryForm');
  const ragQueryInput = document.getElementById('ragQueryInput');
  const ragChatMessages = document.getElementById('ragChatMessages');

  ragIndexForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fp = ragFilePath.value.trim();
    if (!fp) return;

    ragIndexBtn.disabled = true;
    try {
      const res = await apiCall('/rag/index', 'POST', { filepath: fp });
      showToast(`Document indexed: ${res.chunks_indexed} chunks created!`, 'success');
    } catch (err) {
      // toast shown automatically
    } finally {
      ragIndexBtn.disabled = false;
    }
  });

  if (ragSummarizeBtn) {
    ragSummarizeBtn.addEventListener('click', async () => {
      const fp = ragFilePath.value.trim();
      if (!fp) {
        showToast('Please enter a document filepath first.', 'warning');
        return;
      }

      ragSummarizeBtn.disabled = true;
      if (ragSummaryOutputCard) ragSummaryOutputCard.style.display = 'block';
      if (ragSummaryText) ragSummaryText.textContent = 'Generating document summary using local Ollama LLM...';

      try {
        const res = await apiCall('/rag/summarize', 'POST', { filepath: fp });
        if (ragSummaryText) ragSummaryText.textContent = res.summary;
        showToast('Document summary generated!', 'success');
      } catch (err) {
        if (ragSummaryText) ragSummaryText.textContent = `Summarization error: ${err.message}`;
      } finally {
        ragSummarizeBtn.disabled = false;
      }
    });
  }

  ragQueryForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = ragQueryInput.value.trim();
    if (!query) return;

    const fp = ragFilePath.value.trim();

    const uBubble = document.createElement('div');
    uBubble.className = 'chat-bubble user';
    const uContent = document.createElement('div');
    uContent.className = 'msg-content';
    uContent.textContent = query;
    uBubble.appendChild(uContent);
    ragChatMessages.appendChild(uBubble);

    ragQueryInput.value = '';
    ragChatMessages.scrollTop = ragChatMessages.scrollHeight;

    const aBubble = document.createElement('div');
    aBubble.className = 'chat-bubble assistant';
    const aContent = document.createElement('div');
    aContent.className = 'msg-content';
    aContent.textContent = 'Searching document context & synthesizing answer...';
    aBubble.appendChild(aContent);
    ragChatMessages.appendChild(aBubble);

    const ragModelSelect = document.getElementById('ragModelSelect');
    const selectedModel = ragModelSelect ? ragModelSelect.value : null;

    try {
      const res = await apiCall('/rag/query', 'POST', {
        query: query,
        filepath: fp || null,
        top_k: 5,
        model: selectedModel
      });

      aContent.innerHTML = renderMarkdown(res.answer);

      if (res.sources && res.sources.length > 0) {
        const aMeta = document.createElement('div');
        aMeta.className = 'msg-meta';
        aMeta.style.flexDirection = 'column';
        aMeta.style.gap = '0.2rem';
        let sourcesHtml = '';
        res.sources.forEach(s => {
          const sec = s.section_title ? ` (${s.section_title})` : '';
          sourcesHtml += `<div>📄 <strong>${s.filename}</strong>${sec} - Match ${(s.score * 100).toFixed(0)}%</div>`;
        });
        aMeta.innerHTML = sourcesHtml;
        aBubble.appendChild(aMeta);
      }
    } catch (err) {
      aContent.innerHTML = `<span style="color:var(--danger-red);">Error: ${err.message}</span>`;
    } finally {
      ragChatMessages.scrollTop = ragChatMessages.scrollHeight;
    }
  });

  // ==========================================
  // TAB 4: DESKTOP VOICE CONTROL CENTER
  // ==========================================
  const btnDesktopInfoIcon = document.getElementById('btnDesktopInfoIcon');
  const desktopInfoPopover = document.getElementById('desktopInfoPopover');
  const btnVoiceMic = document.getElementById('btnVoiceMic');
  const voiceStatusText = document.getElementById('voiceStatusText');
  const voiceResultCard = document.getElementById('voiceResultCard');
  const voiceTranscriptText = document.getElementById('voiceTranscriptText');
  const voiceResponseBox = document.getElementById('voiceResponseBox');
  const voiceTextForm = document.getElementById('voiceTextForm');
  const voiceTextInput = document.getElementById('voiceTextInput');
  const screenshotPreviewCard = document.getElementById('screenshotPreviewCard');
  const screenshotImg = document.getElementById('screenshotImg');
  const screenshotMeta = document.getElementById('screenshotMeta');

  // Toggle info popover on click if mobile/touch or desktop
  if (btnDesktopInfoIcon && desktopInfoPopover) {
    btnDesktopInfoIcon.addEventListener('click', (e) => {
      e.stopPropagation();
      desktopInfoPopover.classList.toggle('active');
    });
    document.addEventListener('click', () => {
      desktopInfoPopover.classList.remove('active');
    });
  }

  // --- Laptop Password Confirmation Modal System ---
  const modalPasswordConfirmation = document.getElementById('modalPasswordConfirmation');
  const modalPasswordTitle = document.getElementById('modalPasswordTitle');
  const modalPasswordMessage = document.getElementById('modalPasswordMessage');
  const laptopPasswordInput = document.getElementById('laptopPasswordInput');
  const modalPasswordCancelBtn = document.getElementById('modalPasswordCancelBtn');
  const passwordConfirmForm = document.getElementById('passwordConfirmForm');
  let pendingPasswordAction = null;

  function promptPasswordConfirmation(title, message, callback) {
    if (modalPasswordTitle) modalPasswordTitle.textContent = title;
    if (modalPasswordMessage) modalPasswordMessage.textContent = message;
    if (laptopPasswordInput) laptopPasswordInput.value = '';
    pendingPasswordAction = callback;
    if (modalPasswordConfirmation) modalPasswordConfirmation.classList.add('active');
    if (laptopPasswordInput) laptopPasswordInput.focus();
  }

  if (modalPasswordCancelBtn) {
    modalPasswordCancelBtn.addEventListener('click', () => {
      if (modalPasswordConfirmation) modalPasswordConfirmation.classList.remove('active');
      pendingPasswordAction = null;
      showToast('Dangerous action cancelled by user.', 'info');
    });
  }

  if (passwordConfirmForm) {
    passwordConfirmForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const pwd = laptopPasswordInput ? laptopPasswordInput.value.trim() : '';
      if (!pwd) {
        showToast('Laptop password is required for confirmation!', 'warning');
        return;
      }
      if (modalPasswordConfirmation) modalPasswordConfirmation.classList.remove('active');
      if (pendingPasswordAction) {
        const actionToExec = pendingPasswordAction;
        pendingPasswordAction = null;
        actionToExec(pwd);
      }
    });
  }

  // --- Helper: Convert AudioBlob to Base64 WAV ---
  async function audioBlobToBase64Wav(blob) {
    const arrayBuffer = await blob.arrayBuffer();
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

    const numOfChan = audioBuffer.numberOfChannels;
    const sampleRate = audioBuffer.sampleRate;
    const length = audioBuffer.length * numOfChan * 2 + 44;
    const buffer = new ArrayBuffer(length);
    const view = new DataView(buffer);
    const channels = [];
    let sample, offset = 0, pos = 0;

    function setUint32(data) { view.setUint32(pos, data, true); pos += 4; }
    function setUint16(data) { view.setUint16(pos, data, true); pos += 2; }

    setUint32(0x46464952); // "RIFF"
    setUint32(length - 8);
    setUint32(0x45564157); // "WAVE"
    setUint32(0x20746d66); // "fmt "
    setUint32(16);
    setUint16(1); // PCM
    setUint16(numOfChan);
    setUint32(sampleRate);
    setUint32(sampleRate * 2 * numOfChan);
    setUint16(numOfChan * 2);
    setUint16(16);
    setUint32(0x61746164); // "data"
    setUint32(length - pos - 4);

    for (let i = 0; i < numOfChan; i++) channels.push(audioBuffer.getChannelData(i));

    while (offset < audioBuffer.length) {
      for (let i = 0; i < numOfChan; i++) {
        sample = Math.max(-1, Math.min(1, channels[i][offset]));
        sample = (0.5 + sample < 0 ? sample * 32768 : sample * 32767) | 0;
        view.setInt16(pos, sample, true);
        pos += 2;
      }
      offset++;
    }

    let binary = '';
    const bytes = new Uint8Array(buffer);
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }

  // --- Native Local Microphone Assistant ---
  let mediaRecorder = null;
  let audioChunks = [];
  let isListening = false;

  async function startLocalAudioRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunks = [];
      mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        isListening = false;
        if (btnVoiceMic) btnVoiceMic.classList.remove('listening');

        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        if (audioBlob.size < 500) {
          showToast('Voice recording was too short.', 'warning');
          return;
        }

        if (voiceStatusText) voiceStatusText.textContent = '⚙️ Transcribing audio & executing spoken desktop command...';
        if (voiceResultCard) voiceResultCard.style.display = 'flex';
        if (voiceTranscriptText) voiceTranscriptText.textContent = '"Analyzing spoken voice..."';
        if (voiceResponseBox) voiceResponseBox.textContent = '⚙️ Processing...';

        try {
          const wavBase64 = await audioBlobToBase64Wav(audioBlob);
          const res = await apiCall('/automation/voice-audio', 'POST', { audio_base64: wavBase64 });

          if (res.command && voiceTranscriptText) {
            voiceTranscriptText.textContent = `"${res.command}"`;
          }

          if (res.status === 'confirmation_required') {
            if (voiceResponseBox) voiceResponseBox.textContent = `🔒 ${res.response_text}`;
            promptPasswordConfirmation(
              '🔒 Security Protection Required',
              res.response_text,
              async (pwd) => {
                try {
                  if (res.action === 'delete_file') {
                    await apiCall('/automation/file/delete', 'POST', { file_path: res.details?.target_path || res.command, confirmed: true, password: pwd });
                    showToast('Deleted file successfully!', 'success');
                  } else if (res.action === 'close_app') {
                    await apiCall('/automation/app/close', 'POST', { app_name: res.details?.app_name || res.command, confirmed: true, password: pwd });
                    showToast('Closed application!', 'success');
                  } else if (res.action?.startsWith('power_')) {
                    const act = res.action.replace('power_', '');
                    await apiCall(`/automation/power/${act}`, 'POST', { confirmed: true, delay_seconds: 10, password: pwd });
                    showToast(`System ${act} initiated!`, 'warning');
                  }
                  if (voiceResponseBox) voiceResponseBox.textContent = `✅ Security password verified! Action executed.`;
                } catch (err) {
                  if (voiceResponseBox) voiceResponseBox.textContent = `❌ Execution failed: ${err.message}`;
                }
              }
            );
          } else {
            if (voiceResponseBox) voiceResponseBox.textContent = res.response_text || 'Command executed successfully.';
            if (voiceStatusText) voiceStatusText.textContent = `✅ Voice Executed: ${res.response_text}`;
            showToast(res.response_text || 'Voice command executed', res.status === 'error' ? 'warning' : 'success');
          }
        } catch (err) {
          if (voiceResponseBox) voiceResponseBox.textContent = `❌ Audio execution error: ${err.message}`;
          if (voiceStatusText) voiceStatusText.textContent = `Execution error: ${err.message}`;
        }
      };

      mediaRecorder.start();
      isListening = true;
      if (btnVoiceMic) btnVoiceMic.classList.add('listening');
      if (voiceStatusText) voiceStatusText.textContent = '🔴 Microphone Active! Speak your desktop command now. Click mic again when finished.';
      showToast('Microphone Active: Speak your command', 'info');
    } catch (err) {
      isListening = false;
      if (btnVoiceMic) btnVoiceMic.classList.remove('listening');
      if (voiceStatusText) voiceStatusText.textContent = `Microphone permission/access error: ${err.message}. Enter command below.`;
      showToast(`Microphone error: ${err.message}`, 'warning');
      if (voiceTextInput) voiceTextInput.focus();
    }
  }

  if (btnVoiceMic) {
    btnVoiceMic.addEventListener('click', async () => {
      if (isListening) {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
          mediaRecorder.stop();
          if (mediaRecorder.stream) {
            mediaRecorder.stream.getTracks().forEach(t => t.stop());
          }
        }
        isListening = false;
        if (btnVoiceMic) btnVoiceMic.classList.remove('listening');
        return;
      }

      await startLocalAudioRecording();
    });
  }

  async function executeSpokenCommand(spokenText) {
    if (!spokenText || !spokenText.trim()) return;
    const cleanCmd = spokenText.trim();

    if (voiceResultCard) voiceResultCard.style.display = 'flex';
    if (voiceTranscriptText) voiceTranscriptText.textContent = `"${cleanCmd}"`;
    if (voiceResponseBox) voiceResponseBox.textContent = '⚙️ Processing spoken voice instruction...';

    try {
      const res = await apiCall('/automation/voice-command', 'POST', { command: cleanCmd });

      if (res.status === 'confirmation_required') {
        if (voiceResponseBox) voiceResponseBox.textContent = `🔒 ${res.response_text}`;

        // Trigger Laptop Password modal
        promptPasswordConfirmation(
          '🔒 Security Protection Required',
          res.response_text,
          async (pwd) => {
            try {
              if (res.action === 'delete_file') {
                await apiCall('/automation/file/delete', 'POST', { file_path: res.details?.target_path || cleanCmd, confirmed: true, password: pwd });
                showToast('Deleted file successfully!', 'success');
              } else if (res.action === 'close_app') {
                await apiCall('/automation/app/close', 'POST', { app_name: res.details?.app_name || cleanCmd, confirmed: true, password: pwd });
                showToast('Closed application!', 'success');
              } else if (res.action?.startsWith('power_')) {
                const act = res.action.replace('power_', '');
                await apiCall(`/automation/power/${act}`, 'POST', { confirmed: true, delay_seconds: 10, password: pwd });
                showToast(`System ${act} initiated!`, 'warning');
              }
              if (voiceResponseBox) voiceResponseBox.textContent = `✅ Security password verified! Action executed.`;
            } catch (err) {
              if (voiceResponseBox) voiceResponseBox.textContent = `❌ Execution failed: ${err.message}`;
            }
          }
        );
      } else {
        if (voiceResponseBox) voiceResponseBox.textContent = res.response_text || 'Action executed successfully.';
        showToast(res.response_text || 'Voice command executed', 'success');

        // If screenshot was taken, show preview artifact
        if (res.action === 'take_screenshot' && res.details?.details) {
          const dt = res.details.details;
          if (screenshotPreviewCard && screenshotImg) {
            screenshotPreviewCard.style.display = 'block';
            screenshotImg.src = dt.base64_preview.length > 500 ? dt.base64_preview : `data:image/png;base64,${dt.base64_preview}`;
            if (screenshotMeta) screenshotMeta.textContent = `Saved to: ${dt.file_path}`;
          }
        }
      }
    } catch (err) {
      if (voiceResponseBox) voiceResponseBox.textContent = `❌ Error: ${err.message}`;
    }
  }

  if (voiceTextForm) {
    voiceTextForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const txt = voiceTextInput ? voiceTextInput.value.trim() : '';
      if (!txt) return;
      executeSpokenCommand(txt);
      voiceTextInput.value = '';
    });
  }

  // ==========================================
  // TAB 5: BROWSER AUTOMATION CONTROLLER
  // ==========================================
  const browserTypeSelect = document.getElementById('browserTypeSelect');
  const browserOpenForm = document.getElementById('browserOpenForm');
  const browserUrlInput = document.getElementById('browserUrlInput');

  const googleSearchForm = document.getElementById('googleSearchForm');
  const googleQueryInput = document.getElementById('googleQueryInput');

  const youtubeSearchForm = document.getElementById('youtubeSearchForm');
  const youtubeQueryInput = document.getElementById('youtubeQueryInput');

  const btnOpenGitHub = document.getElementById('btnOpenGitHub');
  const btnOpenLinkedIn = document.getElementById('btnOpenLinkedIn');

  const browserAgentForm = document.getElementById('browserAgentForm');
  const browserAgentTaskInput = document.getElementById('browserAgentTaskInput');
  const btnRunBrowserAgent = document.getElementById('btnRunBrowserAgent');
  const browserAgentOutput = document.getElementById('browserAgentOutput');

  const browserResultsBody = document.getElementById('browserResultsBody');

  // Open Website (Optional legacy handler)
  if (browserOpenForm) {
    browserOpenForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const url = browserUrlInput ? browserUrlInput.value.trim() : '';
      if (!url) return;

      try {
        const res = await apiCall('/browser/open', 'POST', {
          url,
          browser: browserTypeSelect ? browserTypeSelect.value : 'chrome',
          headless: true
        });
        showToast(`Navigated to '${res.data.title}'`, 'success');
      } catch (err) { }
    });
  }

  // Google Search (Optional legacy handler)
  if (googleSearchForm) {
    googleSearchForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const q = googleQueryInput ? googleQueryInput.value.trim() : '';
      if (!q) return;

      if (browserResultsBody) {
        browserResultsBody.innerHTML = '<tr><td colspan="3" style="text-align:center; padding:1.5rem;"><div class="spinner" style="margin:0 auto;"></div></td></tr>';
      }

      try {
        const res = await apiCall('/browser/search/google', 'POST', {
          query: q,
          browser: browserTypeSelect ? browserTypeSelect.value : 'chrome',
          headless: true
        });

        renderBrowserResults(res.data.results, 'Google Search');
        showToast(`Google Search returned ${res.data.results.length} results`, 'success');
      } catch (err) {
        if (browserResultsBody) {
          browserResultsBody.innerHTML = `<tr><td colspan="3" style="text-align:center; color:var(--danger-red); padding:1.5rem;">Search failed: ${err.message}</td></tr>`;
        }
      }
    });
  }

  // YouTube Search (Optional legacy handler)
  if (youtubeSearchForm) {
    youtubeSearchForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const q = youtubeQueryInput ? youtubeQueryInput.value.trim() : '';
      if (!q) return;

      if (browserResultsBody) {
        browserResultsBody.innerHTML = '<tr><td colspan="3" style="text-align:center; padding:1.5rem;"><div class="spinner" style="margin:0 auto;"></div></td></tr>';
      }

      try {
        const res = await apiCall('/browser/search/youtube', 'POST', {
          query: q,
          browser: browserTypeSelect ? browserTypeSelect.value : 'chrome',
          headless: true
        });

        renderBrowserResults(res.data.videos, 'YouTube');
        showToast(`YouTube Search returned ${res.data.videos.length} videos`, 'success');
      } catch (err) {
        if (browserResultsBody) {
          browserResultsBody.innerHTML = `<tr><td colspan="3" style="text-align:center; color:var(--danger-red); padding:1.5rem;">YouTube search failed: ${err.message}</td></tr>`;
        }
      }
    });
  }

  if (btnOpenGitHub) {
    btnOpenGitHub.addEventListener('click', async () => {
      try {
        const res = await apiCall('/browser/github', 'POST', {
          browser: browserTypeSelect ? browserTypeSelect.value : 'chrome',
          headless: true
        });
        showToast('Opened GitHub portal!', 'success');
      } catch (err) { }
    });
  }

  if (btnOpenLinkedIn) {
    btnOpenLinkedIn.addEventListener('click', async () => {
      try {
        const res = await apiCall('/browser/linkedin', 'POST', {
          browser: browserTypeSelect ? browserTypeSelect.value : 'chrome',
          headless: true
        });
        showToast('Opened LinkedIn portal!', 'success');
      } catch (err) { }
    });
  }

  // Helper: Renders markdown formatting into structured HTML for Browser Agent
  function renderFormattedMarkdown(text) {
    if (!text) return '';
    let html = text;

    // Escape HTML special characters
    html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    // Headers: ###, ##, #
    html = html.replace(/^### (.*$)/gim, '<h4 style="color:var(--accent-cyan); font-weight:600; margin:0.4rem 0 0.4rem 0; font-size:0.95rem;">$1</h4>');
    html = html.replace(/^## (.*$)/gim, '<h3 style="color:var(--accent-cyan); font-weight:600; margin:0.5rem 0 0.4rem 0; font-size:1rem;">$1</h3>');
    html = html.replace(/^# (.*$)/gim, '<h2 style="color:var(--accent-cyan); font-weight:700; margin:0.6rem 0 0.4rem 0; font-size:1.1rem;">$1</h2>');

    // Markdown Links: [Title](url) -> <a href="url" target="_blank">Title 🔗</a>
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="color:var(--accent-cyan); text-decoration:underline; font-weight:500;">$1 🔗</a>');

    // Bold & Italic
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em style="color:var(--text-muted);">$1</em>');

    // Line items (numbered or bullet points)
    const lines = html.split('\n');
    const formattedLines = lines.map(line => {
      const trimmed = line.trim();
      if (!trimmed) return '';
      if (/^\d+\.\s/.test(trimmed)) {
        return `<div style="margin-bottom:0.4rem; padding:0.35rem 0.6rem; background:rgba(255,255,255,0.03); border-left:3px solid var(--accent-cyan); border-radius:4px;">${line}</div>`;
      }
      if (/^[-*]\s/.test(trimmed)) {
        return `<div style="margin-bottom:0.3rem; padding-left:0.5rem;">${line}</div>`;
      }
      return `<div style="margin-bottom:0.25rem;">${line}</div>`;
    });

    return formattedLines.join('');
  }

  // Browser Agent Runner
  browserAgentForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const task = browserAgentTaskInput.value.trim();
    if (!task) return;

    btnRunBrowserAgent.disabled = true;
    browserAgentOutput.innerHTML = '<span style="color:var(--accent-cyan);">⚙️ Autonomous Browser Agent executing task...</span>';

    try {
      const res = await apiCall('/browser/agent/execute', 'POST', {
        task: task,
        browser: browserTypeSelect.value,
        headless: true
      });

      const summaryText = res.data ? (res.data.summary || JSON.stringify(res.data, null, 2)) : 'Task completed.';
      browserAgentOutput.innerHTML = renderFormattedMarkdown(summaryText);
      if (res.data && res.data.data && Array.isArray(res.data.data)) {
        renderBrowserResults(res.data.data, 'Browser Agent');
      }
      showToast('Browser Agent completed task!', 'success');
    } catch (err) {
      browserAgentOutput.innerHTML = `<span style="color:var(--danger-red);">Agent Task Error: ${err.message}</span>`;
    } finally {
      btnRunBrowserAgent.disabled = false;
    }
  });

  function renderBrowserResults(items, sourceName) {
    if (!items || items.length === 0) {
      browserResultsBody.innerHTML = '<tr><td colspan="3" style="text-align:center; color:var(--text-dim); padding:1.5rem;">No web results returned.</td></tr>';
      return;
    }

    browserResultsBody.innerHTML = '';
    items.forEach(item => {
      const tr = document.createElement('tr');
      const title = item.title || item.name || 'Untitled';
      const url = item.url || '#';
      const extra = item.channel || item.snippet || sourceName;

      tr.innerHTML = `
        <td><strong>${title}</strong></td>
        <td><a href="${url}" target="_blank" style="color:var(--accent-cyan); font-family:var(--font-mono); font-size:0.75rem;">${url}</a></td>
        <td><span class="pill pill-purple">${extra}</span></td>
      `;
      browserResultsBody.appendChild(tr);
    });
  }

  // ==========================================
  // TAB 6: AI CODING ASSISTANT CONTROLLER
  // ==========================================
  const codingModeSelect = document.getElementById('codingModeSelect');
  const codingSubpanels = document.querySelectorAll('.coding-subpanel');

  if (codingModeSelect) {
    codingModeSelect.addEventListener('change', (e) => {
      const targetSub = e.target.value;

      codingSubpanels.forEach(p => {
        p.style.display = 'none';
        p.classList.remove('active');
      });

      const targetPanel = document.getElementById(`coding-panel-${targetSub}`);
      if (targetPanel) {
        targetPanel.style.display = 'block';
        targetPanel.classList.add('active');
      }
    });
  }

  // 1. Read Project
  const codingReadProjectForm = document.getElementById('codingReadProjectForm');
  const codingProjectPathInput = document.getElementById('codingProjectPathInput');
  const btnBrowseCodingProjectDir = document.getElementById('btnBrowseCodingProjectDir');
  const btnCodingProjectPickerHidden = document.getElementById('btnCodingProjectPickerHidden');
  const codingProjectOutput = document.getElementById('codingProjectOutput');

  if (btnBrowseCodingProjectDir) {
    btnBrowseCodingProjectDir.addEventListener('click', async () => {
      if (window.electronAPI && window.electronAPI.selectDirectory) {
        const selectedDir = await window.electronAPI.selectDirectory();
        if (selectedDir && codingProjectPathInput) {
          codingProjectPathInput.value = selectedDir;
          showToast(`Selected directory: ${selectedDir}`, 'info');
          if (codingReadProjectForm) codingReadProjectForm.dispatchEvent(new Event('submit'));
        }
        return;
      }
      if (btnCodingProjectPickerHidden) {
        btnCodingProjectPickerHidden.click();
      }
    });
  }

  if (btnCodingProjectPickerHidden) {
    btnCodingProjectPickerHidden.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        const firstFile = e.target.files[0];
        if (firstFile.path && codingProjectPathInput) {
          const dirPath = firstFile.path.substring(0, firstFile.path.lastIndexOf('\\')) || firstFile.path.substring(0, firstFile.path.lastIndexOf('/'));
          codingProjectPathInput.value = dirPath || firstFile.path;
          showToast(`Selected directory: ${codingProjectPathInput.value}`, 'info');
          if (codingReadProjectForm) codingReadProjectForm.dispatchEvent(new Event('submit'));
        }
      }
    });
  }

  if (codingReadProjectForm) {
    codingReadProjectForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const pPath = codingProjectPathInput.value.trim();
      if (!pPath) return;

      codingProjectOutput.textContent = 'Scanning project codebase structure...';
      try {
        const res = await apiCall('/coding/read-project', 'POST', { project_path: pPath });
        codingProjectOutput.textContent = JSON.stringify(res, null, 2);
        showToast(`Scanned ${res.total_files} project files!`, 'success');
      } catch (err) {
        codingProjectOutput.textContent = `Error scanning project: ${err.message}`;
      }
    });
  }

  // 2. Code Assistant (Unified Generate, Explain & Debug)
  const codingAssistantForm = document.getElementById('codingAssistantForm');
  const codingAssistantAction = document.getElementById('codingAssistantAction');
  const codingAssistantLang = document.getElementById('codingAssistantLang');
  const codingAssistantPrompt = document.getElementById('codingAssistantPrompt');
  const codingAssistantErrorGroup = document.getElementById('codingAssistantErrorGroup');
  const codingAssistantErrorLog = document.getElementById('codingAssistantErrorLog');
  const codingAssistantOutput = document.getElementById('codingAssistantOutput');

  if (codingAssistantAction) {
    codingAssistantAction.addEventListener('change', () => {
      const act = codingAssistantAction.value;
      if (codingAssistantErrorGroup) {
        codingAssistantErrorGroup.style.display = (act === 'debug') ? 'block' : 'none';
      }
      if (act === 'generate') {
        codingAssistantPrompt.placeholder = "Enter prompt e.g. 'Write a Python utility to parse JSON log files and extract errors'...";
      } else if (act === 'explain') {
        codingAssistantPrompt.placeholder = "Paste code snippet to explain logic, variables, and function breakdown...";
      } else if (act === 'debug') {
        codingAssistantPrompt.placeholder = "Paste failing / buggy code snippet here...";
      }
    });
  }

  if (codingAssistantForm) {
    codingAssistantForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const action = codingAssistantAction ? codingAssistantAction.value : 'generate';
      const promptText = codingAssistantPrompt.value.trim();
      const lang = codingAssistantLang ? codingAssistantLang.value : 'python';
      const errLog = codingAssistantErrorLog ? codingAssistantErrorLog.value.trim() : '';

      if (!promptText) return;

      codingAssistantOutput.textContent = `Executing ${action} action...`;

      try {
        if (action === 'generate') {
          const res = await apiCall('/coding/generate', 'POST', {
            prompt: promptText,
            language: lang
          });
          codingAssistantOutput.textContent = res.generated_code || res.explanation;
          showToast('Code generated successfully!', 'success');
        } else if (action === 'explain') {
          const res = await apiCall('/coding/explain', 'POST', {
            code_snippet: promptText,
            language: lang
          });
          codingAssistantOutput.textContent = res.explanation;
          showToast('Code explanation generated!', 'success');
        } else if (action === 'debug') {
          const res = await apiCall('/coding/debug', 'POST', {
            code_snippet: promptText,
            error_log: errLog || null
          });
          codingAssistantOutput.textContent = `### Diagnosis & Root Cause\n${res.diagnosis}\n\n### Fixed Code\n\`\`\`${res.language}\n${res.fixed_code}\n\`\`\``;
          showToast('Debug analysis completed!', 'success');
        }
      } catch (err) {
        codingAssistantOutput.textContent = `Action Error: ${err.message}`;
      }
    });
  }

  // 5. Refactor & Suggest Improvements
  const codingSuggestForm = document.getElementById('codingSuggestForm');
  const codingSuggestAspect = document.getElementById('codingSuggestAspect');
  const codingSuggestCode = document.getElementById('codingSuggestCode');
  const codingSuggestOutput = document.getElementById('codingSuggestOutput');

  codingSuggestForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const code = codingSuggestCode.value.trim();
    if (!code) return;

    codingSuggestOutput.textContent = 'Conducting code review & refactoring analysis...';
    try {
      const res = await apiCall('/coding/suggest-improvements', 'POST', {
        code_snippet: code,
        aspect: codingSuggestAspect.value
      });
      codingSuggestOutput.textContent = res.suggestions;
      showToast('Code refactoring suggestions generated!', 'success');
    } catch (err) {
      codingSuggestOutput.textContent = `Review Error: ${err.message}`;
    }
  });

  // 6. Generate Docs
  const codingDocsForm = document.getElementById('codingDocsForm');
  const codingDocsFormat = document.getElementById('codingDocsFormat');
  const codingDocsCode = document.getElementById('codingDocsCode');
  const codingDocsOutput = document.getElementById('codingDocsOutput');

  codingDocsForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const code = codingDocsCode.value.trim();
    if (!code) return;

    codingDocsOutput.textContent = 'Generating documentation...';
    try {
      const res = await apiCall('/coding/generate-docs', 'POST', {
        code_snippet: code,
        doc_format: codingDocsFormat.value
      });
      codingDocsOutput.textContent = res.documentation;
      showToast('Documentation generated!', 'success');
    } catch (err) {
      codingDocsOutput.textContent = `Docs Error: ${err.message}`;
    }
  });

  // 7. Repo Question
  const codingRepoForm = document.getElementById('codingRepoForm');
  const codingRepoPath = document.getElementById('codingRepoPath');
  const btnBrowseCodingRepoDir = document.getElementById('btnBrowseCodingRepoDir');
  const btnCodingRepoPickerHidden = document.getElementById('btnCodingRepoPickerHidden');
  const codingRepoQuestion = document.getElementById('codingRepoQuestion');
  const codingRepoOutput = document.getElementById('codingRepoOutput');

  if (btnBrowseCodingRepoDir) {
    btnBrowseCodingRepoDir.addEventListener('click', async () => {
      if (window.electronAPI && window.electronAPI.selectDirectory) {
        const selectedDir = await window.electronAPI.selectDirectory();
        if (selectedDir && codingRepoPath) {
          codingRepoPath.value = selectedDir;
          showToast(`Selected directory: ${selectedDir}`, 'info');
        }
        return;
      }
      if (btnCodingRepoPickerHidden) {
        btnCodingRepoPickerHidden.click();
      }
    });
  }

  if (btnCodingRepoPickerHidden) {
    btnCodingRepoPickerHidden.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        const firstFile = e.target.files[0];
        if (firstFile.path && codingRepoPath) {
          const dirPath = firstFile.path.substring(0, firstFile.path.lastIndexOf('\\')) || firstFile.path.substring(0, firstFile.path.lastIndexOf('/'));
          codingRepoPath.value = dirPath || firstFile.path;
          showToast(`Selected directory: ${codingRepoPath.value}`, 'info');
        }
      }
    });
  }

  if (codingRepoForm) {
    codingRepoForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const q = codingRepoQuestion.value.trim();
      if (!q) return;

      codingRepoOutput.textContent = 'Evaluating repository code structure & answering question...';
      try {
        const res = await apiCall('/coding/repo-question', 'POST', {
          question: q,
          project_path: codingRepoPath.value.trim() || null
        });
        codingRepoOutput.textContent = res.answer;
        showToast('Repository question answered!', 'success');
      } catch (err) {
        codingRepoOutput.textContent = `Repo Question Error: ${err.message}`;
      }
    });
  }

  // Settings & Monitor subnav pill switching
  const settingsSubnavPills = document.querySelectorAll('.settings-subnav-pill');
  const settingsSubpanels = document.querySelectorAll('.settings-subpanel');

  settingsSubnavPills.forEach(pill => {
    pill.addEventListener('click', () => {
      settingsSubnavPills.forEach(p => {
        p.classList.remove('active', 'btn-primary');
        p.classList.add('btn-secondary');
      });
      pill.classList.remove('btn-secondary');
      pill.classList.add('active', 'btn-primary');

      const subtab = pill.getAttribute('data-subtab');
      settingsSubpanels.forEach(sp => {
        sp.style.display = (sp.id === `settings-panel-${subtab}`) ? 'block' : 'none';
      });
    });
  });

  // ==========================================
  // TAB 7: LOGS CONTROLLER
  // ==========================================
  btnClearLogs.addEventListener('click', () => {
    if (terminalLog) {
      terminalLog.innerHTML = '<div class="log-entry log-info">[SYSTEM LOG CLEARED] Log buffer cleared by user.</div>';
      showToast('Cleared event log', 'info');
    }
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

