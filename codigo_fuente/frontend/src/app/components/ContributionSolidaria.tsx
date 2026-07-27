"use client";

import React from 'react';
import { Heart, ExternalLink } from 'lucide-react';

export const ContributionSolidaria: React.FC = () => {
  return (
    <div className="glass-panel" style={{
      padding: '20px',
      borderRadius: 'var(--radius-lg)',
      marginTop: '20px',
      textAlign: 'center',
      border: '1px solid var(--glass-border)',
      boxShadow: 'var(--glass-shadow)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '10px' }}>
        <Heart size={32} style={{ color: 'hsl(var(--accent))', filter: 'drop-shadow(0 0 8px hsl(var(--accent) / 0.5))' }} />
      </div>
      <h4 style={{ fontSize: '1.1rem', marginBottom: '8px', color: '#fff', fontFamily: 'var(--font-display)' }}>
        Contribución Solidaria
      </h4>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', lineHeight: '1.4', marginBottom: '16px', maxWidth: '320px', margin: '0 auto 16px auto' }}>
        Sysmap es un proyecto de código abierto operado de forma gratuita por <strong>TecnoAncon</strong>. Si te es de utilidad, considera apoyar su mantenimiento.
      </p>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <a
          href="https://cafecito.app/tecnoancon"
          target="_blank"
          rel="noreferrer"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            fontSize: '0.85rem',
            color: '#fff',
            backgroundColor: 'rgba(217, 119, 6, 0.15)',
            border: '1px solid rgba(217, 119, 6, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '10px',
            textDecoration: 'none',
            fontWeight: 600,
            transition: 'var(--transition-fast)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(217, 119, 6, 0.25)';
            e.currentTarget.style.borderColor = 'rgba(217, 119, 6, 0.5)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(217, 119, 6, 0.15)';
            e.currentTarget.style.borderColor = 'rgba(217, 119, 6, 0.3)';
          }}
        >
          ☕ Invitar un Cafecito (Argentina)
          <ExternalLink size={12} />
        </a>

        <a
          href="https://ko-fi.com/tecnoancon"
          target="_blank"
          rel="noreferrer"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            fontSize: '0.85rem',
            color: '#fff',
            backgroundColor: 'rgba(28, 160, 242, 0.15)',
            border: '1px solid rgba(28, 160, 242, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '10px',
            textDecoration: 'none',
            fontWeight: 600,
            transition: 'var(--transition-fast)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(28, 160, 242, 0.25)';
            e.currentTarget.style.borderColor = 'rgba(28, 160, 242, 0.5)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(28, 160, 242, 0.15)';
            e.currentTarget.style.borderColor = 'rgba(28, 160, 242, 0.3)';
          }}
        >
          ❤️ Apoyar en Ko-fi (Internacional)
          <ExternalLink size={12} />
        </a>
      </div>
    </div>
  );
};
