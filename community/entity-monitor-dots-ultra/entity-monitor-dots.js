/* Entity Monitor Dots Ultra v1.0.1
 * Public Release with Sparkline
 * MIT License
 */

class EntityMonitorDotsUltra extends HTMLElement {

  setConfig(config) {
    this.config = {
      group_by_domain: true,
      animation: "calm",
      sparkline: false,
      show_badge: false,
      dotSize: 18,
      sparklinePoints: 2, // number of points in sparkline
      language: "default",
      ...config
    };

    // Merge translations
    this.config.stateTranslations = window.EntityMonitorDotsTranslations?.[this.config.language] || {};
  }

  set hass(hass) {
    this._hass = hass;

    const sensor = hass.states["sensor.entity_monitor_entity_monitor"];
    if (!sensor) return;

    this._entities = sensor.attributes.entities || [];
    this._current = sensor.attributes.current_entity;

    this._groupEntities();
    this.render();
  }

  _groupEntities() {
    if (!this.config.group_by_domain) {
      this._grouped = { all: this._entities };
      return;
    }

    const grouped = {};
    this._entities.forEach(e => {
      const entityId = typeof e === "string" ? e : e.entity_id;
      const domain = entityId.split(".")[0];
      if (!grouped[domain]) grouped[domain] = [];
      grouped[domain].push(e);
    });

    this._grouped = grouped;
  }

  _getHistory(e) {
    // For now, use last n states from sensor or random for demo
    const entityId = typeof e === "string" ? e : e.entity_id;
    const points = this.config.sparklinePoints || 10;

    // Try to get last states from sensor attributes if available
    // Otherwise generate demo 0/1 values
    if (typeof e === "object" && Array.isArray(e.history)) {
      return e.history.slice(-points).map(s => s === "on" ? 1 : 0);
    } else {
      return Array.from({length: points}, () => Math.random() > 0.7 ? 1 : 0);
    }
  }

  // Sparkline centered vertically inside dot
  _renderSparkline(e) {
    if (!this.config.sparkline) return "";

    const history = this._getHistory(e);
    return history.map(v => `
      <div style="
        display:inline-block;
        width:2px;
        height:${v ? 6 : 3}px;      /* taller if 'on', shorter if 'off' */
        margin:0 1px;
        background:${v ? 'var(--success-color)' : 'var(--primary-color)'};
        vertical-align:middle;      /* center vertically */
      "></div>
    `).join("");
  }

  _renderDot(e) {
    const entityId = typeof e === "string" ? e : e.entity_id;
    const state = typeof e === "string"
      ? this._hass.states[entityId]?.state || "unknown"
      : e.state || this._hass.states[entityId]?.state || "unknown";

    const friendly = this._hass.states[entityId]?.attributes?.friendly_name || entityId;
    const displayState = this.config.stateTranslations?.[state] || state;
    const size = this.config.dotSize || 14;
    const isCurrent = entityId === this._current;
    const isOn = state === "on";

    const color = isCurrent
      ? "var(--warning-color)"
      : isOn
        ? "var(--success-color)"
        : "var(--primary-color)";

    return `
      <div
        style="
          width: ${size}px;
          height: ${size}px;
          border-radius: 50%;
          background-color: ${color};
          margin: 2px;
          cursor: pointer;
          position: relative;
          transition: all 0.3s ease;
          display: flex;
          align-items: center;      /* vertical centering */
          justify-content: center;  /* horizontal centering */
        "
        title="${friendly} — ${displayState}"
        onclick="this.dispatchEvent(new CustomEvent('hass-more-info',{bubbles:true,composed:true,detail:{entityId:'${entityId}'}}))"
      >
        ${this._renderSparkline(e)}
      </div>
    `;
  }

  render() {
    if (!this._grouped) return;

    const badgeCount = this.config.show_badge
      ? this._entities.filter(e => {
          const entityId = typeof e === "string" ? e : e.entity_id;
          return this._hass.states[entityId]?.state === "on";
        }).length
      : 0;

    this.innerHTML = `
      <ha-card style="padding: 12px; position: relative;">
        ${this.config.header ? `<div style="font-weight:600;margin-bottom:12px;">${this.config.header}</div>` : ""}
        ${badgeCount > 0 ? `<div style="position:absolute;top:8px;right:8px;background:var(--error-color);color:white;border-radius:50%;padding:4px 8px;font-size:11px;">${badgeCount}</div>` : ""}
        ${Object.keys(this._grouped).map(domain => `
          <div style="margin-bottom:14px;">
            ${this.config.group_by_domain ? `<div style="font-size:12px;opacity:0.6;margin-bottom:6px;text-transform:capitalize;">${domain}</div>` : ""}
            <div style="display:flex;flex-wrap:wrap;gap:8px;">
              ${this._grouped[domain].map(e => this._renderDot(e)).join("")}
            </div>
          </div>
        `).join("")}
      </ha-card>
    `;
  }

  getCardSize() {
    return 2;
  }
}

customElements.define("entity-monitor-dots-ultra", EntityMonitorDotsUltra);