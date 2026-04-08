-- KisanMitra AI Platform - Database Schema
-- Version: 1.0
-- Matches TDD Section 2.1 exactly

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================
-- USERS & AUTH
-- =============================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(15) NOT NULL UNIQUE,
    name VARCHAR(100),
    language VARCHAR(5) DEFAULT 'hi',  -- hi, en, ta, te, mr
    state VARCHAR(50),
    district VARCHAR(100),
    pincode VARCHAR(6),
    category VARCHAR(20),  -- general, obc, sc, st
    gender VARCHAR(10),
    income_annual DECIMAL(12,2),
    land_acres DECIMAL(6,2),
    occupation VARCHAR(50),  -- farmer, msme_owner, student, etc.
    udyam_number VARCHAR(30),
    aadhaar_reference VARCHAR(50),  -- tokenized, NOT actual Aadhaar
    pan_reference VARCHAR(20),
    onboarded_at TIMESTAMP DEFAULT NOW(),
    last_active_at TIMESTAMP,
    subscription_tier VARCHAR(20) DEFAULT 'free',  -- free, basic, premium
    subscription_expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_state_district ON users(state, district);

CREATE TABLE user_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    product_code VARCHAR(30) NOT NULL,  -- kisanmitra, udyamsathi, vidyabot
    enrolled_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_user_products_user ON user_products(user_id);

-- =============================================
-- GOVERNMENT SCHEMES
-- =============================================

CREATE TABLE schemes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_code VARCHAR(50) UNIQUE NOT NULL,
    name_en VARCHAR(200) NOT NULL,
    name_hi VARCHAR(200),
    ministry VARCHAR(100),
    department VARCHAR(100),
    scheme_type VARCHAR(30),  -- central, state, both
    state VARCHAR(50),  -- NULL for central schemes
    sector VARCHAR(50),  -- agriculture, msme, education, health, dairy, etc.
    subsector VARCHAR(50),

    -- Eligibility criteria (JSONB for flexibility)
    eligibility_criteria JSONB NOT NULL DEFAULT '{}',

    -- Benefits
    benefit_type VARCHAR(30),  -- subsidy, loan, grant, training, dbt
    subsidy_percentage DECIMAL(5,2),
    max_subsidy_amount DECIMAL(12,2),
    loan_amount_max DECIMAL(12,2),
    interest_subsidy DECIMAL(5,2),

    -- Application
    application_url VARCHAR(500),
    documents_required JSONB DEFAULT '[]',
    application_process TEXT,

    -- Metadata
    description_en TEXT,
    description_hi TEXT,
    last_verified_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    source_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_schemes_sector ON schemes(sector);
CREATE INDEX idx_schemes_state ON schemes(state);
CREATE INDEX idx_schemes_active ON schemes(is_active);
CREATE INDEX idx_schemes_code ON schemes(scheme_code);
CREATE INDEX idx_schemes_eligibility ON schemes USING GIN (eligibility_criteria);

-- =============================================
-- SCHEME APPLICATIONS
-- =============================================

CREATE TABLE scheme_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    scheme_id UUID REFERENCES schemes(id) ON DELETE CASCADE,
    status VARCHAR(30) DEFAULT 'identified',  -- identified, documents_ready, applied, under_review, approved, rejected
    applied_at TIMESTAMP,
    documents_submitted JSONB DEFAULT '[]',
    notes TEXT,
    next_action TEXT,
    next_deadline TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_scheme_apps_user ON scheme_applications(user_id);
CREATE INDEX idx_scheme_apps_scheme ON scheme_applications(scheme_id);
CREATE INDEX idx_scheme_apps_status ON scheme_applications(status);

-- =============================================
-- MANDI PRICES
-- =============================================

