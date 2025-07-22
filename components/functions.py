import streamlit as st
import pandas as pd
from datetime import datetime

@st.cache_data
def load_data(file_path):
    try:
        return pd.read_csv(file_path, encoding='utf-8', sep=';', on_bad_lines='skip')
    except TypeError:
        return pd.read_csv(file_path, encoding='utf-8', sep=';', error_bad_lines=False)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo CSV: {e}")
        return pd.DataFrame()

def save_data(df, file_path, suffix=""):
    if file_path.lower().endswith('.csv'):
        if not suffix:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = file_path.replace('.csv', f'_{timestamp}.csv')
            df.to_csv(backup_path, index=False)
        df.to_csv(file_path, index=False)
        return file_path
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if not suffix else suffix
        novo_arquivo = file_path.replace('.xlsx', f'_{timestamp}.xlsx')
        df.to_excel(novo_arquivo, index=False)
        return novo_arquivo

def mostrar_diferencas(df_original, df_editado):
    diff = []
    if len(df_editado) > len(df_original):
        novas_linhas = df_editado.iloc[len(df_original):]
        diff.append("Novas linhas adicionadas:")
        diff.append(novas_linhas)
    alteracoes = []
    linhas_comuns = min(len(df_original), len(df_editado))
    for i in range(linhas_comuns):
        for col in df_original.columns:
            val_orig = df_original.iloc[i][col]
            val_edit = df_editado.iloc[i][col]
            if (pd.isna(val_orig) and pd.isna(val_edit)):
                continue
            if str(val_orig) != str(val_edit):
                alteracoes.append(
                    f"Linha {i+1}, Coluna '{col}': '{val_orig if not pd.isna(val_orig) else ''}' → '{val_edit if not pd.isna(val_edit) else ''}'"
                )
    if alteracoes:
        diff.append("Células alteradas:")
        diff.extend(alteracoes)
    if not diff:
        diff.append("Nenhuma diferença encontrada.")
    return diff
