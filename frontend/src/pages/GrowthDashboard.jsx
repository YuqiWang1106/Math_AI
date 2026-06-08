import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchStudentGrowth } from "../api/client";
import "../css/GrowthDashboard.css";

function GrowthDashboard() {
  const { studentId } = useParams();
  const [growth, setGrowth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");

    fetchStudentGrowth(studentId)
      .then((data) => {
        if (active) setGrowth(data);
      })
      .catch((err) => {
        if (active) setError(err.message || "Could not load growth data.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [studentId]);

  const groupedObservations = useMemo(() => {
    if (!growth?.observations) return [];
    return [...growth.observations].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  }, [growth]);

  if (loading) {
    return <div className="growth-shell"><div className="growth-status">Loading growth data...</div></div>;
  }

  if (error) {
    return (
      <div className="growth-shell">
        <div className="growth-status growth-error">{error}</div>
        <Link to="/" className="growth-link">Back to assessment</Link>
      </div>
    );
  }

  const overallMastery = toPercent(growth.overall_mastery);

  return (
    <div className="growth-shell">
      <header className="growth-header">
        <div>
          <p className="growth-eyebrow">Student growth</p>
          <h1>{growth.student_id}</h1>
        </div>
        <nav className="growth-actions">
          <Link to="/" className="growth-button secondary">New Assessment</Link>
          <Link to="/chat" className="growth-button primary">Open Tutor</Link>
        </nav>
      </header>

      <section className="growth-summary">
        <div className="growth-summary-main">
          <span className="growth-score">{overallMastery}%</span>
          <span className="growth-score-label">Overall mastery</span>
        </div>
        <div className="growth-summary-meta">
          <div>
            <strong>{growth.attempt_count}</strong>
            <span>Attempts</span>
          </div>
          <div>
            <strong>{growth.knowledge_traces.length}</strong>
            <span>Tracked dimensions</span>
          </div>
        </div>
      </section>

      {growth.knowledge_traces.length === 0 ? (
        <section className="growth-empty">
          <h2>No tracked growth yet</h2>
          <p>Submit a self assessment first so the backend can create BKT mastery traces.</p>
          <Link to="/" className="growth-button primary">Start Assessment</Link>
        </section>
      ) : (
        <>
          <section className="growth-grid">
            {growth.knowledge_traces.map((trace) => (
              <article className="growth-card" key={`${trace.dimension}-${trace.knowledge_point}`}>
                <div className="growth-card-header">
                  <div>
                    <p>{trace.dimension}</p>
                    <h2>{trace.knowledge_point}</h2>
                  </div>
                  <span className={trace.is_mastered ? "mastery-pill mastered" : "mastery-pill"}>
                    {trace.is_mastered ? "Mastered" : "Learning"}
                  </span>
                </div>
                <div className="growth-meter" aria-label={`${trace.knowledge_point} mastery`}>
                  <span style={{ width: `${toPercent(trace.mastery_probability)}%` }} />
                </div>
                <div className="growth-card-stats">
                  <strong>{toPercent(trace.mastery_probability)}%</strong>
                  <span>{trace.correct_count} correct / {trace.incorrect_count} needs work</span>
                </div>
              </article>
            ))}
          </section>

          <section className="growth-panel">
            <div className="growth-panel-header">
              <h2>Observation History</h2>
              <span>{groupedObservations.length} observations</span>
            </div>
            <div className="growth-history">
              {groupedObservations.map((observation, index) => (
                <div className="growth-history-row" key={`${observation.attempt_id}-${observation.knowledge_point}-${index}`}>
                  <div>
                    <strong>{observation.knowledge_point}</strong>
                    <span>{formatDate(observation.created_at)}</span>
                  </div>
                  <div className="growth-history-change">
                    {toPercent(observation.mastery_before)}% -> {toPercent(observation.mastery_after)}%
                  </div>
                  <span className={observation.is_correct ? "result-pill correct" : "result-pill needs-work"}>
                    {observation.is_correct ? "Correct" : "Needs work"}
                  </span>
                </div>
              ))}
            </div>
          </section>

          {growth.latest_report && (
            <section className="growth-panel">
              <div className="growth-panel-header">
                <h2>Latest Evaluation Report</h2>
              </div>
              <pre className="growth-report">{JSON.stringify(growth.latest_report, null, 2)}</pre>
            </section>
          )}
        </>
      )}
    </div>
  );
}

function toPercent(value) {
  return Math.round((Number(value) || 0) * 100);
}

function formatDate(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export default GrowthDashboard;
