import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import pandas as pd

# --- Configuração da Página ---
st.set_page_config(page_title="HCPA - Gestão de Caixas", layout="centered")

# --- Conexão com Google Sheets ---
def conectar_google():
    try:
        escopo = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # Certifique-se que o arquivo credenciais.json está na mesma pasta
        creds = Credentials.from_service_account_file('credenciais.json', scopes=escopo)
        client = gspread.authorize(creds)
        return client.open("Controle de caixas HCPA")
    except Exception as e:
        st.error(f"Erro ao conectar com a planilha: {e}")
        return None

planilha = conectar_google()
aba_historico = planilha.get_worksheet(0) if planilha else None
aba_pendentes = planilha.get_worksheet(1) if planilha else None

# --- Captura de Parâmetro da URL (Passo 02) ---
# Se acessar: .../?setor=EMERGENCIA, o campo setor será preenchido.
setor_url = st.query_params.get("setor", "").upper()

st.title("📦 Sistema de Caixas HCPA")

tab1, tab2, tab3 = st.tabs(["📢 Notificar", "📊 Painel", "✅ Coleta"])

# --- ABA 1: NOTIFICAR ---
with tab1:
    st.subheader("Notificar Acúmulo")
    setor_notif = st.text_input("Unidade/Setor", value=setor_url, placeholder="Ex: Emergência")
    vol_estimado = st.selectbox("Volume Estimado", 
                                ["Até 5 (Skate)", "Até 10 (1 carro)", "+ de 10 (Várias viagens)"])
    
    if st.button("ENVIAR ALERTA", type="primary"):
        if setor_notif and aba_pendentes:
            hora = datetime.datetime.now().strftime("%H:%M")
            aba_pendentes.append_row([setor_notif, vol_estimado, hora, "ABERTO"])
            st.success(f"Alerta enviado para {setor_notif}!")
        else:
            st.warning("Preencha o setor ou verifique a conexão.")

# --- ABA 2: PAINEL ---
with tab2:
    st.subheader("Chamados Ativos")
    if aba_pendentes:
        dados = aba_pendentes.get_all_records()
        if dados:
            df = pd.DataFrame(dados)
            st.table(df)
            
            # Análise Inteligente básica
            st.info(f"Existem {len(df)} pontos aguardando coleta no momento.")
        else:
            st.write("✅ Tudo limpo! Nenhuma pendência.")

# --- ABA 3: REGISTRAR COLETA ---
with tab3:
    st.subheader("Registrar Coleta")
    cartao = st.text_input("Cartão Ponto")
    setor_coleta = st.text_input("Confirmar Setor", value=setor_url)
    qtd = st.number_input("Quantidade Coletada", min_value=1, step=1)
    limpo = st.checkbox("O local ficou totalmente limpo?")
    
    if st.button("FINALIZAR REGISTRO", type="primary"):
        if cartao and setor_coleta and aba_historico:
            agora = datetime.datetime.now()
            # Salva no histórico
            aba_historico.append_row([
                agora.strftime("%d/%m/%Y %H:%M"),
                setor_coleta,
                qtd,
                cartao,
                "SIM" if limpo else "NÃO"
            ])
            
            # Remove da lista de pendentes
            try:
                celula = aba_pendentes.find(setor_coleta)
                aba_pendentes.delete_rows(celula.row)
            except:
                pass # Se não achar o chamado, apenas segue
                
            st.balloons()
            st.success("Coleta registrada com sucesso!")
        else:
            st.error("Preencha todos os campos.")
