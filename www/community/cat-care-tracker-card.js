/**
 * Cat Care Tracker Card for Home Assistant
 * A custom Lovelace card for tracking cat care activities
 */

class CatCareTrackerCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('You need to define an entity');
    }
    this.config = {
      name: config.name || 'Cat Care Tracker',
      entity: config.entity,
      show_recent: config.show_recent !== false,
      show_quick_actions: config.show_quick_actions !== false,
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  render() {
    if (!this._hass || !this.config) return;

    const entity = this._hass.states[this.config.entity];
    const attrs = entity ? entity.attributes : {};

    const foodCount = attrs.food_count || 0;
    const insulinCount = attrs.insulin_count || 0;
    const waterCount = attrs.water_count || 0;
    const bgCount = attrs.bg_count || 0;
    const entries = attrs.entries || [];

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          --card-primary-color: var(--primary-color, #03a9f4);
          --card-background: var(--ha-card-background, var(--card-background-color, white));
          --card-text-color: var(--primary-text-color, #212121);
          --card-secondary-color: var(--secondary-text-color, #727272);
        }
        
        ha-card {
          padding: 16px;
          background: var(--card-background);
          color: var(--card-text-color);
        }
        
        .header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 16px;
        }
        
        .header-icon {
          font-size: 32px;
        }
        
        .header-title {
          font-size: 1.2em;
          font-weight: 500;
        }
        
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 8px;
          margin-bottom: 16px;
        }
        
        .stat-card {
          background: var(--secondary-background-color, #f5f5f5);
          border-radius: 8px;
          padding: 12px;
          text-align: center;
        }
        
        .stat-icon {
          font-size: 24px;
          margin-bottom: 4px;
        }
        
        .stat-value {
          font-size: 1.5em;
          font-weight: bold;
        }
        
        .stat-label {
          font-size: 0.8em;
          color: var(--card-secondary-color);
        }
        
        .quick-actions {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 8px;
          margin-bottom: 16px;
        }
        
        .action-btn {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 16px;
          border: none;
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.2s ease;
          font-size: 14px;
          font-weight: 500;
        }
        
        .action-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .action-btn:active {
          transform: translateY(0);
        }
        
        .action-btn .icon {
          font-size: 28px;
          margin-bottom: 8px;
        }
        
        .btn-food {
          background: linear-gradient(135deg, #FF9800, #F57C00);
          color: white;
        }
        
        .btn-insulin {
          background: linear-gradient(135deg, #4CAF50, #388E3C);
          color: white;
        }
        
        .btn-water {
          background: linear-gradient(135deg, #2196F3, #1976D2);
          color: white;
        }
        
        .btn-bg {
          background: linear-gradient(135deg, #9C27B0, #7B1FA2);
          color: white;
        }
        
        .btn-combo {
          background: linear-gradient(135deg, #607D8B, #455A64);
          color: white;
          grid-column: span 2;
        }
        
        .recent-entries {
          margin-top: 16px;
        }
        
        .recent-title {
          font-size: 0.9em;
          color: var(--card-secondary-color);
          margin-bottom: 8px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        
        .entry-list {
          max-height: 200px;
          overflow-y: auto;
        }
        
        .entry-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px 0;
          border-bottom: 1px solid var(--divider-color, #e0e0e0);
        }
        
        .entry-item:last-child {
          border-bottom: none;
        }
        
        .entry-time {
          font-size: 0.85em;
          color: var(--card-secondary-color);
          min-width: 60px;
        }
        
        .entry-types {
          display: flex;
          gap: 4px;
          flex-wrap: wrap;
        }
        
        .entry-badge {
          padding: 4px 8px;
          border-radius: 12px;
          font-size: 0.75em;
          font-weight: 500;
        }
        
        .badge-food { background: #FFF3E0; color: #E65100; }
        .badge-insulin { background: #E8F5E9; color: #2E7D32; }
        .badge-water { background: #E3F2FD; color: #1565C0; }
        .badge-bg { background: #F3E5F5; color: #7B1FA2; }
        
        .bg-modal {
          display: none;
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: rgba(0,0,0,0.5);
          z-index: 1000;
          justify-content: center;
          align-items: center;
        }
        
        .bg-modal.show {
          display: flex;
        }
        
        .modal-content {
          background: var(--card-background);
          padding: 24px;
          border-radius: 16px;
          min-width: 280px;
          box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        }
        
        .modal-title {
          font-size: 1.2em;
          font-weight: 500;
          margin-bottom: 16px;
        }
        
        .modal-input {
          width: 100%;
          padding: 12px;
          font-size: 24px;
          text-align: center;
          border: 2px solid var(--divider-color, #e0e0e0);
          border-radius: 8px;
          margin-bottom: 16px;
          box-sizing: border-box;
        }
        
        .modal-input:focus {
          outline: none;
          border-color: var(--card-primary-color);
        }
        
        .modal-buttons {
          display: flex;
          gap: 8px;
          justify-content: flex-end;
        }
        
        .modal-btn {
          padding: 10px 20px;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 14px;
          font-weight: 500;
        }
        
        .modal-btn-cancel {
          background: var(--secondary-background-color, #f5f5f5);
          color: var(--card-text-color);
        }
        
        .modal-btn-confirm {
          background: var(--card-primary-color);
          color: white;
        }
        
        .toast {
          position: fixed;
          bottom: 20px;
          left: 50%;
          transform: translateX(-50%) translateY(100px);
          background: #323232;
          color: white;
          padding: 12px 24px;
          border-radius: 8px;
          z-index: 1001;
          transition: transform 0.3s ease;
        }
        
        .toast.show {
          transform: translateX(-50%) translateY(0);
        }
      </style>
      
      <ha-card>
        <div class="header">
          <span class="header-icon">🐱</span>
          <span class="header-title">${this.config.name}</span>
        </div>
        
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">🍽️</div>
            <div class="stat-value">${foodCount}</div>
            <div class="stat-label">Food</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">💉</div>
            <div class="stat-value">${insulinCount}</div>
            <div class="stat-label">Insulin</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">💧</div>
            <div class="stat-value">${waterCount}</div>
            <div class="stat-label">Water</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">🩸</div>
            <div class="stat-value">${bgCount}</div>
            <div class="stat-label">BG</div>
          </div>
        </div>
        
        ${this.config.show_quick_actions ? `
        <div class="quick-actions">
          <button class="action-btn btn-food" id="btn-food">
            <span class="icon">🍽️</span>
            <span>Log Feeding</span>
          </button>
          <button class="action-btn btn-insulin" id="btn-insulin">
            <span class="icon">💉</span>
            <span>Log Insulin</span>
          </button>
          <button class="action-btn btn-water" id="btn-water">
            <span class="icon">💧</span>
            <span>Log Water</span>
          </button>
          <button class="action-btn btn-bg" id="btn-bg">
            <span class="icon">🩸</span>
            <span>Log BG</span>
          </button>
          <button class="action-btn btn-combo" id="btn-combo">
            <span class="icon">🍽️💉</span>
            <span>Log Food + Insulin</span>
          </button>
        </div>
        ` : ''}
        
        ${this.config.show_recent && entries.length > 0 ? `
        <div class="recent-entries">
          <div class="recent-title">Today's Entries</div>
          <div class="entry-list">
            ${entries.map(entry => this._renderEntry(entry)).join('')}
          </div>
        </div>
        ` : ''}
        
        <div class="bg-modal" id="bg-modal">
          <div class="modal-content">
            <div class="modal-title">Enter Blood Glucose Level</div>
            <input type="number" class="modal-input" id="bg-input" placeholder="mg/dL" min="0" max="500">
            <div class="modal-buttons">
              <button class="modal-btn modal-btn-cancel" id="modal-cancel">Cancel</button>
              <button class="modal-btn modal-btn-confirm" id="modal-confirm">Log</button>
            </div>
          </div>
        </div>
        
        <div class="bg-modal" id="water-modal">
          <div class="modal-content">
            <div class="modal-title">Enter Water Refill Amount</div>
            <input type="text" class="modal-input" id="water-input" placeholder="e.g., 250ml">
            <div class="modal-buttons">
              <button class="modal-btn modal-btn-cancel" id="water-modal-cancel">Cancel</button>
              <button class="modal-btn modal-btn-confirm" id="water-modal-confirm">Log</button>
            </div>
          </div>
        </div>
        
        <div class="toast" id="toast">Entry logged successfully!</div>
      </ha-card>
    `;

    this._setupEventListeners();
  }

  _renderEntry(entry) {
    const date = entry['Date'] || '';
    const types = entry['Checkin Type'] || '';
    const time = date.includes(' ') ? date.split(' ')[1] : '';
    
    const badges = [];
    if (types.includes('Food')) badges.push('<span class="entry-badge badge-food">Food</span>');
    if (types.includes('Insulin')) badges.push('<span class="entry-badge badge-insulin">Insulin</span>');
    if (types.includes('Water')) badges.push('<span class="entry-badge badge-water">Water</span>');
    if (types.includes('Blood Glucose')) badges.push('<span class="entry-badge badge-bg">BG</span>');
    
    return `
      <div class="entry-item">
        <span class="entry-time">${time || 'Today'}</span>
        <div class="entry-types">${badges.join('')}</div>
      </div>
    `;
  }

  _setupEventListeners() {
    const btnFood = this.shadowRoot.getElementById('btn-food');
    const btnInsulin = this.shadowRoot.getElementById('btn-insulin');
    const btnWater = this.shadowRoot.getElementById('btn-water');
    const btnBg = this.shadowRoot.getElementById('btn-bg');
    const btnCombo = this.shadowRoot.getElementById('btn-combo');
    const bgModal = this.shadowRoot.getElementById('bg-modal');
    const modalCancel = this.shadowRoot.getElementById('modal-cancel');
    const modalConfirm = this.shadowRoot.getElementById('modal-confirm');
    const bgInput = this.shadowRoot.getElementById('bg-input');
    const waterModal = this.shadowRoot.getElementById('water-modal');
    const waterModalCancel = this.shadowRoot.getElementById('water-modal-cancel');
    const waterModalConfirm = this.shadowRoot.getElementById('water-modal-confirm');
    const waterInput = this.shadowRoot.getElementById('water-input');

    if (btnFood) {
      btnFood.addEventListener('click', () => this._logEntry(['Food']));
    }

    if (btnInsulin) {
      btnInsulin.addEventListener('click', () => this._logEntry(['Insulin']));
    }

    if (btnWater) {
      btnWater.addEventListener('click', () => {
        waterModal.classList.add('show');
        waterInput.focus();
      });
    }

    if (btnBg) {
      btnBg.addEventListener('click', () => {
        bgModal.classList.add('show');
        bgInput.focus();
      });
    }

    if (btnCombo) {
      btnCombo.addEventListener('click', () => this._logEntry(['Food', 'Insulin']));
    }

    if (modalCancel) {
      modalCancel.addEventListener('click', () => {
        bgModal.classList.remove('show');
        bgInput.value = '';
      });
    }

    if (modalConfirm) {
      modalConfirm.addEventListener('click', () => {
        const bgValue = parseInt(bgInput.value, 10);
        if (bgValue && bgValue > 0) {
          this._logBgEntry(bgValue);
          bgModal.classList.remove('show');
          bgInput.value = '';
        }
      });
    }

    if (bgInput) {
      bgInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') {
          const bgValue = parseInt(bgInput.value, 10);
          if (bgValue && bgValue > 0) {
            this._logBgEntry(bgValue);
            bgModal.classList.remove('show');
            bgInput.value = '';
          }
        }
      });
    }

    if (waterModalCancel) {
      waterModalCancel.addEventListener('click', () => {
        waterModal.classList.remove('show');
        waterInput.value = '';
      });
    }

    if (waterModalConfirm) {
      waterModalConfirm.addEventListener('click', () => {
        const waterValue = waterInput.value.trim();
        if (waterValue) {
          this._logWaterEntry(waterValue);
          waterModal.classList.remove('show');
          waterInput.value = '';
        }
      });
    }

    if (waterInput) {
      waterInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') {
          const waterValue = waterInput.value.trim();
          if (waterValue) {
            this._logWaterEntry(waterValue);
            waterModal.classList.remove('show');
            waterInput.value = '';
          }
        }
      });
    }

    // Close modal when clicking outside
    if (bgModal) {
      bgModal.addEventListener('click', (e) => {
        if (e.target === bgModal) {
          bgModal.classList.remove('show');
          bgInput.value = '';
        }
      });
    }

    // Close water modal when clicking outside
    if (waterModal) {
      waterModal.addEventListener('click', (e) => {
        if (e.target === waterModal) {
          waterModal.classList.remove('show');
          waterInput.value = '';
        }
      });
    }
  }

  _logEntry(types) {
    this._hass.callService('cat_care_tracker', 'log_entry', {
      checkin_types: types,
    });
    this._showToast();
  }

  _logBgEntry(bgLevel) {
    this._hass.callService('cat_care_tracker', 'log_blood_glucose', {
      bg_level: bgLevel,
    });
    this._showToast();
  }

  _logWaterEntry(waterRefill) {
    this._hass.callService('cat_care_tracker', 'log_water', {
      water_refill: waterRefill,
    });
    this._showToast();
  }

  _showToast() {
    const toast = this.shadowRoot.getElementById('toast');
    if (toast) {
      toast.classList.add('show');
      setTimeout(() => {
        toast.classList.remove('show');
      }, 2000);
    }
  }

  getCardSize() {
    return 4;
  }

  static getConfigElement() {
    return document.createElement('cat-care-tracker-card-editor');
  }

  static getStubConfig() {
    return {
      entity: 'sensor.my_cat_todays_entries',
      name: 'Cat Care Tracker',
      show_recent: true,
      show_quick_actions: true,
    };
  }
}

// Card Editor for Visual Config
class CatCareTrackerCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  render() {
    if (!this._hass) return;

    this.innerHTML = `
      <style>
        .config-row {
          margin-bottom: 16px;
        }
        .config-row label {
          display: block;
          margin-bottom: 4px;
          font-weight: 500;
        }
        .config-row input, .config-row select {
          width: 100%;
          padding: 8px;
          border: 1px solid #ccc;
          border-radius: 4px;
          box-sizing: border-box;
        }
        .config-row input[type="checkbox"] {
          width: auto;
          margin-right: 8px;
        }
        .checkbox-row {
          display: flex;
          align-items: center;
        }
      </style>
      
      <div class="config-row">
        <label>Entity</label>
        <input type="text" id="entity" value="${this._config.entity || ''}">
      </div>
      
      <div class="config-row">
        <label>Card Name</label>
        <input type="text" id="name" value="${this._config.name || 'Cat Care Tracker'}">
      </div>
      
      <div class="config-row checkbox-row">
        <input type="checkbox" id="show_recent" ${this._config.show_recent !== false ? 'checked' : ''}>
        <label for="show_recent">Show Recent Entries</label>
      </div>
      
      <div class="config-row checkbox-row">
        <input type="checkbox" id="show_quick_actions" ${this._config.show_quick_actions !== false ? 'checked' : ''}>
        <label for="show_quick_actions">Show Quick Actions</label>
      </div>
    `;

    this.querySelector('#entity').addEventListener('change', (e) => this._updateConfig('entity', e.target.value));
    this.querySelector('#name').addEventListener('change', (e) => this._updateConfig('name', e.target.value));
    this.querySelector('#show_recent').addEventListener('change', (e) => this._updateConfig('show_recent', e.target.checked));
    this.querySelector('#show_quick_actions').addEventListener('change', (e) => this._updateConfig('show_quick_actions', e.target.checked));
  }

  _updateConfig(key, value) {
    this._config = {
      ...this._config,
      [key]: value,
    };

    const event = new CustomEvent('config-changed', {
      detail: { config: this._config },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }
}

customElements.define('cat-care-tracker-card', CatCareTrackerCard);
customElements.define('cat-care-tracker-card-editor', CatCareTrackerCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'cat-care-tracker-card',
  name: 'Cat Care Tracker Card',
  description: 'A card for tracking cat care activities (feeding, insulin, water, blood glucose) synced with Google Sheets',
  preview: true,
});

console.info(
  '%c CAT CARE TRACKER CARD %c v1.0.0 ',
  'color: white; background: #FF9800; font-weight: bold; padding: 2px 4px;',
  'color: #FF9800; background: white; font-weight: bold; padding: 2px 4px;'
);
