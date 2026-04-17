# Quantum Phase Estimation Simulator

An interactive desktop simulator for Quantum Phase Estimation (QPE), modelling the algorithm using photon-counting statistics to mimic optical experimental noise.

## Features

- **Counts View** — bar chart and table of measurement outcomes for a chosen number of qubits, with estimated phase and error
- **1–10 Qubit Scaling** — visual comparison of QPE precision across 1–10 qubits simultaneously
- **Poissonian noise model** — total photon counts drawn from a Poisson distribution, matching real optical experiments
- Interactive controls for target phase, shots (integration time), photons per shot, and active qubits

## Installation & Setup

### macOS
1. Open Terminal and `cd` to the project folder.
2. Fix permissions on the launch script:
   ```bash
   xattr -c *.command && chmod +x *.command
   ```
3. Double-click **`launch.command`** (handles venv setup on first run).

### Windows
1. Double-click **`launch.bat`** (handles venv setup on first run).

### Manual
```bash
pip install -r requirements.txt
python main.py
```

## Main Files

| File | Description |
|------|-------------|
| `main.py` | Entry point |
| `app/interface.py` | PyQt5 GUI: control panel, counts tab, scaling tab |
| `requirements.txt` | Python dependencies (PyQt5, pyqtgraph, numpy) |
