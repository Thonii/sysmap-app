"use client";

import React, { useState } from 'react';
import { Mail, Phone, CheckCircle, AlertCircle } from 'lucide-react';

interface SubscriptionFormProps {
  apiBaseUrl: string;
  latitude: number | null;
  longitude: number | null;
}

export const SubscriptionForm: React.FC<SubscriptionFormProps> = ({
  apiBaseUrl,
  latitude,
  longitude
}) => {
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [preferenceChannel, setPreferenceChannel] = useState<'email' | 'whatsapp'>('email');
  const radiusKm = 15;
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setStatus('error');
      setMessage('El correo electrónico es requerido.');
      return;
    }

    setStatus('loading');
    try {
      // Construir parámetros
      const params = new URLSearchParams({
        email,
        preference_channel: preferenceChannel,
        radius_km: radiusKm.toString(),
        city: 'Buenos Aires'
      });

      if (phone) params.append('phone', phone);
      if (latitude) params.append('latitude', latitude.toString());
      if (longitude) params.append('longitude', longitude.toString());

      const response = await fetch(`${apiBaseUrl}/subscriptions?${params.toString()}`, {
        method: 'POST'
      });

      const data = await response.json();

      if (response.ok) {
        setStatus('success');
        setMessage(data.message || '¡Suscripción exitosa!');
        setEmail('');
        setPhone('');
      } else {
        setStatus('error');
        setMessage(data.detail || 'Ocurrió un error al procesar la suscripción.');
      }
    } catch (error) {
      console.error(error);
      setStatus('error');
      setMessage('No se pudo conectar con el servidor.');
    }
  };

  return (
    <div className="glass-panel" style={{
      padding: '20px',
      borderRadius: 'var(--radius-lg)',
      animation: 'slideInUp 0.4s ease-out',
      maxWidth: '400px',
      width: '100%',
      margin: '0 auto'
    }}>
      <h3 style={{ fontSize: '1.25rem', marginBottom: '8px', fontFamily: 'var(--font-display)' }}>
        Boletín de Eventos
      </h3>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '20px', lineHeight: '1.4' }}>
        Recibe semanalmente en Buenos Aires los 3 eventos tech más cercanos a tu ubicación.
      </p>

      {status === 'success' ? (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          backgroundColor: 'hsl(var(--secondary) / 0.1)',
          border: '1px solid hsl(var(--secondary) / 0.3)',
          borderRadius: 'var(--radius-md)',
          padding: '16px',
          color: '#fff',
          animation: 'fadeIn 0.3s ease-in'
        }}>
          <CheckCircle size={24} style={{ color: 'hsl(var(--secondary))', flexShrink: 0 }} />
          <div>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 600 }}>¡Suscripción Activada!</h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{message}</p>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Canal de Preferencia Toggle */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
              ¿Dónde quieres recibir el boletín?
            </span>
            <div style={{
              display: 'flex',
              backgroundColor: 'var(--bg-tertiary)',
              padding: '4px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--glass-border)'
            }}>
              <button
                type="button"
                onClick={() => setPreferenceChannel('email')}
                style={{
                  flex: 1,
                  padding: '8px',
                  backgroundColor: preferenceChannel === 'email' ? 'hsl(var(--primary) / 0.2)' : 'transparent',
                  color: preferenceChannel === 'email' ? '#fff' : 'var(--text-secondary)',
                  border: preferenceChannel === 'email' ? '1px solid hsl(var(--primary) / 0.4)' : 'none',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                  transition: 'var(--transition-fast)'
                }}
              >
                <Mail size={14} /> Email
              </button>
              <button
                type="button"
                onClick={() => setPreferenceChannel('whatsapp')}
                style={{
                  flex: 1,
                  padding: '8px',
                  backgroundColor: preferenceChannel === 'whatsapp' ? 'hsl(var(--secondary) / 0.2)' : 'transparent',
                  color: preferenceChannel === 'whatsapp' ? '#fff' : 'var(--text-secondary)',
                  border: preferenceChannel === 'whatsapp' ? '1px solid hsl(var(--secondary) / 0.4)' : 'none',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                  transition: 'var(--transition-fast)'
                }}
              >
                <Phone size={14} /> WhatsApp
              </button>
            </div>
          </div>

          {/* Email input */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label htmlFor="email" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Correo Electrónico</label>
            <div style={{ position: 'relative' }}>
              <input
                id="email"
                type="email"
                required
                placeholder="ejemplo@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px 12px 12px 40px',
                  backgroundColor: 'var(--bg-tertiary)',
                  border: '1px solid var(--glass-border)',
                  borderRadius: 'var(--radius-md)',
                  color: '#fff',
                  fontSize: '0.875rem',
                  outline: 'none',
                  transition: 'var(--transition-fast)'
                }}
              />
              <Mail size={16} style={{ position: 'absolute', left: '12px', top: '14px', color: 'var(--text-muted)' }} />
            </div>
          </div>

          {/* Phone input (WhatsApp preferred) */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label htmlFor="phone" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Teléfono Celular {preferenceChannel === 'email' && '(Opcional)'}
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="phone"
                type="tel"
                required={preferenceChannel === 'whatsapp'}
                placeholder="+54 9 11 1234 5678"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px 12px 12px 40px',
                  backgroundColor: 'var(--bg-tertiary)',
                  border: '1px solid var(--glass-border)',
                  borderRadius: 'var(--radius-md)',
                  color: '#fff',
                  fontSize: '0.875rem',
                  outline: 'none',
                  transition: 'var(--transition-fast)'
                }}
              />
              <Phone size={16} style={{ position: 'absolute', left: '12px', top: '14px', color: 'var(--text-muted)' }} />
            </div>
          </div>

          {status === 'error' && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: 'var(--radius-sm)',
              padding: '10px',
              color: '#fca5a5',
              fontSize: '0.75rem'
            }}>
              <AlertCircle size={16} style={{ flexShrink: 0 }} />
              <span>{message}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={status === 'loading'}
            className="glow-btn"
            style={{
              padding: '14px',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.9rem',
              marginTop: '8px',
              opacity: status === 'loading' ? 0.7 : 1
            }}
          >
            {status === 'loading' ? 'Procesando...' : 'Suscribirse Ahora'}
          </button>
        </form>
      )}
    </div>
  );
};
