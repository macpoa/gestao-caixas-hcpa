import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import pandas as pd

# --- Configuração da Página ---
st.set_page_config(page_title="HCPA - Gestão de Caixas", layout="centered")

# --- Conexão Segura OBRIGATÓRIA via Secrets ---
def conectar_google():
    try:
        escopo = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds_info = st.secrets["gcp_service_account"]
            creds = Credentials.from_service_account_info(creds_info, scopes=escopo)
            client = gspread.authorize(creds)
            return client.open("Controle de caixas HCPA")
        return None
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")
        return None

planilha = conectar_google()
aba_historico = planilha.get_worksheet(0) if planilha else None
aba_pendentes = planilha.get_worksheet(1) if planilha else None

# Captura setor da URL
setor_url = st.query_params.get("setor", "").upper()

st.title("📦 Sistema de Caixas HCPA")

if not planilha:
    st.warning("⚠️ Erro de conexão com a planilha.")
else:
    tab1, tab2, tab3 = st.tabs(["📢 Notificar Acúmulo", "📊 Painel de Chamados", "✅ Registar Coleta"])

    # --- ABA 1: NOTIFICAR (Ajustada para limpar após envio) ---
    with tab1:
        st.subheader("Informar Caixas Vazias")
        # Usamos um formulário para facilitar a limpeza da tela
        with st.form("form_notificar", clear_on_submit=True):
            setor_notif = st.text_input("Setor/Unidade", value=setor_url)
            vol_estimado = st.selectbox("Volume Estimado", ["Até 5 (Skate)", "Até 10 (1 carro)", "+ de 10"])
            submit_notif = st.form_submit_button("ENVIAR ALERTA", type="primary")
            
            if submit_notif:
                if setor_notif:
                    hora = datetime.datetime.now().strftime("%H:%M")
                    aba_pendentes.append_row([setor_notif, vol_estimado, hora, "ABERTO"])
                    st.success(f"Notificação enviada com sucesso para {setor_notif}!")
                    # O 'clear_on_submit=True' do form já limpa os campos para o próximo uso
                else:
                    st.error("Por favor, indique o setor.")

    # --- ABA 2: PAINEL ---
    with tab2:
        st.subheader("Locais aguardando recolha")
        dados = aba_pendentes.get_all_records()
        if dados:
            st.table(pd.DataFrame(dados))
        else:
            st.info("✅ Excelente! Não há caixas pendentes no hospital.")

    # --- ABA 3: REGISTAR COLETA (Com indicador de conclusão) ---
    with tab3:
        st.subheader("Finalizar Recolha")
        with st.form("form_coleta", clear_on_submit=True):
            cartao = st.text_input("Cartão Ponto")
            setor_coleta = st.text_input("Setor onde recolheu", value=setor_url)
            qtd = st.number_input("Qtd de caixas recolhidas", min_value=1, step=1)
            
            # NOVO AJUSTE: Indicador de que o local ficou limpo
            local_ficou_limpo = st.checkbox("O local ficou totalmente limpo? (Conclui a tarefa)")
            
            submit_coleta = st.form_submit_button("CONFIRMAR RECOLHA")

            if submit_coleta:
                if cartao and setor_coleta:
                    agora = datetime.datetime.now()
                    # Salva no histórico
                    aba_historico.append_row([agora.strftime("%d/%m/%Y %H:%M"), setor_coleta, qtd, cartao, "SIM" if local_ficou_limpo else "NÃO"])
                    
                    # Se marcou que ficou limpo, remove o chamado do painel de pendentes
                    if local_ficou_limpo:
                        try:
                            # Procura a linha do setor na aba de pendentes
                            celula = aba_pendentes.find(setor_coleta)
                            aba_pendentes.delete_rows(celula.row)
                            st.success(f"Tarefa concluída! Setor {setor_coleta} removido do painel.")
                        except:
                            st.success("Coleta registada (nenhum chamado pendente encontrado para este setor).")
                    else:
                        st.warning(f"Coleta registada, mas o setor {setor_coleta} continua no painel pois ainda há caixas.")
                else:
                    st.error("Preencha o cartão ponto e o setor.")
