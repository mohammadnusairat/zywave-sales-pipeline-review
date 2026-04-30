import { useEffect, useState } from "react";
import "./index.css";

const API_BASE = "http://localhost:8000";

function formatCurrency(value) {
  return value.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  });
}

function badgeClass(value) {
  if (["Expansion", "Pulled In", "Progression"].includes(value)) return "badge good";
  if (["Contraction", "Pushed Out", "Regression"].includes(value)) return "badge bad";
  return "badge neutral";
}

function getRiskColor(level) {
  if (level === "High") return "risk-high";
  if (level === "Medium") return "risk-medium";
  return "risk-low";
}

function RiskMethodologyTooltip() {
  const [open, setOpen] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });

  function handleMouseEnter(event) {
    const rect = event.currentTarget.getBoundingClientRect();

    setTooltipPosition({
      top: rect.top,
      left: rect.right + 10,
    });

    setOpen(true);
  }

  return (
    <span
      className="risk-methodology-wrapper"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        className="risk-info-button"
        aria-label="View risk methodology"
      >
        ?
      </button>

      {open && (
        <div
          className="risk-methodology-popup"
          style={{
            "--methodology-tooltip-top": `${tooltipPosition.top}px`,
            "--methodology-tooltip-left": `${tooltipPosition.left}px`,
          }}
        >
          <div className="methodology-section">
            <div className="methodology-title">Risk level rules</div>
            <div className="methodology-line">
              <strong>Low:</strong> 0
            </div>
            <div className="methodology-line">
              <strong>Medium:</strong> 1–2
            </div>
            <div className="methodology-line">
              <strong>High:</strong> 3+
            </div>
          </div>

          <div className="methodology-section">
            <div className="methodology-title">Risk driver rules</div>
            <div className="methodology-line">
              <strong>ACV Contraction:</strong> +2
            </div>
            <div className="methodology-line">
              <strong>Close Date Pushed Out:</strong> +1
            </div>
            <div className="methodology-line">
              <strong>Forecast Regression:</strong> +2
            </div>
            <div className="methodology-line">
              <strong>No negative movement:</strong> +0
            </div>
          </div>
        </div>
      )}
    </span>
  );
}

