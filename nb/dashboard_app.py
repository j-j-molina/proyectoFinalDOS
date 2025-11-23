import os

import pandas as pd
import streamlit as st


# ==============================
# 1. Carga de datos (con caché)
# ==============================
@st.cache_data
def load_data():
    """
    Carga el archivo maestro sipsa_master.csv desde las rutas más probables.
    Devuelve un DataFrame con las columnas esperadas:
    fecha, grupo, producto, codigo_cpc_ac, mercado, precio_promedio_por_kilogramo
    """
    possible_paths = [
        "data/processed/sipsa_master.csv",
        "/content/data/processed/sipsa_master.csv",
    ]

    df = None
    chosen_path = None

    for path in possible_paths:
        if os.path.exists(path):
            df = pd.read_csv(path, parse_dates=["fecha"])
            chosen_path = path
            break

    if df is None:
        return None, None

    # Normalización suave por si acaso
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("*", "", regex=False)
    )

    for col in ["grupo", "producto", "mercado"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()

    # Nos aseguramos de que la columna de precio sea numérica
    if "precio_promedio_por_kilogramo" in df.columns:
        df["precio_promedio_por_kilogramo"] = pd.to_numeric(
            df["precio_promedio_por_kilogramo"], errors="coerce"
        )

    # Quitamos filas sin fecha o sin precio
    if "fecha" in df.columns and "precio_promedio_por_kilogramo" in df.columns:
        df = df.dropna(subset=["fecha", "precio_promedio_por_kilogramo"])

    return df, chosen_path


# ==============================
# 2. Layout principal
# ==============================
def main():
    st.set_page_config(
        page_title="Dashboard de Precios de Alimentos (SIPSA-P)",
        layout="wide",
    )

    st.title("📊 Dashboard de Precios de Alimentos – SIPSA-P")
    st.markdown(
        """
        Este dashboard usa el dataset consolidado **`sipsa_master.csv`** para explorar:

        - Evolución de precios promedio por producto y mercado  
        - Comparación de mercados (más caros / más baratos)  
        - Indicadores rápidos para apoyar decisiones sobre costo de vida

        Usa el panel lateral para filtrar.
        """
    )

    # ---- Cargar datos ----
    df, path = load_data()

    if df is None or df.empty:
        st.error(
            "No encontré el archivo `sipsa_master.csv`.\n\n"
            "Revisa que exista en `data/processed/sipsa_master.csv` "
            "o `/content/data/processed/sipsa_master.csv`."
        )
        st.stop()

    with st.sidebar:
        st.header("⚙️ Filtros")

        if path is not None:
            st.caption(f"Usando archivo: `{path}`")

        # Rango de fechas
        min_date = df["fecha"].min()
        max_date = df["fecha"].max()

        start_date, end_date = st.slider(
            "Rango de fechas",
            min_value=min_date.to_pydatetime(),
            max_value=max_date.to_pydatetime(),
            value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
            format="DD/MM/YYYY",
        )

        # Filtrar por fecha
        mask_fecha = (df["fecha"] >= pd.to_datetime(start_date)) & (
            df["fecha"] <= pd.to_datetime(end_date)
        )
        df_periodo = df[mask_fecha].copy()

        # Selección de producto
        productos = sorted(df_periodo["producto"].dropna().unique())
        producto_sel = st.selectbox(
            "Producto",
            options=productos,
            index=0 if productos else None,
        )

        # Filtrar por producto seleccionado
        df_producto = df_periodo[df_periodo["producto"] == producto_sel].copy()

        # Selección de mercados
        mercados_disponibles = sorted(df_producto["mercado"].dropna().unique())
        mercados_default = (
            mercados_disponibles
            if len(mercados_disponibles) <= 5
            else mercados_disponibles[:5]
        )

        mercados_sel = st.multiselect(
            "Mercados",
            options=mercados_disponibles,
            default=mercados_default,
            help="Si no seleccionas ninguno, se usarán todos los mercados.",
        )

        if mercados_sel:
            df_producto = df_producto[df_producto["mercado"].isin(mercados_sel)]

    # Si tras filtros no hay datos, avisamos y paramos
    if df_producto.empty:
        st.warning(
            "No hay datos para la combinación de filtros seleccionada "
            "(fechas, producto, mercados). Prueba con otro rango."
        )
        st.stop()

    # ==============================
    # 3. KPIs principales
    # ==============================
    st.subheader(f"📌 Indicadores para **{producto_sel}**")

    df_producto_sorted = df_producto.sort_values("fecha")

    # Precio promedio inicial y final (promedio sobre mercados)
    primer_fecha = df_producto_sorted["fecha"].min()
    ultima_fecha = df_producto_sorted["fecha"].max()

    precio_inicial = (
        df_producto_sorted[df_producto_sorted["fecha"] == primer_fecha]
        ["precio_promedio_por_kilogramo"]
        .mean()
    )

    precio_final = (
        df_producto_sorted[df_producto_sorted["fecha"] == ultima_fecha]
        ["precio_promedio_por_kilogramo"]
        .mean()
    )

    variacion_pct = (
        (precio_final / precio_inicial - 1) * 100 if precio_inicial > 0 else None
    )

    precio_prom_periodo = df_producto_sorted["precio_promedio_por_kilogramo"].mean()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Precio promedio actual (última fecha)",
        f"${precio_final:,.0f} / kg".replace(",", "."),
        help=f"Promedio de todos los mercados seleccionados en {ultima_fecha.date()}",
    )

    col2.metric(
        "Precio promedio en el periodo",
        f"${precio_prom_periodo:,.0f} / kg".replace(",", "."),
    )

    if variacion_pct is not None:
        col3.metric(
            "Variación % entre primera y última fecha",
            f"{variacion_pct:,.1f} %",
        )
    else:
        col3.metric("Variación %", "N/A")

    # ==============================
    # 4. Gráficos principales
    # ==============================
    tab1, tab2 = st.tabs(
        ["📈 Serie de tiempo por mercado", "🏆 Mercados más caros / baratos"]
    )

    # --- Tab 1: Serie de tiempo ---
    with tab1:
        st.markdown(
            f"### Evolución del precio de **{producto_sel}** por mercado "
            f"({start_date.date()} a {end_date.date()})"
        )

        serie = (
            df_producto_sorted.groupby(["fecha", "mercado"])[
                "precio_promedio_por_kilogramo"
            ]
            .mean()
            .reset_index()
        )

        # Pivot para que Streamlit trace una línea por mercado
        pivot = serie.pivot(
            index="fecha",
            columns="mercado",
            values="precio_promedio_por_kilogramo",
        )

        st.line_chart(pivot)

        st.caption(
            "Cada línea representa el precio promedio por kilogramo en un mercado. "
            "Sirve para ver qué mercados son sistemáticamente más caros o más baratos."
        )

    # --- Tab 2: ranking de mercados ---
    with tab2:
        st.markdown(
            f"### Mercados más caros y más baratos para **{producto_sel}** "
            f"en el periodo seleccionado"
        )

        ranking_mercados = (
            df_producto_sorted.groupby("mercado")[
                "precio_promedio_por_kilogramo"
            ]
            .mean()
            .sort_values(ascending=False)
        )

        top_n = 10 if len(ranking_mercados) > 10 else len(ranking_mercados)

        col_izq, col_der = st.columns(2)

        with col_izq:
            st.markdown(f"#### 🟥 Top {top_n} mercados más caros")
            st.bar_chart(ranking_mercados.head(top_n))

        with col_der:
            st.markdown(f"#### 🟩 Top {top_n} mercados más baratos")
            st.bar_chart(ranking_mercados.tail(top_n).sort_values(ascending=True))

        st.dataframe(
            ranking_mercados.reset_index().rename(
                columns={
                    "mercado": "Mercado",
                    "precio_promedio_por_kilogramo": "Precio promedio ($/kg)",
                }
            ),
            use_container_width=True,
        )

        st.caption(
            "Esta vista ayuda a identificar dónde es más costoso comprar el producto "
            "y dónde es relativamente más barato."
        )

    # ==============================
    # 5. Vista rápida general (opcional)
    # ==============================
    st.markdown("---")
    st.subheader("🔎 Tabla filtrada (para inspección rápida)")

    st.dataframe(
        df_producto_sorted[
            ["fecha", "mercado", "grupo", "producto", "codigo_cpc_ac",
             "precio_promedio_por_kilogramo"]
        ].sort_values(["fecha", "mercado"]),
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
