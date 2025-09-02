# ms_stud_trainer_streamlit.py
# Mississippi Stud — AP3 Trainer (3rd → 4th → 5th streets) with sprite UI + felt
# - One fixed hand per round (h1,h2,c1,c2,c3) — no redeal until Fold / Next Hand
# - AP3 flow (hole-card peek on 3rd):
#     * 3rd: c1 visible, c2/c3 down → bet
#     * 4th: still only c1 visible → bet → then flip c2
#     * 5th: c1+c2 visible → bet (c3 stays down during action)
# - “Why” (street, evaluator summary, AP recommendation) shown only after your action

import sys, io, base64, time, random
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List

import streamlit as st
from PIL import Image

ANTE = 5

# --------------------------
# Import shim so Streamlit can import your codebase
# --------------------------
HERE = Path(__file__).resolve()
PKG_ROOT = HERE.parent.parent           # .../msstud_trainer
REPO_ROOT = PKG_ROOT.parent
for p in (str(PKG_ROOT), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from card_lib.card import Card as LibCard
from core.strategies.ap3 import AdvantagePlay3rdStrategy
from core.hand_features import evaluate_partial_hand

from card_lib.evaluators.mississippi import evaluate_mississippi_stud_hand
import card_lib.simulation.mississippi_simulator as ms_sim

# --------------------------
# Local UI Card type (rank "T" for ten, suit symbols)
# --------------------------
SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["2","3","4","5","6","7","8","9","T","J","Q","K","A"]

@dataclass(frozen=True)
class CardUI:
    rank: str
    suit: str
    def __str__(self): return f"{self.rank}{self.suit}"

def sample_cards(n: int) -> List[CardUI]:
    deck = [CardUI(r,s) for s in SUITS for r in RANKS]
    return random.sample(deck, n)

# --------------------------
# Sprite sheets + felt
# --------------------------
SPRITE_DIR = Path(__file__).parent / "card_sprites"
FRONTS_PATH = SPRITE_DIR / "Playing Cards.png"
BACKS_PATH  = SPRITE_DIR / "Card Backs, Enhancers and Seals.png"
FELT_PATH   = SPRITE_DIR / "felt.png"   # optional

# Fronts sheet is 923x380 → 13x4 grid, each cell 71x95
CELL_W, CELL_H = 71, 95
RANK_TO_COL = {"A":12,"2":0,"3":1,"4":2,"5":3,"6":4,"7":5,"8":6,"9":7,"10":8,"J":9,"Q":10,"K":11}
SUIT_TO_ROW = {"♥":0,"♣":1,"♦":2,"♠":3}

@st.cache_data(show_spinner=False)
def _load_sheets():
    fronts = Image.open(FRONTS_PATH).convert("RGBA")
    backs  = Image.open(BACKS_PATH).convert("RGBA")
    felt   = Image.open(FELT_PATH).convert("RGBA") if FELT_PATH.exists() else None
    return fronts, backs, felt

def _crop_front(rank_symbol: str, suit_symbol: str) -> Image.Image:
    rank = "10" if rank_symbol == "T" else rank_symbol
    col = RANK_TO_COL[rank]; row = SUIT_TO_ROW[suit_symbol]
    x0, y0 = col * CELL_W, row * CELL_H
    return _load_sheets()[0].crop((x0, y0, x0 + CELL_W, y0 + CELL_H))

def _crop_back() -> Image.Image:
    # top-left back cell
    return _load_sheets()[1].crop((0, 0, CELL_W, CELL_H))

def _img_to_data_url(img: Image.Image, scale=2) -> str:
    # Composite onto white so transparent sprite regions become white
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    bg.paste(img, (0, 0), img)
    img = bg
    if scale != 1:
        img = img.resize((CELL_W*scale, CELL_H*scale), Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"

def card_data_url_ui(card: CardUI, scale=2) -> str:
    return _img_to_data_url(_crop_front(card.rank, card.suit), scale=scale)

def back_data_url(scale=2) -> str:
    return _img_to_data_url(_crop_back(), scale=scale)

def felt_data_url() -> Optional[str]:
    felt = _load_sheets()[2]
    if felt is None: return None
    buf = io.BytesIO()
    felt.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"

# --------------------------
# AP3 decision + “why”
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

def ap3_decision(stage: str, h1: CardUI, h2: CardUI, c1: CardUI, c2: CardUI, c3: CardUI, strategy=AdvantagePlay3rdStrategy()):
    """Return (best_action, evs, why_dict) for given stage using AP3."""
    Lh1, Lh2, Lc1, Lc2, Lc3 = map(to_lib, [h1,h2,c1,c2,c3])
    ante = 1

    # Build revealed/peeked per stage exactly like simulate_round does
    if stage == "3rd":
        revealed = []                          # c1 not officially revealed yet
        peeked   = {"3rd": Lc1, "4th": None, "5th": None}
        known    = [Lh1, Lh2, Lc1]             # for player-facing evaluation text
        current_total = ante                   # ante only when choosing 3rd
    elif stage == "4th":
        revealed = [Lc1]                       # after 3rd bet, c1 is revealed
        peeked   = {"3rd": Lc1, "4th": None, "5th": None}
        known    = [Lh1, Lh2, Lc1]
        current_total = ante + 0               # we don't track totals; irrelevant to choice labels
    else:  # "5th"
        revealed = [Lc1, Lc2]                  # c2 flips after 4th bet
        peeked   = {"3rd": Lc1, "4th": None, "5th": None}
        known    = [Lh1, Lh2, Lc1, Lc2]
        current_total = ante + 0

    bet = strategy.get_bet([Lh1, Lh2], revealed, stage, ante, current_total, peeked)

    if bet == "fold":
        best = "fold"
    elif bet == 1:
        best = "1x"
    elif bet == 3:
        best = "3x"
    else:
        best = f"{bet}x" if isinstance(bet, int) else "fold"

    why = {
        "street": stage,
        "evaluation": _describe_partial(known),
        "ap_recommendation": f"AP3 says: {best}",
    }
    return best, {}, why, strategy

# --------------------------
# Felt + top layout
# --------------------------
def inject_table_css():
    felt_url = felt_data_url()
    felt_bg = f"url('{felt_url}')" if felt_url else "radial-gradient(1600px 800px at 50% 30%, #137a3a, #0b4f27 70%)"
    st.markdown(f"""
    <style>
      .felt {{
        position: relative; width: 100%; min-height: 560px;
        background-image: {felt_bg}; background-size: cover; background-position: center;
        border-radius: 16px; border: 2px solid #083a1c; box-shadow: inset 0 0 60px rgba(0,0,0,.25);
        padding: 24px 12px;
      }}
      .top {{ display: flex; flex-direction: column; gap: 16px; align-items: center; }}
      .row {{ display: flex; gap: 16px; align-items: center; justify-content: center; width: 100%; }}
      .row.player {{ gap: 24px; }}
      .card-img {{ width: {CELL_W*2}px; height: {CELL_H*2}px; image-rendering: pixelated;
                   border-radius: 10px; box-shadow: 0 8px 22px rgba(0,0,0,.35); }}

      .card {{
        position: relative;
        width: {CELL_W*2}px;
        height: {CELL_H*2}px;
        border-radius: 10px;
      }}
      .card-img {{
        width: 100%; height: 100%; image-rendering: pixelated;
        border-radius: inherit; box-shadow: 0 8px 22px rgba(0,0,0,.35);
        display: block;
      }}

      .card.peek::after {{
        content: "";
        position: absolute; inset: 0;
        border-radius: inherit;
        pointer-events: none;
        background:
          linear-gradient(120deg, rgba(255,255,255,0.00) 30%, rgba(255,255,255,0.35) 45%, rgba(255,255,255,0.00) 60%) 0 0 / 200% 100% no-repeat,
          rgba(255,255,255,0.18);
        animation: sheen-move 2.4s linear infinite;
      }}
      @keyframes sheen-move {{
        0%   {{ background-position: -150% 0, 0 0; }}
        100% {{ background-position: 150% 0, 0 0; }}
      }}

      .card.peek::before {{
        content: "PEEK";
        position: absolute; top: 6px; left: 8px;
        font-size: 10px; font-weight: 800; letter-spacing: .5px;
        padding: 2px 6px; border-radius: 6px;
        background: rgba(0,0,0,.55); color: #fff;
        pointer-events: none;
      }}

      .spot {{ width: 96px; height: 96px; border-radius: 50%;
               border: 3px dashed rgba(255,255,255,.45); background: rgba(255,255,255,.08);
               color: #fff; display: flex; align-items: center; justify-content: center;
               font-weight: 800; letter-spacing: 1px; text-transform: uppercase;
               text-shadow: 0 1px 0 rgba(0,0,0,.5); }}
      .spot.small {{ width: 72px; height: 72px; font-size: 12px; }}
      .glow {{ box-shadow: 0 0 0 3px rgba(255,255,255,.35), 0 0 20px rgba(255,255,255,.35) !important; }}

      /* --- Success toast (top-right, 5s fade) --- */
    .ap-toast {{
        position: fixed;
        top: 60px;        /* was 20px */
        right: 20px;
        margin-top: 0;    /* optional, can be 10–15px if you prefer */
        z-index: 9999;
        background: rgba(28, 141, 64, .95);
        color: #fff;
        padding: 12px 16px;
        border-radius: 12px;
        box-shadow: 0 8px 22px rgba(0,0,0,.25);
        font-weight: 700;
        max-width: 360px;
        line-height: 1.25;
        opacity: 0;
        transform: translateY(-6px);
        animation: ap-toast-inout 5s ease forwards;
        pointer-events: none;
        }}
    .ap-toast small {{ display:block; opacity:.9; font-weight:600; margin-top:6px; }}
    @keyframes ap-toast-inout {{
        0%   {{ opacity: 0; transform: translateY(-6px); }}
        8%   {{ opacity: 1; transform: translateY(0); }}
        80%  {{ opacity: 1; transform: translateY(0); }}
        100% {{ opacity: 0; transform: translateY(-6px); }}
    }}

    </style>
    """, unsafe_allow_html=True)

def show_success_toast(best_action: str, why: dict):
    details = []
    if why:
        if 'evaluation' in why: details.append(f"**Why** — {why['evaluation']}")
        if 'ap_recommendation' in why: details.append(why['ap_recommendation'])
    html = f"""
    <div class="ap-toast">
      ✅ Correct: <strong>{best_action}</strong> is the AP play.
      <small>{'  •  '.join(details)}</small>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_table_top(h1: CardUI, h2: CardUI, c1: CardUI, c2: CardUI, c3: CardUI, stage: str):
    inject_table_css()
    # Visibility rules
    c1_src = card_data_url_ui(c1, 2)  # c1 face-up always for our trainer view
    c2_src = card_data_url_ui(c2, 2) if stage == "5th" or stage == "f" else back_data_url(2)
    c3_src = card_data_url_ui(c3, 2) if stage == "f" else back_data_url(2)         # stays down during 5th action

    h1_src = card_data_url_ui(h1, 2)
    h2_src = card_data_url_ui(h2, 2)

    # Active street glow
    glow3 = "glow" if stage == "3rd" else ""
    glow4 = "glow" if stage == "4th" else ""
    glow5 = "glow" if stage == "5th" else ""

    # Apply the peek sheen only on 3rd street
    peek_cls = "peek" if stage == "3rd" else ""

    # html = f"""
    # <div class="felt">
    #   <div class="top">
    #     <!-- row 1: community cards -->
    #     <div class="row community">
    #       <img class="card-img" src="{c1_src}" />
    #       <img class="card-img" src="{c2_src}" />
    #       <img class="card-img" src="{c3_src}" />
    #     </div>
    #     <!-- row 2: ante -->
    #     <div class="row ante"><div class="spot">ANTE</div></div>
    #     <!-- row 3: street spots -->
    #     <div class="row streets">
    #       <div class="spot small {glow3}">3RD</div>
    #       <div class="spot small {glow4}">4TH</div>
    #       <div class="spot small {glow5}">5TH</div>
    #     </div>
    #     <!-- row 4: player cards -->
    #     <div class="row player">
    #       <img class="card-img" src="{h1_src}" />
    #       <img class="card-img" src="{h2_src}" />
    #     </div>
    #   </div>
    # </div>
    # """

    html = f"""
    <div class="felt">
      <div class="top">
        <!-- row 1: community cards -->
        <div class="row community">
          <div class="card {peek_cls}"><img class="card-img" src="{c1_src}" /></div>
          <div class="card"><img class="card-img" src="{c2_src}" /></div>
          <div class="card"><img class="card-img" src="{c3_src}" /></div>
        </div>
        <!-- row 2: ante -->
        <div class="row ante"><div class="spot">ANTE</div></div>
        <!-- row 3: street spots -->
        <div class="row streets">
          <div class="spot small {glow3}">3RD</div>
          <div class="spot small {glow4}">4TH</div>
          <div class="spot small {glow5}">5TH</div>
        </div>
        <!-- row 4: player cards -->
        <div class="row player">
          <div class="card"><img class="card-img" src="{h1_src}" /></div>
          <div class="card"><img class="card-img" src="{h2_src}" /></div>
        </div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# --------------------------
# Streamlit app state
# --------------------------
st.set_page_config(page_title="Mississippi Stud — AP3 Trainer", page_icon="🂠", layout="centered")


# ---- Incorrect-answer modal ----
@st.dialog("Incorrect decision")
def incorrect_modal():
    st.error("❌ Not quite.")
    w = st.session_state.get("why", {})
    if w:
        st.markdown(
            f"**Street:** {w.get('street','?')}  \n"
            f"**Evaluation:** {w.get('evaluation','–')}  \n"
            f"**AP:** {w.get('ap_recommendation','–')}"
        )
    st.markdown("---")
    # One primary action: new round
    if st.button("Deal Next Hand", type="primary"):
        # Close dialog & reset round
        st.session_state.show_incorrect_modal = False
        # reuse your existing helper
        deal_next()

def get_payout(h1: CardUI, h2: CardUI, c1: CardUI, c2: CardUI, c3: CardUI, current_total: int) -> int:
    """Calculate payout based on the final hand."""
    # Convert to LibCard for evaluation
    Lh1, Lh2, Lc1, Lc2, Lc3 = map(to_lib, [h1,h2,c1,c2,c3])
    final_hand = [Lh1, Lh2, Lc1, Lc2, Lc3]
    payout = ms_sim.get_payout_multiplier(evaluate_mississippi_stud_hand(final_hand))
    if payout == "push":
        return current_total  # no loss, no gain
    else:
        if isinstance(payout, str):
            raise ValueError(f"Unexpected payout type: {payout}")
    if payout == 0:
        return 0
    else:
        return payout * current_total + current_total

def start_new_hand():
    h1, h2, c1, c2, c3 = sample_cards(5)
    st.session_state.hand = {"h1":h1, "h2":h2, "c1":c1, "c2":c2, "c3":c3}
    st.session_state.stage = "3rd"        # action street
    st.session_state.feedback = ""
    st.session_state.show_why = False
    st.session_state.why = {}
    st.session_state.evs = {}
    st.session_state.strategy = AdvantagePlay3rdStrategy()  # reset strategy instance
    # scoring
    st.session_state.hands_played = st.session_state.get("hands_played", 0)
    st.session_state.score = st.session_state.get("score", 0)
    st.session_state.streak = st.session_state.get("streak", 0)
    st.session_state.current_total = ANTE   # current total bet (ante only for 3rd street)
    st.session_state.bankroll = st.session_state.get("bankroll", 10000) - ANTE

    if "start_time" not in st.session_state:
        st.session_state.start_time = time.time()

    st.session_state.show_incorrect_modal = False
    st.session_state.last_correct = None

    st.session_state.toast_until = 0
    st.session_state.toast = None

if "hand" not in st.session_state:
    start_new_hand()

print("Starting Mississippi Stud AP3 Trainer...")
st.title("Mississippi Stud — AP3 Trainer")
st.caption("Advantage Play 3rd‑street hole‑card trainer with correct multi‑street flow.")

# after title/caption and before the table is fine
now = time.time()
toast = st.session_state.get("toast")
toast_until = st.session_state.get("toast_until", 0)
if toast and now < toast_until:
    show_success_toast(toast["best_action"], toast["why"])
elif toast and now >= toast_until:
    # auto-clear once expired
    st.session_state.toast = None

# Score row
cA, cB, cC, cD = st.columns(4)
with cA: st.metric("Score", st.session_state.score)
with cB: st.metric("Streak", st.session_state.streak)
with cC:
    elapsed = int(time.time() - st.session_state.start_time)
    st.metric("Time (min)", f"{elapsed//60}:{elapsed%60:02d}")
with cD: st.metric("Bankroll", st.session_state.bankroll)

# Unpack current hand & stage
h = st.session_state.hand
stage = st.session_state.stage
h1, h2, c1, c2, c3 = h["h1"], h["h2"], h["c1"], h["c2"], h["c3"]

# Table
st.subheader("Table")
render_table_top(h1, h2, c1, c2, c3, stage)

# Decision for current stage (not revealed until user acts)
print(f"Cards: h1={h1}, h2={h2}, c1={c1}, c2={c2}, c3={c3}")

if stage != "f":  # not final stage
    best_action, evs, why, strategy = ap3_decision(stage, h1, h2, c1, c2, c3, strategy=st.session_state.strategy)
    st.session_state.strategy = strategy  # update strategy instance in session state
    if st.session_state.get("show_incorrect_modal"):
        incorrect_modal()

# Action buttons
st.markdown(f"### Choose your action — **{stage.upper()} street**")
cols = st.columns(3)
choice = None
if cols[0].button("Fold"): choice = "fold"
if cols[1].button("Bet 1x"): choice = "1x"
if cols[2].button("Bet 3x"): choice = "3x"

def deal_next():
    start_new_hand()
    print('Dealing next hand...')
    st.rerun()

if choice is not None:
    st.session_state.hands_played += 1
    correct = (choice == best_action)
    st.session_state.last_correct = correct

    # bankroll update
    if choice == "fold":
        st.session_state.bankroll -= st.session_state.current_total

    elif choice == "1x":
        st.session_state.current_total += ANTE
        st.session_state.bankroll -= ANTE
    else:
        st.session_state.current_total += 3 * ANTE
        st.session_state.bankroll -= 3 * ANTE

    # stash "why"/evs regardless
    st.session_state.why = why
    st.session_state.evs = evs
    st.session_state.show_why = True

    # handling training part
    if correct:
        # scoring updates
        st.session_state.score += 1
        st.session_state.streak += 1

        # persist toast for 5 seconds across reruns
        st.session_state.toast = {"best_action": best_action, "why": why}
        st.session_state.toast_until = time.time() + 5

        # Advance AP3 flow (do NOT redeal)
        if choice == "fold":
            deal_next()
        else:
            if stage == "3rd":
                st.session_state.stage = "4th"
            elif stage == "4th":
                st.session_state.stage = "5th"
            else:  # "5th"
                # optional: move to a brief "final reveal" state, then Next Hand
                st.session_state.stage = "f"
                st.session_state.bankroll += get_payout(h1, h2, c1, c2, c3, st.session_state.current_total)
            st.rerun()

    else:
        # incorrect -> block progress with a modal
        st.session_state.streak = 0
        st.session_state.show_incorrect_modal = True
        # Open the modal immediately on this click
        incorrect_modal()
        # Prevent any further UI from rendering underneath
        st.stop()

# Feedback + Why
# if st.session_state.feedback:
#     st.info(st.session_state.feedback)

# (Optional) remove old generic info banner:
# if st.session_state.feedback:
#     st.info(st.session_state.feedback)

# Keep a static "Why" section if you still want it below the table.
# st.markdown("### Why (AP3 reference)")
# if st.session_state.show_why and isinstance(st.session_state.why, dict) and st.session_state.why:
#     w = st.session_state.why
#     st.markdown(
#         f"**Street:** {w.get('street','?')}  \n"
#         f"**Evaluation:** {w.get('evaluation','–')}  \n"
#         f"**AP:** {w.get('ap_recommendation','–')}"
#     )
# else:
#     st.markdown("_Explanation will appear after you act._")

st.divider()
st.button("Deal Next Hand", on_click=deal_next, type="primary")
