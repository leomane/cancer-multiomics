# Cancer Multi-Omics Analytics Pipeline

**From Silicon to Cytoplasm** — Tracing the flow of biological information from DNA through clinical outcomes, using multiple molecular measurement types to identify where cellular regulation breaks down in cancer.

A learning-focused portfolio project that integrates genomic, transcriptomic, proteomic, and clinical data from [TCGA](https://www.cancer.gov/ccg/research/genome-sequencing/tcga) and [CPTAC](https://proteomics.cancer.gov/programs/cptac) public datasets on Google Cloud Platform.

**Author:** Tony Leo — Technical PM and data scientist with 14 years in tech, transitioning into biomedicine.
**Portfolio:** [tonyleo.bio](https://tonyleo.bio)

---

## Why Multi-Omics?

Cancer is not a single-layer problem. A tumor's behavior emerges from the interplay of its mutated DNA, the genes it transcribes, the proteins it builds, and whether those proteins are switched on or off. No single measurement captures the full picture — but by integrating multiple molecular layers, we can trace *where* the signal breaks down.

This pipeline follows the **central dogma of molecular biology**, extended through post-translational modification to clinical outcome, and maps each public dataset to the biological layer it measures:

```mermaid
flowchart TD
    subgraph GENOME["DNA — The Instruction Set"]
        DNA["Somatic mutations alter\nthe genomic blueprint"]
    end

    subgraph TRANSCRIPTOME["RNA — The Readout"]
        RNA["mRNA expression determines\nwhat the cell builds & how much"]
    end

    subgraph PROTEOME["Protein — The Machinery"]
        PROT["Proteins carry out\ncellular functions"]
    end

    subgraph PHOSPHOPROTEOME["Activated Protein — The Switch"]
        PHOSPHO["Post-translational modifications\ntoggle protein activity ON/OFF"]
    end

    subgraph BEHAVIOR["Cellular Behavior"]
        CELL["Proliferation, apoptosis,\nmigration, metabolism"]
    end

    subgraph CLINICAL["Clinical Outcome"]
        OUTCOME["Survival, recurrence,\ntreatment response, staging"]
    end

    DNA -->|"Transcription"| RNA
    RNA -->|"Translation"| PROT
    PROT -->|"Post-translational\nModification"| PHOSPHO
    PHOSPHO -->|"Signaling\nCascades"| CELL
    CELL -->|"Disease\nProgression"| OUTCOME

    TCGA_MUT["TCGA Somatic\nMutations"]:::dataset -.->|measures| DNA
    TCGA_RNA["TCGA RNA-seq\n~20K genes"]:::dataset -.->|measures| RNA
    CPTAC_PROT["CPTAC Mass Spec\nProteomics"]:::dataset -.->|measures| PROT
    CPTAC_PHOSPHO["CPTAC Phospho-\nproteomics & PTMs"]:::dataset -.->|measures| PHOSPHO
    CLIN_DATA["TCGA / CPTAC\nClinical Data"]:::dataset -.->|measures| OUTCOME

    DNA ~~~ DECOUPLE1["Mutation may be\npassenger, not driver"]:::warning
    RNA ~~~ DECOUPLE2["Protein may be\nrapidly degraded"]:::warning
    PROT ~~~ DECOUPLE3["Protein may never\nbe phosphorylated"]:::warning

    classDef dataset fill:#4A90D9,stroke:#2C5F8A,color:#fff,font-size:12px
    classDef warning fill:#F5A623,stroke:#D4891A,color:#000,font-size:11px
```

### The Biological Layers

| Layer | What It Is | What It Tells Us | Dataset |
|-------|-----------|------------------|---------|
| **Genome** | DNA — the instruction set | Somatic mutations show where cancer has rewritten the code | TCGA somatic mutation data |
| **Transcriptome** | RNA — the readout | mRNA expression reveals what the cell is *trying* to build, and how much (~20,000 protein-coding genes plus non-coding RNA) | TCGA RNA-seq (TPM/FPKM) |
| **Proteome** | Protein — the machinery | Protein abundance shows what actually got built — but doesn't always match RNA levels due to post-transcriptional regulation, translation rates, and degradation | CPTAC mass spectrometry proteomics |
| **Phosphoproteome** | Activated protein — the switch | Post-translational modifications (especially phosphorylation) toggle proteins ON/OFF. The same protein at the same abundance can be functionally active or inactive depending on its modification state. This is where signaling cascades operate. | CPTAC phosphoproteomics (also acetylomics, ubiquitylomics, glycoproteomics in select cohorts) |
| **Clinical** | What happened to the patient | Survival, recurrence, treatment response, staging | TCGA/CPTAC clinical data |

### The Key Insight

**Regulation can decouple at any transition.** A gene can be mutated but the RNA still expressed normally (passenger mutation, not driver). RNA can be overexpressed but the protein rapidly degraded (post-transcriptional regulation). Protein can be abundant but never phosphorylated (inactive). Multi-omics integration lets you trace *where* the signal breaks down — which is far more powerful than any single measurement type alone.

---

## Data Integration Architecture

The pipeline joins two major public cancer datasets that were designed to complement each other:

```mermaid
flowchart LR
    subgraph TCGA["TCGA — The Cancer Genome Atlas\n~11,000 patients · 33 cancer types"]
        T_MUT["Somatic Mutations"]
        T_RNA["RNA-seq Expression"]
        T_CLIN["Clinical & Survival"]
        T_MUT --- T_RNA --- T_CLIN
    end

    subgraph CPTAC2["CPTAC-2 Prospective Studies\nSame TCGA tumor samples"]
        C2_BRCA["Breast Cancer\n~115 patients"]
        C2_COAD["Colon Cancer\n~105 patients"]
        C2_OV["Ovarian Cancer\n~71 patients"]
    end

    subgraph CPTAC3["CPTAC-3 Discovery Studies\nIndependent cohorts with own genomics"]
        C3_KIRC["Kidney\n257 patients"]
        C3_UCEC["Uterine\n241 patients"]
        C3_LUAD["Lung\n230 patients"]
        C3_GBM["Brain\n211 patients"]
    end

    subgraph MODALITIES["Proteomic Modalities per Cohort"]
        MOD_PROT["Global Proteome"]
        MOD_PHOSPHO["Phosphoproteome"]
        MOD_ACETYL["Acetylome"]
        MOD_UBIQ["Ubiquitylome"]
        MOD_GLYCO["Glycoproteome"]
    end

    TCGA ==>|"Shared patient IDs\nsame tumor samples"| CPTAC2
    CPTAC2 --> MODALITIES
    CPTAC3 --> MODALITIES

    subgraph BQ["BigQuery · isb-cgc-bq"]
        BQ_NODE["All data accessed via\nGCP public datasets"]
    end

    TCGA --> BQ
    CPTAC2 --> BQ
    CPTAC3 --> BQ
```

### How the Data Connects

- **TCGA** provides the genomic and clinical foundation: somatic mutations, RNA-seq expression, and clinical/survival data across ~11,000 patients and 33 cancer types.
- **CPTAC** adds the proteomic dimension — what's actually being built and activated at the protein level.
- **CPTAC-2 "prospective" studies** were performed on actual TCGA tumor samples (breast, colon, ovarian). These share patient identifiers with TCGA, enabling true same-patient multi-omics integration across all molecular layers.
- **CPTAC-3 "discovery" studies** are independent cohorts (kidney, uterine, lung, brain) with their own genomic and proteomic data.
- **All data** is accessed via BigQuery public datasets in the `isb-cgc-bq` project — no downloads, no local storage, no egress fees.

---

## Pipeline Architecture

The project is structured in phases, building from exploratory analysis toward a production-grade ML pipeline:

```mermaid
flowchart TD
    subgraph P0["Phase 0 — EDA & Problem Discovery  ← CURRENT"]
        P0A["BigQuery notebooks exploring\nTCGA/CPTAC coverage"]
        P0B["Mutation burden &\nexpression patterns"]
        P0C["Coverage matrix across cancer\ntypes & molecular modalities"]
        P0A --> P0B --> P0C
    end

    subgraph P05["Phase 0.5 — Targeted Literature Review"]
        P05A["8-12 papers grounding\nanalytical question"]
        P05B["Existing research on\nmulti-omics integration"]
        P05A --> P05B
    end

    subgraph P1["Phase 1 — Infrastructure-as-Code"]
        P1A["Terraform: BigQuery datasets"]
        P1B["Terraform: Cloud Storage buckets"]
        P1C["Terraform: Pub/Sub topics"]
        P1D["Terraform: IAM roles"]
        P1A --> P1B --> P1C --> P1D
    end

    subgraph P2["Phase 2 — Data Modeling"]
        P2A["dbt staging models"]
        P2B["dbt intermediate models"]
        P2C["dbt mart models"]
        P2D["Tests & documentation"]
        P2A --> P2B --> P2C --> P2D
    end

    subgraph P3["Phase 3 — Streaming Pipelines"]
        P3A["Pub/Sub ingestion\nof bioRxiv preprints"]
        P3B["NLP enrichment\nvia Cloud Functions"]
        P3C["Landing in BigQuery"]
        P3A --> P3B --> P3C
    end

    subgraph P4["Phase 4 — ML Deployment"]
        P4A["Vertex AI model training\non multi-omics features"]
        P4B["Endpoint serving"]
        P4C["Batch predictions\nback to BigQuery"]
        P4A --> P4B --> P4C
    end

    P0 --> P05 --> P1 --> P2 --> P3 --> P4
```

### Phase Details

| Phase | Focus | Key Deliverables |
|-------|-------|-----------------|
| **0** | EDA & Problem Discovery | BigQuery notebooks exploring TCGA/CPTAC coverage, mutation burden distributions, expression patterns. Building the coverage matrix across cancer types and molecular modalities to understand what questions the data can answer. |
| **0.5** | Targeted Literature Review | 8-12 papers grounding the analytical question in existing multi-omics research. Establishing what's known, what's novel, and where this pipeline can contribute. |
| **1** | Infrastructure-as-Code | Terraform provisioning of BigQuery datasets, Cloud Storage buckets, Pub/Sub topics, and IAM roles. Reproducible, version-controlled infrastructure. |
| **2** | Data Modeling | dbt models transforming raw public data through staging, intermediate, and mart layers. Full test coverage and documentation. Clean, documented, queryable analytical tables. |
| **3** | Streaming Pipelines | Pub/Sub + Cloud Functions ingesting bioRxiv preprints, NLP enrichment for gene/pathway extraction, landing enriched records in BigQuery. Keeping the knowledge base current. |
| **4** | ML Deployment | Vertex AI model training on multi-omics features, endpoint serving for real-time inference, batch predictions written back to BigQuery. |

---

## Project Structure

```
cancer-multiomics/
├── README.md
├── CLAUDE.md                          # AI assistant context & conventions
│
├── notebooks/                         # Phase 0: EDA & exploration
│   └── *.ipynb                        # BigQuery exploration notebooks
│
├── literature/                        # Phase 0.5: Research grounding
│   └── references.md                  # Annotated bibliography
│
├── terraform/                         # Phase 1: Infrastructure-as-Code
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules/
│       ├── bigquery/
│       ├── storage/
│       ├── pubsub/
│       └── iam/
│
├── dbt/                               # Phase 2: Data modeling
│   ├── dbt_project.yml
│   └── models/
│       ├── staging/                   # Raw → clean
│       ├── intermediate/              # Cross-source joins
│       └── marts/                     # Analytical tables
│
├── functions/                         # Phase 3: Cloud Functions
│   ├── biorxiv_ingestion/
│   └── nlp_enrichment/
│
├── ml/                                # Phase 4: ML pipelines
│   ├── training/
│   ├── serving/
│   └── evaluation/
│
└── docs/                              # Architecture decisions & diagrams
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Compute & Storage** | Google BigQuery | Zero-infrastructure analytics on petabyte-scale public datasets. TCGA and CPTAC are already hosted here via ISB-CGC. |
| **Infrastructure** | Terraform | Reproducible, version-controlled GCP resource provisioning. |
| **Data Modeling** | dbt (BigQuery adapter) | SQL-based transformations with built-in testing, documentation, and lineage. |
| **Streaming** | Cloud Pub/Sub + Cloud Functions | Serverless event-driven ingestion. Pay only when preprints arrive. |
| **ML** | Vertex AI | Managed training and serving, native BigQuery integration. |
| **Notebooks** | Jupyter / Colab | Interactive EDA with direct BigQuery access. |
| **Version Control** | Git + GitHub | Standard collaboration and CI/CD foundation. |

### Budget Strategy: $20-50/month

This project is designed to run on a graduate-student budget by leveraging GCP's generous free tiers:

- **BigQuery**: 1 TB/month free queries, 10 GB/month free storage. Public dataset queries (TCGA/CPTAC via `isb-cgc-bq`) don't count against the query quota when accessed in the same region.
- **Cloud Functions**: 2 million invocations/month free.
- **Cloud Storage**: 5 GB free standard storage.
- **Pub/Sub**: 10 GB/month free messaging.
- **Vertex AI**: Training costs managed through small instance types and spot instances.

---

## Data Sources

All data is accessed through BigQuery public datasets — no downloads, no local copies, no data management overhead.

| Source | Project | Content | Scale |
|--------|---------|---------|-------|
| [TCGA](https://www.cancer.gov/ccg/research/genome-sequencing/tcga) | `isb-cgc-bq` | Somatic mutations, RNA-seq, clinical data | ~11,000 patients, 33 cancer types |
| [CPTAC](https://proteomics.cancer.gov/programs/cptac) | `isb-cgc-bq` | Proteomics, phosphoproteomics, acetylomics, ubiquitylomics, glycoproteomics | ~1,200+ patients across 10 cancer types |
| [ISB-CGC](https://isb-cgc.appspot.com/) | `isb-cgc-bq` | Curated BigQuery tables for cancer genomics cloud computing | Unified access layer |

---

## Getting Started

### Prerequisites

- Google Cloud Platform account with billing enabled
- `gcloud` CLI installed and authenticated
- Python 3.10+
- Terraform 1.5+
- dbt-core with BigQuery adapter

### Quick Start

```bash
# Clone the repository
git clone https://github.com/tonyleo/cancer-multiomics.git
cd cancer-multiomics

# Authenticate with GCP
gcloud auth application-default login

# Query TCGA data directly (no setup required)
bq query --use_legacy_sql=false \
  'SELECT project_short_name, COUNT(*) as n_patients
   FROM `isb-cgc-bq.TCGA.clinical_gdc_current`
   GROUP BY 1
   ORDER BY 2 DESC
   LIMIT 10'
```

---

## Current Status

**Phase 0 — EDA & Problem Discovery** (active)

Building the foundational understanding of what data exists, how it connects across TCGA and CPTAC, and which cancer types have sufficient multi-omics coverage to support integrated analysis. This phase is deliberately exploratory — the goal is to let the data guide the analytical question rather than forcing a hypothesis onto incomplete coverage.

---

## License

This project uses publicly available data from TCGA and CPTAC. These datasets are open access and available for research use. See individual dataset documentation for specific terms.

---

<sub>Built by [Tony Leo](https://tonyleo.bio) as part of a career transition from technology into biomedicine.</sub>
