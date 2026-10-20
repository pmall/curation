-- The structure of Drakkar, written by tests/build_fixture.py: never edit it.

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';

CREATE FUNCTION public.constrain_taxon() RETURNS integer
    LANGUAGE sql STRICT SECURITY DEFINER
    AS $$
CREATE RULE rule_taxon_i
       AS ON INSERT TO taxon
       WHERE (
             SELECT taxon_id FROM taxon 
             WHERE ncbi_taxon_id = new.ncbi_taxon_id
             )
       	     IS NOT NULL
       DO INSTEAD NOTHING
;
SELECT 1;
$$;

CREATE FUNCTION public.unconstrain_taxon() RETURNS integer
    LANGUAGE sql STRICT SECURITY DEFINER
    AS $$
DROP RULE rule_taxon_i ON taxon;
SELECT 1;
$$;

CREATE TABLE public.associations (
    id integer NOT NULL,
    run_id integer NOT NULL,
    pmid bigint NOT NULL,
    state character varying(10) DEFAULT 'pending'::character varying NOT NULL,
    annotation text DEFAULT ''::text NOT NULL,
    updated_at timestamp(0) without time zone DEFAULT now() NOT NULL,
    ai_pass_at timestamp without time zone,
    CONSTRAINT associations_state_check CHECK (((state)::text = ANY (ARRAY[('pending'::character varying)::text, ('selected'::character varying)::text, ('discarded'::character varying)::text, ('curated'::character varying)::text])))
);

CREATE SEQUENCE public.associations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.associations_id_seq OWNED BY public.associations.id;

CREATE TABLE public.descriptions (
    id integer NOT NULL,
    stable_id character(10) NOT NULL,
    version smallint NOT NULL,
    association_id integer NOT NULL,
    method_id integer NOT NULL,
    protein1_id integer NOT NULL,
    name1 character varying(32) NOT NULL,
    start1 integer NOT NULL,
    stop1 integer NOT NULL,
    mapping1 json NOT NULL,
    protein2_id integer NOT NULL,
    name2 character varying(32) NOT NULL,
    start2 integer NOT NULL,
    stop2 integer NOT NULL,
    mapping2 json NOT NULL,
    created_at timestamp(0) without time zone DEFAULT now() NOT NULL,
    deleted_at timestamp(0) without time zone,
    annotation text DEFAULT ''::text NOT NULL
);

CREATE TABLE public.methods (
    id integer NOT NULL,
    psimi_id character varying(7) NOT NULL,
    name character varying(255) NOT NULL,
    search text
);

CREATE TABLE public.proteins (
    id integer NOT NULL,
    type character(1) NOT NULL,
    ncbi_taxon_id integer NOT NULL,
    accession character varying(10) NOT NULL,
    name character varying(255) NOT NULL,
    description text NOT NULL,
    version character(7) NOT NULL,
    sequences jsonb NOT NULL,
    CONSTRAINT proteins_type_check CHECK (((type)::text = ANY (ARRAY[('h'::character varying)::text, ('v'::character varying)::text])))
);

CREATE TABLE public.proteins_versions (
    accession character varying(10) NOT NULL,
    version character(7) NOT NULL,
    current_version character(7) NOT NULL,
    names character varying[] NOT NULL,
    features jsonb NOT NULL,
    search text
);

CREATE TABLE public.runs (
    id integer NOT NULL,
    type character(2) NOT NULL,
    name text NOT NULL,
    populated boolean DEFAULT false NOT NULL,
    created_at timestamp(0) without time zone DEFAULT now() NOT NULL,
    info text DEFAULT ''::text NOT NULL,
    CONSTRAINT runs_type_check CHECK (((type)::text = ANY (ARRAY[('hh'::character varying)::text, ('vh'::character varying)::text])))
);

CREATE SEQUENCE public.taxon_pk_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE public.taxon (
    taxon_id integer DEFAULT nextval('public.taxon_pk_seq'::regclass) NOT NULL,
    ncbi_taxon_id integer,
    parent_taxon_id integer,
    node_rank character varying(32),
    genetic_code smallint,
    mito_genetic_code smallint,
    left_value integer,
    right_value integer
);

CREATE TABLE public.taxon_name (
    taxon_id integer NOT NULL,
    name character varying(255) NOT NULL,
    name_class character varying(32) NOT NULL
);

