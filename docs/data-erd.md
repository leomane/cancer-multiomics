# Data Entity-Relationship Documentation

Living document tracking the relationships, join keys, and rules discovered across the TCGA and CPTAC datasets in BigQuery (`isb-cgc-bq`).

Last updated: 2026-03-06

---

## Identifier Systems

Two identifier formats coexist across all tables. Understanding which system each table uses is the single most important thing for writing correct joins.

| Format | Example | Origin | Used by |
|--------|---------|--------|---------|
| **TCGA barcode** | `TCGA-A2-A0T2` | Submitting project (TCGA/CPTAC) | ISB-CGC curated tables, clinical `submitter_id` |
| **GDC UUID** | `1f5e3f10-7f14-4b3a-...` | Genomic Data Commons | GDC-native tables, CPTAC proteomics `case_id` |

**Rule:** You cannot join a UUID to a barcode directly. Use a clinical table as a bridge (it has both).

---

## TCGA Barcode Hierarchy

TCGA barcodes encode a hierarchy. Each level adds characters:

```
TCGA-A2-A0T2        (case_barcode    = patient)
TCGA-A2-A0T2-01A    (sample_barcode  = tumor/normal sample from that patient)
TCGA-A2-A0T2-01A-11 (aliquot_barcode = physical portion sent to a lab)
```

- One patient can have multiple samples (e.g., primary tumor + metastasis + matched normal)
- One sample can have multiple aliquots (sent to different labs/platforms)
- Most analyses aggregate at the **case (patient) level**, but sample type matters (tumor vs. normal)

---

## Master ERD: Cross-Dataset Relationships

```mermaid
erDiagram
    TCGA_CLINICAL["TCGA.clinical_gdc_current"] {
        string submitter_id PK "TCGA barcode (e.g., TCGA-A2-A0T2)"
        string case_id UK "GDC UUID"
        string proj__project_id "e.g., TCGA-BRCA"
        string primary_site
        string disease_type
    }

    TCGA_MUTATIONS["TCGA.masked_somatic_mutation_hg38_gdc_current"] {
        string case_barcode FK "TCGA barcode"
        string project_short_name "e.g., TCGA-BRCA"
        string Hugo_Symbol "Gene name"
        string Variant_Classification
        string sample_barcode_tumor
        string sample_barcode_normal
    }

    TCGA_RNASEQ["TCGA.RNAseq_hg38_gdc_current"] {
        string case_barcode FK "TCGA barcode"
        string sample_barcode
        string aliquot_barcode
        string project_short_name
        string gene_name
        string gene_type
        float tpm_unstranded
        float fpkm_unstranded
    }

    CPTAC_CLINICAL["CPTAC.clinical_gdc_current"] {
        string case_id PK "GDC UUID"
        string submitter_id UK "Barcode (TCGA-XX-XXXX or C3L-XXXXX)"
        string proj__project_id "CPTAC-2 or CPTAC-3"
        string primary_site
        string disease_type
    }

    CPTAC_PROTEOME["CPTAC.quant_proteome_*"] {
        string case_id FK "GDC UUID"
        string sample_id
        string aliquot_id
        string aliquot_submitter_id
        string gene_symbol
        float protein_abundance_log2ratio
        string study_name
    }

    CPTAC_PHOSPHO["CPTAC.quant_phosphoproteome_*"] {
        string case_id FK "GDC UUID"
        string sample_id
        string aliquot_id
        string aliquot_submitter_id
        string gene_symbol
        float protein_abundance_log2ratio
        string study_name
    }

    CPTAC_RNASEQ["CPTAC.RNAseq_hg38_gdc_current"] {
        string case_barcode FK "Barcode"
        string sample_barcode
        string project_short_name
        string gene_name
        float tpm_unstranded
    }

    CPTAC_MUTATIONS["CPTAC.masked_somatic_mutation_hg38_gdc_current"] {
        string case_barcode FK "Barcode"
        string project_short_name
        string Hugo_Symbol
        string Variant_Classification
    }

    %% TCGA internal joins (barcode to barcode -- direct)
    TCGA_CLINICAL ||--o{ TCGA_MUTATIONS : "submitter_id = case_barcode"
    TCGA_CLINICAL ||--o{ TCGA_RNASEQ : "submitter_id = case_barcode"

    %% CPTAC internal joins (UUID to UUID -- direct)
    CPTAC_CLINICAL ||--o{ CPTAC_PROTEOME : "case_id = case_id"
    CPTAC_CLINICAL ||--o{ CPTAC_PHOSPHO : "case_id = case_id"

    %% CPTAC clinical bridges UUID proteomics to barcode genomics
    CPTAC_CLINICAL ||--o{ CPTAC_RNASEQ : "submitter_id = case_barcode"
    CPTAC_CLINICAL ||--o{ CPTAC_MUTATIONS : "submitter_id = case_barcode"

    %% Cross-dataset join (Strategy 1: CPTAC-2 prospective patients exist in TCGA)
    TCGA_CLINICAL ||--o| CPTAC_CLINICAL : "submitter_id = submitter_id (CPTAC-2 only)"
```

---

## Join Rules

