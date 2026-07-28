"use client";

import { useState, useEffect } from "react";
import { useSession, signIn, signOut } from "next-auth/react";
import { 
  List, Mail, RefreshCw, AlertCircle, Search, 
  Settings, LogIn, LogOut, Check, Sliders,
  X, CheckCircle
} from "lucide-react";
import { EventList } from "./components/EventList";
import { SubscriptionForm } from "./components/SubscriptionForm";
import { ContributionSolidaria } from "./components/ContributionSolidaria";
import { ImportEventBar } from "./components/ImportEventBar";

// Custom Github Icon SVG Component since it's not exported by lucide-react in this version
const GithubIcon = ({ size = 16 }: { size?: number }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);

interface EventData {
  id: string;
  title: string;
  source_platform: string;
  source_url: string;
  start_time: string;
  venue_name: string;
  address: string;
  latitude: number | null;
  longitude: number | null;
  distance_km: number | null;
  tags: string[];
  description?: string | null;
}

interface Preferences {
  tags: string[];
  radiusKm: number;
  latitude: number | null;
  longitude: number | null;
}

const getApiBaseUrl = () => {
  if (process.env.NEXT_PUBLIC_VITE_API_BASE_URL) {
    return process.env.NEXT_PUBLIC_VITE_API_BASE_URL;
  }
  if (typeof window !== "undefined") {
    const { hostname, protocol } = window.location;
    if (
      hostname === "localhost" || 
      hostname === "127.0.0.1" ||
      hostname.startsWith("192.168.") ||
      hostname.startsWith("10.") ||
      hostname.startsWith("172.")
    ) {
      return `http://${hostname}:8000`;
    }
    return `${protocol}//${hostname}/api`;
  }
  return "http://localhost:8000";
};

const API_BASE_URL = getApiBaseUrl();

// Tags predefinidos comunes para selección de preferencias
const POPULAR_TAGS = [
  "python", "javascript", "typescript", "react", "vue", "node", 
  "devops", "cloud", "ai", "datascience", "ux", "ui", "qa"
];

