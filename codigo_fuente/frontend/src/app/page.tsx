"use client";

import { useState, useEffect } from "react";
import { useSession, signIn, signOut } from "next-auth/react";
import { 
  List, Mail, RefreshCw, Compass, AlertCircle, Search, 
  Settings, LogIn, LogOut, Check, Sliders, Map 
} from "lucide-react";
import { EventList } from "./components/EventList";
import { SubscriptionForm } from "./components/SubscriptionForm";
import { ContributionSolidaria } from "./components/ContributionSolidaria";

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

  // Ubicación del navegador (Local-First y Opt-in)
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null);
  const [locating, setLocating] = useState(false);

  // Panel y datos de preferencias del usuario autenticado
  const [showPrefPanel, setShowPrefPanel] = useState(false);
  const [preferences, setPreferences] = useState<Preferences>({
    tags: [],
    radiusKm: 15.0,
    latitude: null,
    longitude: null,
  });
  const [prefSaveStatus, setPrefSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

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
    } catch (err: any) {
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
      await fetchEvents(coords?.lat, coords?.lon);
    } catch (err: any) {
      console.error(err);
      setError("No se pudo completar la sincronización automática.");
    } finally {
      setIsIngesting(false);
    }
  };

  // 3. Activar búsqueda geolocalizada (Opt-in)
  const handleRequestLocation = () => {
    setLocating(true);
    if (!navigator.geolocation) {
      setError("La geolocalización no está soportada por tu navegador.");
      setLocating(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        setCoords({ lat, lon });
        setLocating(false);
        fetchEvents(lat, lon);
        
        // Si está logueado, autocompletar coordenadas de preferencias
        if (session) {
          setPreferences(prev => ({
            ...prev,
            latitude: lat,
            longitude: lon
          }));
        }
      },
      (error) => {
        console.error(error);
        setError("Permiso denegado o error de geolocalización. Usando Buenos Aires centro.");
        setLocating(false);
        fetchEvents();
      },
      { timeout: 10000 }
    );
  };

  // 4. Cargar preferencias del usuario al iniciar sesión
  useEffect(() => {
    if (session) {
      fetch("/api/preferences")
        .then(res => res.json())
        .then(data => {
          if (!data.error) {
            setPreferences(data);
          }
        })
        .catch(err => console.error("Error cargando preferencias:", err));
    }
  }, [session]);

  // Ejecución inicial
  useEffect(() => {
    fetchEvents();
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
        setTimeout(() => setPrefSaveStatus('idle'), 3000);
      } else {
        setPrefSaveStatus('error');
      }
    } catch (err) {
      console.error(err);
      setPrefSaveStatus('error');
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

  // Tags dinámicos únicos obtenidos de los eventos
  const availableTags = Array.from(
    new Set(events.flatMap(event => event.tags || []))
  ).slice(0, 12);

  const togglePreferenceTag = (tag: string) => {
    setPreferences(prev => {
      const tags = prev.tags.includes(tag)
        ? prev.tags.filter(t => t !== tag)
        : [...prev.tags, tag];
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
        boxShadow: "var(--glass-shadow)"
      }}>
        <div>
          <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>
            Sys<span className="text-gradient-solarpunk">map</span>
          </h1>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>
            TecnoAncon Open-Core MVP
          </span>
        </div>

        {/* Login de Google / Avatar de Usuario */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
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
      </header>

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
                  const isSelected = preferences.tags.includes(tag);
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
              {loading ? (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "80px 20px", gap: "12px", color: "var(--text-secondary)" }}>
                  <RefreshCw size={24} className="spin-anim" style={{ animation: "spin 1.5s linear infinite" }} />
                  <span style={{ fontSize: "0.85rem" }}>Cargando directorio de eventos locales...</span>
                </div>
              ) : (
                <EventList
                  events={filteredEvents}
                  selectedEventId={selectedEventId}
                  onEventSelect={setSelectedEventId}
                  onTriggerIngest={handleTriggerIngest}
                  isIngesting={isIngesting}
                />
              )}
            </div>

            {/* Columna lateral de boletín + donación */}
            <div className={`col-sidebar ${activeTab === 'subscribe' ? 'mobile-visible' : 'mobile-hidden'}`}>
              <SubscriptionForm
                apiBaseUrl={API_BASE_URL}
                latitude={coords?.lat || null}
                longitude={coords?.lon || null}
              />
              
              <ContributionSolidaria />
            </div>
          </div>
        </div>
      </div>

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

