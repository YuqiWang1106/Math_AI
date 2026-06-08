// src/pages/ChatPage.jsx
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { askTutor } from "../api/client";

function ChatPage() {
  const [assessment, setAssessment] = useState(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const data = localStorage.getItem("assessmentData");
    if (data) {
      setAssessment(JSON.parse(data));
    }
  }, []);

  const handleAsk = async () => {
    if (!question.trim() || !assessment) return;
    setLoading(true);
    setError("");
    try {
      const data = await askTutor({
        student_id: assessment.student_id,
        question,
        json_data: assessment.json_data,
      });
      setAnswer(data.response);
      setQuestion("");
    } catch (err) {
      setError(err.message || "Error asking question.");
    } finally {
      setLoading(false);
    }
  };

  if (!assessment) {
    return <div className="container mt-4">Loading assessment...</div>;
  }

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-start mb-3">
        <div>
          <h3>Student: {assessment.student_id}</h3>
          <p><strong>Problem:</strong> {assessment.json_data.self_assessment.problem}</p>
        </div>
        <Link className="btn btn-outline-primary" to={`/growth/${encodeURIComponent(assessment.student_id)}`}>
          View Growth
        </Link>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="mb-3">
        <label>Your question:</label>
        <textarea
          className="form-control"
          rows={3}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        ></textarea>
        <button className="btn btn-success mt-2" onClick={handleAsk} disabled={loading || !question.trim()}>
          {loading ? "Thinking..." : "Ask AI Tutor"}
        </button>
      </div>

      {answer && (
        <div className="mt-4">
          <h5>AI Tutor's Answer:</h5>
          <div className="alert alert-primary" style={{ whiteSpace: "pre-wrap" }}>
            {answer}
          </div>
        </div>
      )}
    </div>
  );
}

export default ChatPage;
