import streamlit as st
import pandas as pd
from chart_mercado import render_mercado

FILE_PATH = "mercado bursatil.xlsx"


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_excel(FILE_PATH)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={"Monto en PYG": "Monto_en_PYG"})
    df["Periodo"] = pd.to_datetime(df["Periodo"])
    return df


def main() -> None:
    df = load_data()

    st.title("Mercado bursátil Paraguay")

    pagina = st.sidebar.selectbox(
        "Navegación",
        ["Datos", "Mercado bursátil"],
        index=0,
    )

    if pagina == "Datos":
        st.subheader("Datos originales")
        st.dataframe(df, use_container_width=True)

        st.markdown(
            """
**Fuente**

Datos oficiales del [Banco Central del Paraguay – Mercado bursátil]
(https://www.bcp.gov.py/web/institucional/mercado-bursatil).
"""
        )
    else:
        render_mercado(df)


if __name__ == "__main__":
    main()
