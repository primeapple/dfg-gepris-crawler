------------------------------------
-------- Scrapy Schema -------------
------------------------------------

CREATE TYPE SPIDER_TYPE AS ENUM ('search_results', 'details');
CREATE TYPE CONTEXT_TYPE AS ENUM ('projekt', 'person', 'institution');

CREATE SEQUENCE spider_runs_id;

CREATE TABLE spider_runs
(
id INTEGER PRIMARY KEY DEFAULT nextval('spider_runs_id'),
spider SPIDER_TYPE NOT NULL,
context CONTEXT_TYPE NOT NULL,
run_started_at TIMESTAMP WITH TIME ZONE NOT NULL,
run_ended_at TIMESTAMP WITH TIME ZONE,
total_scraped_items INTEGER,
UNIQUE (spider, context, run_started_at)
);

CREATE TABLE available_items
(
id INTEGER,
context CONTEXT_TYPE,
last_available_seen INTEGER REFERENCES spider_runs(id),
last_available_change INTEGER REFERENCES spider_runs(id),
last_available_item JSONB,
last_detail_check INTEGER REFERENCES spider_runs(id),
detail_check_needed BOOLEAN NOT NULL,
PRIMARY KEY (id, context)
);

CREATE TYPE DETAIL_STATUS_TYPE AS ENUM ('success', 'error', 'moved');
CREATE TABLE details_items_history
(
id INTEGER,
context CONTEXT_TYPE,
created_at INTEGER REFERENCES spider_runs(id),
item JSONB,
status DETAIL_STATUS_TYPE NOT NULL,
PRIMARY KEY (id, context, created_at),
FOREIGN KEY (id, context) REFERENCES available_items (id, context),
CHECK ((status = 'success' AND item IS NOT NULL) OR (status != 'success' AND item IS NULL))
);

-- this gives the latest item for each id/context from details
CREATE VIEW latest_detail_items AS
SELECT DISTINCT ON (h.id, h.context) h.id, h.context, h.created_at, h.item, h.status
FROM details_items_history h JOIN spider_runs r ON (h.created_at = r.id)
ORDER BY h.id, h.context, r.run_started_at DESC;

-- this gives the latest item for each id/context from details
-- if there was an error in the latest item of details, the we try to set it to the latest available item
-- if there also is no available item, then we set it to an empty json
CREATE VIEW latest_items AS
SELECT i.id, i.context,
    CASE
        WHEN i.status = 'success' THEN i.item
        WHEN i.status = 'error' AND a.last_available_item IS NOT NULL THEN a.last_available_item
        WHEN i.status = 'error' THEN '{}'::JSONB
    END AS item
FROM latest_detail_items i JOIN available_items a ON (i.id = a.id AND i.context = a.context)
WHERE i.status != 'moved';

CREATE TYPE PERSON_PROJEKT_BEZIEHUNG_TYPE AS ENUM (
    'antragsteller_personen',
    'auslaendische_antragsteller_personen',
    'ehemalige_antragsteller_personen',
    'mit_antragsteller_personen',
    'sprecher_personen',
    'auslaendische_sprecher_personen',
    'co_sprecher_personen',
    'leiter_personen',
    'stellvertreter_personen',
    'teilprojekt_leiter_personen',
    'gastgeber_personen',
    'kooperationspartner_personen',
    'beteiligte_personen',
    'beteiligte_wissenschaftler_personen',
    'mit_verantwortliche_personen',
    'igk_personen',
    'stellvertreter_sprecher_personen'
);

CREATE TYPE INSTITUTION_PROJEKT_BEZIEHUNG_TYPE AS ENUM (
    'antragstellende_institutionen',
    'mit_antragstellende_institutionen',
    'beteiligte_institutionen',
    'beteiligte_einrichtungen_institutionen',
    'beteiligte_hochschule_institutionen',
    'partner_institutionen',
    'partner_organisation_institutionen',
    'unternehmen_institutionen',
    'auslaendische_institutionen',
    'igk_institutionen'
);

