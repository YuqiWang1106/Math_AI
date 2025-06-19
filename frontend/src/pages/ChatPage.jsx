// src/pages/ChatPage.jsx
import React, { useEffect, useState } from "react";

function ChatPage() {
  const [assessment, setAssessment] = useState(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const data = localStorage.getItem("assessmentData");
    if (data) {
      setAssessment(JSON.parse(data));
    }
  }, []);

  const handleAsk = async () => {
    if (!question.trim()) return;
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/ask/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          student_id: assessment.student_id,
          question,
          json_data: assessment.json_data,
        }),
      });
      const data = await res.json();
      setAnswer(data.response);
    } catch (error) {
      console.error("Error asking question:", error);
    } finally {
      setLoading(false);
    }
  };

  if (!assessment) {
    return <div className="container">Loading assessment...</div>;
  }

  return (
    <div className="container mt-4">
      <h3>Student: {assessment.student_id}</h3>
      <p><strong>Problem:</strong> {assessment.json_data.self_assessment.problem}</p>

      <div className="mb-3">
        <label>Your question:</label>
        <textarea
          className="form-control"
          rows={3}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        ></textarea>
        <button className="btn btn-success mt-2" onClick={handleAsk} disabled={loading}>
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
