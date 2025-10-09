# AlxGa₁₋ₓAs Rapid Screening Project

**Efficient CPU-Based Graph Neural Networks for Rapid Screening of AlₓGa₁₋ₓAs Alloys as a Fast Alternative to First-Principles Calculations**

---

## 🧠 Overview
This repository aims to develop a **simplified CGCNN (s-CGCNN)** architecture optimized for CPU-based computation to accelerate the screening of **AlₓGa₁₋ₓAs semiconductor alloys**.  
It leverages data-driven approaches using the **Materials Project API** and **PyTorch Geometric (PyG)** to predict material properties without running expensive DFT simulations.

---

## 📂 Project Structure

algaas_research/
├── config/
│ ├── config.yaml
│ ├── model_config.yaml
│ └── mp_api_key.txt
│
├── data/
│ ├── raw/
│ │ ├── mp-2172_AlAs.json
│ │ ├── mp-2534_GaAs.json
│ │ └── bs_dos/
│ └── processed/
│ ├── graphs/
│ ├── interpolated/
│ └── bs_dos/
│
├── models/graph/
│ ├── scgcnn.py
│ ├── scgcnn_trainer.py
│ ├── graph_builder.py
│ └── scgcnn_config.py
│
├── scripts/
│ ├── run_all.py
│ └── validate_all.py
│
├── utils/
│ ├── constants.py
│ ├── device_utils.py
│ ├── file_io.py
│ ├── logger.py
│ └── metrics.py
│
├── logs/
├── results/
├── requirements.txt
├── README.md
└── CHANGELOG.md

---

## 🚀 Phases

| Phase | Description | Status |
|-------|--------------|--------|
| 1 | Data fetch from Materials Project API | 🟩 In progress |
| 2 | Data processing & interpolation | ⏳ Planned |
| 3 | Simplified CGCNN (s-CGCNN) model | ⏳ Planned |
| 4 | BS/DOS predictor & interactive viewer | ⏳ Planned |
| 5 | Visualization & analysis | ⏳ Planned |
| 6 | Screening & device suitability analysis | ⏳ Planned |

---

## ⚙️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/hasandafa/algaas_research.git
   cd algaas_research
(Optional) Create a virtual environment:

bash
Copy code
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Add your Materials Project API key:

bash
Copy code
echo "YOUR_API_KEY_HERE" > config/mp_api_key.txt
🧩 Key Features
CPU-optimized Graph Neural Network (s-CGCNN)

Material property interpolation (VCA method)

Multi-task learning for property prediction

Band structure (BS) and Density of States (DOS) prediction

Plotly-based interactive visualization

Publication-ready figures and evaluation metrics

📈 Output Examples
Graph data in /data/processed/graphs/

Predicted band structures and DOS plots

Model performance metrics and cross-validation logs

Screening results for optimal AlₓGa₁₋ₓAs composition

🧑‍💻 Author
Abdullah Hasan Dafa
B.Eng. in Physics Engineering (Instrumentation & Control)
Universitas Nasional, Indonesia
📜 License

This project is currently in research and development phase.
All rights reserved © 2025 Abdullah Hasan Dafa.


---