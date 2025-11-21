-- =====================================================================
-- ESTRUCTURA COMPLETA: SCHEMA + ACCOUNTS + CAMPAIGNS + ADSETS + ADS
-- Sistema de tablas relacionadas para AutoRepCuentas
-- PRIMARY KEY compuesta para permitir múltiples insights por día
-- =====================================================================

-- Crear esquema si no existe
CREATE SCHEMA IF NOT EXISTS "Markeitng";

-- Eliminar tablas si existen (en orden correcto por las foreign keys)
DROP TABLE IF EXISTS "Markeitng".ads CASCADE;
DROP TABLE IF EXISTS "Markeitng".adsets CASCADE;
DROP TABLE IF EXISTS "Markeitng".campaigns CASCADE;
DROP TABLE IF EXISTS "Markeitng".accounts CASCADE;

-- =====================================================================
-- TABLA: ACCOUNTS (Cuentas de Meta Ads)
-- =====================================================================
CREATE TABLE "Markeitng".accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    account_name VARCHAR(255) NOT NULL,
    account_key VARCHAR(10) NOT NULL,
    multimarca VARCHAR(10),
    marcas TEXT,
    app_id VARCHAR(100),
    has_valid_token BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_sync_date TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(account_key)
);

-- =====================================================================
-- TABLA: CAMPAIGNS (Campañas + Insights)
-- PRIMARY KEY compuesta (campaign_id, insights_date_start)
-- Permite múltiples insights diarios por campaña
-- =====================================================================
CREATE TABLE "Markeitng".campaigns (
    -- PRIMARY KEY COMPUESTA
    campaign_id VARCHAR(50) NOT NULL,
    insights_date_start DATE NOT NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Relación con account
    account_id VARCHAR(50) NOT NULL REFERENCES "Markeitng".accounts(account_id) ON DELETE CASCADE,
    account_name VARCHAR(255),

    -- Información de campaña
    campaign_name TEXT,
    campaign_status VARCHAR(50),
    campaign_objective VARCHAR(100),
    campaign_created_time TIMESTAMP WITH TIME ZONE,
    campaign_updated_time TIMESTAMP WITH TIME ZONE,
    campaign_start_time TIMESTAMP WITH TIME ZONE,
    campaign_stop_time TIMESTAMP WITH TIME ZONE,

    -- Configuración
    buying_type VARCHAR(50),
    bid_strategy VARCHAR(100),
    budget_remaining DECIMAL(12,2),
    configured_status VARCHAR(50),
    effective_status VARCHAR(50),
    special_ad_category VARCHAR(50),
    can_use_spend_cap BOOLEAN,
    budget_rebalance_flag BOOLEAN,
    is_skadnetwork_attribution BOOLEAN,
    smart_promotion_type VARCHAR(100),
    can_create_brand_lift_study BOOLEAN,

    -- Período de insights
    insights_date_stop DATE,

    -- Métricas de rendimiento
    impressions BIGINT DEFAULT 0,
    clicks BIGINT DEFAULT 0,
    spend DECIMAL(12,2) DEFAULT 0.00,
    reach BIGINT DEFAULT 0,
    frequency DECIMAL(8,6) DEFAULT 0,

    -- Métricas de costos
    cpm DECIMAL(8,2) DEFAULT 0.00,
    cpc DECIMAL(8,2) DEFAULT 0.00,
    ctr DECIMAL(8,6) DEFAULT 0,

    -- Métricas de clics
    inline_link_clicks BIGINT DEFAULT 0,
    inline_link_click_ctr DECIMAL(8,6) DEFAULT 0,
    unique_clicks BIGINT DEFAULT 0,
    unique_ctr DECIMAL(8,6) DEFAULT 0,

    -- Configuración de optimización
    optimization_goal VARCHAR(100),

    -- Metadatos
    extraction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data_source VARCHAR(50) DEFAULT 'LEO_4.0_EXTRACTOR',

    -- PRIMARY KEY COMPUESTA
    PRIMARY KEY (campaign_id, insights_date_start)
);

-- Índices para mejorar búsquedas
CREATE INDEX idx_campaigns_date_range ON "Markeitng".campaigns(insights_date_start, insights_date_stop);
CREATE INDEX idx_campaigns_account ON "Markeitng".campaigns(account_id);
CREATE INDEX idx_campaigns_spend ON "Markeitng".campaigns(spend DESC);

