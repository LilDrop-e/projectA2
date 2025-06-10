import streamlit as st
import pandas as pd
from datetime import datetime
import time
from backend.raspador_g1 import raspar_g1, salvar_noticias
from backend.raspador_cnn import raspar_noticias_cnn  # Seu código existente
import os

# Configuração da página
st.set_page_config(
    page_title="Monitor de Notícias",
    page_icon="📰",
    layout="wide"
)

# Sidebar - Controles
with st.sidebar:
    st.title("Configurações")
    
    sites = st.multiselect(
        "Selecione as fontes:",
        ['G1', 'CNN Brasil'],
        default=['G1', 'CNN Brasil']
    )
    
    paginas = st.slider("Número de páginas a raspar (G1)", 1, 5, 2)
    
    if st.button("Atualizar Notícias", type="primary"):
        with st.spinner("Raspando notícias..."):
            noticias = []
            
            if 'G1' in sites:
                noticias_g1 = raspar_g1(paginas=paginas)
                noticias.extend(noticias_g1)
                salvar_noticias(noticias_g1)
            
            if 'CNN Brasil' in sites:
                noticias_cnn = raspar_noticias_cnn()
                noticias.extend([{
                    'titulo': titulo,
                    'site': 'CNN Brasil',
                    'data': datetime.now().strftime('%Y-%m-%d'),
                    'secao': 'Geral'
                } for titulo in noticias_cnn])
                
            # Converter para DataFrame
            df = pd.DataFrame(noticias)
            
            # Salvar dados da sessão
            st.session_state.df_noticias = df
            st.session_state.ultima_atualizacao = datetime.now()
            
        st.success("Notícias atualizadas com sucesso!")

# Página principal
st.title("📰 Monitor de Notícias em Tempo Real")

# Mostrar status
if 'ultima_atualizacao' in st.session_state:
    st.caption(f"Última atualização: {st.session_state.ultima_atualizacao.strftime('%d/%m/%Y %H:%M')}")

# Filtros
if 'df_noticias' in st.session_state:
    df = st.session_state.df_noticias
    
    col1, col2 = st.columns(2)
    
    with col1:
        filtro_data = st.date_input(
            "Filtrar por data",
            value=pd.to_datetime(df['data'].max()).date() if 'data' in df.columns else None
        )
    
    with col2:
        filtro_palavra = st.text_input("Filtrar por palavra-chave")
    
    # Aplicar filtros
    if 'data' in df.columns:
        df_filtrado = df[pd.to_datetime(df['data']).dt.date == filtro_data]
    else:
        df_filtrado = df
    
    if filtro_palavra:
        df_filtrado = df_filtrado[
            df_filtrado['titulo'].str.contains(filtro_palavra, case=False, na=False)
        ]
    
    # Mostrar resultados
    st.subheader(f"Notícias encontradas: {len(df_filtrado)}")
    
    for _, row in df_filtrado.iterrows():
        with st.expander(f"{row['site']} - {row['titulo']}"):
            st.markdown(f"""
            **Seção:** {row.get('secao', 'Geral')}  
            **Data:** {row.get('data', 'Não disponível')}  
            **URL:** {row.get('url', '#') if 'url' in row else '#'}
            """)
            
            if st.button("Ver detalhes", key=row['titulo']):
                st.session_state.noticia_selecionada = row
                st.rerun()
    
    # Estatísticas
    st.subheader("Estatísticas")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total de notícias", len(df))
    
    with col2:
        if filtro_palavra:
            st.metric(
                f"Ocorrências de '{filtro_palavra}'",
                df_filtrado['titulo'].str.count(filtro_palavra, flags=re.IGNORECASE).sum()
            )
    
    # Gráfico de distribuição
    st.bar_chart(df['site'].value_counts())
    
else:
    st.info("Clique em 'Atualizar Notícias' para começar")

# Detalhes da notícia selecionada
if 'noticia_selecionada' in st.session_state:
    noticia = st.session_state.noticia_selecionada
    
    st.subheader("Detalhes da Notícia")
    st.markdown(f"""
    **Site:** {noticia['site']}  
    **Título:** {noticia['titulo']}  
    **Seção:** {noticia.get('secao', 'Geral')}  
    **Data:** {noticia.get('data', 'Não disponível')}  
    """)
    
    if st.button("Voltar"):
        del st.session_state.noticia_selecionada
        st.rerun()
