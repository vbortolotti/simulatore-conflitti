import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Configurazione Pagina
st.set_page_config(page_title="Simulatore Conflitti Generali", layout="centered")

# CSS Avanzato per forzare la visibilità in Dark Mode e Light Mode
st.markdown("""
    <style>
    /* Sfondo rosso leggero generale */
    .stApp {
        background-color: #fdf2f2 !important;
    }
    
    /* Forza il colore del testo principale a Nero per leggibilità */
    .stApp p, .stApp span, .stApp label, .stMarkdown {
        color: #1a1a1a !important;
    }

    /* Stile Titoli */
    h1, h2, h3 {
        color: #C52228 !important;
        font-weight: bold;
    }

    /* Personalizzazione Pulsanti */
    .stButton>button {
        background-color: #C52228 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        padding: 0.5rem 1rem !important;
    }

    /* Colore testo all'interno dei menu a tendina (Selectbox) */
    div[data-baseweb="select"] > div {
        background-color: white !important;
        color: black !important;
    }
    
    /* Stile per i messaggi di successo/errore per contrasto */
    .stAlert {
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        xls = pd.ExcelFile("prodotti.xlsx")
        attivi = pd.read_excel(xls, sheet_name="Attivi")
        ptf = pd.read_excel(xls, sheet_name="PTF")
        attivi.columns = [c.strip().lower() for c in attivi.columns]
        ptf.columns = [c.strip().lower() for c in ptf.columns]
        dict_attivi = dict(zip(attivi['prodotto'].astype(str).str.strip(), attivi['categoria'].astype(str).str.strip()))
        dict_ptf = dict(zip(ptf['prodotto'].astype(str).str.strip(), ptf['categoria'].astype(str).str.strip()))
        return dict_attivi, dict_ptf
    except Exception as e:
        st.error(f"Errore caricamento Excel: {e}")
        return {}, {}

prodotti_attivi, prodotti_ptf = load_data()

st.title("🔴 Simulatore Conflitti Generali")

if not prodotti_attivi:
    st.warning("Assicurati di aver caricato 'prodotti.xlsx' con i fogli 'Attivi' e 'PTF'.")
    st.stop()

# --- INTERFACCIA ---
st.subheader("1. Selezione Prodotto")
nuovo_prodotto = st.selectbox("Cosa vuoi proporre al cliente?", options=[""] + sorted(list(prodotti_attivi.keys())))

st.info("⚠️ NOTA: Verifica anche l'IBAN di accredito per identificare eventuali riscatti collegati.")

st.subheader("2. Eventi Precedenti")
if 'eventi' not in st.session_state:
    st.session_state.eventi = []

c1, c2 = st.columns(2)
with c1:
    if st.button("+ Aggiungi Riscatto"):
        st.session_state.eventi.append({"tipo": "Riscatto", "data": datetime.now()})
with c2:
    if st.button("+ Aggiungi Risoluzione"):
        st.session_state.eventi.append({"tipo": "Risoluzione", "data": datetime.now()})

eventi_validi = []
for i, ev in enumerate(st.session_state.eventi):
    with st.expander(f"Dettaglio {ev['tipo']} #{i+1}", expanded=True):
        col_a, col_b, col_c = st.columns([2, 1, 0.5])
        nome_v = col_a.selectbox(f"Prodotto vecchio", options=[""] + sorted(list(prodotti_ptf.keys())), key=f"n_{i}")
        data_v = col_b.date_input(f"Data", value=ev['data'], key=f"d_{i}")
        if col_c.button("🗑️", key=f"del_{i}"):
            st.session_state.eventi.pop(i)
            st.rerun()
        if nome_v:
            eventi_validi.append({"nome": nome_v, "data": data_v, "cat": prodotti_ptf[nome_v]})

st.markdown("---")

if st.button("VERIFICA FATTIBILITÀ", use_container_width=True):
    if not nuovo_prodotto:
        st.warning("Seleziona prima il prodotto di interesse.")
    else:
        cat_nuovo = prodotti_attivi[nuovo_prodotto].lower()
        conflitto = False
        data_max = None
        dettaglio = ""

        for ev in eventi_validi:
            cat_v = ev['cat'].lower()
            d_v = datetime.combine(ev['data'], datetime.min.time())
            if data_max is None or d_v > data_max:
                data_max = d_v

            # REGOLE DI CONFLITTO
            if cat_nuovo == "protezione" and cat_v == "protezione": conflitto = True
            elif cat_nuovo == "previdenza" and cat_v == "previdenza": conflitto = True
            elif cat_nuovo == "investimento" and cat_v == "investimento": conflitto = True
            elif cat_nuovo == "risparmio" and (cat_v == "investimento" or cat_v == "risparmio"): conflitto = True
            
            if conflitto:
                dettaglio = f"Conflitto rilevato: {nuovo_prodotto} ({cat_nuovo.upper()}) vs {ev['nome']} ({cat_v.upper()})"
                break

        if conflitto:
            st.error(f"### ❌ NON PROCEDIBILE\n{dettaglio}")
        else:
            st.success("### ✅ PROCEDIBILE")

        # Liste disponibilità
        cats_inserite = [ev['cat'].lower() for ev in eventi_validi]
        disp, blocc = [], []
        for p, c in prodotti_attivi.items():
            c_l = c.lower()
            ok = True
            if c_l == "protezione" and "protezione" in cats_inserite: ok = False
            elif c_l == "previdenza" and "previdenza" in cats_inserite: ok = False
            elif c_l == "investimento" and "investimento" in cats_inserite: ok = False
            elif c_l == "risparmio" and ("investimento" in cats_inserite or "risparmio" in cats_inserite): ok = False
            if ok: disp.append(p)
            else: blocc.append(p)

        st.write("**Prodotti sottoscrivibili oggi:**")
        st.write(", ".join(disp) if disp else "Nessuno")

        if blocc and data_max:
            sblocco = data_max + timedelta(days=367)
            st.warning(f"**Disponibili dal {sblocco.strftime('%d/%m/%Y')}:**")
            st.write(", ".join(blocc))

st.markdown("---")
st.caption("ℹ️ Questo simulatore non fornisce elemento certo e non è perfetto, non verifica ad esempio le componenti protection.")
