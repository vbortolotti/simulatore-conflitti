import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Configurazione Pagina
st.set_page_config(page_title="Simulatore Conflitti Generali", layout="centered")

# CSS: Stile basato sull'immagine (Rosa, Rosso Acceso, Testi Neri)
st.markdown("""
    <style>
    .stApp { background-color: #fdf2f2 !important; }
    
    /* Testo Nero forzato */
    .stApp p, .stApp span, .stApp label, .stMarkdown { color: #1a1a1a !important; font-weight: 500; }

    /* Titoli Rosso Generali */
    h1, h2, h3, h4 { color: #E4002B !important; font-weight: bold; }

    /* Bottoni Rosso Acceso */
    .stButton>button {
        background-color: #E4002B !important;
        color: white !important;
        border-radius: 5px !important;
        border: none !important;
        font-weight: bold !important;
        width: 100% !important;
    }
    
    /* Stile per i box dei risultati (successo/errore) */
    .stAlert { border-radius: 10px !important; border: 1px solid #E4002B !important; }

    /* Input bianchi */
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
        background-color: white !important;
        color: black !important;
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
        st.error(f"Errore: Assicurati che il file si chiami 'prodotti.xlsx' e i fogli 'Attivi' e 'PTF'.")
        return {}, {}

prodotti_attivi, prodotti_ptf = load_data()

st.title("🔴 Simulatore Conflitti Generali")
st.markdown("---")

# 1. Selezione Prodotto
st.subheader("Seleziona il prodotto di interesse")
nuovo_prodotto = st.selectbox("", options=[""] + sorted(list(prodotti_attivi.keys())), label_visibility="collapsed")
st.info("⚠️ Ricordati di controllare anche l'IBAN di accredito")

# 2. Riscatti
st.markdown("### Ci sono stati riscatti?")
if 'riscatti' not in st.session_state: st.session_state.riscatti = []
if st.button("+ ", key="add_risc"):
    st.session_state.riscatti.append({"data": datetime.now()})

eventi_riscatti = []
for i, r in enumerate(st.session_state.riscatti):
    c1, c2, c3 = st.columns([2, 1, 0.5])
    p = c1.selectbox(f"Prodotto riscatto {i+1}", [""] + sorted(list(prodotti_ptf.keys())), key=f"pr_{i}")
    d = c2.date_input(f"Data liq.", value=r['data'], key=f"dr_{i}")
    if c3.button("🗑️", key=f"delr_{i}"):
        st.session_state.riscatti.pop(i)
        st.rerun()
    if p: eventi_riscatti.append({"cat": prodotti_ptf[p], "data": d})

# 3. Risoluzioni
st.markdown("### Ci sono polizze in risoluzione o sospese?")
if 'risoluzioni' not in st.session_state: st.session_state.risoluzioni = []
if st.button("+ ", key="add_risol"):
    st.session_state.risoluzioni.append({"data": datetime.now()})

eventi_risoluzioni = []
for i, r in enumerate(st.session_state.risoluzioni):
    c1, c2, c3 = st.columns([2, 1, 0.5])
    p = c1.selectbox(f"Prodotto risoluzione {i+1}", [""] + sorted(list(prodotti_ptf.keys())), key=f"ps_{i}")
    d = c2.date_input(f"Data interr.", value=r['data'], key=f"ds_{i}")
    if c3.button("🗑️", key=f"dels_{i}"):
        st.session_state.risoluzioni.pop(i)
        st.rerun()
    if p: eventi_risoluzioni.append({"cat": prodotti_ptf[p], "data": d})

st.markdown("---")

# 4. Calcolo
if st.button("VERIFICA", use_container_width=True):
    if not nuovo_prodotto:
        st.error("Seleziona un prodotto!")
    else:
        cat_nuovo = prodotti_attivi[nuovo_prodotto].lower()
        tutti_eventi = eventi_riscatti + eventi_risoluzioni
        
        # Logica blocco
        bloccato = False
        date_per_cat = {}
        for ev in tutti_eventi:
            cv = ev['cat'].lower()
            dv = datetime.combine(ev['data'], datetime.min.time())
            if cv not in date_per_cat or dv > date_per_cat[cv]: date_per_cat[cv] = dv
            
            if cat_nuovo == "protezione" and cv == "protezione": bloccato = True
            elif cat_nuovo == "previdenza" and cv == "previdenza": bloccato = True
            elif cat_nuovo == "investimento" and cv == "investimento": bloccato = True
            elif cat_nuovo == "risparmio" and (cv == "investimento" or cv == "risparmio"): bloccato = True

        st.subheader("Risultato")
        if bloccato:
            st.error(f"Per il prodotto {nuovo_prodotto} l'esito è: **NON PROCEDIBILE**")
        else:
            st.success(f"Per il prodotto {nuovo_prodotto} l'esito è: **PROCEDIBILE**")

        # 5. Liste prodotti (come da immagine)
        st.markdown("#### Per il prodotto che hai scelto è possibile fare i seguenti prodotti:")
        disponibili = []
        blocchi_futuri = {} # {data: [prodotti]}

        for p, c in prodotti_attivi.items():
            cl = c.lower()
            match_data = None
            for cv, dv in date_per_cat.items():
                is_conf = False
                if cl == "protezione" and cv == "protezione": is_conf = True
                elif cl == "previdenza" and cv == "previdenza": is_conf = True
                elif cl == "investimento" and cv == "investimento": is_conf = True
                elif cl == "risparmio" and (cv == "investimento" or cv == "risparmio"): is_conf = True
                
                if is_conf:
                    ds = (dv + timedelta(days=367)).strftime("%d/%m/%Y")
                    if match_data is None or datetime.strptime(ds, "%d/%m/%Y") > datetime.strptime(match_data, "%d/%m/%Y"):
                        match_data = ds
            
            if not match_data: disponibili.append(p)
            else:
                if match_data not in blocchi_futuri: blocchi_futuri[match_data] = []
                blocchi_futuri[match_data].append(p)

        st.write(", ".join(disponibili) if disponibili else "Nessuno")

        st.markdown("---")
        st.markdown("#### I seguenti prodotti saranno disponibili dopo la data riportata:")
        for data_s, prods in blocchi_futuri.items():
            st.warning(f"**Disponibili dal {data_s}:**")
            st.write(", ".join(prods))

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("Questo simulatore non fornisce elemento certo e non è perfetto, non verifica ad esempio le componenti protection.")
