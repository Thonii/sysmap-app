"use client";

import { useState } from "react";
import { Link, Plus, Loader2, CheckCircle, XCircle, AlertTriangle, X } from "lucide-react";

interface ImportEventBarProps {
  apiBaseUrl: string;
  onImportSuccess: () => void;
}

export function ImportEventBar({ apiBaseUrl, onImportSuccess }: ImportEventBarProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{
    type: "success" | "warning" | "error" | "idle";
    message: string;
  }>({ type: "idle", message: "" });

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    // Validación básica de URL en frontend
    const urlLower = url.trim().toLowerCase();
    const isSupported = urlLower.includes("eventbrite") || 
                        urlLower.includes("lu.ma") || 
                        urlLower.includes("luma.com") || 
                        urlLower.includes("meetup.com");

    if (!isSupported || (!urlLower.startsWith("http://") && !urlLower.startsWith("https://"))) {
      setStatus({
        type: "error",
        message: "Enlace no válido. Solo se admiten enlaces oficiales de los sitios soportados (Eventbrite, Luma y Meetup)."
      });
      return;
    }

    setLoading(true);
    setStatus({ type: "idle", message: "" });

    try {
      const response = await fetch(`${apiBaseUrl}/events/import-url`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ url: url.trim() })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Error al intentar importar el evento.");
      }

      setUrl("");
      if (data.is_tech) {
        setStatus({
          type: "success",
          message: `¡Evento "${data.event?.title || "Importado"}" añadido con éxito!`
        });
        onImportSuccess(); // Refrescar la lista de eventos
        // Colapsar tras éxito después de un retraso corto
        setTimeout(() => {
          setIsExpanded(false);
          setStatus({ type: "idle", message: "" });
        }, 3000);
      } else {
        setStatus({
          type: "warning",
          message: `Se importó "${data.event?.title || "Evento"}", pero fue clasificado como NO tecnológico, por lo que no aparecerá en la lista.`
        });
      }
    } catch (err: unknown) {
      console.error(err);
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Error al conectar con el servidor."
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setIsExpanded(false);
    setUrl("");
    setStatus({ type: "idle", message: "" });
  };

  // 1. Estado colapsado: Botón súper compacto para alineación en fila
  if (!isExpanded) {
    return (
      <button
        onClick={() => setIsExpanded(true)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "5px",
          padding: "6px 12px",
          borderRadius: "var(--radius-sm)",
          border: "1px dashed rgba(255, 255, 255, 0.15)",
          backgroundColor: "rgba(255, 255, 255, 0.02)",
          color: "var(--text-secondary)",
          fontSize: "0.75rem",
          fontWeight: 600,
          cursor: "pointer",
          transition: "all 0.2s ease",
          outline: "none"
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = "hsl(var(--primary))";
          e.currentTarget.style.color = "#fff";
          e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.04)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.15)";
          e.currentTarget.style.color = "var(--text-secondary)";
          e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.02)";
        }}
      >
        <Plus size={13} style={{ color: "hsl(var(--primary))" }} />
        Importar
      </button>
    );
  }

  // 2. Estado expandido: Formulario que ocupa el 100% de ancho de fila abajo
  return (
    <div style={{
      width: "100%",
      display: "flex",
      flexDirection: "column",
      gap: "10px",
      padding: "12px",
      borderRadius: "var(--radius-md)",
      backgroundColor: "var(--bg-secondary)",
      border: "1px solid var(--glass-border)",
      boxShadow: "var(--glass-shadow)",
      animation: "slideDown 0.25s ease-out",
      marginTop: "8px"
    }}>
      <form onSubmit={handleImport} style={{
        display: "flex",
        gap: "8px",
        width: "100%"
      }} className="import-form">
        <div style={{ position: "relative", flex: 1 }}>
          <input
            type="text"
            placeholder="Pegar URL de Eventbrite, Luma o Meetup..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={loading}
            autoFocus
            style={{
              width: "100%",
              padding: "10px 12px 10px 36px",
              backgroundColor: "var(--bg-primary)",
              border: "1px solid var(--glass-border)",
              borderRadius: "var(--radius-sm)",
              color: "#fff",
              fontSize: "0.825rem",
              outline: "none",
              transition: "var(--transition-fast)"
            }}
          />
          <Link size={14} style={{
            position: "absolute",
            left: "12px",
            top: "12px",
            color: "var(--text-muted)"
          }} />
        </div>

        <div style={{ display: "flex", gap: "6px" }}>
          <button
            type="submit"
            disabled={loading || !url.trim()}
            className="glow-btn"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "6px",
              padding: "0 16px",
              height: "38px",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.8rem",
              fontWeight: 700,
              cursor: url.trim() && !loading ? "pointer" : "default",
              opacity: url.trim() && !loading ? 1 : 0.6,
              border: "none",
              backgroundColor: "hsl(var(--primary))",
              color: "#000",
              transition: "all 0.2s"
            }}
          >
            {loading ? (
              <Loader2 size={14} className="spin-anim" style={{ animation: "spin 1.5s linear infinite" }} />
            ) : (
              <Plus size={14} />
            )}
            <span>{loading ? "Procesando" : "Importar"}</span>
          </button>

          <button
            type="button"
            onClick={handleCancel}
            disabled={loading}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "38px",
              height: "38px",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--glass-border)",
              backgroundColor: "var(--bg-tertiary)",
              color: "var(--text-secondary)",
              cursor: "pointer",
              transition: "all 0.2s"
            }}
            title="Cancelar"
          >
            <X size={16} />
          </button>
        </div>
      </form>

      {/* Mensajes de Estado */}
      {status.type !== "idle" && (
        <div style={{
          display: "flex",
          alignItems: "flex-start",
          gap: "8px",
          padding: "10px 12px",
          borderRadius: "var(--radius-sm)",
          fontSize: "0.75rem",
          animation: "fadeIn 0.3s ease-out",
          backgroundColor: status.type === "success" 
            ? "rgba(16, 185, 129, 0.08)" 
            : status.type === "warning"
            ? "rgba(245, 158, 11, 0.08)"
            : "rgba(239, 68, 68, 0.08)",
          border: status.type === "success"
            ? "1px solid rgba(16, 185, 129, 0.2)"
            : status.type === "warning"
            ? "1px solid rgba(245, 158, 11, 0.2)"
            : "1px solid rgba(239, 68, 68, 0.2)",
          color: status.type === "success"
            ? "#a7f3d0"
            : status.type === "warning"
            ? "#fde68a"
            : "#fca5a5"
        }}>
          {status.type === "success" && <CheckCircle size={14} style={{ color: "#34d399", marginTop: "2px", flexShrink: 0 }} />}
          {status.type === "warning" && <AlertTriangle size={14} style={{ color: "#fbbf24", marginTop: "2px", flexShrink: 0 }} />}
          {status.type === "error" && <XCircle size={14} style={{ color: "#f87171", marginTop: "2px", flexShrink: 0 }} />}
          <span style={{ lineHeight: "1.4" }}>{status.message}</span>
        </div>
      )}
      
      <style jsx>{`
        @keyframes slideDown {
          from { opacity: 0; transform: translateY(-8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @media (max-width: 480px) {
          .import-form {
            flex-direction: column;
          }
          .import-form button {
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
}
