-- Habilitar extensión para generación de UUIDs si no está habilitada
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabla de Eventos Normalizados
CREATE TABLE IF NOT EXISTS eventos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    source_platform VARCHAR(50) NOT NULL, -- 'luma', 'meetup', 'eventbrite'
    source_id VARCHAR(100) NOT NULL, -- ID único de la plataforma origen para evitar duplicados
    source_url TEXT,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    venue_name VARCHAR(255),
    address TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    city VARCHAR(100) NOT NULL,
    tags JSONB DEFAULT '[]'::jsonb,
    raw_data JSONB,
    is_tech BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_source_event UNIQUE (source_platform, source_id)
);

-- Tabla de Suscripciones (Distribución)
CREATE TABLE IF NOT EXISTS suscripciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50), -- Opcional, para futuros boletines de WhatsApp
    preference_channel VARCHAR(50) DEFAULT 'email', -- 'email' o 'whatsapp'
    city VARCHAR(100) DEFAULT 'Buenos Aires',
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    radius_km DOUBLE PRECISION DEFAULT 15.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Caché de Procesamiento de IA (Token-Economy)
CREATE TABLE IF NOT EXISTS cache_ia (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) UNIQUE NOT NULL, -- Ej: hash del contenido/título del evento evaluado
    value JSONB NOT NULL, -- Ej: { "is_tech": true, "reason": "...", "tags": [...] }
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices de Optimización
CREATE INDEX IF NOT EXISTS idx_eventos_start_time ON eventos(start_time);
CREATE INDEX IF NOT EXISTS idx_eventos_city_is_tech ON eventos(city, is_tech);
CREATE INDEX IF NOT EXISTS idx_eventos_geo ON eventos(latitude, longitude) WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_suscripciones_email ON suscripciones(email);
