"use client";

import React, { useEffect, useState } from "react";
import { AlertTriangle, RotateCw, Home, Copy, Check, Eye } from "lucide-react";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorPage({ error, reset }: ErrorProps) {
  const [copied, setCopied] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    // Log typical errors to console for trace
    console.error("Error capturado por la frontera de error:", error);
  }, [error]);

  const handleCopyDetails = async () => {
    try {
      const details = `Message: ${error.message}\nDigest: ${error.digest || "N/A"}\nStack: ${error.stack || "N/A"}`;
      await navigator.clipboard.writeText(details);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch (err) {
      console.error("Error al copiar al portapapeles:", err);
    }
  };

  const handleGoHome = () => {
    window.location.href = "/";
  };

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        backgroundColor: "var(--bg-primary)",
        color: "var(--text-primary)",
        padding: "20px",
        fontFamily: "var(--font-sans)",
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: "100%",
          maxWidth: "420px",
          borderRadius: "var(--radius-lg)",
          padding: "32px 24px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
          gap: "24px",
          animation: "slideInUp 0.4s ease-out",
          boxShadow: "0 20px 40px rgba(0, 0, 0, 0.4)",
        }}
      >
        {/* Glowing Warning Icon */}
        <div
          style={{
            position: "relative",
            width: "64px",
            height: "64px",
            borderRadius: "var(--radius-full)",
            backgroundColor: "hsl(var(--accent) / 0.1)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            border: "1px solid hsl(var(--accent) / 0.2)",
            boxShadow: "0 0 20px hsl(var(--accent) / 0.15)",
          }}
        >
          <AlertTriangle
            size={32}
            style={{
              color: "hsl(var(--accent))",
              filter: "drop-shadow(0 0 8px hsl(var(--accent) / 0.5))",
            }}
          />
        </div>

        {/* Text Headers */}
        <div>
          <h2
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              fontFamily: "var(--font-display)",
              marginBottom: "8px",
              lineHeight: 1.2,
            }}
          >
            ¡Ups! Algo salió{" "}
            <span className="text-gradient-solarpunk">mal</span>
          </h2>
          <p
            style={{
              fontSize: "0.875rem",
              color: "var(--text-secondary)",
              lineHeight: 1.5,
            }}
          >
            Sysmap se ha topado con un obstáculo temporal. Este incidente ha
            sido registrado por la infraestructura de{" "}
            <strong style={{ color: "#fff", fontWeight: 600 }}>TecnoAncon</strong>.
          </p>
        </div>

        {/* Action Buttons */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "10px",
            width: "100%",
          }}
        >
          <button
            id="btn-error-retry"
            onClick={reset}
            className="glow-btn"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              padding: "12px",
              borderRadius: "var(--radius-md)",
              fontSize: "0.9rem",
              width: "100%",
            }}
          >
            <RotateCw size={16} />
            Reintentar
          </button>

          <button
            id="btn-error-home"
            onClick={handleGoHome}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              padding: "12px",
              borderRadius: "var(--radius-md)",
              fontSize: "0.9rem",
              width: "100%",
              backgroundColor: "var(--bg-tertiary)",
              border: "1px solid var(--glass-border)",
              color: "var(--text-primary)",
              cursor: "pointer",
              transition: "var(--transition-fast)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "var(--bg-secondary)";
              e.currentTarget.style.borderColor = "hsl(var(--primary) / 0.5)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "var(--bg-tertiary)";
              e.currentTarget.style.borderColor = "var(--glass-border)";
            }}
          >
            <Home size={16} />
            Ir al Inicio
          </button>
        </div>

        {/* Collapsible details for development */}
        <div style={{ width: "100%", marginTop: "8px" }}>
          <button
            id="btn-error-details"
            onClick={() => setShowDetails(!showDetails)}
            style={{
              fontSize: "0.75rem",
              color: "var(--text-muted)",
              background: "none",
              border: "none",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "6px",
              margin: "0 auto 10px auto",
              padding: "4px 8px",
              borderRadius: "var(--radius-sm)",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-secondary)")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
          >
            <Eye size={12} />
            {showDetails ? "Ocultar detalles técnicos" : "Ver detalles técnicos"}
          </button>

          {showDetails && (
            <div
              style={{
                textAlign: "left",
                backgroundColor: "#06090f",
                border: "1px solid var(--glass-border)",
                borderRadius: "var(--radius-sm)",
                padding: "12px",
                fontSize: "0.725rem",
                fontFamily: "monospace",
                color: "#ff7b72",
                maxHeight: "150px",
                overflowY: "auto",
                whiteSpace: "pre-wrap",
                wordBreak: "break-all",
                display: "flex",
                flexDirection: "column",
                gap: "10px",
              }}
            >
              <div style={{ overflowY: "auto", flexGrow: 1 }}>
                <strong>Error:</strong> {error.message || error.toString()}
                {error.digest && (
                  <>
                    <br />
                    <strong>Digest:</strong> {error.digest}
                  </>
                )}
              </div>
              <button
                onClick={handleCopyDetails}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "4px",
                  padding: "6px",
                  borderRadius: "4px",
                  backgroundColor: copied ? "hsl(var(--secondary) / 0.1)" : "var(--bg-tertiary)",
                  border: copied ? "1px solid hsl(var(--secondary) / 0.3)" : "1px solid var(--glass-border)",
                  color: copied ? "hsl(var(--secondary))" : "var(--text-secondary)",
                  cursor: "pointer",
                  fontSize: "0.7rem",
                  width: "100%",
                }}
              >
                {copied ? <Check size={12} /> : <Copy size={12} />}
                {copied ? "¡Copiado!" : "Copiar Detalles"}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
