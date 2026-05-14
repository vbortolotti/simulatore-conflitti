import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Simulatore Conflitti", layout="centered")

# CSS: FORZATURA TESTO NERO E COLORI RICHIESTI
st.markdown("""
    <style>
    .stApp { background-color: #fdf2f2 !important; }
    .stApp p, .stApp span, .stApp label, .stMarkdown, h1, h2, h3, h4 { color: #000000 !important; }

    /* FORZATURA TESTO NERO NEI CAMPI BIANCHI */
    input { color: #000000 !important; -webkit-text-fill-color: #000000 !important; }
    div[data-baseweb="select"] * { color: #000000 !important; }
    div[role="listbox"] * { color: #000000 !important; }
    .stDateInput div { color: #000000 !important; }

    /* BOX NOTA: Azzurro con contorno Blu */
    .nota-box {
        background-color: #e1f5fe !important;
        border: 2px solid #01579b !important;
        padding: 12px !important;
        border-radius: 8px !important;
        margin: 10px 0px !important;
        font-weight: 500;
    }

    /* PULSANTI AGGIUNGI: Azzurro Cielo */
    button[kind="secondary"] {
        background-color: #00b0ff !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: bold !important;
    }

    /* PULSANTE VERIFICA: Verde Prato Chiaro */
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
    st.warning("Assicurati di caricare 'prodotti.xlsx'.")
    st.stop()

# 1. Selezione Prodotto
st.write("ciao inserisci il prodotto che vuoi fare")
nuovo_prodotto = st.selectbox("Scegli prodotto", options=[""] + sorted(list(prodotti_attivi.keys())), label_visibility="collapsed")

# NOTA AZZURRA
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

# Gestione Riscatti
for i, r in enumerate(st.session_state.ev_r):
    c1, c2, c3 = st.columns([1.5, 1.5, 0.4])
    p = c1.selectbox(f"Seleziona Prodotto Riscatto #{i+1}", [""] + sorted(list(prodotti_ptf.keys())), key=f"pr_{i}")
    d = c2.date_input(f"Data liquidazione riscatto", value=r['data'], key=f"dr_{i}")
    if c3.button("🗑️", key=f"delr_{i}"):
        st.session_state.ev_r.pop(i)
        st.rerun()
    if p:
        data_evento = datetime.combine(d, datetime.min.time())
        # Ignora se sono già passati 367 giorni
        if (data_evento + timedelta(days=367)) > oggi:
            tutti_eventi.append({"cat": prodotti_ptf[p], "data": d})

# Gestione Risoluzioni
for i, s in enumerate(st.session_state.ev_s):
    c1, c2, c3 = st.columns([1.5, 1.5, 0.4])
    p = c1.selectbox(f"Seleziona Prodotto Risoluzione #{i+1}", [""] + sorted(list(prodotti_ptf.keys())), key=f"ps_{i}")
    d = c2.date_input(f"Data interruzione polizza", value=s['data'], key=f"ds_{i}")
    if c3.button("🗑️", key=f"dels_{i}"):
        st.session_state.ev_s.pop(i)
        st.rerun()
    if p:
        data_evento = datetime.combine(d, datetime.min.time())
        # Ignora se sono già passati 367 giorni
        if (data_evento + timedelta(days=367)) > oggi:
            tutti_eventi.append({"cat": prodotti_ptf[p], "data": d})

st.markdown("---")

# 3. VERIFICA
if st.button("VERIFICA", type="primary"):
    if nuovo_prodotto:
        cat_n = prodotti_attivi[nuovo_prodotto].lower()
        date_per_cat = {}
        bloccato = False
        
        for ev in tutti_eventi:
            cv = ev['cat'].lower()
            dv = datetime.combine(ev['data'], datetime.min.time())
            if cv not in date_per_cat or dv > date_per_cat[cv]: date_per_cat[cv] = dv
            
            if (cat_n == "protezione" and cv == "protezione") or \
               (cat_n == "previdenza" and cv == "previdenza") or \
               (cat_n == "investimento" and cv == "investimento") or \
               (cat_n == "risparmio" and (cv == "investimento" or cv == "risparmio")):
                bloccato = True

        st.write("#### risultato")
        if bloccato:
            st.error(f"Per il prodotto {nuovo_prodotto} l'esito è: **NON PROCEDIBILE**")
        else:
            st.success(f"Per il prodotto {nuovo_prodotto} l'esito è: **PROCEDIBILE**")

        st.markdown("**per il prodotto che hai scelto è possibile fare i seguenti prodotti**")
        disp, blocchi = [], {}

        for p, c in prodotti_attivi.items():
            cl = c.lower()
            m_data = None
            for cv, dv in date_per_cat.items():
                conf = False
                if (cl == "protezione" and cv == "protezione") or \
                   (cl == "previdenza" and cv == "previdenza") or \
                   (cl == "investimento" and cv == "investimento") or \
                   (cl == "risparmio" and (cv == "investimento" or cv == "risparmio")):
                    conf = True
                if conf:
                    data_sblocco = dv + timedelta(days=367)
                    if data_sblocco > oggi:
                        ds_str = data_sblocco.strftime("%d/%m/%Y")
                        if m_data is None or data_sblocco > datetime.strptime(m_data, "%d/%m/%Y"):
                            m_data = ds_str
            
            if not m_data: disp.append(p)
            else:
                if m_data not in blocchi: blocchi[m_data] = []
                blocchi[m_data].append(p)

        st.write(", ".join(disp) if disp else "Nessuno")
        st.markdown("---")
        if blocchi:
            st.write("**i seguenti prodotti saranno disponibili dopo la data riportata**")
            for d_s, prods in blocchi.items():
                st.info(f"Dal {d_s}: " + ", ".join(prods))
        else:
            st.write("_Nessun blocco attivo per il futuro._")

st.markdown("<br><br><small>Questo simulatore non fornisce elemento certo e non è perfetto.</small>", unsafe_allow_html=True)
