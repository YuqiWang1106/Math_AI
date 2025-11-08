import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import TemplatePage from "./pages/TemplatePage";
import ChatPage from "./pages/ChatPage"; // 先留着，占位
import PreferencePage from "./pages/PreferencePage";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<PreferencePage />} />
        <Route path="/assessment" element={<TemplatePage />} />
        <Route path="/chat" element={<ChatPage />} />
      </Routes>
    </Router>
  );
}

export default App;
