import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import pandas as pd

# --- Configuração da Página ---
st.set_page_config(page_title="HCPA - Gestão de Caixas", layout="centered")

# --- Conexão Segura (Apenas via Secrets) ---
def conectar_google():
    try:
        escopo = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # Aqui o código ignora arquivos e lê direto do que você colou no Streamlit
        if "gcp_service_account" in st.secrets:
            creds_info = st.secrets["gcp_service_account"]
            creds = Credentials.from_service_account_info(creds_info, scopes=escopo)
            client = gspread.authorize(creds)
            return client.open("Controle de caixas HCPA")
        else:
            st.error("Configuração 'gcp_service_account' não encontrada nos Secrets!")
            return None
    except Exception as e:
        st.error(f"Erro ao conectar com a planilha: {e}")
        return None

# Inicializa as variáveis
planilha = conectar_google()
aba_historico = planilha.get_worksheet(0) if planilha else None
aba_pendentes = planilha.get_worksheet(1) if planilha else None

# --- Restante do código (Notificar, Painel, Coleta) ---
setor_url = st.query_params.get("setor", "").upper()

st.title("📦 Sistema de Caixas HCPA")
tab1, tab2, tab3 = st.tabs(["📢 Notificar", "📊 Painel", "✅ Coleta"])

with tab1:
    st.subheader("Notificar Acúmulo")
    setor_notif = st.text_input("Unidade/Setor", value=setor_url, placeholder="Ex: Emergência")
    vol_estimado = st.selectbox("Volume Estimado", ["Até 5 (Skate)", "Até 10 (1 carro)", "+ de 10 (Várias viagens)"])
    if st.button("ENVIAR ALERTA", type="primary"):
        if setor_notif and aba_pendentes:
            hora = datetime.datetime.now().strftime("%H:%M")
            aba_pendentes.append_row([setor_notif, vol_estimado, hora, "ABERTO"])
            st.success(f"Alerta enviado para {setor_notif}!")

with tab2:
    st.subheader("Chamados Ativos")
    if aba_pendentes:
        dados = aba_pendentes.get_all_records()
        if dados:
            st.table(pd.DataFrame(dados))
        else:
            st.write("✅ Tudo limpo!")

with tab3:
    st.subheader("Registrar Coleta")
    cartao = st.text_input("Cartão Ponto")
    setor_coleta = st.text_input("Confirmar Setor", value=setor_url, key="col_input")
    qtd = st.number_input("Quantidade Coletada", min_value=1, step=1)
    if st.button("FINALIZAR REGISTRO"):
        if cartao and setor_coleta and aba_historico:
            aba_historico.append_row([datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), setor_coleta, qtd, cartao])
            try:
                celula = aba_pendentes.find(setor_coleta)
                aba_pendentes.delete_rows(celula.row)
            except: pass
            st.success("Coleta registrada!")
