import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Simulatore Conflitti", layout="wide")

# CSS: Stile consolidato, testi neri, pulsanti vivaci e tabelle pulite
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
        margin: 8px 0px !important;
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
        
        attivi.columns = [str(c).strip().lower() for c in attivi.columns]
        ptf.columns = [str(c).strip().lower() for c in ptf.columns]
        
        comp_col_attivi = next((c for c in attivi.columns if 'compon' in c), None)
        comp_col_ptf = next((c for c in ptf.columns if 'compon' in c), None)
        
        dict_attivi = {}
        for _, row in attivi.iterrows():
            p_name = str(row['prodotto']).strip()
            categoria = str(row['categoria']).strip()
            componenti = str(row[comp_col_attivi]).strip().upper() if comp_col_attivi and pd.notna(row[comp_col_attivi]) else "N.D."
            dict_attivi[p_name] = {"categoria": categoria, "componenti": componenti}
            
        dict_ptf = {}
        for _, row in ptf.iterrows():
            p_name = str(row['prodotto']).strip()
            categoria = str(row['categoria']).strip()
            componenti = str(row[comp_col_ptf]).strip().upper() if comp_col_ptf and pd.notna(row[comp_col_ptf]) else "N.D."
            dict_ptf[p_name] = {"categoria": categoria, "componenti": componenti}
            
        return dict_attivi, dict_ptf
    except Exception as e:
        st.error(f"Errore tecnico nella lettura del file Excel: {e}")
        return {}, {}

prodotti_attivi, prodotti_ptf = load_data()
oggi = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

st.write("### Simulatore Conflitti")

if not prodotti_attivi:
    st.warning("Verifica il file 'prodotti.xlsx' su GitHub.")
    st.stop()

# 1. Selezione Prodotto
st.write("ciao inserisci il prodotto che vuoi fare")
nuovo_prodotto = st.selectbox("Scegli prodotto", options=[""] + sorted(list(prodotti_attivi.keys())), label_visibility="collapsed")

# --- SEZIONE NOTE ---
st.markdown('<div class="nota-box">Nota: RICORDATI DI CONTROLLARE ANCHE I RISCATTI CHE HANNO AVUTO IN COMUNE L\'IBAN</div>', unsafe_allow_html=True)
st.markdown('<div class="nota-box">Nota: RICORDATI DI CHIEDERE SE VI SONO RISCATTI DI ALTRE AGENZIE</div>', unsafe_allow_html=True)
st.markdown('<div class="nota-box">Nota: RICORDATI DI CONTROLLARE SE NON CI SONO PREMI UNICI AGGIUNTIVI NELLA POLIZZA RISCATTATA</div>', unsafe_allow_html=True)
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
        tutti_eventi.append({"cat": prodotti_ptf[p]["categoria"], "comp": prodotti_ptf[p]["componenti"], "data": d})

for i, s in enumerate(st.session_state.ev_s):
    c1, c2, c3 = st.columns([1.5, 1.5, 0.4])
    p = c1.selectbox(f"Prodotto Risoluzione #{i+1}", [""] + sorted(list(prodotti_ptf.keys())), key=f"ps_{i}")
    d = c2.date_input(f"Data interruzione polizza", value=s['data'], key=f"ds_{i}")
    if c3.button("🗑️", key=f"dels_{i}"):
        st.session_state.ev_s.pop(i)
        st.rerun()
    if p and (datetime.combine(d, datetime.min.time()) + timedelta(days=367)) > oggi:
        tutti_eventi.append({"cat": prodotti_ptf[p]["categoria"], "comp": prodotti_ptf[p]["componenti"], "data": d})

st.markdown("---")

