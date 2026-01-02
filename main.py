import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import pandas as pd

# --- Configuração da Página 1 ---
st.set_page_config(page_title="HCPA - Gestão de Caixas", layout="centered")

# --- Conexão Segura OBRIGATÓRIA via Secrets ---
def conectar_google():
    try:
        # Definimos o escopo de acesso
        escopo = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # Verificamos se o segredo existe no Streamlit Cloud
        if "gcp_service_account" in st.secrets:
            # Puxa as informações do "Cofre" (Secrets)
            creds_info = st.secrets["gcp_service_account"]
            # Cria a credencial a partir do DICIONÁRIO e não do arquivo
            creds = Credentials.from_service_account_info(creds_info, scopes=escopo)
            client = gspread.authorize(creds)
            
            # Tenta abrir a planilha pelo nome
            return client.open("Controle de caixas HCPA")
        else:
            st.error("Erro: Configuração 'gcp_service_account' não encontrada nos Secrets do Streamlit.")
            return None
    except Exception as e:
        st.error(f"Erro ao conectar com a planilha: {e}")
        return None

# Tenta estabelecer a conexão
planilha = conectar_google()
aba_historico = planilha.get_worksheet(0) if planilha else None
aba_pendentes = planilha.get_worksheet(1) if planilha else None

# --- Captura de Setor via URL (Para os QR Codes) ---
setor_url = st.query_params.get("setor", "").upper()

st.title("📦 Sistema de Caixas HCPA")

# Se a planilha não conectou, avisa o usuário
if not planilha:
    st.warning("⚠️ O sistema não conseguiu se conectar à base de dados. Verifique os Secrets e o compartilhamento da planilha.")
else:
    tab1, tab2, tab3 = st.tabs(["📢 Notificar", "📊 Painel", "✅ Coleta"])

    # --- ABA 1: NOTIFICAR ---
    with tab1:
        st.subheader("Notificar Acúmulo de Caixas")
        setor_notif = st.text_input("Unidade/Setor", value=setor_url, placeholder="Ex: Emergência")
        vol_estimado = st.selectbox("Volume Estimado", 
                                    ["Até 5 (Skate)", "Até 10 (1 carro)", "+ de 10 (Várias viagens)"])
        
        if st.button("ENVIAR ALERTA", type="primary"):
            if setor_notif and aba_pendentes:
                hora = datetime.datetime.now().strftime("%H:%M")
                aba_pendentes.append_row([setor_notif, vol_estimado, hora, "ABERTO"])
                st.success(f"Alerta enviado para {setor_notif}!")
            else:
                st.error("Por favor, informe o setor.")

    # --- ABA 2: PAINEL ---
    with tab2:
        st.subheader("Chamados Ativos na Expedição")
        if aba_pendentes:
            dados = aba_pendentes.get_all_records()
            if dados:
                df = pd.DataFrame(dados)
                st.table(df)
            else:
                st.info("✅ Tudo limpo! Nenhuma caixa pendente de coleta.")

    # --- ABA 3: REGISTRAR COLETA ---
    with tab3:
        st.subheader("Registrar Coleta Realizada")
        cartao = st.text_input("Cartão Ponto")
        setor_coleta = st.text_input("Confirmar Setor", value=setor_url, key="coleta_input")
        qtd = st.number_input("Quantidade de Caixas Coletadas", min_value=1, step=1)
        
        if st.button("FINALIZAR REGISTRO"):
            if cartao and setor_coleta and aba_historico:
                agora = datetime.datetime.now()
                # 1. Salva no Histórico
                aba_historico.append_row([
                    agora.strftime("%d/%m/%Y %H:%M"),
                    setor_coleta,
                    qtd,
                    cartao
                ])
                # 2. Tenta remover da lista de pendentes
                try:
                    celula = aba_pendentes.find(setor_coleta)
                    aba_pendentes.delete_rows(celula.row)
                    st.success("Coleta registrada e painel atualizado!")
                except:
                    st.success("Coleta registrada no histórico!")
            else:
                st.error("Preencha o Cartão Ponto e o Setor.")
