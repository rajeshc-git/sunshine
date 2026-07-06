# AI Requirements — Root Cause Analysis (RCA) for Asset Health Monitoring

## Overview

This document outlines the key open-source AI/ML libraries and frameworks to evaluate for building a **Root Cause Analysis (RCA)** system focused on **asset health monitoring**. Each tool provides different capabilities — from time-series analysis to causal inference to deep learning — that can be composed into an end-to-end solution.

---

## Reference Libraries & Repositories

### 1. PyRCA — Salesforce

| Field        | Details |
|--------------|---------|
| **Source**   | Salesforce Research |
| **Repo**     | [github.com/salesforce/PyRCA](https://github.com/salesforce/PyRCA) |
| **Focus**    | Root cause analysis in **time-series data** |
| **Use Case** | Asset health monitoring via time-series anomaly detection and causal discovery |

**Key Capabilities:**
- Purpose-built Python library for RCA on time-series datasets
- Supports multiple causal discovery and attribution algorithms
- Directly applicable to sensor/telemetry data from monitored assets

---

### 2. Manufacturing Root Cause Analysis — Databricks

| Field        | Details |
|--------------|---------|
| **Source**   | Databricks Industry Solutions |
| **Repo**     | [github.com/databricks-industry-solutions/manufacturing-root-cause-analysis](https://github.com/databricks-industry-solutions/manufacturing-root-cause-analysis) |
| **Focus**    | Industry-specific RCA using **causal inference** techniques |
| **Use Case** | Understanding and diagnosing asset/equipment failures in manufacturing |

**Key Capabilities:**
- Industry-tailored solution for manufacturing environments
- Leverages causal inference to identify failure root causes
- Provides reusable notebooks and pipelines on the Databricks platform

---

### 3. ML for RCA — Deep Learning Approach

| Field        | Details |
|--------------|---------|
| **Source**   | Community / Research |
| **Repo**     | [github.com/grjadhav409/ML_for_RCA](https://github.com/grjadhav409/ML_for_RCA) |
| **Focus**    | Predicting root causes using **deep learning** models |
| **Use Case** | Adaptable for analyzing health and failure patterns across various asset types |

**Key Capabilities:**
- Uses deep learning models for root cause prediction
- Model architectures can be adapted to different asset domains
- Suitable for scenarios with large labeled failure datasets

---

## Quick Comparison

| Library | Approach | Best For | Platform |
|---------|----------|----------|----------|
| **PyRCA** | Time-series causal analysis | Sensor/telemetry monitoring | Python (standalone) |
| **Databricks MFG RCA** | Causal inference | Manufacturing failure diagnosis | Databricks |
| **ML for RCA** | Deep learning prediction | Pattern-based failure prediction | Python (standalone) |

---

## Next Steps

- [ ] Evaluate each repository against project-specific data and infrastructure
- [ ] Identify which approach (causal vs. predictive) best fits the use case
- [ ] Prototype with the most promising library using real asset data
- [ ] Define integration requirements with existing monitoring systems