CREATE MATERIALIZED VIEW public.dataset AS
 SELECT d.stable_id,
    r.type,
    r.id AS run_id,
    r.name AS run,
    a.id AS association_id,
    a.state,
    a.annotation,
    d.id AS description_id,
    a.pmid,
    m.id AS method_id,
    m.psimi_id,
    m.name AS method,
    p1.id AS protein1_id,
    p1.type AS type1,
    p1.accession AS accession1,
    p1.name AS name1,
    d.start1,
    d.stop1,
    p1.description AS description1,
    p1.ncbi_taxon_id AS ncbi_taxon_id1,
    (COALESCE(tn1.name, 'Obsolete'::character varying))::text AS taxon1,
    t1.left_value AS left_value1,
    t1.right_value AS right_value1,
    d.mapping1,
    p1.version AS original_version1,
    v1.current_version AS current_version1,
    (v1.current_version IS NULL) AS is_obsolete1,
    p2.id AS protein2_id,
    p2.type AS type2,
    p2.accession AS accession2,
    d.name2,
    d.start2,
    d.stop2,
    p2.description AS description2,
    p2.ncbi_taxon_id AS ncbi_taxon_id2,
    COALESCE(tn2.name, 'Obsolete'::character varying) AS taxon2,
    t2.left_value AS left_value2,
    t2.right_value AS right_value2,
    d.mapping2,
    p2.version AS original_version2,
    v2.current_version AS current_version2,
    (v2.current_version IS NULL) AS is_obsolete2,
    d.created_at,
    d.deleted_at
   FROM (((((((((((public.descriptions d
     JOIN public.associations a ON ((a.id = d.association_id)))
     JOIN public.runs r ON ((r.id = a.run_id)))
     JOIN public.methods m ON ((m.id = d.method_id)))
     JOIN public.proteins p1 ON ((p1.id = d.protein1_id)))
     LEFT JOIN public.proteins_versions v1 ON ((((v1.accession)::text = (p1.accession)::text) AND (v1.version = p1.version))))
     LEFT JOIN public.taxon t1 ON ((t1.ncbi_taxon_id = p1.ncbi_taxon_id)))
     LEFT JOIN public.taxon_name tn1 ON (((tn1.taxon_id = t1.taxon_id) AND ((tn1.name_class)::text = 'scientific name'::text))))
     JOIN public.proteins p2 ON ((p2.id = d.protein2_id)))
     LEFT JOIN public.proteins_versions v2 ON ((((v2.accession)::text = (p2.accession)::text) AND (v2.version = p2.version))))
     LEFT JOIN public.taxon t2 ON ((t2.ncbi_taxon_id = p2.ncbi_taxon_id)))
     LEFT JOIN public.taxon_name tn2 ON (((tn2.taxon_id = t2.taxon_id) AND ((tn2.name_class)::text = 'scientific name'::text))))
  WITH NO DATA;

CREATE SEQUENCE public.descriptions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.descriptions_id_seq OWNED BY public.descriptions.id;

CREATE TABLE public.keywords (
    id integer NOT NULL,
    type character(1) NOT NULL,
    pattern character varying(255) NOT NULL
);

CREATE SEQUENCE public.keywords_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.keywords_id_seq OWNED BY public.keywords.id;

CREATE SEQUENCE public.methods_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.methods_id_seq OWNED BY public.methods.id;

CREATE SEQUENCE public.proteins_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.proteins_id_seq OWNED BY public.proteins.id;

CREATE TABLE public.publications (
    pmid bigint NOT NULL,
    populated boolean DEFAULT false,
    metadata jsonb
);

CREATE SEQUENCE public.runs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.runs_id_seq OWNED BY public.runs.id;

ALTER TABLE ONLY public.associations ALTER COLUMN id SET DEFAULT nextval('public.associations_id_seq'::regclass);

ALTER TABLE ONLY public.descriptions ALTER COLUMN id SET DEFAULT nextval('public.descriptions_id_seq'::regclass);

ALTER TABLE ONLY public.keywords ALTER COLUMN id SET DEFAULT nextval('public.keywords_id_seq'::regclass);

ALTER TABLE ONLY public.methods ALTER COLUMN id SET DEFAULT nextval('public.methods_id_seq'::regclass);

ALTER TABLE ONLY public.proteins ALTER COLUMN id SET DEFAULT nextval('public.proteins_id_seq'::regclass);

ALTER TABLE ONLY public.runs ALTER COLUMN id SET DEFAULT nextval('public.runs_id_seq'::regclass);

ALTER TABLE ONLY public.associations
    ADD CONSTRAINT associations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.associations
    ADD CONSTRAINT associations_run_id_pmid_key UNIQUE (run_id, pmid);

ALTER TABLE ONLY public.descriptions
    ADD CONSTRAINT descriptions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.descriptions
    ADD CONSTRAINT descriptions_stable_id_version_id_key UNIQUE (stable_id, version);

ALTER TABLE ONLY public.keywords
    ADD CONSTRAINT keywords_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.methods
    ADD CONSTRAINT methods_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.methods
    ADD CONSTRAINT methods_psimi_id_key UNIQUE (psimi_id);

ALTER TABLE ONLY public.proteins
    ADD CONSTRAINT proteins_accession_version_key UNIQUE (accession, version);

