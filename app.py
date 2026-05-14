import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Simulatore Conflitti", layout="centered")

# CSS: Stile fedele all'immagine, testi neri e colori vivaci
st.markdown("""
    <style>
    .stApp { background-color: #fdf2f2 !important; }
    .stApp p, .stApp span, .stApp label, .stMarkdown, h1, h2, h3, h4 { color: #000000 !important; }

    /* Forzatura testo nero nei campi bianchi */
    input { color: #000000 !important; -webkit-text-fill-color: #000000 !important; }
    div[data-baseweb="select"] * { color: #000000 !important; }
    div[role="listbox"] * { color: #000000 !important; }
    .stDateInput div { color: #000000 !important; }

    /* Box Nota Azzurra */
    .nota-box {
        background-color: #e1f5fe !important;
        border: 2px solid #01579b !important;
        padding: 12px !important;
        border-radius: 8px !important;
        margin: 10px 0px !important;
        font-weight: 500;
    }

    /* Pulsanti Aggiungi: Azzurro Cielo */
    button[kind="secondary"] {
        background-color: #00b0ff !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: bold !important;
    }

    /* Pulsante Verifica: Verde Prato Chiaro */
    button[kind="primary"] {
        background-color: #76ff03 !important;
        color: black !important;
        border: 2px solid #64dd17 !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
        width: 100% !important;
    }

    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
        background-color: white !important;
        border: 1px solid #cccccc !important;
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
    except:
        return {}, {}

prodotti_attivi, prodotti_ptf = load_data()
oggi = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

st.write("### Simulatore Conflitti")

if not prodotti_attivi:
    st.warning("Carica il file prodotti.xlsx per procedere.")
    st.stop()

# 1. Selezione Prodotto
st.write("ciao inserisci il prodotto che vuoi fare")
nuovo_prodotto = st.selectbox("Scegli prodotto", options=[""] + sorted(list(prodotti_attivi.keys())), label_visibility="collapsed")

st.markdown('<div class="nota-box">Nota: RICORDATI DI CONTROLLARE ANCHE I RISCATTI CHE HANNO AVUTO IN COMUNE L\'IBAN</div>', unsafe_allow_html=True)

st.markdown("---")

# 2. Eventi Precedenti
st.write("### 2 Eventi precedenti")
if 'ev_r' not in st.session_state: st.session_state.ev_r = []
if 'ev_s' not in st.session_state: st.session_state.ev_s = []

col1, col2 = st.columns(2)
with col1:
    if st.button("+aggiungi riscatto", type="secondary"):
        st.session_state.ev_r.append({"data": datetime.now()})
with col2:
    if st.button("+aggiungi risoluzione o sospese", type="secondary"):
        st.session_state.ev_s.append({"data": datetime.now()})

tutti_eventi = []

# Funzione per filtrare date vecchie
def is_valid_conflict(date_input):
    return (datetime.combine(date_input, datetime.min.time()) + timedelta(days=367)) > oggi

for i, r in enumerate(st.session_state.ev_r):
    c1, c2, c3 = st.columns([1.5, 1.5, 0.4])
    p = c1.selectbox(f"Prodotto Riscatto #{i+1}", [""] + sorted(list(prodotti_ptf.keys())), key=f"pr_{i}")
    d = c2.date_input(f"Data liquidazione riscatto", value=r['data'], key=f"dr_{i}")
    if c3.button("🗑️", key=f"delr_{i}"):
        st.session_state.ev_r.pop(i)
        st.rerun()
    if p and is_valid_conflict(d):
        tutti_eventi.append({"cat": prodotti_ptf[p], "data": d})

for i, s in enumerate(st.session_state.ev_s):
    c1, c2, c3 = st.columns([1.5, 1.5, 0.4])
    p = c1.selectbox(f"Prodotto Risoluzione #{i+1}", [""] + sorted(list(prodotti_ptf.keys())), key=f"ps_{i}")
    d = c2.date_input(f"Data interruzione polizza", value=s['data'], key=f"ds_{i}")
    if c3.button("🗑️", key=f"dels_{i}"):
        st.session_state.ev_s.pop(i)
        st.rerun()
    if p and is_valid_conflict(d):
        tutti_eventi.append({"cat": prodotti_ptf[p], "data": d})

st.markdown("---")

# 3. VERIFICA
if st.button("VERIFICA", type="primary"):
    if nuovo_prodotto:
        cat_scelta = prodotti_attivi[nuovo_prodotto].lower()
        categorie_bloccate = {}
        for ev in tutti_eventi:
            cv = ev['cat'].lower()
            data_sblocco = datetime.combine(ev['data'], datetime.min.time()) + timedelta(days=367)
            if cv not in categorie_bloccate or data_sblocco > categorie_bloccate[cv]:
                categorie_bloccate[cv] = data_sblocco

        # Check prodotto scelto
        check_blocco = False
        if cat_scelta in categorie_bloccate: check_blocco = True
        elif cat_scelta == "risparmio" and "investimento" in categorie_bloccate: check_blocco = True

        st.write("#### Risultato Prodotto Selezionato")
        if check_blocco:
            st.error(f"Per il prodotto {nuovo_prodotto} l'esito è: **NON PROCEDIBILE**")
        else:
            st.success(f"Per il prodotto {nuovo_prodotto} l'esito è: **PROCEDIBILE**")

        st.markdown("---")

        # --- SEZIONE PRODOTTI DISPONIBILI (SUDDIVISI PER CATEGORIA) ---
        st.write("### ✅ SI - Prodotti Disponibili Oggi")
        
        prods_si = {"Protezione": [], "Previdenza": [], "Investimento": [], "Risparmio": []}
        prods_no = []

        for p, c in prodotti_attivi.items():
            cl = c.lower()
            m_data = None
            if cl in categorie_bloccate: m_data = categorie_bloccate[cl]
            elif cl == "risparmio" and "investimento" in categorie_bloccate: m_data = categorie_bloccate["investimento"]
            
            if m_data:
                prods_no.append({"prodotto": p, "categoria": c, "sblocco": m_data.strftime("%d/%m/%Y")})
            else:
                prods_si[c].append(p)

        # Mostra SI in colonne
        cols = st.columns(4)
        for i, (cat_name, list_p) in enumerate(prods_si.items()):
            with cols[i]:
                st.markdown(f"**{cat_name}**")
                if list_p:
                    for lp in list_p: st.write(f"- {lp}")
                else:
                    st.write("_Nessuno_")

        st.markdown("---")

        # --- SEZIONE PRODOTTI BLOCCATI (TABELLA) ---
        st.write("### ❌ NO - Prodotti Momentaneamente Bloccati")
        if prods_no:
            df_no = pd.DataFrame(prods_no)
            # Rinominiamo colonne per estetica
            df_no.columns = ["Prodotto", "Categoria", "Disponibile dal"]
            st.table(df_no)
        else:
            st.write("_Nessun prodotto bloccato._")

st.markdown("<br><br><small>Questo simulatore non fornisce elemento certo e non è perfetto.</small>", unsafe_allow_html=True)
