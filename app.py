import re
import cloudscraper
from bs4 import BeautifulSoup
import streamlit as st

st.set_page_config(page_title="Simulador Importação DIY", layout="wide", page_icon="🚗")
st.title("🚗 Simulador de Importação Automóvel DIY")

def extrair_dados_mobile_de(url):
    """Extrai os dados do anúncio diretamente no Mobile.de usando cloudscraper."""
    try:
        # Extrai o ID do anúncio a partir do URL
        match_id = re.search(r"id=(\d+)", url) or re.search(r"(\d{8,10})", url)
        if not match_id:
            return None, "Não foi possível identificar o ID do anúncio no URL."

        ad_id = match_id.group(1)
        target_url = f"https://suchen.mobile.de/fahrzeuge/details.html?id={ad_id}&lang=de"

        # Simula um navegador real para contornar bloqueios
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )

        res = scraper.get(target_url, timeout=15)
        if res.status_code != 200:
            return None, f"O Mobile.de recusou a ligação (Código {res.status_code})."

        soup = BeautifulSoup(res.text, "html.parser")
        texto = soup.get_text()

        # Extração de Preço (€)
        preco = 16999.00
        m_preco = re.search(r'["\']price["\']:\s*\{\s*["\']gross["\']:\s*([\d\.]+)', texto) or re.search(r"€\s?([\d\.]+)", texto)
        if m_preco:
            preco = float(m_preco.group(1).replace(".", ""))

        # Extração de Cilindrada (cm³)
        cc = 1200
        m_cc = re.search(r"([\d\.]+)\s?cm³", texto)
        if m_cc:
            cc = int(m_cc.group(1).replace(".", ""))

        # Extração de CO2 (g/km)
        co2 = 115
        m_co2 = re.search(r"([\d]+)\s?g/km", texto, re.IGNORECASE)
        if m_co2:
            co2 = int(m_co2.group(1))

        # Extração de Idade (Anos)
        idade = 4
        m_ano = re.search(r"(0[1-9]|1[0-2])\/((?:19|20)\d{2})", texto) or re.search(r'["\']firstRegistration["\']:\s*["\'](\d{4})', texto)
        if m_ano:
            ano = int(m_ano.group(2) if len(m_ano.groups()) > 1 else m_ano.group(1))
            idade = max(0, 2026 - ano)

        # Extração de Combustível
        combustivel = "Gasolina"
        if re.search(r"Diesel|Gasóleo", texto, re.IGNORECASE):
            combustivel = "Diesel"
        elif re.search(r"Hybrid|Híbrido", texto, re.IGNORECASE):
            combustivel = "Híbrido"
        elif re.search(r"Electric|Elétrico", texto, re.IGNORECASE):
            combustivel = "Elétrico"

        return {
            "preco": preco,
            "cc": cc,
            "co2": co2,
            "idade": idade,
            "combustivel": combustivel
        }, None

    except Exception as e:
        return None, f"Erro ao processar anúncio: {str(e)}"

# Estado inicial dos campos
if "dados" not in st.session_state:
    st.session_state.dados = {
        "preco": 16999.00,
        "combustivel": "Gasolina",
        "cc": 1200,
        "co2": 115,
        "idade": 4
    }

url_link = st.text_input("Link do anúncio (Mobile.de):", placeholder="Cole aqui o URL do anúncio...")

if st.button("🔎 Extrair Dados do Anúncio"):
    if url_link:
        with st.spinner("A importar dados do Mobile.de..."):
            dados_extraidos, erro = extrair_dados_mobile_de(url_link)
            if dados_extraidos:
                st.session_state.dados = dados_extraidos
                st.success("Dados importados com sucesso!")
            else:
                st.warning(f"{erro} Ajusta os valores manualmente se necessário.")

st.divider()

col1, col2 = st.columns(2)
with col1:
    preco = st.number_input("Preço na Origem (€)", value=float(st.session_state.dados["preco"]), step=500.0)
    combustivel = st.selectbox(
        "Combustível",
        ["Gasolina", "Diesel", "Elétrico", "Híbrido Plug-in", "Híbrido"],
        index=["Gasolina", "Diesel", "Elétrico", "Híbrido Plug-in", "Híbrido"].index(st.session_state.dados["combustivel"])
    )
    cilindrada = st.number_input("Cilindrada (cm³)", value=int(st.session_state.dados["cc"]), step=100)

with col2:
    co2 = st.number_input("Emissões CO2 (g/km)", value=int(st.session_state.dados["co2"]), step=5)
    idade = st.number_input("Idade (Anos)", value=int(st.session_state.dados["idade"]), min_value=0)

st.divider()
st.subheader("Custos Adicionais & Legalização")

col3, col4 = st.columns(2)
with col3:
    transporte = st.number_input("Transporte (Camião)", value=1230.00)
    inspecao = st.number_input("Inspeção B", value=93.00)
    despachante = st.number_input("Despachante (70IMT+55RI+Honorários)", value=309.50)

with col4:
    mediacao = st.number_input("Mediação", value=1000.00)
    custos_admin = st.number_input("Custos Admin Concessionário", value=0.00)
    matriculas = st.number_input("Matrículas Portuguesas", value=25.00)

# Cálculo ISV
if combustivel == "Elétrico":
    isv = 0.0
else:
    desc_idade = 0.35 if idade <= 4 else 0.52
    comp_cc = max(0, (cilindrada * 1.09 - 849.03))
    comp_co2 = max(0, (co2 * 1.5 - 50))
    isv = (comp_cc + comp_co2) * (1 - desc_idade)

if isv <= 0:
    isv = 146.19

despesas = transporte + inspecao + despachante + mediacao + custos_admin + matriculas + isv
total = preco + despesas

st.divider()
st.metric("CUSTO TOTAL FINAL", f"{total:,.2f} €", delta=f"{isv:,.2f} € ISV")
