-- backend/migrations/013_epr_country_rules.sql
-- Purpose: Per-country EPR rules with thresholds, deadlines, registration links
-- NOT for: Actual EPR report data (that's epr_reports table)

CREATE TABLE IF NOT EXISTS epr_country_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_code TEXT NOT NULL,
    country_name TEXT NOT NULL,
    category TEXT NOT NULL,         -- packaging, weee, batteries
    registration_required BOOLEAN NOT NULL DEFAULT TRUE,
    authority_name TEXT,            -- Name of registration body
    authority_url TEXT,             -- Link to registration portal
    threshold_description TEXT,     -- Human-readable threshold
    threshold_units INTEGER,        -- Minimum units/year (NULL = always required)
    threshold_revenue_eur INTEGER,  -- Minimum revenue EUR/year (NULL = no threshold)
    deadline TEXT,                  -- Next compliance deadline
    penalty_description TEXT,       -- What happens if non-compliant
    notes TEXT,                     -- Extra info
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_epr_country_code ON epr_country_rules(country_code);
CREATE UNIQUE INDEX IF NOT EXISTS idx_epr_country_category ON epr_country_rules(country_code, category);

-- ── Seed data: 7 EU countries × 3 categories ────────────────────────────────
-- Source: Public EPR regulations as of 2024-2025

-- GERMANY (DE)
INSERT INTO epr_country_rules (country_code, country_name, category, registration_required, authority_name, authority_url, threshold_description, threshold_units, threshold_revenue_eur, deadline, penalty_description, notes)
VALUES
('DE', 'Niemcy', 'packaging', TRUE, 'LUCID / Zentrale Stelle', 'https://lucid.verpackungsregister.org/', 'Każdy sprzedawca wprowadzający opakowania na rynek DE', NULL, NULL, 'Obowiązuje od 2019', 'Zakaz sprzedaży + kary do 200 000 EUR', 'Dual system: Grüner Punkt, Interseroh, BellandVision, Reclay. Raportowanie roczne + obowiązek licencji.'),
('DE', 'Niemcy', 'weee', TRUE, 'stiftung EAR', 'https://www.stiftung-ear.de/', 'Każdy producent/importer sprzętu elektrycznego', NULL, NULL, 'Obowiązuje od 2005', 'Zakaz sprzedaży + kary do 100 000 EUR', 'ElektroG. Rejestracja przez stiftung EAR. Koszty zależą od kategorii i masy.'),
('DE', 'Niemcy', 'batteries', TRUE, 'UBA / BattG Melderegister', 'https://www.umweltbundesamt.de/themen/abfall-ressourcen/produktverantwortung-in-der-abfallwirtschaft/batterien', 'Każdy producent/importer baterii', NULL, NULL, 'Obowiązuje od 2009', 'Zakaz sprzedaży + kary do 100 000 EUR', 'BattG. Rejestracja + umowa z systemem zbiórki (GRS, REBAT).'),

-- FRANCE (FR)
('FR', 'Francja', 'packaging', TRUE, 'CITEO', 'https://www.citeo.com/', 'Każdy sprzedawca z obrotem > 1 mln EUR/rok lub > 10 000 jednostek', 10000, 1000000, 'Obowiązuje od 1994', 'Kary do 200 000 EUR + zakaz sprzedaży', 'Triman logo obowiązkowe. Raportowanie roczne do CITEO. Obowiązek Info-tri od 2022.'),
('FR', 'Francja', 'weee', TRUE, 'Ecosystem / Ecologic', 'https://www.ecosystem.eco/', 'Każdy producent/importer sprzętu elektrycznego', NULL, NULL, 'Obowiązuje od 2006', 'Kary do 750 000 EUR', 'DEEE. Unique identifier number (UIN) wymagany. Obowiązkowe oznaczenie crossed-out bin.'),
('FR', 'Francja', 'batteries', TRUE, 'Corepile / Screlec', 'https://www.corepile.fr/', 'Każdy producent/importer baterii', NULL, NULL, 'Obowiązuje od 2001', 'Kary do 450 000 EUR', 'Obowiązek eco-contribution per kg baterii.'),

-- SPAIN (ES)
('ES', 'Hiszpania', 'packaging', TRUE, 'Ecoembes', 'https://www.ecoembes.com/', 'Każdy sprzedawca wprowadzający opakowania na rynek ES', NULL, NULL, 'Obowiązuje od 2022 (Real Decreto 1055/2022)', 'Kary do 1 750 000 EUR', 'Rejestracja w Registro de Productores. Nowe obowiązki od 2025: etykietowanie opakowań.'),
('ES', 'Hiszpania', 'weee', TRUE, 'Registro Integrado Industrial (RII)', 'https://industria.gob.es/', 'Każdy producent/importer sprzętu elektrycznego', NULL, NULL, 'Obowiązuje od 2015', 'Kary do 1 750 000 EUR', 'Real Decreto 110/2015. Rejestracja w RII + system zbiórki.'),
('ES', 'Hiszpania', 'batteries', TRUE, 'Ecopilas / ERP', 'https://www.ecopilas.es/', 'Każdy producent/importer baterii', NULL, NULL, 'Obowiązuje od 2010', 'Kary do 1 750 000 EUR', 'Rejestracja + umowa z PRO (Producer Responsibility Organisation).'),

-- ITALY (IT)
('IT', 'Włochy', 'packaging', TRUE, 'CONAI', 'https://www.conai.org/', 'Każdy sprzedawca wprowadzający opakowania na rynek IT', NULL, NULL, 'Obowiązuje od 1997', 'Kary do 25 000 EUR + zakaz sprzedaży', 'CONAI environmental contribution. Obowiązkowe etykietowanie opakowań od 2023 (Decreto 116/2020).'),
('IT', 'Włochy', 'weee', TRUE, 'Registro AEE', 'https://www.registroaee.it/', 'Każdy producent/importer sprzętu elektrycznego', NULL, NULL, 'Obowiązuje od 2014', 'Kary do 100 000 EUR', 'D.Lgs 49/2014. Rejestracja w Registro AEE obowiązkowa.'),
('IT', 'Włochy', 'batteries', TRUE, 'CDCNPA', 'https://www.cdcnpa.it/', 'Każdy producent/importer baterii', NULL, NULL, 'Obowiązuje od 2008', 'Kary do 100 000 EUR', 'D.Lgs 188/2008. Rejestracja + contribution do systemu zbiórki.'),

-- SWEDEN (SE)
('SE', 'Szwecja', 'packaging', TRUE, 'Naturvårdsverket / FTI', 'https://www.fti.se/', 'Każdy sprzedawca wprowadzający opakowania na rynek SE', NULL, NULL, 'Obowiązuje od 2024 (nowe wymogi)', 'Kary do 500 000 SEK (~45 000 EUR)', 'Nowa ordinance 2022:1274. Od 2024 producent odpowiada za zbiórkę opakowań.'),
('SE', 'Szwecja', 'weee', TRUE, 'Naturvårdsverket / El-Kretsen', 'https://www.el-kretsen.se/', 'Każdy producent/importer sprzętu elektrycznego', NULL, NULL, 'Obowiązuje od 2005', 'Kary do 1 000 000 SEK (~90 000 EUR)', 'SFS 2014:1075. Rejestracja w Naturvårdsverket.'),
('SE', 'Szwecja', 'batteries', TRUE, 'Naturvårdsverket / Batteriåtervinning', 'https://www.batteriatervinning.se/', 'Każdy producent/importer baterii', NULL, NULL, 'Obowiązuje od 2008', 'Kary do 500 000 SEK (~45 000 EUR)', 'SFS 2008:834. Obowiązek zbiórki + raportowanie.'),

-- NETHERLANDS (NL)
('NL', 'Holandia', 'packaging', TRUE, 'Afvalfonds Verpakkingen', 'https://afvalfondsverpakkingen.nl/', 'Każdy sprzedawca z obrotem > 50 000 EUR', NULL, 50000, 'Obowiązuje od 2006', 'Kary + zakaz sprzedaży', 'Decreto Verpakkingen. Raportowanie roczne + waste management contribution.'),
('NL', 'Holandia', 'weee', TRUE, 'Nationaal WEEE Register', 'https://www.nationaalweeeregister.nl/', 'Każdy producent/importer sprzętu elektrycznego', NULL, NULL, 'Obowiązuje od 2014', 'Kary do 450 000 EUR', 'Regeling afgedankte elektrische en elektronische apparatuur.'),
('NL', 'Holandia', 'batteries', TRUE, 'Stibat', 'https://www.stibat.nl/', 'Każdy producent/importer baterii', NULL, NULL, 'Obowiązuje od 2008', 'Kary do 450 000 EUR', 'Regeling beheer batterijen. Obowiązek zbiórki.'),

-- POLAND (PL)
('PL', 'Polska', 'packaging', TRUE, 'BDO (Baza Danych o Odpadach)', 'https://bdo.mos.gov.pl/', 'Każdy sprzedawca wprowadzający opakowania na rynek PL', NULL, NULL, 'Obowiązuje od 2020', 'Kary do 1 000 000 PLN (~230 000 EUR)', 'Rejestracja w BDO obowiązkowa. Raportowanie roczne + opłata produktowa.'),
('PL', 'Polska', 'weee', TRUE, 'GIOŚ + BDO', 'https://bdo.mos.gov.pl/', 'Każdy producent/importer sprzętu elektrycznego', NULL, NULL, 'Obowiązuje od 2016', 'Kary do 1 000 000 PLN (~230 000 EUR)', 'Ustawa o zużytym sprzęcie elektrycznym. Rejestracja w BDO.'),
('PL', 'Polska', 'batteries', TRUE, 'GIOŚ + BDO', 'https://bdo.mos.gov.pl/', 'Każdy producent/importer baterii', NULL, NULL, 'Obowiązuje od 2009', 'Kary do 500 000 PLN (~115 000 EUR)', 'Ustawa o bateriach i akumulatorach. Rejestracja w BDO + opłata depozytowa.')

ON CONFLICT (country_code, category) DO NOTHING;
