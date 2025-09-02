# ms_stud_trainer_streamlit.py
# Mississippi Stud — 3rd Street Advantage Play Trainer
# ----------------------------------------------------
# Quick-start UI built with Streamlit.
# - Presents random 3rd-street situations (2 hole cards + first community card).
# - Asks for your action (Fold / 1x / 3x).
# - Gives instant feedback with the correct play and the "why" (EV breakdown if available).
# - Tracks score, streak, and time.
#
# How to run:
#   pip install streamlit
#   streamlit run ms_stud_trainer_streamlit.py
#
# Integration points:
#   1) Replace `compute_optimal_action_3rd()` with your real solver that uses your codebase
#      (e.g., functions from mississippi.py, mississippi_simulator.py, cli_ap_3rd.py, etc.).
#   2) Replace `deal_training_hand()` with your true dealing model if you want to bias drills
#      (e.g., spaced repetition, specific card families, or "hole-card" peeks).
#
# Notes:
#   - This file is fully self-contained to let you try the UX immediately.
#   - All EV math here is placeholder. Plug in your existing EV engine for true numbers.
#   - Advantage Play (AP) strategy drives the “correct” answer: choose the action with max EV.
#
# Author: You + ChatGPT (Advantage Play project)
# License: MIT

# --- import shim so we can run via `streamlit run .../training/ms_stud_trainer_streamlit.py`
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
PKG_ROOT = HERE.parents[1]        # .../msstud_trainer
REPO_ROOT = HERE.parents[2]       # repo root (in case card_lib is sibling to msstud_trainer)

for p in (PKG_ROOT, REPO_ROOT):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

# ===== Sprites & Table Rendering =====
from pathlib import Path
from PIL import Image
import streamlit as st
import base64

SPRITE_DIR = Path(__file__).parent / "card_sprites"
FRONTS_PATH = SPRITE_DIR / "Playing Cards.png"
BACKS_PATH  = SPRITE_DIR / "Card Backs, Enhancers and Seals.png"

# The fronts sheet is 923x380 → 13 columns (A..K), 4 rows (♥, ♣, ♦, ♠)
FRONTS_COLS, FRONTS_ROWS = 13, 4
CELL_W, CELL_H = 71, 95  # 923/13, 380/4

# Rank → column index on the sheet
RANK_TO_COL = {
    "A": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5, "7": 6,
    "8": 7, "9": 8, "10": 9, "J": 10, "Q": 11, "K": 12
}
# Suit (symbol) → row index on the sheet (top→bottom)
SUIT_TO_ROW = {"♥": 0, "♣": 1, "♦": 2, "♠": 3}

@st.cache_data(show_spinner=False)
def _load_sheets():
    fronts = Image.open(FRONTS_PATH).convert("RGBA")
    backs  = Image.open(BACKS_PATH).convert("RGBA")
    return fronts, backs

def _crop_front(rank_symbol: str, suit_symbol: str) -> Image.Image:
    rank = "10" if rank_symbol == "T" else rank_symbol
    col = RANK_TO_COL[rank]
    row = SUIT_TO_ROW[suit_symbol]
    x0, y0 = col * CELL_W, row * CELL_H
    return _load_sheets()[0].crop((x0, y0, x0 + CELL_W, y0 + CELL_H))

def _crop_back() -> Image.Image:
    # "top left" back — crop a 71x95 cell from 0,0 on the backs sheet
    return _load_sheets()[1].crop((0, 0, CELL_W, CELL_H))

def _img_to_data_url(img: Image.Image, scale=2) -> str:
    if scale != 1:
        img = img.resize((CELL_W*scale, CELL_H*scale), Image.NEAREST)
    buf = st.runtime.media_file_manager._BytesIO()  # type: ignore
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"

def card_data_url(rank: str, suit: str, scale=2) -> str:
    return _img_to_data_url(_crop_front(rank, suit), scale=scale)

def back_data_url(scale=2) -> str:
    return _img_to_data_url(_crop_back(), scale=scale)

def felt_data_url() -> str | None:
    felt = _load_sheets()[2]
    if felt is None:
        return None
    # make it big so it covers; browser will cover/contain anyway
    buf = st.runtime.media_file_manager._BytesIO()  # type: ignore
    felt.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"

# --- Streamlit UI for Mississippi Stud 3rd Street Trainer ---
import random
import time
from dataclasses import dataclass
from typing import Tuple, Dict, List, Optional

