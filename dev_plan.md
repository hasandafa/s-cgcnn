# Development Plan — AlxGa1-xAs Rapid Screening Project

## Overview
This project aims to develop an efficient CPU-based Graph Neural Network (s-CGCNN) for rapid screening of ternary AlxGa1-xAs alloys as a faster alternative to first-principles DFT calculations.

---

## Phase 1 — Data Fetch from Materials Project API
- Configure API access (`mp_api_key.txt`)
- Fetch raw data for AlAs, GaAs, and 41 interpolated compositions
- Store BS/DOS data in `/data/raw/bs_dos/`
- Implement validation and preprocessing pipeline

---

## Phase 2 — Data Processing & Interpolation
- Structure interpolation (VCA approach)
- BS/DOS interpolation
- Property calculation (mobility, dielectric, thermal)
- Graph builder (Structure → PyG Graph)
- Save graphs to `/data/processed/graphs/`

---

## Phase 3 — Simplified CGCNN (s-CGCNN)
✅ CPU-optimized CGCNN-Lite  
✅ Multi-task learning  
✅ 5-fold cross-validation  
✅ Model interpretation  
❌ Ensemble & SchNet (skipped for efficiency)

Output: `/results/model_performance/`  

---

## Phase 4 — BS-DOS Predictor & Viewer
- Predict BS/DOS features from structure
- Visualize using Plotly (interactive)
- Derive extended electronic features

---

## Phase 5 — Visualization & Analysis
- 3D structure viewer (Crystal Toolkit)
- Property evolution plots
- Error analysis & publication-ready figures

---

## Phase 6 — Material Screening & Device Analysis
- GNN-based composition screening
- Optimal x determination
- Comparison with literature
- Final recommendation for microelectronic device suitability