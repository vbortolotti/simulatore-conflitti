import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Simulatore Conflitti", layout="wide")

# CSS: Stile consolidato, testi neri, pulsanti vivaci
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
    st.warning("Carica il file prodotti.xlsx per iniziare.")
    st.stop()

# 1. Selezione Prodotto
st.write("ciao inserisci il prodotto che vuoi fare")
nuovo_prodotto = st.selectbox("Scegli prodotto", options=[""] + sorted(list(prodotti_attivi.keys())), label_visibility="collapsed")

st.markdown('<div class="nota-box">Nota: RICORDATI DI CONTROLLARE ANCHE I RISCATTI CHE HANNO AVUTO IN COMUNE L\'IBAN</div>', unsafe_allow_html=True)
st.markdown('<div class="nota-box">Nota: RICORDATI DI CHIEDERE SE VI SONO RISCATTI DI ALTRE AGENZIE</div>', unsafe_allow_html=True)
st.markdown('<div class="nota-box">Nota: RICORDATI DI CONTROLLARE SE NON CI SONO PREMI UNICI AGGIUNTIVI NELLA POLZZIA RISCATTATA</div>', unsafe_allow_html=True)
st.markdown('<div class="nota-box">Nota: RICORDATI SE IL RISCATTO È PA (RISPARMIO) CI PUÒ ESSERE IL CONFLITTO PER LA PARTE PROTECTION</div>', unsafe_allow_html=True)
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
    if p and (datetime.combine(d, datetime.min.time()) + timedelta(days=367)) > oggi:
        tutti_eventi.append({"cat": prodotti_ptf[p], "data": d})

for i, s in enumerate(st.session_state.ev_s):
    c1, c2, c3 = st.columns([1.5, 1.5, 0.4])
    p = c1.selectbox(f"Prodotto Risoluzione #{i+1}", [""] + sorted(list(prodotti_ptf.keys())), key=f"ps_{i}")
    d = c2.date_input(f"Data interruzione polizza", value=s['data'], key=f"ds_{i}")
    if c3.button("🗑️", key=f"dels_{i}"):
        st.session_state.ev_s.pop(i)
        st.rerun()
    if p and (datetime.combine(d, datetime.min.time()) + timedelta(days=367)) > oggi:
        tutti_eventi.append({"cat": prodotti_ptf[p], "data": d})

st.markdown("---")

# 3. VERIFICA
if st.button("VERIFICA", type="primary"):
    if nuovo_prodotto:
        cat_scelta = prodotti_attivi[nuovo_prodotto].lower()
        
        # Mappa data sblocco massima per ogni categoria riscontrata negli eventi
        max_sblocco_cat = {}
        for ev in tutti_eventi:
            cv = ev['cat'].lower()
            data_sblocco = datetime.combine(ev['data'], datetime.min.time()) + timedelta(days=367)
            if cv not in max_sblocco_cat or data_sblocco > max_sblocco_cat[cv]:
                max_sblocco_cat[cv] = data_sblocco

        # Logica specifica per determinare la data di blocco effettiva per ogni categoria "attiva"
        final_block_dates = {}
        for p, c in prodotti_attivi.items():
            cl = c.lower()
            m_date = None
            
            if cl in max_sblocco_cat:
                m_date = max_sblocco_cat[cl]
            
            # Regola speciale: Risparmio è influenzato anche da Investimento
            if cl == "risparmio" and "investimento" in max_sblocco_cat:
                date_inv = max_sblocco_cat["investimento"]
                if m_date is None or date_inv > m_date:
                    m_date = date_inv
            
            if m_date:
                final_block_dates[p] = m_date

        # Esito prodotto selezionato
        is_bloccato = nuovo_prodotto in final_block_dates
        st.write("#### Esito Prodotto")
        if is_bloccato:
            st.error(f"Per il prodotto **{nuovo_prodotto}** l'esito è: **NON PROCEDIBILE** (fino al {final_block_dates[nuovo_prodotto].strftime('%d/%m/%Y')})")
        else:
            st.success(f"Per il prodotto **{nuovo_prodotto}** l'esito è: **PROCEDIBILE**")

        st.markdown("---")

        # --- SUDDIVISIONE PRODOTTI ---
        prods_si = {}
        prods_no = []

        for p, c in prodotti_attivi.items():
            if p in final_block_dates:
                prods_no.append({
                    "Prodotto": p, 
                    "Categoria": c, 
                    "Disponibile dal": final_block_dates[p].strftime("%d/%m/%Y")
                })
            else:
                if c not in prods_si: prods_si[c] = []
                prods_si[c].append(p)

        # Visualizzazione SI
        st.write("### ✅ SI - Prodotti Disponibili Oggi")
        if prods_si:
            si_cols = st.columns(len(prods_si))
            for i, (cat_name, list_p) in enumerate(sorted(prods_si.items())):
                with si_cols[i]:
                    st.markdown(f"**{cat_name}**")
                    for lp in sorted(list_p):
                        st.write(f"• {lp}")
        else:
            st.write("_Nessun prodotto disponibile oggi._")

        st.markdown("---")

        # Visualizzazione NO
        st.write("### ❌ NO - Prodotti Momentaneamente Bloccati")
        if prods_no:
            # Ordiniamo per data di sblocco più recente
            df_no = pd.DataFrame(prods_no).sort_values(by="Disponibile dal", ascending=False)
            st.table(df_no)
        else:
            st.write("_Nessun blocco attivo per il futuro._")

st.markdown("<br><br><small>Questo simulatore non fornisce elemento certo e non è perfetto.</small>", unsafe_allow_html=True)