# ===== Table CSS (felt background outside of .top) =====
def inject_table_css():
    felt_url = felt_data_url()
    felt_bg = f"url('{felt_url}')" if felt_url else "radial-gradient(1600px 800px at 50% 30%, #137a3a, #0b4f27 70%)"
    st.markdown(f"""
    <style>
      .felt {{
        position: relative;
        width: 100%;
        min-height: 520px;
        background-image: {felt_bg};
        background-size: cover;
        background-position: center;
        border-radius: 16px;
        border: 2px solid #083a1c;
        box-shadow: inset 0 0 60px rgba(0,0,0,.25);
        padding: 24px 12px;
      }}
      .top {{
        display: flex;
        flex-direction: column;
        gap: 16px;
        align-items: center;
        justify-content: flex-start;
      }}
      .row {{
        display: flex;
        gap: 16px;
        align-items: center;
        justify-content: center;
        width: 100%;
      }}
      .row.player {{ gap: 24px; }}
      .card-img {{
        width: {CELL_W*2}px; height: {CELL_H*2}px;  /* scale 2x */
        image-rendering: pixelated;
        border-radius: 10px;
        box-shadow: 0 8px 22px rgba(0,0,0,.35);
      }}
      .spot {{
        width: 96px; height: 96px; border-radius: 50%;
        border: 3px dashed rgba(255,255,255,.45);
        background: rgba(255,255,255,.08);
        color: #fff; display: flex; align-items: center; justify-content: center;
        font-weight: 800; letter-spacing: 1px; text-transform: uppercase;
        text-shadow: 0 1px 0 rgba(0,0,0,.5);
      }}
      .spot.small {{ width: 72px; height: 72px; font-size: 12px; }}
      .label {{ color: rgba(255,255,255,.9); font-weight: 700; }}
    </style>
    """, unsafe_allow_html=True)