# 3. VERIFICA
if st.button("VERIFICA", type="primary"):
    if nuovo_prodotto:
        cat_scelta = prodotti_attivi[nuovo_prodotto]["categoria"].lower()
        comp_scelta = prodotti_attivi[nuovo_prodotto]["componenti"]
        
        max_sblocco_cat_identica = {}
        max_sblocco_comp = {"PA": None, "PU": None}
        
        for ev in tutti_eventi:
            cv = ev['cat'].lower()
            ev_comp = ev['comp']
            data_sblocco = datetime.combine(ev['data'], datetime.min.time()) + timedelta(days=367)
            
            # 1. Registra blocco SOLO se la categoria coincide al 100% (es. Risparmio con Risparmio)
            if cv == cat_scelta:
                if cv not in max_sblocco_cat_identica or data_sblocco > max_sblocco_cat_identica[cv]:
                    max_sblocco_cat_identica[cv] = data_sblocco
                
            # 2. Registra scadenze generali delle componenti per i potenziali incroci (es. Investimento con Risparmio)
            if "PA" in ev_comp:
                if max_sblocco_comp["PA"] is None or data_sblocco > max_sblocco_comp["PA"]:
                    max_sblocco_comp["PA"] = data_sblocco
            if "PU" in ev_comp:
                if max_sblocco_comp["PU"] is None or data_sblocco > max_sblocco_comp["PU"]:
                    max_sblocco_comp["PU"] = data_sblocco

        final_block_dates = {}
        possibili_conflitti = []

        for p, info in prodotti_attivi.items():
            cl = info["categoria"].lower()
            cp = info["componenti"]
            m_date = None
            
            # Se la categoria è esattamente identica a quella bloccata, allora è blocco certo
            if cl in max_sblocco_cat_identica:
                m_date = max_sblocco_cat_identica[cl]
                    
            if m_date:
                final_block_dates[p] = m_date
            else:
                # Altrimenti, se le categorie sono diverse ma condividono componenti, è un potenziale conflitto
                comp_block_date = None
                componenti_colpite = []
                
                if "PA" in cp and max_sblocco_comp["PA"]:
                    comp_block_date = max_sblocco_comp["PA"]
                    componenti_colpite.append("PA")
                if "PU" in cp and max_sblocco_comp["PU"]:
                    if comp_block_date is None or max_sblocco_comp["PU"] > comp_block_date:
                        comp_block_date = max_sblocco_comp["PU"]
                    if "PU" not in componenti_colpite:
                        componenti_colpite.append("PU")
                        
                if comp_block_date:
                    txt_rischio = "Entrambe (PA e PU)" if len(componenti_colpite) > 1 else componenti_colpite[0]
                    possibili_conflitti.append({
                        "Prodotto": p,
                        "Categoria": info["categoria"],
                        "Componenti Prodotto": cp,
                        "Componente a Rischio": txt_rischio,
                        "In Sicurezza dal": comp_block_date.strftime("%d/%m/%Y")
                    })

        # --- VISUALIZZAZIONE ESITO PRODOTTO SELEZIONATO ---
        st.write("#### Esito Prodotto Selezionato")
        if nuovo_prodotto in final_block_dates:
            st.error(f"Per il prodotto **{nuovo_prodotto}** l'esito è: **NON PROCEDIBILE** (fino al {final_block_dates[nuovo_prodotto].strftime('%d/%m/%Y')})")
        else:
            conflitto_corrente = next((item for item in possibili_conflitti if item["Prodotto"] == nuovo_prodotto), None)
            
            if conflitto_corrente:
                comp_rischio = conflitto_corrente["Componente a Rischio"]
                data_sic = conflitto_corrente["In Sicurezza dal"]
                
                if comp_rischio == "Entrambe (PA e PU)":
                    st.warning(f"Per il prodotto **{nuovo_prodotto}** l'esito è: **ATTENZIONE**. È possibile farlo ma attenzione rischio conflitto per entrambe le componenti (sia PA che PU). In sicurezza totale dal {data_sic}")
                elif "+" in comp_scelta:
                    st.warning(f"Per il prodotto **{nuovo_prodotto}** l'esito è: **ATTENZIONE**. È possibile farlo ma attenzione rischio conflitto con componente {comp_rischio}. In sicurezza totale dal {data_sic}")
                else:
                    st.warning(f"Per il prodotto **{nuovo_prodotto}** l'esito è: **ATTENZIONE**. È possibile farlo ma attenzione rischio conflitto con componente {comp_scelta}. In sicurezza totale dal {data_sic}")
            else:
                st.success(f"Per il prodotto **{nuovo_prodotto}** l'esito è: **PROCEDIBILE**")

        st.markdown("---")

        # --- TABELLA 1: SI ---
        prods_si = {}
        for p, info in prodotti_attivi.items():
            if p not in final_block_dates:
                c = info["categoria"]
                if c not in prods_si: prods_si[c] = []
                prods_si[c].append(p)

        st.write("### ✅ SI - Prodotti Disponibili Oggi (Senza Conflitti di Categoria)")
        if prods_si:
            si_cols = st.columns(len(prods_si))
            for i, (cat_name, list_p) in enumerate(sorted(prods_si.items())):
                with si_cols[i]:
                    st.markdown(f"**{cat_name}**")
                    for lp in sorted(list_p):
                        check_alert = "⚠️ " if any(item["Prodotto"] == lp for item in possibili_conflitti) else "• "
                        st.write(f"{check_alert}{lp}")
        else:
            st.write("_Nessun prodotto disponibile oggi._")

        st.markdown("---")

        # TABELLA 2: NO
        st.write("### ❌ NO - Prodotti Momentaneamente Bloccati per Categoria")
        if final_block_dates:
            prods_no = [{"Prodotto": p, "Categoria": prodotti_attivi[p]["categoria"], "Disponibile dal": final_block_dates[p].strftime("%d/%m/%Y")} for p in final_block_dates]
            df_no = pd.DataFrame(prods_no).sort_values(by="Disponibile dal", ascending=False)
            st.table(df_no)
        else:
            st.write("_Nessun blocco di categoria attivo per il futuro._")

        st.markdown("---")

        # TABELLA 3: POTENZIALI
        st.write("### ⚠️ Possibili conflitti con i prodotti (Stesse Componenti PA / PU)")
        if possibili_conflitti:
            df_possibili = pd.DataFrame(possibili_conflitti)
            st.table(df_possibili[["Prodotto", "Categoria", "Componenti Prodotto", "Componente a Rischio", "In Sicurezza dal"]])
        else:
            st.write("_Nessun potenziale conflitto rilevato sulle componenti o colonna componenti non presente nell'Excel._")

st.markdown("<br><br><small>Questo simulatore non fornisce elemento certo e non è perfetto.</small>", unsafe_allow_html=True)
