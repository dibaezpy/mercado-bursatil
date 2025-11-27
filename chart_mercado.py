import streamlit as st
import pandas as pd
import altair as alt

MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


def render_mercado(df: pd.DataFrame) -> None:
    tab_mercado, tab_instrumento = st.tabs(["Mercado", "Por instrumento"])

    # ======= TAB 1: MERCADO =======
    with tab_mercado:
        st.subheader("Volumen acumulado por año y moneda")

        d = df.copy()
        d["Anio"] = d["Periodo"].dt.year
        d["Mes"] = d["Periodo"].dt.month
        d["Moneda_short"] = d["Moneda"].replace({"Guaraní": "PYG", "Dólar": "USD"})
        d["Monto_millones"] = d["Monto_en_PYG"] / 1_000_000

        # selector de mes (acumulado enero -> mes elegido)
        meses_disp = sorted(d["Mes"].unique())
        mes_sel_nombre = st.selectbox(
            "Mes acumulado hasta",
            [MESES[m] for m in meses_disp],
            index=len(meses_disp) - 1,
        )
        mes_sel = {v: k for k, v in MESES.items()}[mes_sel_nombre]

        d = d[d["Mes"] <= mes_sel]

        # agregación anual por moneda
        df_year = (
            d.groupby(["Anio", "Moneda_short"], as_index=False)["Monto_millones"]
             .sum()
             .sort_values("Anio")
        )

        # % vs año anterior por moneda
        df_year["YoY_pct"] = (
            df_year.groupby("Moneda_short")["Monto_millones"]
                   .pct_change() * 100
        )
        def fmt_pct(x):
            if pd.isna(x):
                return ""
            return f"{x:+.1f}%"
        df_year["YoY_label"] = df_year["YoY_pct"].apply(fmt_pct)

        base = alt.Chart(df_year)

        # barras agrupadas
        bars = base.mark_bar().encode(
            x=alt.X("Anio:O", title="Año"),
            xOffset="Moneda_short",
            y=alt.Y("Monto_millones:Q", title="Millones de PYG"),
            color=alt.Color("Moneda_short:N", title="Moneda"),
            tooltip=[
                "Anio:O",
                "Moneda_short:N",
                alt.Tooltip("Monto_millones:Q", title="Millones PYG", format=",.1f"),
                alt.Tooltip("YoY_label:N", title="% vs año anterior"),
            ],
        )

        # etiquetas con el % arriba de cada barra
        labels = base.mark_text(dy=-5).encode(
            x=alt.X("Anio:O"),
            xOffset="Moneda_short",
            y="Monto_millones:Q",
            text="YoY_label:N",
            color=alt.Color("Moneda_short:N", legend=None),
        )

        st.altair_chart(bars + labels, use_container_width=True)


    # ======= TAB 2: INSTRUMENTO =======
    with tab_instrumento:
        st.subheader("Volumen por instrumento (total período)")

        d2 = df.copy()
        d2["Monto_millones"] = d2["Monto_en_PYG"] / 1_000_000

        df_i = (
            d2.groupby("Instrumento", as_index=False)["Monto_millones"]
             .sum()
             .sort_values("Monto_millones", ascending=False)
        )

        chart2 = (
            alt.Chart(df_i)
            .mark_bar()
            .encode(
                x=alt.X("Monto_millones:Q", title="Millones de PYG"),
                y=alt.Y("Instrumento:N", sort="-x"),
                tooltip=[
                    "Instrumento:N",
                    alt.Tooltip("Monto_millones:Q", title="Millones PYG", format=",.1f"),
                ],
            )
        )

        st.altair_chart(chart2, use_container_width=True)
