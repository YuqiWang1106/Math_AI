import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import TemplatePage from "./pages/TemplatePage";
import ChatPage from "./pages/ChatPage";
import GrowthDashboard from "./pages/GrowthDashboard";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<TemplatePage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/growth/:studentId" element={<GrowthDashboard />} />
      </Routes>
    </Router>
  );
}

export default App;