CREATE TABLE mandi_prices (
    id BIGSERIAL PRIMARY KEY,
    commodity VARCHAR(50) NOT NULL,
    market VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    district VARCHAR(100),
    min_price DECIMAL(10,2),
    max_price DECIMAL(10,2),
    modal_price DECIMAL(10,2),
    arrival_tonnes DECIMAL(10,2),
    price_date DATE NOT NULL,
    scraped_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_mandi_commodity_market ON mandi_prices(commodity, market, price_date DESC);
CREATE INDEX idx_mandi_date ON mandi_prices(price_date);

-- =============================================
-- PRICE ALERTS
-- =============================================

CREATE TABLE price_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    commodity VARCHAR(50) NOT NULL,
    market VARCHAR(100) NOT NULL,
    alert_type VARCHAR(20),  -- price_above, price_below, daily_update, sell_signal
    threshold_price DECIMAL(10,2),
    is_active BOOLEAN DEFAULT true,
    last_triggered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_price_alerts_user ON price_alerts(user_id);
CREATE INDEX idx_price_alerts_active ON price_alerts(is_active);

-- =============================================
-- LOAN TRACKING
-- =============================================

CREATE TABLE loan_inquiries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    loan_type VARCHAR(30),  -- mudra_shishu, mudra_kishor, mudra_tarun, kcc, nabard_deds, pmegp
    amount_requested DECIMAL(12,2),
    eligible BOOLEAN,
    eligibility_details JSONB,
    emi_calculated DECIMAL(10,2),
    bank_recommended VARCHAR(100),
    status VARCHAR(20) DEFAULT 'inquiry',  -- inquiry, applied, approved, rejected, disbursed
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_loan_user ON loan_inquiries(user_id);

-- =============================================
-- MSME DISPUTES (Payment Recovery)
-- =============================================

CREATE TABLE disputes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    buyer_name VARCHAR(200),
    buyer_gstin VARCHAR(20),
    invoice_number VARCHAR(50),
    invoice_date DATE,
    invoice_amount DECIMAL(12,2),
    due_date DATE,
    days_overdue INTEGER,
    interest_amount DECIMAL(12,2),
    total_claim DECIMAL(12,2),
    legal_notice_generated BOOLEAN DEFAULT false,
    legal_notice_sent_at TIMESTAMP,
    odr_case_filed BOOLEAN DEFAULT false,
    odr_case_id VARCHAR(50),
    status VARCHAR(30) DEFAULT 'new',  -- new, notice_sent, waiting_response, odr_filed, resolved, escalated
    resolution_amount DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_disputes_user ON disputes(user_id);
CREATE INDEX idx_disputes_status ON disputes(status);

-- =============================================
-- CONVERSATIONS & AGENT LOGS
-- =============================================

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    product_code VARCHAR(30),
    channel VARCHAR(20) DEFAULT 'whatsapp',  -- whatsapp, sms, web
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    agents_used VARCHAR[] DEFAULT '{}',
    satisfaction_score INTEGER  -- 1-5 if user rates
);

CREATE INDEX idx_conversations_user ON conversations(user_id);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(10) NOT NULL,  -- user, agent, system
    content TEXT NOT NULL,
    content_type VARCHAR(20) DEFAULT 'text',  -- text, voice, image, document
    language VARCHAR(5) DEFAULT 'hi',
    agent_name VARCHAR(30),  -- scheme_agent, mandi_agent, etc.
    tools_used VARCHAR[] DEFAULT '{}',
    llm_model VARCHAR(50),
    tokens_used INTEGER,
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);

-- =============================================
-- NOTIFICATIONS & ALERTS
-- =============================================

CREATE TABLE scheduled_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    notification_type VARCHAR(30),  -- price_alert, deadline_reminder, scheme_update, status_change
    channel VARCHAR(20) DEFAULT 'whatsapp',
    message_template TEXT NOT NULL,
    message_params JSONB DEFAULT '{}',
    scheduled_at TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, sent, failed, cancelled
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_scheduled ON scheduled_notifications(scheduled_at, status);

-- =============================================
-- DPR (DETAILED PROJECT REPORTS)
-- =============================================

CREATE TABLE project_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    business_type VARCHAR(50),  -- dairy_farm, cattle_feed, food_processing, goat_farming
    project_name VARCHAR(200),
    total_cost DECIMAL(12,2),
    subsidy_amount DECIMAL(12,2),
    own_contribution DECIMAL(12,2),
    loan_amount DECIMAL(12,2),
    expected_revenue_year1 DECIMAL(12,2),
    breakeven_months INTEGER,
    report_data JSONB,  -- full DPR data
    pdf_storage_key VARCHAR(200),  -- S3/MinIO key
    generated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_reports_user ON project_reports(user_id);

-- =============================================
-- AUTO-UPDATE TRIGGER
-- =============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_schemes_updated BEFORE UPDATE ON schemes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_scheme_apps_updated BEFORE UPDATE ON scheme_applications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_disputes_updated BEFORE UPDATE ON disputes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_notifications_updated BEFORE UPDATE ON scheduled_notifications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
