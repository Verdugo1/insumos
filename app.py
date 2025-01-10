import streamlit as st
import pandas as pd
from fuzzywuzzy import process

# Función para procesar las tablas de insumos
def procesar_insumos(archivo):
    data = pd.ExcelFile(archivo)
    hoja = data.sheet_names[4]  # Ajusta según la hoja que necesitas
    df = pd.read_excel(archivo, sheet_name=hoja)

    insumos = {}
    item_actual = None

    for index, row in df.iterrows():
        if isinstance(row[0], str) and "***" in row[0]:  # Detectar secciones
            item_actual = row[1].strip()  # Nombre del ítem
            insumos[item_actual] = {}
        elif item_actual and isinstance(row[1], str):
            insumo = row[1].strip()
            cantidad = row[6]  # Ajusta según la columna de cantidad
            if pd.notna(cantidad):
                insumos[item_actual][insumo] = cantidad

    return insumos

# Función para encontrar el mejor match usando fuzzywuzzy
def encontrar_mejor_match(nombre, opciones, umbral):
    match, similitud = process.extractOne(nombre, opciones)
    if similitud >= umbral:
        return match
    return None

# Función principal para procesar las ventas
def procesar_ventas(archivo_ventas, archivo_promociones, insumos, umbral_similitud):
    df_promociones = pd.read_excel(archivo_promociones)
    df_ventas = pd.read_excel(archivo_ventas, sheet_name=3)

    promociones = {}
    for i, row in df_promociones.iterrows():
        nombre_promocion = row[0]
        items = row[1:]
        promociones[nombre_promocion] = [item for item in items if pd.notna(item)]

    items_unicos = set()
    for items in promociones.values():
        items_unicos.update(items)
    items_unicos = list(items_unicos)

    consumo_total = {}
    for i, row in df_ventas.iterrows():
        item_vendido = row["Nombre"]
        cantidad_vendida = row["Unidades vendidas"]

        mejor_match = encontrar_mejor_match(item_vendido, promociones.keys(), umbral_similitud)
        if mejor_match:
            for item in promociones[mejor_match]:
                item_match = encontrar_mejor_match(item, items_unicos, umbral_similitud)
                if item_match:
                    consumo_total[item_match] = consumo_total.get(item_match, 0) + cantidad_vendida
        else:
            item_match = encontrar_mejor_match(item_vendido, items_unicos, umbral_similitud)
            if item_match:
                consumo_total[item_match] = consumo_total.get(item_match, 0) + cantidad_vendida

    return pd.DataFrame(consumo_total.items(), columns=["Item", "Cantidad Consumida"])

# Interfaz Streamlit
st.title("Procesador de Ventas y Consumos")
st.write("Sube el archivo de ventas para procesar los datos.")

# Cargar archivos en el backend
archivo_insumos = "/insumos.xlsx"  # Ruta del archivo de insumos en el backend
archivo_promociones = "/promociones.xlsx"  # Ruta del archivo de promociones en el backend

# Subida de archivo de ventas por parte del usuario
archivo_ventas = st.file_uploader("Sube el archivo de ventas", type=["xlsx"])
umbral_similitud = st.slider("Umbral de similitud", 0, 100, 80)

if archivo_ventas:
    st.success("Archivo de ventas cargado correctamente.")

    # Procesar archivos
    insumos = procesar_insumos(archivo_insumos)
    resultado = procesar_ventas(archivo_ventas, archivo_promociones, insumos, umbral_similitud)

    st.write("Resultado del procesamiento:")
    st.dataframe(resultado)

    # Botón para descargar el archivo procesado
    if st.button("Descargar resultado como Excel"):
        resultado_excel = resultado.to_excel(index=False, engine="openpyxl")
        st.download_button(
            label="Descargar Excel",
            data=resultado_excel,
            file_name="resultado_procesado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