CREATE VIEW latest_person_projekt_references AS
SELECT jsonb_array_elements_text(item->'attributes'->attr_name::TEXT)::INT AS person_id,
id AS projekt_id,
attr_name::PERSON_PROJEKT_BEZIEHUNG_TYPE AS reference_type
FROM latest_detail_items JOIN
(SELECT UNNEST(enum_range(NULL::PERSON_PROJEKT_BEZIEHUNG_TYPE))::TEXT AS attr_name) attrs
ON (jsonb_exists(item->'attributes', attr_name))
WHERE context='projekt';

CREATE VIEW latest_institution_projekt_references AS
SELECT jsonb_array_elements_text(item->'attributes'->attr_name::TEXT)::INT AS institution_id,
id AS projekt_id,
attr_name::INSTITUTION_PROJEKT_BEZIEHUNG_TYPE AS reference_type
FROM latest_detail_items l JOIN
(SELECT UNNEST(enum_range(NULL::INSTITUTION_PROJEKT_BEZIEHUNG_TYPE))::TEXT AS attr_name) attrs
ON (jsonb_exists(l.item->'attributes', attrs.attr_name))
WHERE context='projekt';

CREATE VIEW institution_hierarchy AS
    WITH RECURSIVE institutionen_abhaengigkeiten AS (
        -- the base query
        SELECT id,
            NULL::INT AS parent_id,
            id AS root_id,
            item->'trees'->'normalised_subinstitutions' AS children
        FROM latest_items
        WHERE context = 'institution'
            AND item->'trees'->'normalised_subinstitutions' IS NOT NULL
        UNION
        -- the recursive query
        SELECT CASE
                WHEN jsonb_typeof(arr_children)='string' THEN (arr_children #>> '{}')::INT
                WHEN jsonb_typeof(arr_children)='object' THEN (SELECT jsonb_object_keys(arr_children))::INT
            END AS id,
            id AS parent_id,
            root_id,
            CASE
                WHEN jsonb_typeof(arr_children)='string' THEN NULL::JSONB
                WHEN jsonb_typeof(arr_children)='object' THEN (arr_children -> (SELECT jsonb_object_keys(arr_children)))
            END AS children
        FROM institutionen_abhaengigkeiten CROSS JOIN jsonb_array_elements(children) arr_children
    )
    SELECT id, parent_id, root_id FROM institutionen_abhaengigkeiten;

CREATE TABLE data_monitor
(
run_ended_at TIMESTAMP WITH TIME ZONE PRIMARY KEY,
last_update DATE NOT NULL,
last_approval DATE NOT NULL,
finished_project_count INTEGER NOT NULL,
project_count INTEGER NOT NULL,
person_count INTEGER NOT NULL,
institution_count INTEGER NOT NULL,
humanities_count INTEGER NOT NULL,
life_count INTEGER NOT NULL,
natural_count INTEGER NOT NULL,
engineering_count INTEGER NOT NULL,
infrastructure_count INTEGER,
research_infrastructure_count INTEGER,
gepris_version TEXT NOT NULL,
current_index_version TEXT NOT NULL,
current_index_date TIMESTAMP WITH TIME ZONE NOT NULL
);


------------------------------------
-------- actual Gepris Schema ------
------------------------------------

CREATE TYPE PERSON_GENDER_TYPE AS ENUM ('male', 'female', 'unknown');

-- TODO: create materialized views for this
CREATE TABLE personen (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  adresse TEXT,
  mail TEXT,
  internet TEXT,
  telefax TEXT,
  telefon TEXT,
  orcid_id TEXT,
  verstorben BOOLEAN,
  gender PERSON_GENDER_TYPE
);

CREATE TABLE institutionen (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  adresse TEXT,
  mail TEXT,
  internet TEXT,
  telefax TEXT,
  telefon TEXT,
  uebergeordnete_institution INTEGER REFERENCES institutionen(id)
);

CREATE TABLE projekte (
  id INTEGER PRIMARY KEY,
  name_de TEXT,
  name_en TEXT,
  beschreibung_de TEXT,
  beschreibung_en TEXT,
  dfg_ansprechpartner TEXT,
  internationaler_bezug TEXT[],
  gross_geraete TEXT[],
  geraetegruppe TEXT[],
  dfg_verfahren TEXT,
  fachrichtungen TEXT[],
  fachliche_zuordnungen TEXT,
  webseite TEXT,
  foerderung_beginn INTEGER,
  foerderung_ende INTEGER,
  -- ergebnis information
  ergebnis_publikationen JSONB,
  ergebnis_zusammenfassung_de TEXT,
  ergebnis_zusammenfassung_en TEXT,
  ergebnis_erstellungsjahr INTEGER,
  -- foreign keys
  teil_projekt_zu INTEGER REFERENCES projekte(id)
);

CREATE TABLE institutionen_projekte (
    institution_id INTEGER REFERENCES institutionen(id),
    projekt_id INTEGER REFERENCES projekte(id),
    beziehung INSTITUTION_PROJEKT_BEZIEHUNG_TYPE,
    PRIMARY KEY (institution_id, projekt_id, beziehung)
);

CREATE TABLE personen_projekte (
    person_id INTEGER REFERENCES personen(id),
    projekt_id INTEGER REFERENCES projekte(id),
    beziehung PERSON_PROJEKT_BEZIEHUNG_TYPE,
    PRIMARY KEY (person_id, projekt_id, beziehung)
);

CREATE FUNCTION create_personen_from_items() RETURNS VOID LANGUAGE PLPGSQL AS $$
    BEGIN
        INSERT INTO personen (id, name, adresse, mail, internet, telefax, telefon, orcid_id, verstorben, gender)
            SELECT id,
                item->>'name_de',
                item->'attributes'->>'adresse',
                item->'attributes'->>'mail',
                item->'attributes'->>'internet',
                item->'attributes'->>'telefax',
                item->'attributes'->>'telefon',
                item->'attributes'->>'orcid_id',
                (item->>'verstorben')::BOOLEAN,
                (item->>'gender')::PERSON_GENDER_TYPE
            FROM latest_items
            WHERE context = 'person';
    END $$;

CREATE FUNCTION create_institutionen_from_items() RETURNS VOID LANGUAGE PLPGSQL AS $$
    BEGIN
        INSERT INTO institutionen (id, name, adresse, mail, internet, telefax, telefon)
            SELECT id,
                item->>'name_de',
                item->'attributes'->>'adresse',
                item->'attributes'->>'mail',
                item->'attributes'->>'internet',
                item->'attributes'->>'telefax',
                item->'attributes'->>'telefon'
            FROM latest_items
            WHERE context = 'institution';
        -- This recursive monstrosity creates a table with ids and it's parent ids that is used to create the
        -- "uebergeordnete_institution" of an institution
        WITH RECURSIVE institutionen_abhaengigkeiten AS (
            -- the base query
            SELECT NULL::INT AS parent_id,
                id,
                item->'trees'->'normalised_subinstitutions' AS children
            FROM latest_items
            WHERE context = 'institution'
                AND item->'trees'->'normalised_subinstitutions' IS NOT NULL
            UNION
            -- the recursive query
            SELECT id AS parent_id,
                CASE
                    WHEN jsonb_typeof(arr_children)='string' THEN (arr_children #>> '{}')::INT
                    WHEN jsonb_typeof(arr_children)='object' THEN (SELECT jsonb_object_keys(arr_children))::INT
                END AS id,
                CASE
                    WHEN jsonb_typeof(arr_children)='string' THEN NULL::JSONB
                    WHEN jsonb_typeof(arr_children)='object' THEN (arr_children -> (SELECT jsonb_object_keys(arr_children)))
                END AS children
            FROM institutionen_abhaengigkeiten CROSS JOIN jsonb_array_elements(children) arr_children
        )
        UPDATE institutionen
            SET uebergeordnete_institution = i.parent_id
            FROM institutionen_abhaengigkeiten i
            WHERE institutionen.id = i.id
                AND i.parent_id IS NOT NULL;
    END $$;

CREATE FUNCTION create_projekte_from_items() RETURNS VOID LANGUAGE PLPGSQL AS $$
    BEGIN
        INSERT INTO projekte (
            id,
            name_de,
            name_en,
            beschreibung_de,
            beschreibung_en,
            dfg_ansprechpartner,
            internationaler_bezug,
            gross_geraete,
            geraetegruppe,
            dfg_verfahren,
            fachrichtungen,
            fachliche_zuordnungen,
            webseite,
            foerderung_beginn,
            foerderung_ende,
            -- ergebnis information
            ergebnis_publikationen,
            ergebnis_zusammenfassung_de,
            ergebnis_zusammenfassung_en,
            ergebnis_erstellungsjahr,
            -- foreign keys
            teil_projekt_zu)
            SELECT id,
                item->>'name_de',
                item->>'name_en',
                item->>'beschreibung_de',
                item->>'beschreibung_en',
                item->'attributes'->>'dfg_ansprechpartner',
                ARRAY(SELECT jsonb_array_elements_text(item->'attributes'->'internationaler_bezug')),
                ARRAY(SELECT jsonb_array_elements_text(item->'attributes'->'gross_geraete')),
                ARRAY(SELECT jsonb_array_elements_text(item->'attributes'->'geraetegruppe')),
                item->'attributes'->>'dfg_verfahren',
                ARRAY(SELECT jsonb_array_elements_text(item->'attributes'->'fachrichtungen')),
                item->'attributes'->>'fachliche_zuordnungen',
                item->'attributes'->>'webseite',
                (item->'attributes'->>'foerderung_beginn')::INT,
                (item->'attributes'->>'foerderung_ende')::INT,
                item->'result'->'ergebnis_publikationen',
                item->'result'->>'ergebnis_zusammenfassung_de',
                item->'result'->>'ergebnis_zusammenfassung_en',
                (item->'result'->'attributes'->>'ergebnis_erstellungsjahr')::INT,
                (item->'attributes'->>'teil_projekt')::INT
            FROM latest_items
            WHERE context = 'projekt';
    END $$;

CREATE FUNCTION create_institutionen_projekte_references() RETURNS VOID LANGUAGE PLPGSQL AS $$
    DECLARE
        attribute text;
    BEGIN
        FOR attribute IN SELECT unnest(enum_range(NULL::INSTITUTION_PROJEKT_BEZIEHUNG_TYPE)) LOOP
            INSERT INTO institutionen_projekte (institution_id, projekt_id, beziehung)
                SELECT jsonb_array_elements_text(item->'attributes'->attribute::TEXT)::INT AS institution_id,
            	    id AS projekt_id,
            	    attribute::INSTITUTION_PROJEKT_BEZIEHUNG_TYPE AS beziehung
                FROM latest_detail_items
                WHERE context='projekt';
        END LOOP;
    END $$;

CREATE FUNCTION create_personen_projekte_references() RETURNS VOID LANGUAGE PLPGSQL AS $$
    DECLARE
        attribute text;
    BEGIN
        FOR attribute IN SELECT unnest(enum_range(NULL::PERSON_PROJEKT_BEZIEHUNG_TYPE)) LOOP
            INSERT INTO personen_projekte (person_id, projekt_id, beziehung)
                SELECT jsonb_array_elements_text(item->'attributes'->attribute::TEXT)::INT AS person_id,
            	    id AS projekt_id,
            	    attribute::PERSON_PROJEKT_BEZIEHUNG_TYPE AS beziehung
                FROM latest_detail_items
                WHERE context='projekt';
        END LOOP;
    END $$;

CREATE FUNCTION update_personen_gender_from_references(male_or_female PERSON_GENDER_TYPE) RETURNS VOID LANGUAGE PLPGSQL AS $$
    BEGIN
        WITH projekt_referenced_gender AS (
            SELECT DISTINCT jsonb_array_elements_text(item->'attributes'->(concat(male_or_female::TEXT, '_personen')))::INT AS id
            FROM latest_detail_items
            WHERE context='projekt'
        )
        UPDATE personen SET gender = male_or_female
        WHERE id IN (SELECT * FROM projekt_referenced_gender);
    END $$;

CREATE FUNCTION handle_projekte_references() RETURNS VOID LANGUAGE PLPGSQL AS $$
    BEGIN
        PERFORM create_institutionen_projekte_references();
        PERFORM create_personen_projekte_references();
        PERFORM update_personen_gender_from_references('male'::PERSON_GENDER_TYPE);
        PERFORM update_personen_gender_from_references('female'::PERSON_GENDER_TYPE);
    END $$;
