import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Configurazione Pagina
st.set_page_config(page_title="Simulatore Conflitti Generali", layout="centered")

# CSS: Sfondo rosa, rosso acceso per bottoni e testi neri forzati
st.markdown("""
    <style>
    /* Sfondo rosa leggero */
    .stApp {
        background-color: #fdf2f2 !important;
    }
    
    /* Testo principale sempre Nero per massima leggibilità */
    .stApp p, .stApp span, .stApp label, .stMarkdown {
        color: #1a1a1a !important;
        font-weight: 500;
    }

    /* Titoli Rosso Acceso Generali */
    h1, h2, h3 {
        color: #E4002B !important;
        font-weight: bold;
    }

    /* Pulsanti Rosso Acceso (#E4002B) con testo bianco */
    .stButton>button {
        background-color: #E4002B !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        height: 3em !important;
        width: 100% !important;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stButton>button:hover {
        background-color: #ff1a40 !important;
        color: white !important;
    }

    /* Selectbox e Input bianchi con testo nero */
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
        background-color: white !important;
        color: black !important;
    }

    /* Linea di separazione rossa */
    hr {
        border: 0;
        height: 2px;
        background: #E4002B;
        margin-bottom: 20px;
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
    st.warning("In attesa del file 'prodotti.xlsx' su GitHub...")
    st.stop()

# --- INTERFACCIA ---
st.subheader("1. Prodotto da Sottoscrivere")
nuovo_prodotto = st.selectbox("Seleziona il prodotto che vuoi proporre:", options=[""] + sorted(list(prodotti_attivi.keys())))

st.info("⚠️ NOTA: Verifica sempre l'IBAN di accredito per identificare eventuali riscatti collegati.")

st.subheader("2. Riscatti e Risoluzioni")
if 'eventi' not in st.session_state:
    st.session_state.eventi = []

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("➕ AGGIUNGI RISCATTO"):
        st.session_state.eventi.append({"tipo": "Riscatto", "data": datetime.now()})
with col_btn2:
    if st.button("➕ AGGIUNGI RISOLUZIONE"):
        st.session_state.eventi.append({"tipo": "Risoluzione", "data": datetime.now()})

eventi_validi = []
for i, ev in enumerate(st.session_state.eventi):
    with st.expander(f"Operazione {ev['tipo']} #{i+1}", expanded=True):
        c1, c2, c3 = st.columns([2, 1, 0.5])
        nome_v = c1.selectbox(f"Prodotto vecchio", options=[""] + sorted(list(prodotti_ptf.keys())), key=f"n_{i}")
        data_v = c2.date_input(f"Data evento", value=ev['data'], key=f"d_{i}")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.eventi.pop(i)
            st.rerun()
        if nome_v:
            eventi_validi.append({"nome": nome_v, "data": data_v, "cat": prodotti_ptf[nome_v]})

st.markdown("<hr>", unsafe_allow_html=True)

if st.button("ESEGUI VERIFICA CONFLITTI"):
    if not nuovo_prodotto:
        st.warning("Seleziona un prodotto di interesse.")
    else:
        cat_nuovo = prodotti_attivi[nuovo_prodotto].lower()
        conflitto = False
        msg_conflitto = ""
        
        # Mappa per trovare la data più recente per ogni categoria di sblocco
        mappa_date_sblocco = {} # {categoria_vecchia: data_max}

        for ev in eventi_validi:
            cat_v = ev['cat'].lower()
            data_v = datetime.combine(ev['data'], datetime.min.time())
            
            if cat_v not in mappa_date_sblocco or data_v > mappa_date_sblocco[cat_v]:
                mappa_date_sblocco[cat_v] = data_v

            # Controllo blocco prodotto attuale
            is_bloccato = False
            if cat_nuovo == "protezione" and cat_v == "protezione": is_bloccato = True
            elif cat_nuovo == "previdenza" and cat_v == "previdenza": is_bloccato = True
            elif cat_nuovo == "investimento" and cat_v == "investimento": is_bloccato = True
            elif cat_nuovo == "risparmio" and (cat_v == "investimento" or cat_v == "risparmio"): is_bloccato = True
            
            if is_bloccato:
                conflitto = True
                msg_conflitto = f"Il prodotto scelto ({cat_nuovo.upper()}) è in conflitto con {ev['nome']} ({cat_v.upper()})."

        if conflitto:
            st.error(f"### ❌ NON PROCEDIBILE\n{msg_conflitto}")
        else:
            st.success("### ✅ PROCEDIBILE")

        # --- RISULTATI DETTAGLIATI ---
        st.subheader("📋 Esito dell'Analisi")
        
        prod_disponibili = []
        prod_bloccati_per_data = {} # {data_sblocco: [lista_prodotti]}

        for p, c in prodotti_attivi.items():
            c_l = c.lower()
            can_do = True
            data_sblocco_finale = None
            
            for cat_v, data_v in mappa_date_sblocco.items():
                blocco_check = False
                if c_l == "protezione" and cat_v == "protezione": blocco_check = True
                elif c_l == "previdenza" and cat_v == "previdenza": blocco_check = True
                elif c_l == "investimento" and cat_v == "investimento": blocco_check = True
                elif c_l == "risparmio" and (cat_v == "investimento" or cat_v == "risparmio"): blocco_check = True
                
                if blocco_check:
                    can_do = False
                    d_s = data_v + timedelta(days=367)
                    if data_sblocco_finale is None or d_s > data_sblocco_finale:
                        data_sblocco_finale = d_s
            
            if can_do:
                prod_disponibili.append(p)
            else:
                d_str = data_sblocco_finale.strftime('%d/%m/%Y')
                if d_str not in prod_bloccati_per_data: prod_bloccati_per_data[d_str] = []
                prod_bloccati_per_data[d_str].append(p)

        st.markdown("#### ✅ Prodotti sottoscrivibili oggi:")
        if prod_disponibili:
            st.info(", ".join(sorted(prod_disponibili)))
        else:
            st.write("_Nessun prodotto disponibile al momento._")

        if prod_bloccati_per_data:
            st.markdown("#### ⏳ Prodotti non disponibili (Blocco 12 mesi):")
            # Ordiniamo le date di sblocco per chiarezza
            for d_sblocco in sorted(prod_bloccati_per_data.keys(), key=lambda x: datetime.strptime(x, '%d/%m/%Y')):
                prods = prod_bloccati_per_data[d_sblocco]
                st.warning(f"📅 **Disponibili dal {d_sblocco}:**")
                st.write(", ".join(sorted(prods)))

st.markdown("<br><hr>", unsafe_allow_html=True)
st.caption("ℹ️ Questo simulatore non fornisce elemento certo e non è perfetto, non verifica ad esempio le componenti protection.")
