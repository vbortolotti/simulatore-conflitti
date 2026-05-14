import streamlit as st
from datetime import datetime, timedelta

# Configurazione della pagina
st.set_page_config(page_title="Simulatore Conflitto di Interessi", layout="centered")

# --- DATABASE PRODOTTI (Estratto dai tuoi file) ---
prodotti_attivi = {
    "Fondo Pensione Aperto Generali Global": "Previdenza",
    "Generali ONE": "Investimento",
    "GeneraSviluppo Sostenibile": "Investimento",
    "GenerAzione Investimento": "Investimento",
    "GenerAzione Previdente": "Previdenza",
    "GenerAzione Risparmio": "Risparmio",
    "ImmaginaFuturo": "Risparmio",
    "Pensione Immediata": "Protezione",
    "Scegli col Cuore - Per chi ami": "Protezione",
    "Scegli per una Lungavita": "Protezione",
    "Valore Futuro": "Investimento",
    "Valore Protetto New": "Risparmio",
    "Rinnova Valore Bonus": "Investimento"
}

# Esempio database PTF (per suggerimenti prodotti vecchi)
prodotti_ptf = {
    "Immaginafuturo": "Risparmio",
    "Generazione previdente": "Previdenza",
    "Scegli per una lungavita": "Protezione",
    "Generasviluppo multiplan": "Risparmio",
    "Valore protetto new": "Risparmio",
    "Lungavita ltc": "Protezione",
    "Generasviluppo sostenibile": "Investimento"
}

# --- INTERFACCIA ---
st.title("🛡️ Simulatore Conflitto di Interessi")
st.markdown("---")

# 1. Selezione Prodotto di Interesse
st.subheader("1. Nuovo Prodotto")
nuovo_prodotto = st.selectbox("Seleziona il prodotto di interesse:", options=[""] + list(prodotti_attivi.keys()))

# 2. Nota IBAN
st.warning("⚠️ **NOTA:** Verifica sempre anche l'IBAN di accredito per eventuali riscatti collegati.")

# 3 & 5. Riscatti e Polizze in Risoluzione
st.subheader("2. Riscatti / Risoluzioni / Sospese")
st.write("Aggiungi i prodotti vecchi che hanno avuto movimenti:")

# Inizializzazione liste nella sessione
if 'eventi' not in st.session_state:
    st.session_state.eventi = []

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("+ Aggiungi Riscatto"):
        st.session_state.eventi.append({"tipo": "Riscatto", "prod": "", "data": datetime.now()})
with col_btn2:
    if st.button("+ Aggiungi Risoluzione/Sospesa"):
        st.session_state.eventi.append({"tipo": "Risoluzione", "prod": "", "data": datetime.now()})

# Visualizzazione input dinamici
eventi_validi = []
for i, evento in enumerate(st.session_state.eventi):
    st.markdown(f"**{evento['tipo']} {i+1}**")
    c1, c2, c3 = st.columns([2, 1, 0.5])
    
    prod_v = c1.selectbox(f"Prodotto vecchio", options=[""] + list(prodotti_ptf.keys()), key=f"p_{i}")
    data_v = c2.date_input(f"Data evento", value=evento['data'], key=f"d_{i}")
    
    if c3.button("🗑️", key=f"del_{i}"):
        st.session_state.eventi.pop(i)
        st.rerun()
    
    if prod_v:
        eventi_validi.append({"nome": prod_v, "data": data_v, "cat": prodotti_ptf[prod_v]})

st.markdown("---")

# 6, 7 & 8. Calcolo e Risultati
if st.button("VERIFICA FATTIBILITÀ", type="primary"):
    if not nuovo_prodotto:
        st.error("Per favore, seleziona un prodotto di interesse.")
    else:
        cat_nuovo = prodotti_attivi[nuovo_prodotto].lower()
        conflitto = False
        data_piu_recente = None
        motivo = ""

        # Logica Regole
        for ev in eventi_validi:
            cat_v = ev['cat'].lower()
            data_v = datetime.combine(ev['data'], datetime.min.time())
            
            if data_piu_recente is None or data_v > data_piu_recente:
                data_piu_recente = data_v

            # REGOLE SCRITTE DA TE
            if cat_nuovo == "protezione" and cat_v == "protezione": conflitto = True
            elif cat_nuovo == "previdenza" and cat_v == "previdenza": conflitto = True
            elif cat_nuovo == "investimento" and cat_v == "investimento": conflitto = True
            elif cat_nuovo == "risparmio" and (cat_v == "investimento" or cat_v == "risparmio"): conflitto = True
            
            if conflitto:
                motivo = f"Il prodotto scelto ({cat_nuovo}) è in conflitto con {ev['nome']} ({cat_v})"
                break

        # Esito
        if conflitto:
            st.error(f"### ❌ ESITO: NON SI PUÒ FARE\n{motivo}")
        else:
            st.success("### ✅ ESITO: SI PUÒ FARE")

        # Elenco prodotti disponibili (Fase 7)
        st.subheader("Elenco prodotti sottoscrivibili:")
        cat_vecchie_inserite = [ev['cat'].lower() for ev in eventi_validi]
        
        disponibili = []
        bloccati = []

        for p, c in prodotti_attivi.items():
            c_low = c.lower()
            can_do = True
            if c_low == "protezione" and "protezione" in cat_vecchie_inserite: can_do = False
            elif c_low == "previdenza" and "previdenza" in cat_vecchie_inserite: can_do = False
            elif c_low == "investimento" and "investimento" in cat_vecchie_inserite: can_do = False
            elif c_low == "risparmio" and ("investimento" in cat_vecchie_inserite or "risparmio" in cat_vecchie_inserite): can_do = False
            
            if can_do: disponibili.append(f"{p} ({c})")
            else: bloccati.append(f"{p} ({c})")

        st.write(", ".join(disponibili))

        # Fase 7-bis: Prodotti disponibili in futuro
        if bloccati and data_piu_recente:
            data_sblocco = data_piu_recente + timedelta(days=367)
            st.warning(f"**I seguenti prodotti saranno disponibili dal {data_sblocco.strftime('%d/%m/%Y')}:**")
            st.write(", ".join(bloccati))

st.markdown("---")
st.caption("ℹ️ Questo simulatore non fornisce elemento certo e non è perfetto, non verifica ad esempio le componenti protection.")