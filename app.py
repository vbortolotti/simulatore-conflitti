import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Configurazione Pagina
st.set_page_config(page_title="Simulatore Conflitti", layout="centered")

# CSS: Copia fedele dello stile dell'immagine (sfondo pesca, testi neri, pulsanti bianchi)
st.markdown("""
    <style>
    /* Sfondo rosa/pesca dell'immagine */
    .stApp { background-color: #fdf2f2 !important; }
    
    /* Testi neri e font pulito */
    .stApp p, .stApp span, .stApp label, .stMarkdown, h1, h2, h3, h4 { 
        color: #000000 !important; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }

    /* FORZATURA TESTO NERO NEGLI INPUT (per evitare che diventi bianco scrivendo) */
    input { color: black !important; }
    div[data-baseweb="select"] div { color: black !important; }
    
    /* Box di inserimento bianchi con bordo sottile grigio */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div,
    div[role="listbox"] {
        background-color: white !important;
        color: black !important;
        border: 1px solid #bdc3c7 !important;
    }

    /* Calendario: forziamo il nero anche qui */
    div[data-baseweb="calendar"] { background-color: white !important; }
    div[data-baseweb="calendar"] button { color: black !important; }

    /* Pulsanti bianchi (stile tasto "+" nell'immagine) */
    .stButton>button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #bdc3c7 !important;
        border-radius: 4px !important;
        font-weight: normal !important;
        padding: 2px 10px !important;
    }
    
    .stButton>button:hover {
        border: 1px solid #000000 !important;
        background-color: #f0f0f0 !important;
    }

    /* Risultati: togliamo i colori accesi, usiamo bordi semplici */
    .stAlert { background-color: white !important; border: 1px solid #bdc3c7 !important; color: black !important; }
    
    hr { border: 0.5px solid #bdc3c7 !important; }
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

# Titolo semplice come da immagine
st.write("### Simulatore Conflitti")

if not prodotti_attivi:
    st.warning("Carica il file prodotti.xlsx per visualizzare i dati.")
    st.stop()

# 1. Selezione Prodotto
st.write("ciao inserisci il prodotto che vuoi fare")
nuovo_prodotto = st.selectbox("", options=[""] + sorted(list(prodotti_attivi.keys())), label_visibility="collapsed")

st.markdown("<br>", unsafe_allow_html=True)

# 2. Sezione Riscatti
st.write("ci sono stati riscatti?")
if 'riscatti' not in st.session_state: st.session_state.riscatti = []
if st.button("+", key="add_r"):
    st.session_state.riscatti.append({"data": datetime.now()})

ev_riscatti = []
for i, r in enumerate(st.session_state.riscatti):
    c1, c2, c3 = st.columns([2, 1, 0.5])
    p = c1.selectbox(f"p_r_{i}", [""] + sorted(list(prodotti_ptf.keys())), key=f"pr_{i}", label_visibility="collapsed")
    d = c2.date_input(f"d_r_{i}", value=r['data'], key=f"dr_{i}", label_visibility="collapsed")
    if c3.button("🗑️", key=f"delr_{i}"):
        st.session_state.riscatti.pop(i)
        st.rerun()
    if p: ev_riscatti.append({"cat": prodotti_ptf[p], "data": d})

st.markdown("<small>Nota: RICORDATI DI CONTROLLARE ANCHE I RISCATTI CHE HANNO AVUTO IN COMUNE L'IBAN</small>", unsafe_allow_html=True)
st.markdown("---")

# 3. Sezione Risoluzioni
st.write("ci sono polizze in risoluzione o sospese?")
if 'risoluzioni' not in st.session_state: st.session_state.risoluzioni = []
if st.button("+", key="add_s"):
    st.session_state.risoluzioni.append({"data": datetime.now()})

ev_risoluzioni = []
for i, r in enumerate(st.session_state.risoluzioni):
    c1, c2, c3 = st.columns([2, 1, 0.5])
    p = c1.selectbox(f"p_s_{i}", [""] + sorted(list(prodotti_ptf.keys())), key=f"ps_{i}", label_visibility="collapsed")
    d = c2.date_input(f"d_s_{i}", value=r['data'], key=f"ds_{i}", label_visibility="collapsed")
    if c3.button("🗑️", key=f"dels_{i}"):
        st.session_state.risoluzioni.pop(i)
        st.rerun()
    if p: ev_risoluzioni.append({"cat": prodotti_ptf[p], "data": d})

st.markdown("---")

# 4. Verifica e Risultati
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
            
            # Logica blocchi
            if (cat_n == "protezione" and cv == "protezione") or \
               (cat_n == "previdenza" and cv == "previdenza") or \
               (cat_n == "investimento" and cv == "investimento") or \
               (cat_n == "risparmio" and (cv == "investimento" or cv == "risparmio")):
                bloccato = True

        st.write("#### risultato")
        if bloccato:
            st.write(f"Per il prodotto {nuovo_prodotto} l'esito è: **NON PROCEDIBILE**")
        else:
            st.write(f"Per il prodotto {nuovo_prodotto} l'esito è: **PROCEDIBILE**")

        st.markdown("<br> **per il prodotto che hai scelto è possibile fare i seguenti prodotti**", unsafe_allow_html=True)
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
                   (cl == "risparmio" and (cv == "investimento" or cv == "risparmio")):
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
        st.write("**i seguenti prodotti saranno disponibili dopo la data riportata**")
        for d_s, prods in blocchi.items():
            st.write(f"**Dal {d_s}:** {', '.join(prods)}")

st.markdown("<br><br><small>Questo simulatore non fornisce elemento certo e non è perfetto, non verifica ad esempio le componenti protection.</small>", unsafe_allow_html=True)
