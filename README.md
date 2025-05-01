
# 🧠 Mississippi Stud Trainer & Simulator

This project provides a modular training and analysis suite for Mississippi Stud, built on top of the `card_lib` engine. It includes both player training tools and betting outcome simulation based on customizable strategies.

---

## 🎯 Goals

- ✅ **Training** with real-time feedback and strategy correction
  - Basic Strategy Mode
  - Advantage Play with 3rd Street Reveal
  - Advantage Play with 5th Street Reveal

- 📈 **Simulation** for statistical analysis of betting systems
  - EV/hour, Std Dev, Risk of Ruin, House Edge
  - Analysis over configurable timeframes and bankrolls

---

## 🗂 Project Structure

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

---

## 🔧 Dependencies

- Python 3.8+
- `card_lib` (must be installed locally or via GitHub)
- (Optional) `matplotlib`, `numpy`, `pandas` for analytics/plots

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

### Training Mode (Basic Strategy)

```bash
python training/cli_basic.py
```

### Simulation Mode

```bash
python core/simulation.py --strategy ap_5th --bankroll 1000 --ante 5 --rounds 100000
```

---

## 📊 Output Metrics (Simulation)

- **EV/hour**: Expected value over time
- **Standard Deviation**
- **Risk of Ruin**
- **House Edge**
- **Hours to Safe Play** (2 SD drop = bankroll 0)

---

## 🧪 Running Tests

```bash
python -m unittest discover tests
```

---

## 🔗 Related Project

This tool is built on the [card_lib](https://github.com/NolanCSE/card_lib) engine.

---

## 📃 License

MIT License
