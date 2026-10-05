-- dataset: one row per description (live or deleted), joining runs, associations, methods,
-- proteins (with their current version) and taxa. For consultation and exports only.
--
-- Same columns, order and types as the original view, with these changes (2026-10-05):
-- - taxon1, left_value1 and right_value1 come from the taxonomy instead of hard-coded values;
-- - a protein whose taxon is missing from `taxon` no longer hides its descriptions
--   (left/right values are NULL and the taxon name is 'Obsolete', as for missing names);
-- - indexes, including a unique one on description_id for REFRESH ... CONCURRENTLY.

BEGIN;

DROP MATERIALIZED VIEW dataset;

CREATE MATERIALIZED VIEW dataset AS
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
       COALESCE(tn1.name, 'Obsolete')::text AS taxon1,
       t1.left_value AS left_value1,
       t1.right_value AS right_value1,
       d.mapping1,
       p1.version AS original_version1,
       v1.current_version AS current_version1,
       v1.current_version IS NULL AS is_obsolete1,
       p2.id AS protein2_id,
       p2.type AS type2,
       p2.accession AS accession2,
       d.name2,
       d.start2,
       d.stop2,
       p2.description AS description2,
       p2.ncbi_taxon_id AS ncbi_taxon_id2,
       COALESCE(tn2.name, 'Obsolete') AS taxon2,
       t2.left_value AS left_value2,
       t2.right_value AS right_value2,
       d.mapping2,
       p2.version AS original_version2,
       v2.current_version AS current_version2,
       v2.current_version IS NULL AS is_obsolete2,
       d.created_at,
       d.deleted_at
FROM descriptions AS d
JOIN associations AS a ON a.id = d.association_id
JOIN runs AS r ON r.id = a.run_id
JOIN methods AS m ON m.id = d.method_id
JOIN proteins AS p1 ON p1.id = d.protein1_id
LEFT JOIN proteins_versions AS v1 ON v1.accession = p1.accession AND v1.version = p1.version
LEFT JOIN taxon AS t1 ON t1.ncbi_taxon_id = p1.ncbi_taxon_id
LEFT JOIN taxon_name AS tn1 ON tn1.taxon_id = t1.taxon_id AND tn1.name_class = 'scientific name'
JOIN proteins AS p2 ON p2.id = d.protein2_id
LEFT JOIN proteins_versions AS v2 ON v2.accession = p2.accession AND v2.version = p2.version
LEFT JOIN taxon AS t2 ON t2.ncbi_taxon_id = p2.ncbi_taxon_id
LEFT JOIN taxon_name AS tn2 ON tn2.taxon_id = t2.taxon_id AND tn2.name_class = 'scientific name';

CREATE UNIQUE INDEX dataset_description_id_key ON dataset (description_id);
CREATE INDEX dataset_stable_id_idx ON dataset (stable_id);
CREATE INDEX dataset_pmid_idx ON dataset (pmid);
CREATE INDEX dataset_accession1_idx ON dataset (accession1);
CREATE INDEX dataset_accession2_idx ON dataset (accession2);

COMMIT;