def render_table_top(hole1, hole2, up1, show_up=True):
    inject_table_css()
    # Build data URLs
    c1 = card_data_url(hole1.rank, hole1.suit, scale=2)
    c2 = card_data_url(hole2.rank, hole2.suit, scale=2)
    cu = card_data_url(up1.rank, up1.suit, scale=2) if show_up else back_data_url(scale=2)
    cb = back_data_url(scale=2)

    # HTML (felt background is the outer layer; .top holds the 4 rows)
    html = f"""
    <div class="felt">
      <div class="top">
        <!-- row 1: community cards -->
        <div class="row community">
          <img class="card-img" src="{cu}" />
          <img class="card-img" src="{cb}" />
          <img class="card-img" src="{cb}" />
        </div>

        <!-- row 2: ante circle centered -->
        <div class="row ante">
          <div class="spot">ANTE</div>
        </div>

        <!-- row 3: 3rd/4th/5th horizontally centered -->
        <div class="row streets">
          <div class="spot small">3RD</div>
          <div class="spot small">4TH</div>
          <div class="spot small">5TH</div>
        </div>

        <!-- row 4: two player cards -->
        <div class="row player">
          <img class="card-img" src="{c1}" />
          <img class="card-img" src="{c2}" />
        </div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# -----------------------------
# Card helpers (lightweight)
# -----------------------------

SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["2","3","4","5","6","7","8","9","T","J","Q","K","A"]
RANK_VALUE = {r:i for i,r in enumerate(RANKS, start=2)}

@dataclass(frozen=True)
class Card:
    rank: str
    suit: str
    def __str__(self): return f"{self.rank}{self.suit}"

def new_deck() -> List[Card]:
    return [Card(r,s) for s in SUITS for r in RANKS]

def sample_cards(n: int, exclude: Optional[List[Card]]=None) -> List[Card]:
    deck = new_deck()
    if exclude:
        exclude_set = set(exclude)
        deck = [c for c in deck if c not in exclude_set]
    return random.sample(deck, n)

# -----------------------------
# Training-hand generator
# -----------------------------

def deal_training_hand(bias: Optional[str]=None) -> Tuple[Card, Card, Card]:
    """
    Returns a 3rd-street state: (hole1, hole2, first_upcard).
    bias: You can add knobs like 'pair-heavy', 'suited', 'gapped', etc.
    """
    cards = sample_cards(3)
    return cards[0], cards[1], cards[2]

# -----------------------------
# AP solver interface
# -----------------------------

# at top of file (imports you already have)
from card_lib.card import Card as LibCard
from core.strategies.ap3 import AdvantagePlay3rdStrategy
from core.hand_features import evaluate_partial_hand  # we use this for the evaluator-style summary

SUIT_MAP = {"♠": "Spades", "♥": "Hearts", "♦": "Diamonds", "♣": "Clubs"}
RANK_MAP = {"T": "10"}

def _to_lib(c):
    return LibCard(SUIT_MAP.get(c.suit, c.suit), RANK_MAP.get(c.rank, c.rank))

def _describe_partial(cards):
    feats = evaluate_partial_hand(cards)  # uses dead-joker padding + draw features
    parts = []
    if feats["pair_rank"]:
        parts.append(f"pair of {feats['pair_rank']}s")
    elif feats["is_made_hand"]:
        parts.append("made hand")
    else:
        if feats["is_straight_draw"]:
            g = feats["straight_gaps"]
            parts.append(f"straight draw ({g} gaps)" if g is not None else "straight draw")
        if feats["is_flush_draw"]:
            parts.append("flush draw")
    parts.append("no high cards" if feats["num_high_cards"] == 0 else f"{feats['num_high_cards']} high card(s)")
    return ", ".join(parts) if parts else "high card / no draw"

def compute_optimal_action_3rd(hole1, hole2, up1):
    street = "3rd"
    h1, h2, u1 = _to_lib(hole1), _to_lib(hole2), _to_lib(up1)
    known_now = [h1, h2, u1]

    # AP3 as ground truth bet on 3rd street with peeked 3rd card
    strategy = AdvantagePlay3rdStrategy()
    ante = 1
    bet = strategy.get_bet([h1, h2], [], "3rd", ante, ante, {"3rd": u1, "4th": None, "5th": None})
    if bet == "fold":
        best = "fold"
    elif bet == 1:
        best = "1x"
    elif bet == 3:
        best = "3x"
    else:
        best = f"{bet}x" if isinstance(bet, int) else "fold"

    why = {
        "street": street,
        "evaluation": _describe_partial(known_now),
        "ap_recommendation": f"AP3 says: {best}",
    }
    # EVs optional; keep empty for now
    return best, {}, why




# -----------------------------
# UI — Streamlit
# -----------------------------

st.set_page_config(page_title="Mississippi Stud — 3rd Street Trainer", page_icon="🂠", layout="centered")

def init_state():
    if "h1" not in st.session_state:
        st.session_state.h1, st.session_state.h2, st.session_state.up1 = deal_training_hand()
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "streak" not in st.session_state:
        st.session_state.streak = 0
    if "hands_played" not in st.session_state:
        st.session_state.hands_played = 0
    if "start_time" not in st.session_state:
        st.session_state.start_time = time.time()
    if "feedback" not in st.session_state:
        st.session_state.feedback = ""
    if "current_why" not in st.session_state:
        st.session_state.current_why = {}
    if "current_evs" not in st.session_state:
        st.session_state.current_evs = {}
    if "show_why" not in st.session_state:
        st.session_state.show_why = False

init_state()

st.title("Mississippi Stud — 3rd Street AP Trainer")
st.caption("Advantage Play training: pick the EV-maximizing action at 3rd street.")

colA, colB, colC = st.columns(3)
with colA:
    st.metric("Score", st.session_state.score)
with colB:
    st.metric("Streak", st.session_state.streak)
with colC:
    elapsed = int(time.time() - st.session_state.start_time)
    st.metric("Time (min)", f"{elapsed//60}:{elapsed%60:02d}")

st.subheader("Table")
# On 3rd street, you’re peeking the 3rd card; the real table would show it up,
# and the later two are facedown.
render_table_top(st.session_state.h1, st.session_state.h2, st.session_state.up1, show_up=True)

best_action, evs, why = compute_optimal_action_3rd(st.session_state.h1, st.session_state.h2, st.session_state.up1)

# persist per-hand explanation so it survives st.rerun()
st.session_state.current_why = why
st.session_state.current_evs = evs

st.markdown("### Choose your action")
buttons = st.columns(3)
choice = None
if buttons[0].button("Fold"):
    choice = "fold"
if buttons[1].button("Bet 1x"):
    choice = "1x"
if buttons[2].button("Bet 3x"):
    choice = "3x"

def next_hand():
    st.session_state.h1, st.session_state.h2, st.session_state.up1 = deal_training_hand()
    st.session_state.feedback = ""
    st.session_state.evs = {}
    st.session_state.current_why = {}
    st.session_state.current_evs = {}
    st.session_state.show_why = False

if choice is not None:
    st.session_state.hands_played += 1
    correct = (choice == best_action)
    if correct:
        st.session_state.score += 1
        st.session_state.streak += 1
        st.session_state.feedback = f"✅ Correct: **{best_action}** is the AP play."
    else:
        st.session_state.streak = 0
        st.session_state.feedback = f"❌ Not quite. Correct is **{best_action}**."

    # persist why/evs for this hand and reveal them
    st.session_state.current_why = why
    st.session_state.current_evs = evs
    st.session_state.show_why = True

    st.toast(st.session_state.feedback, icon="✅" if correct else "❌")
    st.rerun()


st.markdown("### Why (AP3 reference)")
if st.session_state.show_why and isinstance(st.session_state.current_why, dict) and st.session_state.current_why:
    w = st.session_state.current_why
    st.markdown(
        f"**Street:** {w.get('street','?')}  \n"
        f"**Evaluation:** {w.get('evaluation','–')}  \n"
        f"**AP:** {w.get('ap_recommendation','–')}"
    )
    if st.session_state.current_evs:
        st.table({
            "Action": list(st.session_state.current_evs.keys()),
            "EV": [round(v,3) for v in st.session_state.current_evs.values()]
        })
    st.button("Deal Next Hand", on_click=next_hand, type="primary")
else:
    st.markdown("_Explanation will appear after you act._")


st.divider()
with st.expander("Settings"):
    st.write("Biasing not yet wired—this is a plug for spaced-repetition or targeted drills.")
    st.write("Hook your solver by replacing `compute_optimal_action_3rd()` with real EVs from your engine.")
    st.write("If your code exposes hand features, you can print them here as learning cues.")
