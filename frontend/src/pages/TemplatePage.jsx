import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { evaluateAssessment } from "../api/client";
import "../css/TemplatePage.css";

function Template_Page() {
  const navigate = useNavigate();

  const [studentId, setStudentId] = useState("");
  const [problem, setProblem] = useState("");
  const [knowledgeTypes, setKnowledgeTypes] = useState([
    { type: "facts", examples: "", uncertainties: "" },
    { type: "strategies", examples: "", uncertainties: "" },
    { type: "procedures", examples: "", uncertainties: "" },
    { type: "rationales", examples: "", uncertainties: "" },
  ]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleChangeKT = (index, field, value) => {
    const updated = [...knowledgeTypes];
    updated[index][field] = value;
    setKnowledgeTypes(updated);
  };

  const handleSubmit = async () => {
    const normalizedStudentId = studentId.trim() || "anonymous";
    if (!problem.trim()) {
      setError("Please enter the math problem before submitting.");
      return;
    }

    const payload = {
      student_id: normalizedStudentId,
      json_data: {
        self_assessment: {
          problem,
          knowledge_types: knowledgeTypes,
        },
      },
    };

    setSubmitting(true);
    setError("");
    localStorage.setItem("assessmentData", JSON.stringify(payload));

    try {
      const evaluation = await evaluateAssessment(payload);
      localStorage.setItem("lastEvaluation", JSON.stringify(evaluation));
      navigate(`/growth/${encodeURIComponent(normalizedStudentId)}`);
    } catch (err) {
      setError(err.message || "Could not submit assessment.");
    } finally {
      setSubmitting(false);
    }
  };

  const openExistingGrowth = () => {
    const normalizedStudentId = studentId.trim();
    if (normalizedStudentId) {
      navigate(`/growth/${encodeURIComponent(normalizedStudentId)}`);
    }
  };

  return (
    <div className="container-fluid">
      <div className="row nav-part">
        <div className="nav-title">AI Math Tutor</div>
        <button className="btn btn-secondary" onClick={openExistingGrowth} disabled={!studentId.trim()}>
          View Growth
        </button>
      </div>

      <div className="row main-content-part">
        <div className="col-5 left-side">
          <h2>Self Assessment</h2>
          <p>
            Write what you know about the problem across four knowledge dimensions:
            facts, strategies, procedures, and rationales. Each submission becomes
            one learning observation for your growth history.
          </p>
          <p>
            The backend evaluates the assessment, stores the result, and updates a
            knowledge-point mastery trace for each dimension. You can then inspect
            the student's progress over time from the growth dashboard.
          </p>
        </div>

        <div className="col right-side">
          <h3>Student Assessment</h3>

          {error && <div className="assessment-error">{error}</div>}

          <div className="mb-3">
            <label>Student ID</label>
            <input
              type="text"
              className="form-control"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
            />
          </div>

          <div className="mb-3">
            <label>Problem</label>
            <textarea
              className="form-control"
              value={problem}
              onChange={(e) => setProblem(e.target.value)}
            />
          </div>

          {knowledgeTypes.map((kt, i) => (
            <div key={kt.type} className="mb-3">
              <label>{kt.type.charAt(0).toUpperCase() + kt.type.slice(1)}</label>
              <textarea
                className="form-control"
                placeholder="Examples, definitions, or steps you know"
                value={kt.examples}
                onChange={(e) => handleChangeKT(i, "examples", e.target.value)}
              />
              <textarea
                className="form-control mt-1"
                placeholder="Uncertainties or parts you still need to learn"
                value={kt.uncertainties}
                onChange={(e) => handleChangeKT(i, "uncertainties", e.target.value)}
              />
            </div>
          ))}

          <div className="text-end">
            <button className="btn btn-primary submit" onClick={handleSubmit} disabled={submitting}>
              {submitting ? "Evaluating..." : "Submit Assessment"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Template_Page;