-- =====================================================================
-- TABLA: ADSETS (Ad Sets + Insights)
-- PRIMARY KEY compuesta (adset_id, insights_date_start)
-- Permite múltiples insights diarios por adset
-- =====================================================================
CREATE TABLE "Markeitng".adsets (
    -- PRIMARY KEY COMPUESTA
    adset_id VARCHAR(50) NOT NULL,
    insights_date_start DATE NOT NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Relaciones
    account_id VARCHAR(50) NOT NULL REFERENCES "Markeitng".accounts(account_id) ON DELETE CASCADE,
    account_name VARCHAR(255),
    campaign_id VARCHAR(50) NOT NULL,

    -- Información de adset
    adset_name TEXT,
    adset_status VARCHAR(50),
    configured_status VARCHAR(50),
    effective_status VARCHAR(50),

    -- Fechas de adset
    adset_created_time TIMESTAMP WITH TIME ZONE,
    adset_updated_time TIMESTAMP WITH TIME ZONE,
    adset_start_time TIMESTAMP WITH TIME ZONE,
    adset_end_time TIMESTAMP WITH TIME ZONE,

    -- Configuración
    optimization_goal VARCHAR(100),
    billing_event VARCHAR(50),
    bid_amount DECIMAL(12,2),
    budget_remaining DECIMAL(12,2),
    daily_budget DECIMAL(12,2),
    lifetime_budget DECIMAL(12,2),
    bid_strategy VARCHAR(100),
    destination_type VARCHAR(100),
    pacing_type VARCHAR(50),
    is_dynamic_creative BOOLEAN DEFAULT false,

    -- Datos complejos (JSON)
    targeting TEXT,
    attribution_spec TEXT,
    promoted_object TEXT,

    -- Período de insights
    insights_date_stop DATE,

    -- Métricas de rendimiento
    impressions BIGINT DEFAULT 0,
    clicks BIGINT DEFAULT 0,
    spend DECIMAL(12,2) DEFAULT 0.00,
    reach BIGINT DEFAULT 0,
    frequency DECIMAL(8,6) DEFAULT 0,

    -- Métricas de costos
    cpm DECIMAL(8,2) DEFAULT 0.00,
    cpc DECIMAL(8,2) DEFAULT 0.00,
    ctr DECIMAL(8,6) DEFAULT 0,

    -- Métricas de clics
    inline_link_clicks BIGINT DEFAULT 0,
    inline_link_click_ctr DECIMAL(8,6) DEFAULT 0,
    unique_clicks BIGINT DEFAULT 0,
    unique_ctr DECIMAL(8,6) DEFAULT 0,

    -- Metadatos
    extraction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data_source VARCHAR(50) DEFAULT 'LEO_4.0_ADSETS_EXTRACTOR',

    -- PRIMARY KEY COMPUESTA
    PRIMARY KEY (adset_id, insights_date_start)
);

-- Índices para mejorar búsquedas
CREATE INDEX idx_adsets_date_range ON "Markeitng".adsets(insights_date_start, insights_date_stop);
CREATE INDEX idx_adsets_account ON "Markeitng".adsets(account_id);
CREATE INDEX idx_adsets_campaign ON "Markeitng".adsets(campaign_id);
CREATE INDEX idx_adsets_spend ON "Markeitng".adsets(spend DESC);

