# Mississippi Stud Trainer

A simulation and training suite for Mississippi Stud poker, supporting strategy development, evaluation, and bankroll analysis.

## Features

- 🃏 **Basic Strategy**: Implements standard optimal play based on a point-based hand evaluation system.
- 🧠 **Advantage Play Strategies**:
  - **AP-3**: Optimized for known 3rd street (flop) strategy with pre-revealed cards.
  - **AP-5**: Optimized for known 5th street (river) strategy with the 5th street (river) community card known.
- 📈 **Simulator**:
  - Simulates rounds with given ante, strategy, bankroll, and speed (rounds/hr).
  - Calculates EV, standard deviation, risk of ruin, and N₀ (convergence threshold).
- 🧪 **Test Suites** for all evaluators, strategy engines, and feature extraction logic.
- 👨‍🏫 **CLI Training Interface**: Trains the user interactively with immediate feedback and corrections.

## Structure

```
msstud_trainer/
├── core/
│   ├── strategies/         # Basic and AP logic engines
│   ├── evaluator.py        # Error feedback and hand scoring
│   └── simulation.py       # Betting round simulator
│
├── training/
│   ├── cli_basic.py        # Text-based trainer (Basic Strategy)
│   ├── cli_ap_3rd.py       # Text-based trainer (AP 3rd)
│   └── cli_ap_5th.py       # Text-based trainer (AP 5th)
│
├── analysis/
│   ├── bankroll_math.py    # EV, SD, Risk of Ruin, etc.
│   ├── summary.py          # Reporting helpers
│   └── plots.py            # Optional graphing
│
├── data/                   # Precomputed strategy tables
├── tests/                  # Unit tests
├── notebooks/              # Optional Jupyter notebooks
├── main.py                 # CLI launcher
├── README.md
├── setup.py
└── LICENSE
```

## How to Use

### 1. Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -e .
```

### 2. Simulate Strategy

```bash
python -m core.simulation --strategy ap3 --rounds 100000 --ante 5 --bankroll 500 --rounds_per_hour 30 --verbose
```

### 3. Train Interactively

```bash
python -m training.cli_basic
```

### 4. Run Tests

```bash
python -m unittest discover tests
```

## License

MIT License - see `LICENSE` file.