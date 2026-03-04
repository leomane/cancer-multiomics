# Roadmap

Living progress tracker for the Cancer Multi-Omics Analytics Pipeline. Updated as work progresses.

**Last updated:** 2026-03-03

---

## Phase 0 — EDA & Problem Discovery `IN PROGRESS`

Explore TCGA and CPTAC public datasets to understand data shape, coverage, and join-ability. Let the data guide the analytical question.

### Data Exploration
- [x] GCP project created, BigQuery access configured
- [x] Public datasets starred: `isb-cgc-bq`, `bigquery-public-data`, `open-targets-prod`
- [x] TCGA clinical data explored — patient counts across 33 cancer types
- [x] TCGA mutation data explored — mutation burden patterns across cancer types
- [x] TCGA RNA-seq explored — schema, expression metrics, barcode hierarchy
- [x] CPTAC clinical data explored — CPTAC-2 (342 patients) vs CPTAC-3 (1,683 patients)
- [x] CPTAC full table inventory cataloged (81 tables)
- [x] CPTAC genomic tables confirmed (RNAseq, mutations, copy number exist within CPTAC)
- [x] Two integration strategies identified (CPTAC-2 same-patient vs CPTAC-3 self-contained)

### Dev Workflow
- [x] Local ↔ BQ Studio notebook sync (bidirectional via Dataform API)
- [x] Compatibility shim for running BQ Studio notebooks locally

### Remaining
- [ ] Verify join keys between CPTAC-2 prospective tables and TCGA
- [ ] Build coverage matrix — which cancer types have patients across clinical + mutations + RNA-seq + proteomics + phosphoproteomics
- [ ] Select 2–3 cancer types with richest multi-omics coverage
- [ ] Add Plotly visualizations to EDA notebook (mutation burden, coverage heatmap, gene type distribution)
- [ ] Define specific analytical question based on data availability
- [ ] Write Phase 0 summary and cancer type justification

**Decision gate:** Which cancer type(s), what analytical question, which tables, and a high-level target data model.

---

## Phase 0.5 — Targeted Literature Review `NOT STARTED`

Ground the analytical question in existing multi-omics research.

- [ ] Identify 8–12 papers in chosen cancer type / multi-omics integration space
- [ ] Document what's been done, what can be reproduced/extended, and field terminology
- [ ] Deliverable: `docs/literature-review.md` with annotated bibliography
- [ ] Refine analytical question based on literature gaps

---

## Phase 1 — Infrastructure-as-Code `NOT STARTED`

Provision all GCP resources via Terraform.

- [ ] Terraform project structure (main, variables, outputs, modules)
- [ ] BigQuery datasets (staging, intermediate, marts)
- [ ] Cloud Storage buckets
- [ ] Pub/Sub topics and subscriptions
- [ ] IAM roles and service accounts
- [ ] CI/CD for `terraform plan` on PR, `terraform apply` on merge

---

## Phase 2 — Data Modeling (dbt + BigQuery) `NOT STARTED`

Build the analytical data pipeline.

- [ ] dbt project scaffolding and BigQuery connection
- [ ] Staging models — one per source table, standardize names/types
- [ ] Handle TCGA ↔ CPTAC naming inconsistencies (LSCC/LUSC, HNSCC/HNSC, etc.)
- [ ] Intermediate models — cross-modality joins at patient level
- [ ] Mart models — analysis-ready tables for the analytical question
- [ ] dbt tests, documentation, and lineage graphs
- [ ] Add Plotly/notebook visualizations for transformed data

---

## Phase 3 — Streaming Pipelines `NOT STARTED`

Ingest and enrich external literature data.

- [ ] Pub/Sub topic for bioRxiv preprint ingestion
- [ ] Cloud Function: fetch preprints in relevant cancer biology categories
- [ ] Cloud Function: NLP enrichment (gene/protein/pathway entity extraction)
- [ ] Landing zone in BigQuery, integrated with dbt models

---

## Phase 4 — ML Deployment `NOT STARTED`

Train and serve models on multi-omics features.

- [ ] Feature engineering from multi-omics data
- [ ] BigQuery ML baseline model
- [ ] Vertex AI training pipeline
- [ ] Model endpoint deployment
- [ ] Batch predictions written back to BigQuery
- [ ] Monitoring and evaluation dashboard

---

## Visualization Strategy

Visualizations are layered — start lightweight, add infrastructure only when justified.

| Layer | Tool | When | Cost |
|-------|------|------|------|
| **Exploration** | Plotly in notebook | Phase 0+ | $0 |
| **Publication** | GitHub Pages (static HTML export) | Phase 0+ | $0 |
| **Interactive app** | Streamlit on Cloud Run | Phase 2+ (if needed) | ~$2–5/mo |
