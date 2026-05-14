import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Configurazione stile Generali
st.set_page_config(page_title="Simulatore Conflitti Generali", layout="centered")

# CSS per lo sfondo rosso leggero e pulsanti rossi
st.markdown("""
    <style>
    .stApp {
        background-color: #fdf2f2;
    }
    .stButton>button {
        background-color: #C52228;
        color: white;
        border-radius: 5px;
    }
    h1, h2, h3 {
        color: #C52228;
    }
    </style>
    """, unsafe_allow_html=True)

# Funzione per caricare i dati dall'Excel
@st.cache_data
def load_data():
    try:
        # Carica i due fogli dall'Excel
        attivi = pd.read_excel("prodotti.xlsx", sheet_name="Attivi")
        ptf = pd.read_excel("prodotti.xlsx", sheet_name="PTF")
        
        # Trasforma in dizionari (pulendo eventuali spazi nei nomi colonne)
        dict_attivi = dict(zip(attivi['prodotto'].str.strip(), attivi['categoria'].str.strip()))
        dict_ptf = dict(zip(ptf['prodotto'].str.strip(), ptf['categoria'].str.strip()))
        return dict_attivi, dict_ptf
    except Exception as e:
        st.error(f"Errore nel caricamento del file prodotti.xlsx: {e}")
        return {}, {}

prodotti_attivi, prodotti_ptf = load_data()

st.title("🔴 Simulatore Conflitto di Interessi")
st.write("Struttura basata sui criteri di conformità per nuove emissioni.")

if not prodotti_attivi:
    st.info("In attesa del file prodotti.xlsx su GitHub...")
    st.stop()

# --- INTERFACCIA ---
st.subheader("1. Selezione Prodotto")
nuovo_prodotto = st.selectbox("Cosa vuoi proporre al cliente?", options=[""] + list(prodotti_attivi.keys()))

st.info("ℹ️ Verifica anche l'IBAN di accredito per identificare eventuali riscatti collegati.")

st.subheader("2. Eventi Precedenti")
if 'eventi' not in st.session_state:
    st.session_state.eventi = []

col_a, col_b = st.columns(2)
with col_a:
    if st.button("+ Riscatto"):
        st.session_state.eventi.append({"tipo": "Riscatto", "data": datetime.now()})
with col_b:
    if st.button("+ Risoluzione/Sospensione"):
        st.session_state.eventi.append({"tipo": "Risoluzione", "data": datetime.now()})

eventi_validi = []
for i, ev in enumerate(st.session_state.eventi):
    with st.expander(f"{ev['tipo']} #{i+1}", expanded=True):
        c1, c2, c3 = st.columns([2, 1, 0.5])
        nome_v = c1.selectbox(f"Prodotto vecchio", options=[""] + sorted(list(prodotti_ptf.keys())), key=f"n_{i}")
        data_v = c2.date_input(f"Data", value=ev['data'], key=f"d_{i}")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.eventi.pop(i)
            st.rerun()
        if nome_v:
            eventi_validi.append({"nome": nome_v, "data": data_v, "cat": prodotti_ptf[nome_v]})

st.markdown("---")

if st.button("ESEGUI VERIFICA", use_container_width=True):
    if not nuovo_prodotto:
        st.warning("Seleziona prima il prodotto di interesse.")
    else:
        cat_nuovo = prodotti_attivi[nuovo_prodotto].lower()
        conflitto = False
        data_max = None
        dettaglio_conflitto = ""

        for ev in eventi_validi:
            cat_v = ev['cat'].lower()
            d_v = datetime.combine(ev['data'], datetime.min.time())
            if data_max is None or d_v > data_max:
                data_max = d_v

            # REGOLE
            if cat_nuovo == "protezione" and cat_v == "protezione": conflitto = True
            elif cat_nuovo == "previdenza" and cat_v == "previdenza": conflitto = True
            elif cat_nuovo == "investimento" and cat_v == "investimento": conflitto = True
            elif cat_nuovo == "risparmio" and (cat_v == "investimento" or cat_v == "risparmio"): conflitto = True
            
            if conflitto:
                dettaglio_conflitto = f"Conflitto tra categoria {cat_nuovo.upper()} e prodotto vecchio {ev['nome']} ({cat_v.upper()})"
                break

        if conflitto:
            st.error(f"### ❌ NON PROCEDIBILE\n{dettaglio_conflitto}")
        else:
            st.success("### ✅ PROCEDIBILE")

        # Analisi disponibilità complessiva
        cats_inserite = [ev['cat'].lower() for ev in eventi_validi]
        disponibili = []
        bloccati = []

        for p, c in prodotti_attivi.items():
            c_l = c.lower()
            ok = True
            if c_l == "protezione" and "protezione" in cats_inserite: ok = False
            elif c_l == "previdenza" and "previdenza" in cats_inserite: ok = False
            elif c_l == "investimento" and "investimento" in cats_inserite: ok = False
            elif c_l == "risparmio" and ("investimento" in cats_inserite or "risparmio" in cats_inserite): ok = False
            
            if ok: disponibili.append(p)
            else: bloccati.append(p)

        st.write("**Prodotti che puoi fare oggi:**")
        st.write(", ".join(disponibili) if disponibili else "Nessuno")

        if bloccati and data_max:
            sblocco = data_max + timedelta(days=367)
            st.warning(f"**Prodotti disponibili dal {sblocco.strftime('%d/%m/%Y')}:**")
            st.write(", ".join(bloccati))

st.markdown("---")
st.caption("⚠️ Questo simulatore non fornisce elemento certo e non è perfetto, non verifica ad esempio le componenti protection.")