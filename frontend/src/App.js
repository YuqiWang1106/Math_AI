import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import TemplatePage from "./pages/TemplatePage";
import ChatPage from "./pages/ChatPage"; // 先留着，占位

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<TemplatePage />} />
        <Route path="/chat" element={<ChatPage />} />
      </Routes>
    </Router>
  );
}

export default App;