-- =====================================================================
-- TABLA: ADS (Ads + Insights)
-- PRIMARY KEY compuesta (ad_id, insights_date_start)
-- Permite múltiples insights diarios por ad
-- =====================================================================
CREATE TABLE "Markeitng".ads (
    -- PRIMARY KEY COMPUESTA
    ad_id VARCHAR(50) NOT NULL,
    insights_date_start DATE NOT NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Relaciones
    account_id VARCHAR(50) NOT NULL REFERENCES "Markeitng".accounts(account_id) ON DELETE CASCADE,
    account_name VARCHAR(255),
    adset_id VARCHAR(50) NOT NULL,
    campaign_id VARCHAR(50) NOT NULL,

    -- Información de ad
    ad_name TEXT,
    ad_status VARCHAR(50),
    configured_status VARCHAR(50),
    effective_status VARCHAR(50),

    -- Fechas de ad
    ad_created_time TIMESTAMP WITH TIME ZONE,
    ad_updated_time TIMESTAMP WITH TIME ZONE,

    -- Configuración
    bid_amount DECIMAL(12,2),
    last_updated_by_app_id VARCHAR(100),
    source_ad_id VARCHAR(50),
    demolink_hash VARCHAR(255),
    preview_shareable_link TEXT,

    -- Datos complejos (JSON)
    creative TEXT,
    tracking_specs TEXT,
    conversion_specs TEXT,
    recommendations TEXT,

    -- Período de insights
    insights_date_stop DATE,

    -- Métricas de rendimiento
    impressions BIGINT DEFAULT 0,
    clicks BIGINT DEFAULT 0,
    spend DECIMAL(12,2) DEFAULT 0.00,
    reach BIGINT DEFAULT 0,
    frequency DECIMAL(8,6) DEFAULT 0,

    -- Métricas de costos
    cpm DECIMAL(8,2) DEFAULT 0.00,
    cpc DECIMAL(8,2) DEFAULT 0.00,
    ctr DECIMAL(8,6) DEFAULT 0,

    -- Métricas de clics
    inline_link_clicks BIGINT DEFAULT 0,
    inline_link_click_ctr DECIMAL(8,6) DEFAULT 0,
    unique_clicks BIGINT DEFAULT 0,
    unique_ctr DECIMAL(8,6) DEFAULT 0,

    -- Métricas adicionales
    social_spend DECIMAL(12,2) DEFAULT 0.00,
    unique_inline_link_clicks BIGINT DEFAULT 0,
    unique_inline_link_click_ctr DECIMAL(8,6) DEFAULT 0,

    -- Metadatos
    extraction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data_source VARCHAR(50) DEFAULT 'LEO_4.0_ADS_EXTRACTOR',

    -- PRIMARY KEY COMPUESTA
    PRIMARY KEY (ad_id, insights_date_start)
);

-- Índices para mejorar búsquedas
CREATE INDEX idx_ads_date_range ON "Markeitng".ads(insights_date_start, insights_date_stop);
CREATE INDEX idx_ads_account ON "Markeitng".ads(account_id);
CREATE INDEX idx_ads_campaign ON "Markeitng".ads(campaign_id);
CREATE INDEX idx_ads_adset ON "Markeitng".ads(adset_id);
CREATE INDEX idx_ads_spend ON "Markeitng".ads(spend DESC);

-- =====================================================================
-- POLÍTICAS RLS (ROW LEVEL SECURITY)
-- =====================================================================

-- Habilitar RLS en todas las tablas
ALTER TABLE "Markeitng".accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Markeitng".campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Markeitng".adsets ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Markeitng".ads ENABLE ROW LEVEL SECURITY;

-- Política: permitir todo para service_role (bypass RLS)
CREATE POLICY "Allow service_role full access on accounts" ON "Markeitng".accounts
    FOR ALL USING (auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Allow service_role full access on campaigns" ON "Markeitng".campaigns
    FOR ALL USING (auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Allow service_role full access on adsets" ON "Markeitng".adsets
    FOR ALL USING (auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Allow service_role full access on ads" ON "Markeitng".ads
    FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- =====================================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================================

COMMENT ON SCHEMA "Markeitng" IS 'Esquema para datos de Marketing - AutoRepCuentas';

COMMENT ON TABLE "Markeitng".accounts IS 'Cuentas de Meta Ads registradas en el sistema';
COMMENT ON TABLE "Markeitng".campaigns IS 'Campañas de Meta Ads con insights diarios. PRIMARY KEY compuesta permite múltiples registros por campaña (uno por fecha).';
COMMENT ON TABLE "Markeitng".adsets IS 'Ad Sets de Meta Ads con insights diarios. PRIMARY KEY compuesta permite múltiples registros por adset (uno por fecha).';
COMMENT ON TABLE "Markeitng".ads IS 'Ads de Meta Ads con insights diarios. PRIMARY KEY compuesta permite múltiples registros por ad (uno por fecha).';

COMMENT ON COLUMN "Markeitng".campaigns.insights_date_start IS 'Fecha del insight (parte de PRIMARY KEY). Permite múltiples insights por campaña.';
COMMENT ON COLUMN "Markeitng".adsets.insights_date_start IS 'Fecha del insight (parte de PRIMARY KEY). Permite múltiples insights por adset.';
COMMENT ON COLUMN "Markeitng".ads.insights_date_start IS 'Fecha del insight (parte de PRIMARY KEY). Permite múltiples insights por ad.';

-- =====================================================================
-- FIN DEL SCRIPT
-- =====================================================================
-- Ejecutar este script en Supabase SQL Editor
-- Asegúrate de tener permisos de administrador
-- =====================================================================
