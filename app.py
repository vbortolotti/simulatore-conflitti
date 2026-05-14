import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Configurazione Pagina
st.set_page_config(page_title="Simulatore Conflitti", layout="centered")

# CSS: Sfondo rosa, nota azzurra/blu, pulsanti azzurri e verde chiaro
st.markdown("""
    <style>
    /* Sfondo rosa pesca dell'immagine */
    .stApp { background-color: #fdf2f2 !important; }
    
    /* Testi neri e forzatura colore nero negli input */
    .stApp p, .stApp span, .stApp label, .stMarkdown, h1, h2, h3, h4 { 
        color: #000000 !important; 
    }
    input { color: black !important; }
    div[data-baseweb="select"] div { color: black !important; }

    /* BOX NOTA: Azzurro con contorno Blu */
    .nota-box {
        background-color: #e1f5fe !important;
        border: 2px solid #01579b !important;
        padding: 10px !important;
        border-radius: 5px !important;
        margin-bottom: 20px !important;
        color: #000000 !important;
    }

    /* PULSANTI AGGIUNGI: Azzurro più scuro */
    .stButton>button[key^="add_"] {
        background-color: #0288d1 !important;
        color: white !important;
        border: none !important;
        border-radius: 5px !important;
        font-weight: bold !important;
    }

    /* TASTO VERIFICA: Verde chiaro */
    div.stButton > button:first-child[key="verify_btn"] {
        background-color: #90ee90 !important;
        color: black !important;
        border: 1px solid #7ccd7c !important;
        font-weight: bold !important;
        width: 100% !important;
        height: 3em !important;
    }

    /* Box bianchi per input */
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
        background-color: white !important;
        color: black !important;
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

st.title("Simulatore Conflitti")

if not prodotti_attivi:
    st.warning("Carica il file prodotti.xlsx per iniziare.")
    st.stop()

# --- SEZIONE 1 ---
st.write("ciao inserisci il prodotto che vuoi fare")
nuovo_prodotto = st.selectbox("", options=[""] + sorted(list(prodotti_attivi.keys())), label_visibility="collapsed")

# NOTA EVIDENZIATA
st.markdown('<div class="nota-box">Nota: RICORDATI DI CONTROLLARE ANCHE I RISCATTI CHE HANNO AVUTO IN COMUNE L\'IBAN</div>', unsafe_allow_html=True)

st.markdown("---")

# --- SEZIONE 2: EVENTI PRECEDENTI ---
st.write("### 2 Eventi precedenti")

# Liste per gestire gli eventi separatamente
if 'ev_r' not in st.session_state: st.session_state.ev_r = []
if 'ev_s' not in st.session_state: st.session_state.ev_s = []

col1, col2 = st.columns(2)
with col1:
    if st.button("+aggiungi riscatto", key="add_r"):
        st.session_state.ev_r.append({"data": datetime.now()})
with col2:
    if st.button("+aggiungi risoluzione o sospese", key="add_s"):
        st.session_state.ev_s.append({"data": datetime.now()})

# Visualizzazione dinamica eventi
tutti_eventi_input = []

for i, r in enumerate(st.session_state.ev_r):
    c1, c2, c3 = st.columns([2, 1, 0.5])
    p = c1.selectbox(f"Riscatto {i+1}", [""] + sorted(list(prodotti_ptf.keys())), key=f"pr_{i}")
    d = c2.date_input(f"Data riscatto {i}", value=r['data'], key=f"dr_{i}")
    if c3.button("🗑️", key=f"delr_{i}"):
        st.session_state.ev_r.pop(i)
        st.rerun()
    if p: tutti_eventi_input.append({"cat": prodotti_ptf[p], "data": d})

for i, s in enumerate(st.session_state.ev_s):
    c1, c2, c3 = st.columns([2, 1, 0.5])
    p = c1.selectbox(f"Risoluzione {i+1}", [""] + sorted(list(prodotti_ptf.keys())), key=f"ps_{i}")
    d = c2.date_input(f"Data risoluzione {i}", value=s['data'], key=f"ds_{i}")
    if c3.button("🗑️", key=f"dels_{i}"):
        st.session_state.ev_s.pop(i)
        st.rerun()
    if p: tutti_eventi_input.append({"cat": prodotti_ptf[p], "data": d})

st.markdown("---")

# --- VERIFICA ---
if st.button("VERIFICA", key="verify_btn"):
    if nuovo_prodotto:
        cat_n = prodotti_attivi[nuovo_prodotto].lower()
        
        date_per_cat = {}
        bloccato = False
        for ev in tutti_eventi_input:
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
                    ds = (dv + timedelta(days=367)).strftime("%d/%m/%Y")
                    if m_data is None or datetime.strptime(ds, "%d/%m/%Y") > datetime.strptime(m_data, "%d/%m/%Y"):
                        m_data = ds
            if not m_data: disp.append(p)
            else:
                if m_data not in blocchi: blocchi[m_data] = []
                blocchi[m_data].append(p)

        st.write(", ".join(disp) if disp else "Nessuno")
        st.markdown("---")
        st.markdown("**i seguenti prodotti saranno disponibili dopo la data riportata**")
        for d_s, prods in blocchi.items():
            st.info(f"Dal {d_s}: " + ", ".join(prods))

st.markdown("<br><br><small>Questo simulatore non fornisce elemento certo e non è perfetto.</small>", unsafe_allow_html=True)
