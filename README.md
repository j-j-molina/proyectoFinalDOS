# proyectoFinalDOS – Dashboard de Precios de Alimentos (SIPSA-P)

Dashboard interactivo en Streamlit para explorar precios de alimentos del sistema SIPSA-P (Colombia). Permite filtrar por fechas, producto y mercados, ver KPIs rápidos, series de tiempo y rankings de mercados más caros/baratos.

## Estructura del proyecto
- `nb/dashboard_app.py`: aplicación principal de Streamlit.
- `nb/PrecioAlimentos.ipynb`: notebook usado para análisis y consolidación.
- `data/processed/sipsa_master.csv`: dataset consolidado que consume el dashboard.
- `data/raw/`: insumos originales (archivos mensuales).
- `.venv/`: entorno virtual local (no se versiona).
- `doc/Proyecto Final.pdf`: documento del proyecto.

## Requisitos previos
- Python 3.13 (o 3.10+ debería funcionar).
- pip actualizado (`python3 -m pip install --upgrade pip`).
- Acceso al dataset consolidado en `data/processed/sipsa_master.csv`.

## Instalación rápida
```sh
# 1) Crear y activar un entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # en Windows: .venv\Scripts\activate

# 2) Instalar dependencias mínimas
pip install streamlit pandas
```

> Si usas otro entorno, asegúrate de tener también `pyarrow`, `altair` y `numpy` (se instalan como dependencias de Streamlit).

## Ejecución del dashboard
```sh
source .venv/bin/activate
streamlit run nb/dashboard_app.py
```

Luego abre el navegador en `http://localhost:8501`. El panel lateral permite elegir rango de fechas, producto y mercados. Los KPIs muestran precio actual, promedio del periodo y variación porcentual; las pestañas incluyen la serie temporal por mercado y el ranking de mercados más caros/baratos.

### Datos esperados
- Archivo: `data/processed/sipsa_master.csv`.
- Columnas mínimas: `fecha`, `grupo`, `producto`, `codigo_cpc_ac`, `mercado`, `precio_promedio_por_kilogramo`.
- Fechas en formato reconocible por pandas (se parsean a datetime).

## Notas útiles
- Para detener el servidor: `pkill -f "streamlit run nb/dashboard_app.py"` (o Ctrl+C en la terminal donde corre).
- Si modificas el dataset, deja el archivo en `data/processed/` con el mismo nombre para que la app lo detecte automáticamente.
