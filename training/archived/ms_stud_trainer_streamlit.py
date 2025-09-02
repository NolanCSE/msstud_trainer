
# ms_stud_trainer_streamlit.py
# Mississippi Stud — 3rd Street Advantage Play Trainer (Sprite UI, Felt Table)
# ---------------------------------------------------------------------------
# - Full-bleed felt background with a "top" flex container:
#     Row 1: community cards (first upcard face up/back via flag; next two backs)
#     Row 2: centered ANTE circle
#     Row 3: centered 3RD / 4TH / 5TH circles (horizontal)
#     Row 4: player's two hole cards (face up)
# - Uses spritesheets in ./card_sprites:
#     Playing Cards.png
#     Card Backs, Enhancers and Seals.png (we crop the TOP-LEFT back only)
#     felt.png (optional; if missing we draw a CSS felt gradient)
# - "Why" (street, evaluator summary, AP recommendation) is hidden until the user acts.
#
# Quick start:
#   streamlit run ms_stud_trainer_streamlit.py
#
# Author: You + ChatGPT (Advantage Play project)

import sys, io, base64, time, random
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List

import streamlit as st
from PIL import Image

# --------------------------
# Import path shim so Streamlit can import your core package structure
# --------------------------
HERE = Path(__file__).resolve()
PKG_ROOT = HERE.parent.parent           # .../msstud_trainer
REPO_ROOT = PKG_ROOT.parent             # repo root (if needed)
for p in (str(PKG_ROOT), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Your codebase imports
from card_lib.card import Card as LibCard
from core.strategies.ap3 import AdvantagePlay3rdStrategy
from core.hand_features import evaluate_partial_hand  # <-- fixed location

# --------------------------
# Local UI Card type (ranks use "T" for ten; suits are symbols)
# --------------------------
SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["2","3","4","5","6","7","8","9","T","J","Q","K","A"]
RANK_VALUE = {r:i for i,r in enumerate(RANKS, start=2)}

@dataclass(frozen=True)
class CardUI:
    rank: str
    suit: str
    def __str__(self): return f"{self.rank}{self.suit}"

def new_deck_ui() -> List[CardUI]:
    return [CardUI(r,s) for s in SUITS for r in RANKS]

def sample_cards(n: int, exclude: Optional[List[CardUI]]=None) -> List[CardUI]:
    deck = new_deck_ui()
    if exclude:
        ex = set(exclude)
        deck = [c for c in deck if c not in ex]
    return random.sample(deck, n)

def deal_training_hand() -> Tuple[CardUI, CardUI, CardUI]:
    a,b,c = sample_cards(3)
    return a,b,c

# --------------------------
# Sprite sheets + felt
# --------------------------
SPRITE_DIR = Path(__file__).parent / "card_sprites"
FRONTS_PATH = SPRITE_DIR / "Playing Cards.png"
BACKS_PATH  = SPRITE_DIR / "Card Backs, Enhancers and Seals.png"
FELT_PATH   = SPRITE_DIR / "felt.png"   # optional

# Fronts sheet is 923x380 → 13x4 grid, so each cell is 71x95
FRONTS_COLS, FRONTS_ROWS = 13, 4
CELL_W, CELL_H = 71, 95

RANK_TO_COL = {"A":0,"2":1,"3":2,"4":3,"5":4,"6":5,"7":6,"8":7,"9":8,"10":9,"J":10,"Q":11,"K":12}
SUIT_TO_ROW = {"♥":0,"♣":1,"♦":2,"♠":3}

@st.cache_data(show_spinner=False)
def _load_sheets():
    fronts = Image.open(FRONTS_PATH).convert("RGBA")
    backs  = Image.open(BACKS_PATH).convert("RGBA")
    felt   = Image.open(FELT_PATH).convert("RGBA") if FELT_PATH.exists() else None
    return fronts, backs, felt

def _crop_front(rank_symbol: str, suit_symbol: str) -> Image.Image:
    rank = "10" if rank_symbol == "T" else rank_symbol
    col = RANK_TO_COL[rank]
    row = SUIT_TO_ROW[suit_symbol]
    x0, y0 = col * CELL_W, row * CELL_H
    return _load_sheets()[0].crop((x0, y0, x0 + CELL_W, y0 + CELL_H))

def _crop_back() -> Image.Image:
    # Top-left back
    return _load_sheets()[1].crop((0, 0, CELL_W, CELL_H))

def _img_to_data_url(img: Image.Image, scale=2) -> str:
    # Composite onto white background to remove transparency
    bg = Image.new("RGBA", img.size, (255, 245, 230, 255))  # light cream background
    bg.paste(img, (0, 0), img)  # keep sprite's alpha mask
    img = bg
    if scale != 1:
        img = img.resize((CELL_W*scale, CELL_H*scale), Image.NEAREST)
    buf = io.BytesIO()  # type: ignore
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"

def card_data_url_ui(card: CardUI, scale=2) -> str:
    return _img_to_data_url(_crop_front(card.rank, card.suit), scale=scale)

def back_data_url(scale=2) -> str:
    return _img_to_data_url(_crop_back(), scale=scale)

def felt_data_url() -> Optional[str]:
    felt = _load_sheets()[2]
    if felt is None:
        return None
    buf = io.BytesIO()
    felt.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"

# --------------------------
# AP3 decision + explanation (hidden until after action)
# --------------------------
SUIT_UI2LIB = {"♠": "Spades", "♥": "Hearts", "♦": "Diamonds", "♣": "Clubs"}
RANK_UI2LIB = {"T": "10"}

def to_lib(c: CardUI) -> LibCard:
    return LibCard(SUIT_UI2LIB[c.suit], RANK_UI2LIB.get(c.rank, c.rank))

def _describe_partial(cards: List[LibCard]) -> str:
    feats = evaluate_partial_hand(cards)
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

def compute_optimal_action_3rd(h1: CardUI, h2: CardUI, up1: CardUI) -> Tuple[str, Dict[str,float], dict]:
    street = "3rd"
    Lh1, Lh2, Lu1 = to_lib(h1), to_lib(h2), to_lib(up1)

    strategy = AdvantagePlay3rdStrategy()
    ante = 1
    bet = strategy.get_bet([Lh1, Lh2], [], street, ante, ante, {"3rd": Lu1, "4th": None, "5th": None})

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
        "evaluation": _describe_partial([Lh1, Lh2, Lu1]),
        "ap_recommendation": f"AP3 says: {best}",
    }
    return best, {}, why

