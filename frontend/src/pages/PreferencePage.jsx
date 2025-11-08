import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../css/PreferencePage.css";

function PreferencePage() {
  const navigate = useNavigate();
  const [preference, setPreference] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!preference.trim()) {
      setError("请输入你想了解或咨询的内容。");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/preference/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preference }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "分类失败，请稍后再试。");
      }
      const meta = {
        preference,
        domain: data.domain,
        branch: data.branch,
        confidence: data.confidence,
        reasoning: data.reasoning,
        classifiedAt: new Date().toISOString(),
      };
      localStorage.setItem("preferenceMeta", JSON.stringify(meta));
      navigate("/assessment");
    } catch (err) {
      setError(err.message || "提交失败，请稍后重试。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="preference-wrapper">
      <div className="preference-card">
        <div className="preference-header">
          <p className="preference-kicker">STEP 1 · 学习意图</p>
          <h1>告诉我们你想探索的内容</h1>
          <p className="preference-subtitle">
            用自然语言描述你的目标或问题，例如“我想规划未来四年的大学预算”或者“我想夯实统计学里的回归分析”。
          </p>
        </div>

        <form onSubmit={handleSubmit} className="preference-form">
          <label htmlFor="preferenceInput">你的问题 / 目标</label>
          <textarea
            id="preferenceInput"
            className="preference-textarea"
            rows={6}
            placeholder="写下你想了解或解决的事情……"
            value={preference}
            onChange={(e) => setPreference(e.target.value)}
          />
          {error && <div className="preference-error">{error}</div>}
          <button
            type="submit"
            className="preference-submit"
            disabled={loading}
          >
            {loading ? "正在分析..." : "提交并进入自评"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default PreferencePage;
