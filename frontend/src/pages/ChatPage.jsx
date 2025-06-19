// src/pages/ChatPage.jsx
import React, { useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import '../css/ChatPage.css';

function ChatPage() {
  const [assessment, setAssessment] = useState(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);

  useEffect(() => {
    localStorage.removeItem("chatHistory");
    const rawAssess = localStorage.getItem("assessmentData");
    if (rawAssess) {
      setAssessment(JSON.parse(rawAssess));
    }
    const rawHistory = localStorage.getItem("chatHistory");
    if (rawHistory) {
      setChatHistory(JSON.parse(rawHistory));
    }
  }, []);


const handleAsk = async () => {
  if (!question.trim()) return;

  const entryId = uuidv4();
  const optimisticEntry = { id: entryId, question, answer: null };
  setChatHistory(prev => {
    const next = [...prev, optimisticEntry];
    localStorage.setItem("chatHistory", JSON.stringify(next));
    return next;
  });
  setQuestion("");      
  setLoading(true);       

  try {
    const res  = await fetch("http://localhost:8000/api/ask/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student_id: assessment.student_id,
        question,
        json_data: assessment.json_data,
      }),
    });
    const data = await res.json();
    const answerText = data.response;

    setChatHistory(prev => {
      const next = prev.map(item =>
        item.id === entryId ? { ...item, answer: answerText } : item
      );
      localStorage.setItem("chatHistory", JSON.stringify(next));
      return next;
    });
  } catch (err) {
    console.error(err);
  } finally {
    setLoading(false);
  }
};

 if (!assessment) {
    return (
      <div className="chat-loading">
        <div className="chat-loading-spinner"></div>
        <p>Loading assessment...</p>
      </div>
    );
  }

  return (
    <div className="chat-container">
      {/* Header Section */}
      <div className="chat-header">
        <div className="chat-student-info">
          <h3 className="chat-title">AI Math Tutor</h3>
          <div className="chat-student-details">
            <span className="chat-student-id">Student: {assessment.student_id}</span>
            <span className="chat-problem-text">Problem: {assessment.json_data.self_assessment.problem}</span>
          </div>
        </div>
      </div>


    {/* Chat Messages Area */}
    <div className="chat-messages">
    {chatHistory.length === 0 ? (
        <div className="chat-welcome">
        <div className="chat-welcome-icon">🤖</div>
        <h4>Welcome to AI Math Tutor!</h4>
        <p>Ask me anything about your math problem. I'm here to help you learn step by step.</p>
        </div>
    ) : (
        chatHistory.map((entry) => (
        <div key={entry.id} className="chat-message-group">
            <div className="chat-message chat-message-user">
            <div className="chat-message-avatar chat-avatar-user">👤</div>
            <div className="chat-message-content">
                <div className="chat-message-text">{entry.question}</div>
            </div>
            </div>
            {entry.answer !== null && (
            <div className="chat-message chat-message-ai">
                <div className="chat-message-avatar chat-avatar-ai">🤖</div>
                <div className="chat-message-content">
                <div className="chat-message-text">{entry.answer}</div>
                </div>
            </div>
            )}
        </div>
        ))
    )}

    {loading && (
        <div className="chat-message chat-message-ai">
        <div className="chat-message-avatar chat-avatar-ai">🤖</div>
        <div className="chat-message-content">
            <div className="chat-typing-indicator">
            <span></span>
            <span></span>
            <span></span>
            </div>
        </div>
        </div>
    )}
    </div>


      {/* Input Area */}
      <div className="chat-input-section">
        <div className="chat-input-container">
          <textarea
            className="chat-input"
            placeholder="Type your question here..."
            rows={3}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleAsk();
              }
            }}
          />
          <button
            className={`chat-send-btn ${loading ? 'chat-send-btn-loading' : ''}`}
            onClick={handleAsk}
            disabled={loading || !question.trim()}
          >
            {loading ? (
              <div className="chat-btn-spinner"></div>
            ) : (
              <svg className="chat-send-icon" viewBox="0 0 24 24" fill="none">
                <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z" fill="currentColor"/>
              </svg>
            )}
          </button>
        </div>
      </div>

    </div>
  );
}

export default ChatPage;