# --------------------------
# Felt + "top" flex layout (4 rows)
# --------------------------
def inject_table_css():
    felt_url = felt_data_url()
    felt_bg = f"url('{felt_url}')" if felt_url else "radial-gradient(1600px 800px at 50% 30%, #137a3a, #0b4f27 70%)"
    st.markdown(f"""
    <style>
      .felt {{
        position: relative;
        width: 100%;
        min-height: 560px;
        background-image: {felt_bg};
        background-size: cover;
        background-position: center;
        border-radius: 16px;
        border: 2px solid #083a1c;
        box-shadow: inset 0 0 60px rgba(0,0,0,.25);
        padding: 24px 12px;
      }}
      .top {{ display: flex; flex-direction: column; gap: 16px; align-items: center; }}
      .row {{ display: flex; gap: 16px; align-items: center; justify-content: center; width: 100%; }}
      .row.player {{ gap: 24px; }}
      .card-img {{ width: {CELL_W*2}px; height: {CELL_H*2}px; image-rendering: pixelated;
                   border-radius: 10px; box-shadow: 0 8px 22px rgba(0,0,0,.35); }}
      .spot {{ width: 96px; height: 96px; border-radius: 50%;
               border: 3px dashed rgba(255,255,255,.45); background: rgba(255,255,255,.08);
               color: #fff; display: flex; align-items: center; justify-content: center;
               font-weight: 800; letter-spacing: 1px; text-transform: uppercase;
               text-shadow: 0 1px 0 rgba(0,0,0,.5); }}
      .spot.small {{ width: 72px; height: 72px; font-size: 12px; }}
    </style>
    """, unsafe_allow_html=True)

def render_table_top(h1: CardUI, h2: CardUI, up1: CardUI, show_up=True):
    inject_table_css()
    cu = card_data_url_ui(up1, scale=2) if show_up else back_data_url(scale=2)
    cb = back_data_url(scale=2)
    c1 = card_data_url_ui(h1, scale=2); c2 = card_data_url_ui(h2, scale=2)
    html = f"""
    <div class="felt">
      <div class="top">
        <div class="row community">
          <img class="card-img" src="{cu}" />
          <img class="card-img" src="{cb}" />
          <img class="card-img" src="{cb}" />
        </div>
        <div class="row ante"><div class="spot">ANTE</div></div>
        <div class="row streets">
          <div class="spot small">3RD</div>
          <div class="spot small">4TH</div>
          <div class="spot small">5TH</div>
        </div>
        <div class="row player">
          <img class="card-img" src="{c1}" />
          <img class="card-img" src="{c2}" />
        </div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# --------------------------
# Streamlit UI
# --------------------------
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

# Score row
colA, colB, colC = st.columns(3)
with colA: st.metric("Score", st.session_state.score)
with colB: st.metric("Streak", st.session_state.streak)
with colC:
    elapsed = int(time.time() - st.session_state.start_time)
    st.metric("Time (min)", f"{elapsed//60}:{elapsed%60:02d}")

# Table
st.subheader("Table")
render_table_top(st.session_state.h1, st.session_state.h2, st.session_state.up1, show_up=True)

# Compute decision (not shown until act)
best_action, evs, why = compute_optimal_action_3rd(st.session_state.h1, st.session_state.h2, st.session_state.up1)

# Action buttons
st.markdown("### Choose your action")
buttons = st.columns(3)
choice = None
if buttons[0].button("Fold"): choice = "fold"
if buttons[1].button("Bet 1x"): choice = "1x"
if buttons[2].button("Bet 3x"): choice = "3x"

def next_hand():
    st.session_state.h1, st.session_state.h2, st.session_state.up1 = deal_training_hand()
    st.session_state.feedback = ""
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
    st.session_state.current_why = why
    st.session_state.current_evs = evs
    st.session_state.show_why = True
    st.toast(st.session_state.feedback, icon="✅" if correct else "❌")
    st.rerun()

# Feedback + Why
if st.session_state.feedback:
    st.info(st.session_state.feedback)

st.markdown("### Why (AP3 reference)")
if st.session_state.show_why and isinstance(st.session_state.current_why, dict) and st.session_state.current_why:
    w = st.session_state.current_why
    st.markdown(
        f"**Street:** {w.get('street','?')}  \n"
        f"**Evaluation:** {w.get('evaluation','–')}  \n"
        f"**AP:** {w.get('ap_recommendation','–')}"
    )
else:
    st.markdown("_Explanation will appear after you act._")

st.divider()
st.button("Deal Next Hand", on_click=next_hand, type="primary")