function RiskPriorityCell({ risk }) {
  const [expanded, setExpanded] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });

  function handleMouseEnter(event) {
    const rect = event.currentTarget.getBoundingClientRect();

    setTooltipPosition({
      top: rect.bottom + 8,
      left: rect.left + rect.width / 2,
    });

    setExpanded(true);
  }

  return (
    <div className="risk-priority-cell">
      <div
        className={`risk-summary ${getRiskColor(risk.level)}`}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={() => setExpanded(false)}
      >
        {risk.level}
      </div>

      {expanded && (
        <div
          className="risk-drivers-popup"
          style={{
            "--tooltip-top": `${tooltipPosition.top}px`,
            "--tooltip-left": `${tooltipPosition.left}px`,
          }}
        >
          {risk.drivers.map((driver, idx) => (
            <div key={idx} className="driver-item">
              <div className="driver-header">
                <span className="driver-label">{driver.label}</span>
                <span className="driver-points">+{driver.points}</span>
              </div>
              <div className="driver-detail">{driver.detail}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function renderBoldText(text) {
  const parts = text.split(/(\*\*.*?\*\*)/g);

  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }

    return part;
  });
}

function DecisionBrief({ brief }) {
  return (
    <aside className="panel decision-brief-panel">
      <h2>Insights</h2>
      <div className="brief-section">
        <h3 className="brief-title">Overall Read</h3>
        <p className="brief-text">{renderBoldText(brief.overallRead)}</p>
      </div>
      
      <div className="brief-section">
        <h3 className="brief-title">Top Review Priority</h3>
        <p className="brief-text">{renderBoldText(brief.topReviewPriority)}</p>
      </div>
      
      <div className="brief-section">
        <h3 className="brief-title">Forecast Confidence</h3>
        <p className="brief-text">{renderBoldText(brief.forecastConfidence)}</p>
      </div>
      
      <div className="brief-section">
        <h3 className="brief-title">Recommended Actions</h3>
        <ol className="brief-actions">
          {brief.recommendedActions.map((action, idx) => (
            <li key={idx}>{renderBoldText(action)}</li>
          ))}
        </ol>
      </div>
    </aside>
  );
}

export default function App() {
  const [weeks, setWeeks] = useState([]);
  const [currentWeek, setCurrentWeek] = useState("");
  const [data, setData] = useState(null);
  const [weekData, setWeekData] = useState(null);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [varianceCategory, setVarianceCategory] = useState(null);

  // Load available weeks
  useEffect(() => {
    fetch(`${API_BASE}/weeks`)
      .then((res) => res.json())
      .then((result) => {
        setWeeks(result.weeks);
        setCurrentWeek(result.weeks[result.weeks.length - 1]);
      });
  }, []);

  // Load week data when week changes
  useEffect(() => {
    if (!currentWeek) return;

    fetch(`${API_BASE}/week-data?week=${encodeURIComponent(currentWeek)}`)
      .then((res) => res.json())
      .then((result) => setWeekData(result));
  }, [currentWeek]);

  // Load variance analysis when week changes
  useEffect(() => {
    if (!currentWeek) return;

    if (currentWeek === "Week 1") {
      return;
    }

    const url = new URL(`${API_BASE}/analyze`);
    url.searchParams.set("currentWeek", currentWeek);
    if (varianceCategory) {
      url.searchParams.set("category", varianceCategory);
    }

    fetch(url.toString())
      .then((res) => res.json())
      .then((result) => setData(result));
  }, [currentWeek, varianceCategory]);

  return (
    <main className="page">
      {/* Header Section */}
      <section className="hero">
        <div>
          <p className="eyebrow">Zywave AI Ops Assessment</p>
          <h1>Opportunity Variance Analyzer</h1>
          <p className="subtitle">
            Compare opportunity progression across weeks and track deal movements.
          </p>
        </div>

        <div className="selector-card">
          <label>Current Week</label>
          <select
            value={currentWeek}
            onChange={(e) => {
              setCurrentWeek(e.target.value);
              setVarianceCategory(null);
            }}
          >
            {weeks.map((week) => (
              <option key={week} value={week}>
                {week}
              </option>
            ))}
          </select>
        </div>
      </section>

      {/* Tab Navigation */}
      <div className="tabs-container">
        <div className="tabs">
          <button
            className={`tab ${activeTab === "dashboard" ? "active" : ""}`}
            onClick={() => setActiveTab("dashboard")}
          >
            Dashboard
          </button>
          <button
            className={`tab ${activeTab === "variances" ? "active" : ""}`}
            onClick={() => setActiveTab("variances")}
          >
            Variances
          </button>
        </div>
      </div>

      {/* Dashboard Tab */}
      {activeTab === "dashboard" && weekData && (
        <section className="tab-content">
          <div className="panel large">
            <div className="panel-header">
              <div>
                <h2>Week Data</h2>
                <p>All deals for {weekData.week}</p>
              </div>
            </div>

            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Opportunity</th>
                    <th>ACV</th>
                    <th>Close Date</th>
                    <th>Forecast</th>
                  </tr>
                </thead>
                <tbody>
                  {weekData.deals.map((deal) => (
                    <tr key={deal.opportunity}>
                      <td className="opportunity">{deal.opportunity}</td>
                      <td>{formatCurrency(deal.acv)}</td>
                      <td>{deal.closeDate}</td>
                      <td>{deal.forecast}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      {/* Variances Tab */}
      {activeTab === "variances" && (
        <section className="tab-content">
          {currentWeek === "Week 1" ? (
            <div className="empty-state">
              <p>No prior week available for comparison. Select Week 2 or later to view variances.</p>
            </div>
          ) : data ? (
            <>
              {/* Category Filter */}
              <div className="filter-section">
                <label>Filter by Category:</label>
                <div className="filter-buttons">
                  <button
                    className={`filter-btn ${varianceCategory === null ? "active" : ""}`}
                    onClick={() => setVarianceCategory(null)}
                  >
                    All
                  </button>
                  <button
                    className={`filter-btn ${varianceCategory === "ACV" ? "active" : ""}`}
                    onClick={() => setVarianceCategory("ACV")}
                  >
                    ACV
                  </button>
                  <button
                    className={`filter-btn ${varianceCategory === "CloseDate" ? "active" : ""}`}
                    onClick={() => setVarianceCategory("CloseDate")}
                  >
                    Close Date
                  </button>
                  <button
                    className={`filter-btn ${varianceCategory === "Forecast" ? "active" : ""}`}
                    onClick={() => setVarianceCategory("Forecast")}
                  >
                    Forecast
                  </button>
                </div>
              </div>

              {/* Variances Table and Decision Brief */}
              <section className="content-grid">
                <div className="panel large">
                  <div className="panel-header">
                    <div>
                      <h2>Variances</h2>
                      <p>
                        Comparing {data.summary.priorWeek} → {data.summary.currentWeek}. Displaying {data.variances.length} {data.variances.length === 1 ? "deal" : "deals"} with changes in {varianceCategory || "any category"}.
                      </p>
                    </div>
                  </div>

                  {data.variances.length > 0 ? (
                    <div className="table-wrapper">
                      <table>
                        <thead>
                          <tr>
                            <th>Opportunity</th>
                            <th>ACV Δ</th>
                            <th>ACV Movement</th>
                            <th>Close Δ</th>
                            <th>Date Movement</th>
                            <th>Forecast</th>
                            <th>Direction</th>
                            <th>
                              <span className="risk-header">
                                Risk
                                <RiskMethodologyTooltip />
                              </span>
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.variances.map((row) => (
                            <tr key={row.opportunity}>
                              <td className="opportunity">{row.opportunity}</td>
                              <td>{formatCurrency(row.acvVariance)}</td>
                              <td>
                                <span className={badgeClass(row.acvMovement)}>
                                  {row.acvMovement}
                                </span>
                              </td>
                              <td>{row.closeDateVariance} days</td>
                              <td>
                                <span className={badgeClass(row.closeDateMovement)}>
                                  {row.closeDateMovement}
                                </span>
                              </td>
                              <td>{row.forecastVariance}</td>
                              <td>
                                <span className={badgeClass(row.forecastDirection)}>
                                  {row.forecastDirection}
                                </span>
                              </td>
                              <td>
                                <RiskPriorityCell risk={row.risk} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="empty-state">
                      <p>No deals changed in this category.</p>
                    </div>
                  )}
                </div>

                {data.decisionBrief && <DecisionBrief brief={data.decisionBrief} />}
              </section>
            </>
          ) : null}
        </section>
      )}
    </main>
  );
}