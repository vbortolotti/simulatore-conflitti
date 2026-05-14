import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Configurazione Pagina
st.set_page_config(page_title="Simulatore Conflitti", layout="centered")

# CSS: Sfondo rosa, testi neri, forzatura colore nero negli input/date
st.markdown("""
    <style>
    /* Sfondo rosa chiarissimo */
    .stApp { background-color: #fdf2f2 !important; }
    
    /* Testi neri ovunque */
    .stApp p, .stApp span, .stApp label, .stMarkdown, h1, h2, h3, h4 { 
        color: #000000 !important; 
        font-family: 'Segoe UI', sans-serif !important;
    }

    /* FORZATURA TESTO NERO NEGLI INPUT (Calendario e Selezioni) */
    input { color: black !important; }
    div[data-baseweb="select"] div { color: black !important; }
    div[data-baseweb="calendar"] { color: black !important; }
    
    /* Box bianchi per input e date */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div, 
    div[data-baseweb="popover"] {
        background-color: white !important;
        color: black !important;
        border: 1px solid #cccccc !important;
    }

    /* Pulsanti bianchi stile Excel */
    .stButton>button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
        border-radius: 4px !important;
        font-weight: normal !important;
        width: auto !important;
        padding: 2px 15px !important;
    }
    
    .stButton>button:hover {
        border: 1px solid #000000 !important;
        background-color: #f9f9f9 !important;
    }

    hr { border: 0.5px solid #dddddd !important; }
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

st.title("Simulatore Conflitti")

if not prodotti_attivi:
    st.warning("Carica il file prodotti.xlsx per visualizzare i dati.")
    st.stop()

# --- SEZIONE 1 ---
st.write("ciao inserisci il prodotto che vuoi fare")
nuovo_prodotto = st.selectbox("", options=[""] + sorted(list(prodotti_attivi.keys())), label_visibility="collapsed")

st.markdown("<br>", unsafe_allow_html=True)

# --- SEZIONE 2 ---
st.write("ci sono stati riscatti?")
if 'riscatti' not in st.session_state: st.session_state.riscatti = []
if st.button("+", key="add_r"):
    st.session_state.riscatti.append({"data": datetime.now()})

ev_riscatti = []
for i, r in enumerate(st.session_state.riscatti):
    c1, c2, c3 = st.columns([2, 1, 0.5])
    p = c1.selectbox(f"prodotto riscatto {i+1}", [""] + sorted(list(prodotti_ptf.keys())), key=f"pr_{i}", label_visibility="collapsed")
    d = c2.date_input(f"data liq {i}", value=r['data'], key=f"dr_{i}", label_visibility="collapsed")
    if c3.button("🗑️", key=f"delr_{i}"):
        st.session_state.riscatti.pop(i)
        st.rerun()
    if p: ev_riscatti.append({"cat": prodotti_ptf[p], "data": d})

st.markdown("<small>Nota: RICORDATI DI CONTROLLARE ANCHE I RISCATTI CHE HANNO AVUTO IN COMUNE L'IBAN</small>", unsafe_allow_html=True)
st.markdown("---")

# --- SEZIONE 3 ---
st.write("ci sono polizze in risoluzione o sospese?")
if 'risoluzioni' not in st.session_state: st.session_state.risoluzioni = []
if st.button("+", key="add_s"):
    st.session_state.risoluzioni.append({"data": datetime.now()})

ev_risoluzioni = []
for i, r in enumerate(st.session_state.risoluzioni):
    c1, c2, c3 = st.columns([2, 1, 0.5])
    p = c1.selectbox(f"prodotto risol {i+1}", [""] + sorted(list(prodotti_ptf.keys())), key=f"ps_{i}", label_visibility="collapsed")
    d = c2.date_input(f"data interr {i}", value=r['data'], key=f"ds_{i}", label_visibility="collapsed")
    if c3.button("🗑️", key=f"dels_{i}"):
        st.session_state.risoluzioni.pop(i)
        st.rerun()
    if p: ev_risoluzioni.append({"cat": prodotti_ptf[p], "data": d})

st.markdown("---")

# --- SEZIONE 4: RISULTATO ---
if st.button("VERIFICA"):
    if nuovo_prodotto:
        cat_n = prodotti_attivi[nuovo_prodotto].lower()
        tutti = ev_riscatti + ev_risoluzioni
        
        date_per_cat = {}
        bloccato = False
        for ev in tutti:
            cv = ev['cat'].lower()
            dv = datetime.combine(ev['data'], datetime.min.time())
            if cv not in date_per_cat or dv > date_per_cat[cv]: date_per_cat[cv] = dv
            
            if (cat_n == "protezione" and cv == "protezione") or \
               (cat_n == "previdenza" and cv == "previdenza") or \
               (cat_n == "investimento" and cv == "investimento") or \
               (cat_n == "risparmio" and (cv == "investimento" or cv == "risparmio")):
                bloccato = True

        st.markdown("### risultato")
        if bloccato:
            st.error(f"Per il prodotto {nuovo_prodotto} l'esito è: **NON PROCEDIBILE**")
        else:
            st.success(f"Per il prodotto {nuovo_prodotto} l'esito è: **PROCEDIBILE**")

        st.markdown("**per il prodotto che hai scelto è possibile fare i seguenti prodotti**")
        disponibili = []
        blocchi = {}

        for p, c in prodotti_attivi.items():
            cl = c.lower()
            m_data = None
            for cv, dv in date_per_cat.items():
                conf = False
                if (cl == "protezione" and cv == "protezione") or \
                   (cl == "previdenza" and cv == "previdenza") or \
                   (cl == "investimento" and cv == "investimento") or \
                   (cl == "risparmio" and (cl == "risparmio" and (cv == "investimento" or cv == "risparmio"))):
                    conf = True
                
                if conf:
                    ds = (dv + timedelta(days=367)).strftime("%d/%m/%Y")
                    if m_data is None or datetime.strptime(ds, "%d/%m/%Y") > datetime.strptime(m_data, "%d/%m/%Y"):
                        m_data = ds
            
            if not m_data: disponibili.append(p)
            else:
                if m_data not in blocchi: blocchi[m_data] = []
                blocchi[m_data].append(p)

        st.write(", ".join(disponibili) if disponibili else "Nessuno")

        st.markdown("---")
        st.markdown("**i seguenti prodotti saranno disponibili dopo la data riportata**")
        for d_s, prods in blocchi.items():
            st.info(f"Dal {d_s}: " + ", ".join(prods))

st.markdown("<br><br><small>Questo simulatore non fornisce elemento certo e non è perfetto, non verifica ad esempio le componenti protection.</small>", unsafe_allow_html=True)
