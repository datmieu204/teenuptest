import React, { Component, StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";

class RootErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, errorMessage: "" };
  }

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      errorMessage: error?.message || "Unexpected frontend error"
    };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Root render error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            maxWidth: "900px",
            margin: "40px auto",
            padding: "16px",
            borderRadius: "12px",
            border: "1px solid #f0d5b5",
            background: "#fff8ee",
            color: "#4a2a16",
            fontFamily: "Space Grotesk, sans-serif"
          }}
        >
          <h2 style={{ marginTop: 0 }}>Frontend runtime error</h2>
          <p>The app crashed while rendering. Open browser DevTools Console for details.</p>
          <pre style={{ whiteSpace: "pre-wrap" }}>{this.state.errorMessage}</pre>
        </div>
      );
    }

    return this.props.children;
  }
}

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <RootErrorBoundary>
      <App />
    </RootErrorBoundary>
  </StrictMode>
);