ALTER TABLE ONLY public.proteins
    ADD CONSTRAINT proteins_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.proteins_versions
    ADD CONSTRAINT proteins_versions_accession_current_version_key UNIQUE (accession, current_version);

ALTER TABLE ONLY public.proteins_versions
    ADD CONSTRAINT proteins_versions_pkey PRIMARY KEY (accession, version);

ALTER TABLE ONLY public.publications
    ADD CONSTRAINT publications_pkey PRIMARY KEY (pmid);

ALTER TABLE ONLY public.runs
    ADD CONSTRAINT runs_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.taxon_name
    ADD CONSTRAINT taxon_name_name_name_class_taxon_id_key UNIQUE (name, name_class, taxon_id);

ALTER TABLE ONLY public.taxon
    ADD CONSTRAINT taxon_pkey PRIMARY KEY (taxon_id);

ALTER TABLE ONLY public.taxon
    ADD CONSTRAINT xaktaxon_left_value UNIQUE (left_value);

ALTER TABLE ONLY public.taxon
    ADD CONSTRAINT xaktaxon_ncbi_taxon_id UNIQUE (ncbi_taxon_id);

ALTER TABLE ONLY public.taxon
    ADD CONSTRAINT xaktaxon_right_value UNIQUE (right_value);

CREATE INDEX dataset_accession1_idx ON public.dataset USING btree (accession1);

CREATE INDEX dataset_accession2_idx ON public.dataset USING btree (accession2);

CREATE UNIQUE INDEX dataset_description_id_key ON public.dataset USING btree (description_id);

CREATE INDEX dataset_pmid_idx ON public.dataset USING btree (pmid);

CREATE INDEX dataset_stable_id_idx ON public.dataset USING btree (stable_id);

CREATE INDEX descriptions_association_id_key ON public.descriptions USING btree (association_id);

CREATE INDEX descriptions_method_id_key ON public.descriptions USING btree (method_id);

CREATE INDEX descriptions_protein1_id_key ON public.descriptions USING btree (protein1_id);

CREATE INDEX descriptions_protein2_id_key ON public.descriptions USING btree (protein2_id);

CREATE INDEX methods_search_key ON public.methods USING gin (search public.gin_trgm_ops);

CREATE INDEX proteins_ncbi_taxon_id_key ON public.proteins USING btree (ncbi_taxon_id);

CREATE INDEX proteins_versions_search_key ON public.proteins_versions USING gin (search public.gin_trgm_ops);

CREATE INDEX taxnamename ON public.taxon_name USING btree (name);

CREATE INDEX taxnametaxonid ON public.taxon_name USING btree (taxon_id);

CREATE INDEX taxparent ON public.taxon USING btree (parent_taxon_id);

CREATE RULE rule_taxon_i AS
    ON INSERT TO public.taxon
   WHERE (( SELECT taxon.taxon_id
           FROM public.taxon
          WHERE (taxon.ncbi_taxon_id = new.ncbi_taxon_id)) IS NOT NULL) DO INSTEAD NOTHING;

CREATE RULE rule_taxon_name_i AS
    ON INSERT TO public.taxon_name
   WHERE (( SELECT taxon_name.taxon_id
           FROM public.taxon_name
          WHERE ((taxon_name.taxon_id = new.taxon_id) AND ((taxon_name.name)::text = (new.name)::text) AND ((taxon_name.name_class)::text = (new.name_class)::text))) IS NOT NULL) DO INSTEAD NOTHING;

ALTER TABLE ONLY public.associations
    ADD CONSTRAINT associations_pmid_fkey FOREIGN KEY (pmid) REFERENCES public.publications(pmid);

ALTER TABLE ONLY public.associations
    ADD CONSTRAINT associations_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.runs(id);

ALTER TABLE ONLY public.descriptions
    ADD CONSTRAINT descriptions_association_id_fkey FOREIGN KEY (association_id) REFERENCES public.associations(id);

ALTER TABLE ONLY public.descriptions
    ADD CONSTRAINT descriptions_method_id_fkey FOREIGN KEY (method_id) REFERENCES public.methods(id);

ALTER TABLE ONLY public.descriptions
    ADD CONSTRAINT descriptions_protein1_id_fkey FOREIGN KEY (protein1_id) REFERENCES public.proteins(id);

ALTER TABLE ONLY public.descriptions
    ADD CONSTRAINT descriptions_protein2_id_fkey FOREIGN KEY (protein2_id) REFERENCES public.proteins(id);

ALTER TABLE ONLY public.taxon_name
    ADD CONSTRAINT fktaxon_taxonname FOREIGN KEY (taxon_id) REFERENCES public.taxon(taxon_id) ON DELETE CASCADE;

ALTER TABLE ONLY public.proteins_versions
    ADD CONSTRAINT proteins_versions_accession_version_fkey FOREIGN KEY (accession, version) REFERENCES public.proteins(accession, version);
