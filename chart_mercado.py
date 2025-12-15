import streamlit as st
import pandas as pd
import altair as alt

MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


def _fmt_pct(x: float) -> str:
    if pd.isna(x):
        return ""
    return f"{x:+.1f}%"


def render_mercado(df: pd.DataFrame) -> None:
    tab_moneda, tab_mercado = st.tabs(["Volumen por moneda", "Mercado"])

    # ============= TAB 1: VOLÚMEN POR MONEDA =============
    with tab_moneda:
        st.subheader("Volumen acumulado por año y moneda")

        d = df.copy()
        d["Anio"] = d["Periodo"].dt.year
        d["Mes"] = d["Periodo"].dt.month
        d["Moneda_short"] = d["Moneda"].replace({"Guaraní": "PYG", "Dólar": "USD"})
        d["Monto_millones"] = d["Monto_en_PYG"] / 1_000_000

        meses = sorted(d["Mes"].unique())
        mes_sel_nombre = st.selectbox(
            "Mes acumulado hasta",
            [MESES[m] for m in meses],
            index=len(meses) - 1,
            key="mes_moneda",
        )
        mes_sel = {v: k for k, v in MESES.items()}[mes_sel_nombre]
        d = d[d["Mes"] <= mes_sel]

        df_year = (
            d.groupby(["Anio", "Moneda_short"], as_index=False)["Monto_millones"]
            .sum()
            .sort_values("Anio")
        )
        df_year["YoY_pct"] = (
            df_year.groupby("Moneda_short")["Monto_millones"].pct_change() * 100
        )
        df_year["YoY_label"] = df_year["YoY_pct"].apply(_fmt_pct)

        base = alt.Chart(df_year)

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

        labels = base.mark_text(fontWeight="bold", dy=-5).encode(
            x=alt.X("Anio:O"),
            xOffset="Moneda_short",
            y="Monto_millones:Q",
            text="YoY_label:N",
            color=alt.value("black"),
        )

        st.altair_chart(bars + labels, use_container_width=True)

    # ============= TAB 2: MERCADO =============
    with tab_mercado:
        st.subheader("Volumen acumulado por año y tipo de mercado")

        d = df.copy()
        d["Anio"] = d["Periodo"].dt.year
        d["Mes"] = d["Periodo"].dt.month
        d["Moneda_short"] = d["Moneda"].replace({"Guaraní": "PYG", "Dólar": "USD"})
        d["Monto_PYG"] = d["Monto_en_PYG"]  # eje Y basado en Monto_en_PYG

        # filtros lado a lado
        c1, c2 = st.columns(2)

        with c1:
            moneda_opt = st.selectbox(
                "Moneda",
                ["Ambas", "PYG", "USD"],
                index=0,
                key="moneda_mercado",
            )

        with c2:
            meses_disp = sorted(d["Mes"].unique())
            mes_sel_nombre2 = st.selectbox(
                "Mes acumulado hasta",
                [MESES[m] for m in meses_disp],
                index=len(meses_disp) - 1,
                key="mes_mercado",
            )

        if moneda_opt != "Ambas":
            d = d[d["Moneda_short"] == moneda_opt]

        mes_sel2 = {v: k for k, v in MESES.items()}[mes_sel_nombre2]
        d = d[d["Mes"] <= mes_sel2]

        # volumen por año y mercado (para barras apiladas)
        df_mkt = (
            d.groupby(["Anio", "Mercado"], as_index=False)["Monto_PYG"]
             .sum()
        )

        # % YoY por segmento (Mercado vs mismo Mercado año anterior)
        df_mkt = df_mkt.sort_values(["Mercado", "Anio"])
        df_mkt["YoY_pct"] = df_mkt.groupby("Mercado")["Monto_PYG"].pct_change() * 100
        df_mkt["YoY_label"] = df_mkt["YoY_pct"].apply(_fmt_pct)

        # >>> ORDEN FIJO DE APILADO (de abajo hacia arriba)
        stack_order = ["Repos", "Mercado Secundario", "Mercado Primario"]
        order_map = {name: i for i, name in enumerate(stack_order)}
        df_mkt["Mercado_orden"] = df_mkt["Mercado"].map(order_map).fillna(99).astype(int)

        df_mkt["Mercado"] = pd.Categorical(
            df_mkt["Mercado"], categories=stack_order, ordered=True
        )
        df_mkt = df_mkt.sort_values(["Anio", "Mercado_orden"])

        # centro de cada segmento según el MISMO orden de apilado
        df_mkt["Monto_base"] = df_mkt.groupby("Anio")["Monto_PYG"].cumsum() - df_mkt["Monto_PYG"]
        df_mkt["Monto_centro"] = df_mkt["Monto_base"] + df_mkt["Monto_PYG"] / 2

        base2 = alt.Chart(df_mkt)

        bars2 = base2.mark_bar().encode(
            x=alt.X("Anio:O", title="Año", sort="ascending"),
            y=alt.Y(
                "Monto_PYG:Q",
                title="Monto (PYG)",
                stack="zero",
                axis=alt.Axis(format="~s"),
            ),
            color=alt.Color(
                "Mercado:N",
                title="Mercado",
                scale=alt.Scale(domain=stack_order),
            ),
            order=alt.Order("Mercado_orden:Q", sort="ascending"),
            tooltip=[
                alt.Tooltip("Anio:O", title="Año"),
                alt.Tooltip("Mercado:N", title="Mercado"),
                alt.Tooltip("Monto_PYG:Q", title="Monto (PYG)", format=",.0f"),
                alt.Tooltip("YoY_label:N", title="% vs año anterior"),
            ],
        )

        # % dentro de cada apilado (legible)
        labels_bg = base2.mark_text(
            fontWeight="bold",
            baseline="middle",
            align="center",
            fontSize=16,
            color="black",
            opacity=0.75,
        ).encode(
            x=alt.X("Anio:O", sort="ascending"),
            y=alt.Y("Monto_centro:Q"),
            text="YoY_label:N",
        )

        labels_fg = base2.mark_text(
            fontWeight="bold",
            baseline="middle",
            align="center",
            fontSize=13,
        ).encode(
            x=alt.X("Anio:O", sort="ascending"),
            y=alt.Y("Monto_centro:Q"),
            text="YoY_label:N",
            color=alt.condition(
                alt.datum.Mercado == "Repos",
                alt.value("white"),   # sobre azul oscuro
                alt.value("black"),   # sobre celeste/rojo
            ),
        )


        st.altair_chart((bars2 + labels_fg).properties(height=420), use_container_width=True)