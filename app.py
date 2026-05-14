import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Simulatore Conflitti", layout="centered")

# CSS: Stile consolidato con visibilità garantita e colori vivaci
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

for i, r in enumerate(st.session_state.ev_r):
    c1, c2, c3 = st.columns([1.5, 1.5, 0.4])
    p = c1.selectbox(f"Prodotto Riscatto #{i+1}", [""] + sorted(list(prodotti_ptf.keys())), key=f"pr_{i}")
    d = c2.date_input(f"Data liquidazione riscatto", value=r['data'], key=f"dr_{i}")
    if c3.button("🗑️", key=f"delr_{i}"):
        st.session_state.ev_r.pop(i)
        st.rerun()
    if p:
        if (datetime.combine(d, datetime.min.time()) + timedelta(days=367)) > oggi:
            tutti_eventi.append({"cat": prodotti_ptf[p], "data": d})

for i, s in enumerate(st.session_state.ev_s):
    c1, c2, c3 = st.columns([1.5, 1.5, 0.4])
    p = c1.selectbox(f"Prodotto Risoluzione #{i+1}", [""] + sorted(list(prodotti_ptf.keys())), key=f"ps_{i}")
    d = c2.date_input(f"Data interruzione polizza", value=s['data'], key=f"ds_{i}")
    if c3.button("🗑️", key=f"dels_{i}"):
        st.session_state.ev_s.pop(i)
        st.rerun()
    if p:
        if (datetime.combine(d, datetime.min.time()) + timedelta(days=367)) > oggi:
            tutti_eventi.append({"cat": prodotti_ptf[p], "data": d})

st.markdown("---")

# 3. VERIFICA E ANALISI CATEGORIE
if st.button("VERIFICA", type="primary"):
    if nuovo_prodotto:
        cat_scelta = prodotti_attivi[nuovo_prodotto].lower()
        
        # Mappa dei blocchi attivi per categoria
        categorie_bloccate = {}
        for ev in tutti_eventi:
            cv = ev['cat'].lower()
            dv = datetime.combine(ev['data'], datetime.min.time())
            data_sblocco = dv + timedelta(days=367)
            if cv not in categorie_bloccate or data_sblocco > categorie_bloccate[cv]:
                categorie_bloccate[cv] = data_sblocco

        # Controllo specifico prodotto scelto
        is_bloccato = False
        if cat_scelta in categorie_bloccate:
            # Protezione/Previdenza/Investimento bloccano se stesse
            is_bloccato = True
        elif cat_scelta == "risparmio" and ("investimento" in categorie_bloccate or "risparmio" in categorie_bloccate):
            # Risparmio è bloccato da Investimento O Risparmio
            is_bloccato = True

        st.write("#### Risultato Prodotto Selezionato")
        if is_bloccato:
            st.error(f"Per il prodotto {nuovo_prodotto} l'esito è: **NON PROCEDIBILE**")
        else:
            st.success(f"Per il prodotto {nuovo_prodotto} l'esito è: **PROCEDIBILE**")

        st.markdown("---")
        
        # --- ANALISI PER TUTTE LE CATEGORIE ---
        st.write("### Analisi Disponibilità per Categoria")
        
        # Definiamo le 4 categorie principali
        cats = ["Protezione", "Previdenza", "Investimento", "Risparmio"]
        col_cats = st.columns(4)
        
        for i, c_name in enumerate(cats):
            c_low = c_name.lower()
            status = "✅ SI"
            info_sblocco = ""
            
            # Logica di blocco per categoria
            if c_low in categorie_bloccate:
                status = "❌ NO"
                info_sblocco = f"Fino al {categorie_bloccate[c_low].strftime('%d/%m/%Y')}"
            elif c_low == "risparmio" and "investimento" in categorie_bloccate:
                status = "❌ NO"
                info_sblocco = f"Fino al {categorie_bloccate['investimento'].strftime('%d/%m/%Y')}"
            
            with col_cats[i]:
                st.metric(label=c_name, value=status, delta=info_sblocco, delta_color="inverse" if "❌" in status else "normal")

        st.markdown("---")
        
        # Liste dettagliate prodotti
        st.write("**Dettaglio prodotti sottoscrivibili oggi:**")
        disp, blocchi = [], {}

        for p, c in prodotti_attivi.items():
            cl = c.lower()
            m_data = None
            
            # Verifica se questo specifico prodotto è bloccato
            if cl in categorie_bloccate:
                m_data = categorie_bloccate[cl]
            elif cl == "risparmio" and "investimento" in categorie_bloccate:
                m_data = categorie_bloccate["investimento"]
            
            if m_data:
                ds_str = m_data.strftime("%d/%m/%Y")
                if ds_str not in blocchi: blocchi[ds_str] = []
                blocchi[ds_str].append(p)
            else:
                disp.append(p)

        st.write(", ".join(disp) if disp else "Nessuno")
        
        if blocchi:
            st.markdown("<br>**I seguenti prodotti saranno disponibili dopo la data riportata:**", unsafe_allow_html=True)
            for d_s, prods in blocchi.items():
                st.warning(f"**Dal {d_s}:** {', '.join(prods)}")

st.markdown("<br><br><small>Questo simulatore non fornisce elemento certo e non è perfetto.</small>", unsafe_allow_html=True)