export default function Home() {
  const { data: session, status: authStatus } = useSession();
  const [events, setEvents] = useState<EventData[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Sincronización
  const [isIngesting, setIsIngesting] = useState(false);
  
  // Mobile Tab: 'list' | 'subscribe'
  const [activeTab, setActiveTab] = useState<'list' | 'subscribe'>('list');

  // Filtros
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState<'all' | 'luma' | 'meetup' | 'eventbrite'>("all");
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  // Panel y datos de preferencias del usuario autenticado
  const [showPrefPanel, setShowPrefPanel] = useState(false);
  const [preferences, setPreferences] = useState<Preferences>({
    tags: [],
    radiusKm: 15.0,
    latitude: null,
    longitude: null,
  });
  const [prefSaveStatus, setPrefSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  // === ESTADOS PARA FAVORITOS (NextAuth) ===
  const [savedEventIds, setSavedEventIds] = useState<string[]>([]);

  // === ESTADOS PARA LEADS B2B ===
  const [showLeadModal, setShowLeadModal] = useState(false);
  const [leadName, setLeadName] = useState("");
  const [leadEmail, setLeadEmail] = useState("");
  const [leadCompany, setLeadCompany] = useState("");
  const [leadEventUrl, setLeadEventUrl] = useState("");
  const [leadNotes, setLeadNotes] = useState("");
  const [leadStatus, setLeadStatus] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');
  const [leadError, setLeadError] = useState("");

  // === ESTADO DE TOAST NOTIFICATIONS ===
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'info' | 'error' } | null>(null);

  const showToast = (message: string, type: 'success' | 'info' | 'error') => {
    setToast({ message, type });
  };

  // Ocultar Toast automáticamente tras 4 segundos
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  // Cargar eventos guardados al iniciar sesión
  useEffect(() => {
    if (session) {
      fetch("/api/saved-events")
        .then(res => res.json())
        .then(data => {
          if (data && data.eventIds) {
            setSavedEventIds(data.eventIds);
          }
        })
        .catch(err => console.error("Error cargando favoritos:", err));
    } else {
      setSavedEventIds([]);
    }
  }, [session]);

  // 1. Obtener eventos
  const fetchEvents = async (lat?: number, lon?: number) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        city: "Buenos Aires",
        is_tech: "true"
      });

      if (lat !== undefined && lon !== undefined) {
        params.append("latitude", lat.toString());
        params.append("longitude", lon.toString());
      }

      const response = await fetch(`${API_BASE_URL}/events?${params.toString()}`);
      if (!response.ok) {
        throw new Error("No se pudieron cargar los eventos del servidor.");
      }
      
      const data = await response.json();
      setEvents(data);
      localStorage.setItem("sysmap_events_cache", JSON.stringify(data));
    } catch (err: unknown) {
      console.error(err);
      setError("Error de conexión. Cargando datos locales.");
      const cached = localStorage.getItem("sysmap_events_cache");
      if (cached) {
        setEvents(JSON.parse(cached));
      }
    } finally {
      setLoading(false);
    }
  };

  // 2. Disparar ingesta manual
  const handleTriggerIngest = async () => {
    setIsIngesting(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/ingest`, {
        method: "POST"
      });
      if (!response.ok) {
        throw new Error("Error al iniciar la sincronización de eventos.");
      }
      // Espera de 11 segundos
      await new Promise(resolve => setTimeout(resolve, 11000));
      await fetchEvents();
    } catch (err: unknown) {
      console.error(err);
      setError("No se pudo completar la sincronización automática.");
    } finally {
      setIsIngesting(false);
    }
  };

  // 4. Cargar preferencias del usuario al iniciar sesión
  useEffect(() => {
    if (session) {
      fetch("/api/preferences")
        .then(res => {
          if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
          }
          return res.json();
        })
        .then(data => {
          if (data && !data.error) {
            setPreferences({
              tags: Array.isArray(data.tags) ? data.tags : [],
              radiusKm: typeof data.radiusKm === "number" ? data.radiusKm : 15.0,
              latitude: typeof data.latitude === "number" ? data.latitude : null,
              longitude: typeof data.longitude === "number" ? data.longitude : null,
            });
          }
        })
        .catch(err => console.error("Error cargando preferencias:", err));
    }
  }, [session]);

  // Ejecución inicial diferida para evitar setState en fase de render síncrona
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchEvents();
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  // Guardar preferencias del usuario en SQLite
  const handleSavePreferences = async () => {
    setPrefSaveStatus('saving');
    try {
      const response = await fetch("/api/preferences", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(preferences)
      });
      if (response.ok) {
        setPrefSaveStatus('saved');
        showToast("Preferencias del boletín guardadas.", "success");
        setTimeout(() => setPrefSaveStatus('idle'), 3000);
      } else {
        setPrefSaveStatus('error');
      }
    } catch (err) {
      console.error(err);
      setPrefSaveStatus('error');
    }
  };

  // Guardar/Unsave evento (NextAuth callback)
  const handleToggleSave = async (eventId: string) => {
    if (!session) {
      showToast("Inicia sesión con Google para guardar eventos.", "info");
      return;
    }

    try {
      const response = await fetch("/api/saved-events", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ eventId })
      });

      const data = await response.json();

      if (response.ok) {
        if (data.saved) {
          setSavedEventIds(prev => [...prev, eventId]);
          showToast(data.message || "Evento guardado.", "success");
        } else {
          setSavedEventIds(prev => prev.filter(id => id !== eventId));
          showToast(data.message || "Evento eliminado de guardados.", "success");
        }
      } else {
        showToast(data.error || "No se pudo actualizar el favorito.", "error");
      }
    } catch (err) {
      console.error(err);
      showToast("Error de conexión al guardar evento.", "error");
    }
  };

  // Enviar formulario de Leads B2B
  const handleLeadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!leadName || !leadEmail) {
      setLeadError("Nombre y correo electrónico son requeridos.");
      setLeadStatus("error");
      return;
    }

    setLeadStatus("submitting");
    setLeadError("");

    try {
      const res = await fetch("/api/leads", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          name: leadName,
          email: leadEmail,
          company: leadCompany,
          eventUrl: leadEventUrl,
          notes: leadNotes
        })
      });

      const data = await res.json();

      if (res.ok) {
        setLeadStatus("success");
        showToast("¡Solicitud registrada con éxito!", "success");
        setLeadName("");
        setLeadEmail("");
        setLeadCompany("");
        setLeadEventUrl("");
        setLeadNotes("");
        
        setTimeout(() => {
          setShowLeadModal(false);
          setLeadStatus("idle");
        }, 2200);
      } else {
        setLeadStatus("error");
        setLeadError(data.error || "Ocurrió un error.");
      }
    } catch (err) {
      console.error(err);
      setLeadStatus("error");
      setLeadError("Error al conectar con el servidor.");
    }
  };

  // Filtrado de eventos
  const filteredEvents = events.filter(event => {
    if (selectedPlatform !== "all" && event.source_platform.toLowerCase() !== selectedPlatform) {
      return false;
    }
    if (selectedTag && (!event.tags || !event.tags.includes(selectedTag))) {
      return false;
    }
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const titleMatch = event.title.toLowerCase().includes(query);
      const venueMatch = (event.venue_name || "").toLowerCase().includes(query);
      const addressMatch = (event.address || "").toLowerCase().includes(query);
      const tagsMatch = event.tags ? event.tags.some(tag => tag.toLowerCase().includes(query)) : false;
      if (!titleMatch && !venueMatch && !addressMatch && !tagsMatch) {
        return false;
      }
    }
    return true;
  });

  const hasActiveFilters = searchQuery !== "" || selectedPlatform !== "all" || selectedTag !== null;

  // Tags dinámicos únicos obtenidos de los eventos
  const availableTags = Array.from(
    new Set(events.flatMap(event => event.tags || []))
  ).slice(0, 12);

  const togglePreferenceTag = (tag: string) => {
    setPreferences(prev => {
      const currentTags = Array.isArray(prev?.tags) ? prev.tags : [];
      const tags = currentTags.includes(tag)
        ? currentTags.filter(t => t !== tag)
        : [...currentTags, tag];
      return { ...prev, tags };
    });
  };

  return (
    <div style={{
      width: "100%",
      maxWidth: "1000px",
      margin: "0 auto",
      padding: "20px 16px 80px 16px",
      display: "flex",
      flexDirection: "column",
      gap: "24px"
    }}>
      {/* Cabecera / Navegación */}
      <header style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "16px 20px",
        borderRadius: "var(--radius-lg)",
        backgroundColor: "var(--bg-secondary)",
        border: "1px solid var(--glass-border)",
        boxShadow: "var(--glass-shadow)",
        gap: "10px",
        flexWrap: "wrap"
      }}>
        <div style={{ display: "flex", flexDirection: "column" }}>
          <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>
            Sys<span className="text-gradient-solarpunk">map</span>
          </h1>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>
            TecnoAncon Open-Core v1.0
          </span>
        </div>

        {/* Botones de acción Header */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          {/* CTA Leads B2B en navegación */}
          <button
            onClick={() => setShowLeadModal(true)}
            className="glow-btn"
            style={{
              fontSize: "0.75rem",
              padding: "8px 14px",
              borderRadius: "var(--radius-sm)",
              fontWeight: 600,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "4px"
            }}
          >
            <span>¿Organizas un evento?</span>
            <span className="desktop-only-inline">Destácalo aquí</span>
          </button>

          {/* GitHub Icon */}
          <a
            href="https://github.com/tecnoancon/sysmap"
            target="_blank"
            rel="noreferrer"
            style={{
              color: "var(--text-secondary)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "8px",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--glass-border)",
              backgroundColor: "var(--bg-tertiary)",
              transition: "var(--transition-fast)"
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = "#fff"}
            onMouseLeave={(e) => e.currentTarget.style.color = "var(--text-secondary)"}
            title="Ver código fuente en GitHub"
          >
            <GithubIcon size={16} />
          </a>

          {/* Login de Google / Avatar de Usuario */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            {authStatus === "loading" ? (
              <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>...</span>
            ) : session ? (
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <button
                  onClick={() => setShowPrefPanel(!showPrefPanel)}
                  style={{
                    backgroundColor: showPrefPanel ? "hsl(var(--primary) / 0.2)" : "var(--bg-tertiary)",
                    border: "1px solid var(--glass-border)",
                    borderRadius: "var(--radius-sm)",
                    padding: "8px",
                    cursor: "pointer",
                    color: "#fff",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center"
                  }}
                  title="Preferencias de Boletín"
                >
                  <Settings size={16} />
                </button>
                
                {session.user?.image ? (
                  <img
                    src={session.user.image}
                    alt={session.user.name || "User"}
                    style={{ width: "32px", height: "32px", borderRadius: "var(--radius-full)", border: "1px solid var(--glass-border)" }}
                  />
                ) : (
                  <div style={{
                    width: "32px",
                    height: "32px",
                    borderRadius: "var(--radius-full)",
                    backgroundColor: "hsl(var(--primary))",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "0.85rem",
                    fontWeight: 600,
                    color: "#fff"
                  }}>
                    {session.user?.name?.charAt(0) || "U"}
                  </div>
                )}
                
                <button
                  onClick={() => signOut()}
                  style={{
                    backgroundColor: "transparent",
                    border: "none",
                    cursor: "pointer",
                    color: "var(--text-muted)",
                    padding: "4px"
                  }}
                  title="Cerrar sesión"
                >
                  <LogOut size={16} />
                </button>
              </div>
            ) : (
              <button
                onClick={() => signIn("google")}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  fontSize: "0.8rem",
                  padding: "8px 14px",
                  borderRadius: "var(--radius-sm)",
                  backgroundColor: "var(--bg-tertiary)",
                  border: "1px solid var(--glass-border)",
                  color: "#fff",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "var(--transition-fast)"
                }}
                onMouseEnter={(e) => e.currentTarget.style.borderColor = "hsl(var(--primary))"}
                onMouseLeave={(e) => e.currentTarget.style.borderColor = "var(--glass-border)"}
              >
                <LogIn size={14} /> Google Login
              </button>
            )}
          </div>
        </div>
      </header>

      {/* 1. HERO SECTION MINIMALISTA */}
      <section style={{
        padding: "36px 24px",
        borderRadius: "var(--radius-lg)",
        background: "radial-gradient(ellipse at top, hsl(var(--primary) / 0.08), transparent 70%)",
        border: "1px solid var(--glass-border)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        textAlign: "center",
        gap: "12px",
        animation: "fadeIn 0.5s ease-out"
      }}>
        <h1 style={{
          fontSize: "1.85rem",
          fontWeight: 800,
          fontFamily: "var(--font-display)",
          lineHeight: "1.25"
        }}>
          El radar de la comunidad tech en <span className="text-gradient-solarpunk">Buenos Aires</span>
        </h1>
        <p style={{
          fontSize: "0.9rem",
          color: "var(--text-secondary)",
          maxWidth: "520px",
          lineHeight: "1.65",
          margin: "0 auto"
        }}>
          Descubre eventos locales de programación, diseño y tecnología. Operado de forma local-first, sostenible y comunitaria bajo la infraestructura de TecnoAncon.
        </p>
      </section>

      {/* Alerta de Error */}
      {error && (
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          backgroundColor: "rgba(239, 68, 68, 0.1)",
          border: "1px solid rgba(239, 68, 68, 0.3)",
          borderRadius: "var(--radius-md)",
          padding: "12px 16px",
          color: "#fca5a5",
          fontSize: "0.825rem",
          animation: "fadeIn 0.3s ease-out"
        }}>
          <AlertCircle size={18} style={{ flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}

      {/* Panel de Preferencias del Boletín de NextAuth */}
      {showPrefPanel && session && (
        <div className="glass-panel" style={{
          padding: "24px",
          borderRadius: "var(--radius-lg)",
          animation: "slideInUp 0.3s ease-out",
          display: "flex",
          flexDirection: "column",
          gap: "18px"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ fontSize: "1.1rem", display: "flex", alignItems: "center", gap: "8px" }}>
              <Sliders size={18} style={{ color: "hsl(var(--primary))" }} />
              Ajustes de Boletín Inteligente
            </h3>
            <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
              Sesión iniciada como {session.user?.email}
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {/* Selección de Tags */}
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "8px", fontWeight: 500 }}>
                Temas de Interés:
              </label>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                {POPULAR_TAGS.map(tag => {
                  const isSelected = preferences?.tags?.includes(tag) ?? false;
                  return (
                    <button
                      key={tag}
                      onClick={() => togglePreferenceTag(tag)}
                      style={{
                        fontSize: "0.75rem",
                        padding: "6px 12px",
                        borderRadius: "var(--radius-sm)",
                        backgroundColor: isSelected ? "hsl(var(--primary) / 0.2)" : "var(--bg-tertiary)",
                        border: isSelected ? "1px solid hsl(var(--primary))" : "1px solid var(--glass-border)",
                        color: isSelected ? "#fff" : "var(--text-secondary)",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "4px",
                        fontWeight: isSelected ? 600 : 400
                      }}
                    >
                      {isSelected && <Check size={12} />}
                      #{tag}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Foco Regional */}
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "flex", gap: "6px", alignItems: "center" }}>
              <span>📍</span>
              <span>Foco exclusivo regional: <strong>Buenos Aires, Argentina (CABA)</strong></span>
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
            <button
              onClick={() => setShowPrefPanel(false)}
              style={{
                fontSize: "0.8rem",
                padding: "8px 16px",
                borderRadius: "var(--radius-sm)",
                backgroundColor: "transparent",
                border: "1px solid var(--glass-border)",
                color: "var(--text-secondary)",
                cursor: "pointer"
              }}
            >
              Cerrar
            </button>
            <button
              onClick={handleSavePreferences}
              disabled={prefSaveStatus === "saving"}
              className="glow-btn"
              style={{
                fontSize: "0.8rem",
                padding: "8px 20px",
                borderRadius: "var(--radius-sm)",
                opacity: prefSaveStatus === "saving" ? 0.7 : 1
              }}
            >
              {prefSaveStatus === "saving" ? "Guardando..." : 
               prefSaveStatus === "saved" ? "¡Guardado!" : "Guardar Preferencias"}
            </button>
          </div>
        </div>
      )}

      {/* Grid del Directorio */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr",
        gap: "24px"
      }} className="desktop-layout">
        {/* Vista principal móvil (con pestañas) y escritorio de doble columna */}
        <div style={{
          display: "flex",
          flexDirection: "column",
          gap: "16px"
        }}>
          {/* Controles de Búsqueda y Filtros */}
          <div className="glass-panel" style={{
            padding: "16px",
            borderRadius: "var(--radius-md)",
            display: "flex",
            flexDirection: "column",
            gap: "12px"
          }}>
            {/* Input de Búsqueda */}
            <div style={{ position: "relative" }}>
              <input
                type="text"
                placeholder="Buscar eventos por título, dirección o tecnología..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: "100%",
                  padding: "12px 16px 12px 42px",
                  backgroundColor: "var(--bg-primary)",
                  border: "1px solid var(--glass-border)",
                  borderRadius: "var(--radius-sm)",
                  color: "#fff",
                  fontSize: "0.875rem",
                  outline: "none",
                  transition: "var(--transition-fast)"
                }}
              />
              <Search size={16} style={{ position: "absolute", left: "14px", top: "14px", color: "var(--text-muted)" }} />
            </div>

            {/* Selectores de Plataforma y Geolocalización */}
            <div style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "10px"
            }}>
              {/* Plataformas */}
              <div style={{ display: "flex", gap: "6px" }}>
                {(["all", "luma", "meetup", "eventbrite"] as const).map((platform) => (
                  <button
                    key={platform}
                    onClick={() => setSelectedPlatform(platform)}
                    style={{
                      fontSize: "0.725rem",
                      padding: "6px 12px",
                      borderRadius: "var(--radius-sm)",
                      backgroundColor: selectedPlatform === platform ? "var(--bg-tertiary)" : "transparent",
                      border: selectedPlatform === platform ? "1px solid hsl(var(--primary))" : "1px solid var(--glass-border)",
                      color: selectedPlatform === platform ? "#fff" : "var(--text-secondary)",
                      cursor: "pointer",
                      textTransform: "capitalize",
                      fontWeight: selectedPlatform === platform ? 600 : 400
                    }}
                  >
                    {platform}
                  </button>
                ))}
              </div>

              {/* Foco Regional */}
              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                📍 Buenos Aires
              </span>
            </div>
            
            {/* Tags dinámicos sugeridos */}
            {availableTags.length > 0 && (
              <div style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "6px",
                paddingTop: "6px",
                borderTop: "1px solid rgba(255,255,255,0.05)"
              }}>
                <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", alignSelf: "center" }}>Tags:</span>
                {availableTags.map((tag) => {
                  const isSelected = selectedTag === tag;
                  return (
                    <button
                      key={tag}
                      onClick={() => setSelectedTag(isSelected ? null : tag)}
                      style={{
                        fontSize: "0.675rem",
                        padding: "3px 8px",
                        borderRadius: "4px",
                        backgroundColor: isSelected ? "hsl(var(--primary) / 0.2)" : "var(--bg-tertiary)",
                        border: isSelected ? "1px solid hsl(var(--primary))" : "1px solid var(--glass-border)",
                        color: isSelected ? "#fff" : "var(--text-secondary)",
                        cursor: "pointer"
                      }}
                    >
                      #{tag}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Menú de Pestañas en Móvil */}
          <div className="mobile-tabs" style={{
            display: "flex",
            backgroundColor: "var(--bg-secondary)",
            padding: "4px",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--glass-border)"
          }}>
            <button
              onClick={() => setActiveTab('list')}
              style={{
                flex: 1,
                padding: "10px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
                fontSize: "0.85rem",
                fontWeight: 600,
                color: activeTab === 'list' ? "#fff" : "var(--text-secondary)",
                backgroundColor: activeTab === 'list' ? "var(--bg-tertiary)" : "transparent",
                border: "none",
                borderRadius: "var(--radius-sm)",
                cursor: "pointer"
              }}
            >
              <List size={16} /> Eventos ({filteredEvents.length})
            </button>
            <button
              onClick={() => setActiveTab('subscribe')}
              style={{
                flex: 1,
                padding: "10px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
                fontSize: "0.85rem",
                fontWeight: 600,
                color: activeTab === 'subscribe' ? "#fff" : "var(--text-secondary)",
                backgroundColor: activeTab === 'subscribe' ? "var(--bg-tertiary)" : "transparent",
                border: "none",
                borderRadius: "var(--radius-sm)",
                cursor: "pointer"
              }}
            >
              <Mail size={16} /> Suscribirse
            </button>
          </div>

          {/* Columnas para Desktop / Vistas para móvil */}
          <div className="layout-body-wrapper">
            {/* Columna de eventos */}
            <div className={`col-events ${activeTab === 'list' ? 'mobile-visible' : 'mobile-hidden'}`}>
              <div style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "14px",
                padding: "0 4px",
                flexWrap: "wrap",
                gap: "8px"
              }}>
                <h3 style={{ fontSize: "1.05rem", fontWeight: 700, margin: 0, color: "#fff", fontFamily: "var(--font-display)" }}>
                  Directorio
                </h3>
                <ImportEventBar 
                  apiBaseUrl={API_BASE_URL} 
                  onImportSuccess={() => fetchEvents()} 
                />
              </div>
              {loading ? (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "80px 20px", gap: "12px", color: "var(--text-secondary)" }}>
                  <RefreshCw size={24} className="spin-anim" style={{ animation: "spin 1.5s linear infinite" }} />
                  <span style={{ fontSize: "0.85rem" }}>Cargando directorio de eventos locales...</span>
                </div>
              ) : (
                <EventList
                  events={filteredEvents}
                  selectedEventId={selectedEventId}
                  onEventSelect={(id) => setSelectedEventId((prev) => prev === id ? null : id)}
                  onTriggerIngest={handleTriggerIngest}
                  isIngesting={isIngesting}
                  savedEventIds={savedEventIds}
                  onToggleSave={handleToggleSave}
                  hasActiveFilters={hasActiveFilters}
                  apiBaseUrl={API_BASE_URL}
                />
              )}
            </div>

            {/* Columna lateral de boletín + donación */}
            <div className={`col-sidebar ${activeTab === 'subscribe' ? 'mobile-visible' : 'mobile-hidden'}`}>
              {/* 2. CAPTACIÓN LEADS B2B - SIDEBAR CTA (Liderando columna lateral derecha) */}
              <div className="glass-panel" style={{
                padding: "20px",
                borderRadius: "var(--radius-lg)",
                border: "1px solid hsl(var(--secondary) / 0.3)",
                boxShadow: "0 8px 30px hsl(var(--secondary) / 0.05)",
                display: "flex",
                flexDirection: "column",
                gap: "12px",
                marginBottom: "8px"
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span style={{ fontSize: "1.35rem" }}>🚀</span>
                  <h4 style={{ fontSize: "1rem", fontWeight: 700, color: "#fff", fontFamily: "var(--font-display)" }}>
                    ¿Organizas un evento tech?
                  </h4>
                </div>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.8rem", lineHeight: "1.4" }}>
                  Promociona tu workshop, meetup o conferencia gratis en el radar y llega a toda la comunidad de Buenos Aires.
                </p>
                <button
                  onClick={() => setShowLeadModal(true)}
                  className="glow-btn"
                  style={{
                    padding: "11px",
                    borderRadius: "var(--radius-md)",
                    fontSize: "0.825rem",
                    fontWeight: 700,
                    width: "100%"
                  }}
                >
                  Destácalo aquí
                </button>
              </div>

              <SubscriptionForm
                apiBaseUrl={API_BASE_URL}
                latitude={null}
                longitude={null}
              />
              
              <ContributionSolidaria />
            </div>
          </div>
        </div>
      </div>

      {/* 4. AUTORIDAD DE MARCA - EL FOOTER */}
      <footer style={{
        marginTop: "48px",
        paddingTop: "24px",
        borderTop: "1px solid var(--glass-border)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "14px",
        color: "var(--text-muted)",
        fontSize: "0.8rem",
        textAlign: "center"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          {/* GitHub Icon Footer */}
          <a
            href="https://github.com/tecnoancon/sysmap"
            target="_blank"
            rel="noreferrer"
            style={{
              color: "var(--text-muted)",
              transition: "var(--transition-fast)",
              display: "flex",
              alignItems: "center",
              gap: "4px"
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = "#fff"}
            onMouseLeave={(e) => e.currentTarget.style.color = "var(--text-muted)"}
          >
            <GithubIcon size={15} /> GitHub
          </a>
          <span>•</span>
          <a
            href="https://cafecito.app/tecnoancon"
            target="_blank"
            rel="noreferrer"
            style={{ color: "var(--text-muted)", transition: "var(--transition-fast)" }}
            onMouseEnter={(e) => e.currentTarget.style.color = "#fff"}
            onMouseLeave={(e) => e.currentTarget.style.color = "var(--text-muted)"}
          >
            Cafecito
          </a>
          <span>•</span>
          <a
            href="https://ko-fi.com/tecnoancon"
            target="_blank"
            rel="noreferrer"
            style={{ color: "var(--text-muted)", transition: "var(--transition-fast)" }}
            onMouseEnter={(e) => e.currentTarget.style.color = "#fff"}
            onMouseLeave={(e) => e.currentTarget.style.color = "var(--text-muted)"}
          >
            Ko-fi
          </a>
        </div>
        <div>
          <span>Construido y mantenido por </span>
          <a
            href="https://tecnoancon.com"
            target="_blank"
            rel="noreferrer"
            style={{
              color: "hsl(var(--primary))",
              textDecoration: "none",
              fontWeight: 600,
              transition: "var(--transition-fast)"
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = "#fff"}
            onMouseLeave={(e) => e.currentTarget.style.color = "hsl(var(--primary))"}
          >
            TecnoAncon
          </a>
          <span>. © {new Date().getFullYear()} Todos los derechos reservados.</span>
        </div>
      </footer>

      {/* MODAL CAPTACIÓN LEADS B2B */}
      {showLeadModal && (
        <div className="modal-backdrop" onClick={() => setShowLeadModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setShowLeadModal(false)}>
              <X size={18} />
            </button>
            
            <h3 style={{ fontSize: "1.25rem", marginBottom: "8px", fontFamily: "var(--font-display)" }}>
              Destaca tu Evento Tech
            </h3>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "20px", lineHeight: "1.4" }}>
              Completa los datos y nuestro equipo de operaciones B2B se pondrá en contacto para destacar tu actividad en el radar.
            </p>

            {leadStatus === "success" ? (
              <div style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                padding: "30px 10px",
                gap: "12px",
                textAlign: "center"
              }}>
                <CheckCircle size={44} style={{ color: "hsl(var(--secondary))" }} />
                <h4 style={{ fontSize: "1rem", fontWeight: 600 }}>¡Solicitud Recibida!</h4>
                <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
                  Hemos registrado tus datos. Te contactaremos a la brevedad.
                </p>
              </div>
            ) : (
              <form onSubmit={handleLeadSubmit} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  <label className="form-label-premium">Nombre del Organizador</label>
                  <input
                    type="text"
                    required
                    className="form-input-premium"
                    placeholder="Tu nombre completo"
                    value={leadName}
                    onChange={(e) => setLeadName(e.target.value)}
                  />
                </div>
                
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  <label className="form-label-premium">Correo Electrónico</label>
                  <input
                    type="email"
                    required
                    className="form-input-premium"
                    placeholder="organizador@empresa.com"
                    value={leadEmail}
                    onChange={(e) => setLeadEmail(e.target.value)}
                  />
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  <label className="form-label-premium">Compañía / Comunidad (Opcional)</label>
                  <input
                    type="text"
                    className="form-input-premium"
                    placeholder="Ej. TecnoAncon, Python BA"
                    value={leadCompany}
                    onChange={(e) => setLeadCompany(e.target.value)}
                  />
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  <label className="form-label-premium">Enlace del Evento (Opcional)</label>
                  <input
                    type="url"
                    className="form-input-premium"
                    placeholder="https://luma.lu/... o meetup.com/..."
                    value={leadEventUrl}
                    onChange={(e) => setLeadEventUrl(e.target.value)}
                  />
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  <label className="form-label-premium">Notas o Comentarios</label>
                  <textarea
                    className="form-input-premium"
                    style={{ minHeight: "80px", resize: "vertical" }}
                    placeholder="Cuéntanos brevemente sobre la actividad..."
                    value={leadNotes}
                    onChange={(e) => setLeadNotes(e.target.value)}
                  />
                </div>

                {leadStatus === "error" && (
                  <div style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    backgroundColor: "rgba(239, 68, 68, 0.1)",
                    border: "1px solid rgba(239, 68, 68, 0.3)",
                    borderRadius: "var(--radius-sm)",
                    padding: "10px",
                    color: "#fca5a5",
                    fontSize: "0.75rem"
                  }}>
                    <AlertCircle size={16} style={{ flexShrink: 0 }} />
                    <span>{leadError}</span>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={leadStatus === "submitting"}
                  className="glow-btn"
                  style={{
                    padding: "14px",
                    borderRadius: "var(--radius-md)",
                    fontSize: "0.9rem",
                    fontWeight: 700,
                    marginTop: "6px",
                    opacity: leadStatus === "submitting" ? 0.7 : 1
                  }}
                >
                  {leadStatus === "submitting" ? "Enviando..." : "Enviar Solicitud"}
                </button>
              </form>
            )}
          </div>
        </div>
      )}

      {/* TOAST SYSTEM */}
      {toast && (
        <div className="toast-container">
          <div className={`toast-notification toast-${toast.type}`}>
            {toast.type === "success" && <CheckCircle size={18} style={{ color: "hsl(var(--secondary))" }} />}
            {toast.type === "info" && <AlertCircle size={18} style={{ color: "hsl(var(--primary))" }} />}
            {toast.type === "error" && <AlertCircle size={18} style={{ color: "#ef4444" }} />}
            <span>{toast.message}</span>
          </div>
        </div>
      )}

      {/* CSS embebido para Layout Responsivo y Animaciones */}
      <style jsx global>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .spin-anim {
          animation: spin 1s linear infinite;
        }
        
        /* Layout doble columna en desktop, móvil en cascada controlada */
        .layout-body-wrapper {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .mobile-tabs {
          display: flex;
        }

        .mobile-hidden {
          display: none !important;
        }

        .desktop-only-inline {
          display: inline;
        }

        @media (max-width: 600px) {
          .desktop-only-inline {
            display: none !important;
          }
        }

        @media (min-width: 768px) {
          .mobile-tabs {
            display: none !important;
          }
          
          .layout-body-wrapper {
            display: grid;
            grid-template-columns: 1.5fr 1fr;
            align-items: start;
            gap: 24px;
          }
          
          .col-events.mobile-hidden, .col-sidebar.mobile-hidden {
            display: block !important;
          }
          
          .mobile-visible {
            display: block !important;
          }
        }
      `}</style>
    </div>
  );
}