### Rule 1: Same identifier system -- join directly
When both tables use the same format, join directly:
```sql
-- Both use barcodes
SELECT *
FROM TCGA.RNAseq_hg38_gdc_current r
JOIN TCGA.masked_somatic_mutation_hg38_gdc_current m
  ON r.case_barcode = m.case_barcode
```

### Rule 2: Different identifier systems -- bridge through clinical
When joining UUID tables to barcode tables, use clinical as a crosswalk:
```sql
-- Proteomics (UUID) to RNA-seq (barcode) via CPTAC clinical bridge
SELECT *
FROM CPTAC.quant_proteome_* p
JOIN CPTAC.clinical_gdc_current cc ON p.case_id = cc.case_id
JOIN CPTAC.RNAseq_hg38_gdc_current r ON cc.submitter_id = r.case_barcode
```

### Rule 3: Cross-dataset joins (TCGA <-> CPTAC) -- only CPTAC-2
CPTAC-2 prospective studies used the **same tumor samples** as TCGA. Their patients appear in both clinical tables with matching `submitter_id` barcodes. CPTAC-3 patients are independent and do NOT overlap with TCGA.
```sql
-- Cross-dataset: TCGA genomics + CPTAC-2 proteomics for same patient
SELECT *
FROM CPTAC.clinical_gdc_current cptac_cc
JOIN TCGA.clinical_gdc_current tcga_cc
  ON cptac_cc.submitter_id = tcga_cc.submitter_id
WHERE cptac_cc.proj__project_id = 'CPTAC-2'
```

---

## Column Name Mapping

The same concept has different column names depending on the table's origin:

| Concept | GDC-native tables | ISB-CGC curated tables | CPTAC proteomics (PDC) |
|---------|-------------------|------------------------|------------------------|
| Patient barcode | `submitter_id` | `case_barcode` | `aliquot_submitter_id` (partial) |
| Patient UUID | `case_id` | not present | `case_id` |
| Cancer type | `proj__project_id` | `project_short_name` | `study_name` |
| Gene | n/a | `Hugo_Symbol` / `gene_name` | `gene_symbol` |

---

## Cancer Type Naming Inconsistencies

TCGA and CPTAC use different abbreviations for the same cancers:

| Cancer | TCGA code | CPTAC code | Notes |
|--------|-----------|------------|-------|
| Lung squamous | LUSC | LSCC | |
| Head and neck | HNSC | HNSCC | |
| Kidney clear cell | KIRC | CCRCC | |
| Pancreatic | PAAD | PDA | |
| Uterine | UCEC | UCEC | Same |
| Lung adeno | LUAD | LUAD | Same |
| Glioblastoma | GBM | GBM | Same |

---

## Table Structure Patterns

### Sparse vs. Dense Tables

| Table type | Pattern | Rows per patient | Example |
|------------|---------|-----------------|---------|
| Mutations | Sparse | ~10 to ~1,200 (varies by cancer) | Only mutated genes get rows |
| RNA-seq | Dense | ~60,000-70,000 | Every annotated gene gets a row |
| Proteomics | Dense | ~10,000-12,000 | Every detected protein gets a row |
| Clinical | One row | 1 | One row per patient |

### CPTAC Table Naming Convention
```
quant_{molecular_type}_{study_design}_{cancer}_{lab}_{instrument?}_{source}_current
```
- **molecular_type:** proteome, phosphoproteome, acetylome, ubiquitylome, glycoproteome
- **study_design:** prospective (CPTAC-2), discovery (CPTAC-3), confirmatory (validation)
- **source:** pdc (Proteomic Data Commons)

---

## Integration Strategies Summary

```mermaid
flowchart LR
    subgraph S1["Strategy 1: CPTAC-2 Prospective"]
        direction TB
        S1a["TCGA mutations\n(case_barcode)"]
        S1b["TCGA RNA-seq\n(case_barcode)"]
        S1c["CPTAC-2 proteomics\n(case_id UUID)"]
        S1d["TCGA clinical\n(submitter_id)"]
        S1e["CPTAC clinical\n(case_id + submitter_id)"]

        S1d --- S1a
        S1d --- S1b
        S1e --- S1c
        S1d -.-|"submitter_id\n= submitter_id"| S1e
    end

    subgraph S2["Strategy 2: CPTAC-3 Self-Contained"]
        direction TB
        S2a["CPTAC mutations\n(case_barcode)"]
        S2b["CPTAC RNA-seq\n(case_barcode)"]
        S2c["CPTAC-3 proteomics\n(case_id UUID)"]
        S2d["CPTAC clinical\n(case_id + submitter_id)"]

        S2d --- S2c
        S2d -.-|"submitter_id\n= case_barcode"| S2a
        S2d -.-|"submitter_id\n= case_barcode"| S2b
    end

    style S1 fill:#e8f4f8,stroke:#2196F3
    style S2 fill:#f3e8f4,stroke:#9C27B0
```

- **Strategy 1** joins across TCGA + CPTAC for ~115-291 patients (breast/colon/ovarian). Same physical tumor samples. Most rigorous.
- **Strategy 2** stays within CPTAC for 100-257 patients per cancer type. Self-contained. More cancer types available.
- **Both strategies require the clinical table as a bridge** between UUID and barcode identifiers.
