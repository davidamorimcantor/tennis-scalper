import time
import requests
import streamlit as st

REFRESH_SECONDS = 10  # intervalo de atualização

st.set_page_config(page_title="Tennis Scalper (beta)", layout="wide")
st.title("🎾 Tennis Scalper — dicas ao vivo (beta)")

RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_KEY", "")

if not RAPIDAPI_KEY:
    st.warning("Adicione RAPIDAPI_KEY nos Secrets para testar o app.")
    st.stop()

BASE_URL = "https://tennis-live-data.p.rapidapi.com"
HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "tennis-live-data.p.rapidapi.com"
}

@st.cache_data(ttl=15)
def get_live_matches():
    url = f"{BASE_URL}/matches/live"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()
    return data.get("results", [])

live_matches = get_live_matches()
if not live_matches:
    st.info("Sem partidas ao vivo agora. Tente mais tarde.")
    st.stop()

choices = {
    f"{m['tournament']['name']} — {m['player1']['name']} vs {m['player2']['name']} (id:{m['id']})": m['id']
    for m in live_matches if m.get("id")
}
selected_label = st.selectbox("Escolha um jogo ao vivo:", list(choices.keys()))
match_id = choices[selected_label]

def get_match_detail(mid):
    url = f"{BASE_URL}/match/{mid}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json().get("results", {})

placeholder = st.empty()

def make_tips(match):
    tips = []
    s1 = match.get("player1", {}).get("statistics", {})
    s2 = match.get("player2", {}).get("statistics", {})

    def safe_pct(a, b):
        try:
            return (a/b)*100 if b else 0
        except Exception:
            return 0

    p1_first_serve_in = safe_pct(s1.get("firstServeIn", 0), s1.get("firstServeTotal", 0))
    p2_first_serve_in = safe_pct(s2.get("firstServeIn", 0), s2.get("firstServeTotal", 0))
    p1_bp_saved = safe_pct(s1.get("breakPointsSaved", 0), s1.get("breakPointsFaced", 0))
    p2_bp_saved = safe_pct(s2.get("breakPointsSaved", 0), s2.get("breakPointsFaced", 0))

    score_text = match.get("live_score", "")
    if any(x in score_text for x in ["0-30", "15-40"]):
        tips.append("⚠️ Pressão no saque: possível oportunidade de lay no sacador.")

    streak = match.get("momentum", {}).get("current_streak", 0)
    if streak >= 3:
        tips.append("📈 Momentum: jogador com sequência ≥3 pontos — considerar back curto (scalp).")

    if p1_first_serve_in >= 65 and p2_first_serve_in <= 55:
        tips.append("🎯 Jogador 1 sólido no 1º saque; entradas a favor no seu game de saque.")
    if p2_first_serve_in >= 65 and p1_first_serve_in <= 55:
        tips.append("🎯 Jogador 2 sólido no 1º saque; entradas a favor no seu game de saque.")

    if p1_bp_saved >= 70:
        tips.append("🧱 Jogador 1 salva muitos break points (≥70%): cautela contra ele.")
    if p2_bp_saved >= 70:
        tips.append("🧱 Jogador 2 salva muitos break points (≥70%): cautela contra ele.")

    if not tips:
        tips.append("ℹ️ Sem padrão forte agora. Aguarde oportunidades.")
    return tips

while True:
    try:
        md = get_match_detail(match_id)
        with placeholder.container():
            c1, c2 = st.columns([2, 1])
            with c1:
                st.subheader("Placar ao vivo")
                st.write(md.get("live_score", "carregando…"))
                st.subheader("Dicas automáticas (beta)")
                for t in make_tips(md):
                    st.markdown("- " + t)
            with c2:
                st.subheader("Stats rápidos (estimados)")
                st.json({
                    "P1_first_serve_in_%": "...",
                    "P2_first_serve_in_%": "...",
                    "P1_break_points_saved_%": "...",
                    "P2_break_points_saved_%": "...",
                })
        time.sleep(REFRESH_SECONDS)
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")
        time.sleep(REFRESH_SECONDS)
