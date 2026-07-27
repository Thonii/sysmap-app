"use client";

import React from 'react';
import { Calendar, MapPin, ExternalLink, Map, RefreshCw } from 'lucide-react';

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

interface EventListProps {
  events: EventData[];
  selectedEventId: string | null;
  onEventSelect: (id: string) => void;
  onTriggerIngest?: () => void;
  isIngesting?: boolean;
}

export const EventList: React.FC<EventListProps> = ({
  events,
  selectedEventId,
  onEventSelect,
  onTriggerIngest,
  isIngesting = false
}) => {
  const getPlatformStyle = (platform: string) => {
    switch (platform.toLowerCase()) {
      case 'luma':
        return {
          bg: 'rgba(59, 130, 246, 0.15)',
          border: 'rgba(59, 130, 246, 0.3)',
          text: '#3b82f6',
          label: 'Luma'
        };
      case 'meetup':
        return {
          bg: 'rgba(239, 68, 68, 0.15)',
          border: 'rgba(239, 68, 68, 0.3)',
          text: '#ef4444',
          label: 'Meetup'
        };
      case 'eventbrite':
        return {
          bg: 'rgba(249, 115, 22, 0.15)',
          border: 'rgba(249, 115, 22, 0.3)',
          text: '#f97316',
          label: 'Eventbrite'
        };
      default:
        return {
          bg: 'rgba(148, 163, 184, 0.15)',
          border: 'rgba(148, 163, 184, 0.3)',
          text: '#94a3b8',
          label: 'Evento'
        };
    }
  };

  const formatEventDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleString('es-AR', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getGoogleMapsUrl = (address: string, venueName: string) => {
    const query = address || venueName || 'Buenos Aires, Argentina';
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
  };

  if (events.length === 0) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px 20px',
        textAlign: 'center',
        color: 'var(--text-secondary)',
        gap: '16px'
      }}>
        <div>
          <p style={{ fontSize: '1rem', marginBottom: '8px', color: '#fff', fontWeight: 600 }}>
            La base de datos está vacía
          </p>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', maxWidth: '300px', margin: '0 auto', lineHeight: '1.4' }}>
            No hemos encontrado eventos tecnológicos locales almacenados en tu sistema local aún.
          </span>
        </div>
        
        {onTriggerIngest && (
          <button
            onClick={onTriggerIngest}
            disabled={isIngesting}
            className="glow-btn"
            style={{
              padding: '12px 24px',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.85rem',
              opacity: isIngesting ? 0.7 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginTop: '8px'
            }}
          >
            {isIngesting ? (
              <>
                <RefreshCw size={16} className="spin-anim" style={{ 
                  animation: 'spin 1.5s linear infinite',
                  marginRight: '4px'
                }} />
                Sincronizando eventos... (10s)
              </>
            ) : (
              'Buscar Eventos en Tiempo Real'
            )}
          </button>
        )}
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '14px',
      padding: '2px'
    }}>
      {events.map((event) => {
        const isSelected = event.id === selectedEventId;
        const style = getPlatformStyle(event.source_platform);
        
        return (
          <div
            key={event.id}
            onClick={() => onEventSelect(event.id)}
            style={{
              padding: '20px',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: 'var(--bg-secondary)',
              border: isSelected ? '1px solid hsl(var(--primary))' : '1px solid var(--glass-border)',
              cursor: 'pointer',
              transition: 'var(--transition-normal)',
              boxShadow: isSelected ? '0 10px 30px rgba(0,0,0,0.3)' : 'var(--glass-shadow)',
              transform: isSelected ? 'translateY(-2px)' : 'none'
            }}
          >
            {/* Cabecera Tarjeta */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <span style={{
                fontSize: '0.675rem',
                fontWeight: 700,
                padding: '3px 10px',
                borderRadius: 'var(--radius-full)',
                backgroundColor: style.bg,
                border: `1px solid ${style.border}`,
                color: style.text,
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}>
                {style.label}
              </span>
              
              {event.distance_km !== null && (
                <span style={{
                  fontSize: '0.725rem',
                  fontWeight: 600,
                  color: 'hsl(var(--secondary))',
                  backgroundColor: 'hsl(var(--secondary) / 0.1)',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid hsl(var(--secondary) / 0.2)'
                }}>
                  📍 a {event.distance_km} km
                </span>
              )}
            </div>

            {/* Título del Evento */}
            <h4 style={{
              fontSize: '1.05rem',
              fontWeight: 700,
              lineHeight: 1.4,
              marginBottom: '12px',
              color: '#fff',
              fontFamily: 'var(--font-display)'
            }}>
              {event.title}
            </h4>

            {/* Información de Metadatos */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                <Calendar size={15} style={{ color: 'hsl(var(--primary))', flexShrink: 0 }} />
                <span style={{ textTransform: 'capitalize' }}>
                  {formatEventDate(event.start_time)}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                <MapPin size={15} style={{ color: 'hsl(var(--secondary))', flexShrink: 0 }} />
                <span style={{
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: '300px'
                }} title={event.address || event.venue_name}>
                  {event.venue_name || event.address || 'Online / A confirmar'}
                </span>
              </div>
            </div>

            {/* Tags de Tecnologías */}
            {event.tags && event.tags.length > 0 && (
              <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '6px',
                marginBottom: '18px'
              }}>
                {event.tags.map((tag) => (
                  <span
                    key={tag}
                    style={{
                      fontSize: '0.675rem',
                      fontWeight: 500,
                      padding: '2px 8px',
                      borderRadius: '4px',
                      backgroundColor: 'var(--bg-tertiary)',
                      border: '1px solid var(--glass-border)',
                      color: 'var(--text-secondary)'
                    }}
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            )}

            {/* Acciones */}
            <div style={{
              display: 'flex',
              gap: '10px',
              paddingTop: '12px',
              borderTop: '1px solid rgba(255,255,255,0.05)'
            }}
            onClick={(e) => e.stopPropagation()}
            >
              {/* CTA 2: Google Maps Externo */}
              <a
                href={getGoogleMapsUrl(event.address, event.venue_name)}
                target="_blank"
                rel="noreferrer"
                style={{
                  flex: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                  fontSize: '0.8rem',
                  color: 'var(--text-primary)',
                  backgroundColor: 'var(--bg-tertiary)',
                  border: '1px solid var(--glass-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '10px 12px',
                  textDecoration: 'none',
                  fontWeight: 600,
                  transition: 'var(--transition-fast)'
                }}
              >
                <Map size={14} style={{ color: 'hsl(var(--secondary))' }} />
                Cómo llegar
              </a>
              
              {/* CTA 1: Registro / RSVP Oficial */}
              <a
                href={event.source_url}
                target="_blank"
                rel="noreferrer"
                style={{
                  flex: 1.2,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                  fontSize: '0.8rem',
                  color: '#fff',
                  background: 'linear-gradient(135deg, hsl(var(--primary)), hsl(var(--primary) / 0.8))',
                  borderRadius: 'var(--radius-md)',
                  padding: '10px 12px',
                  textDecoration: 'none',
                  fontWeight: 700,
                  transition: 'var(--transition-fast)',
                  boxShadow: '0 4px 10px rgba(59, 130, 246, 0.15)'
                }}
              >
                Registrarse
                <ExternalLink size={14} />
              </a>
            </div>
          </div>
        );
      })}
    </div>
  );
};
