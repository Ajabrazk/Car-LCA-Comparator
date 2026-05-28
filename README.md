# Passenger Car LCA Comparator

This repository contains a web application developed for the PROJ-H402 Computing Project (Master in Computer Science and Engineering, ULB/VUB). The tool calculates and compares the environmental impacts of different passenger car technologies based on Life Cycle Assessment (LCA) data.

Supervisor: Lea D'Amore 

## Overview

The application processes raw LCA datasets to generate a comparative dashboard. It evaluates the environmental footprint of vehicles from manufacturing to end-of-life, including both Well-to-Tank (WTT) and Tank-to-Wheel (TTW) phases.

Supported technologies: Petrol, Diesel, CNG, LPG, HEV, PHEV, BEV, and FCEV.

Core capabilities:
* Impact calculation across 4 environmental indicators: Climate change, Particulate matter formation, Material resources, and Energy resources.
* Dynamic modeling of cumulative emissions ($Y = ax + b$) to compute the break-even mileage between technologies.
* Energy scenario integration (Current vs. 2050 electricity grids, Grey vs. Green hydrogen).
* Tangible equivalencies for non-expert audiences (e.g., carbon budget limits, material equivalents).

## Architecture

The codebase follows a 3-tier architecture to decouple data processing from the user interface:

* `src/voiture.py`: Defines the vehicle data structure. Handles type casting and basic validation.
* `src/acv_handler.py`: Core business logic. Parses the Excel dataset, handles missing/merged cells programmatically, and executes the mathematical LCA formulas.
* `app.py`: Streamlit frontend. Manages user session state, interface routing, and Plotly data visualization.

## Setup Instructions

### Prerequisites
* Python
* Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/LCA-Passenger-Cars-Comparator.git
   cd LCA-Passenger-Cars-Comparator
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   
   # On Windows: 
   venv\Scripts\activate
   # On macOS/Linux: 
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

Run the application by typing this command in the terminal:
```bash
python -m streamlit run app.py
```
The interface will be accessible in your web browser at `http://localhost:8501`.
