import pandas as pd
import streamlit as st
from fuzzywuzzy import process

# Función para cargar archivo Excel
def cargar_excel(archivo):
    return pd.ExcelFile(archivo)

# Función para encontrar el mejor match usando fuzzywuzzy
def encontrar_mejor_match(nombre, opciones, umbral):
    match, similitud = process.extractOne(nombre, opciones)
    if similitud >= umbral:
        return match
    return None

# Título de la app
st.title("Cálculo de Consumo de Insumos para Ventas")

# Subir archivos
archivo_insumos = st.file_uploader("Sube el archivo de insumos (KENTO costo dosificaciones..xlsx)", type=["xlsx"])
archivo_ventas = st.file_uploader("Sube el archivo de ventas", type=["xlsx"])
archivo_promociones = st.file_uploader("Sube el archivo de promociones", type=["xlsx"])

# Validar si los archivos han sido subidos
if archivo_insumos and archivo_ventas and archivo_promociones:
    # Leer archivos de insumos, ventas y promociones
    df_insumos = pd.read_excel(archivo_insumos, sheet_name=4)  # Ajustar el índice de la hoja si es necesario
    df_ventas = pd.read_excel(archivo_ventas, sheet_name=3)  # Ajustar el índice de la hoja si es necesario
    df_promociones = pd.read_excel(archivo_promociones)
    
    # Crear diccionario de insumos y unidades
    unidades_insumos = {}
    for i, row in df_insumos.iterrows():
        insumo = row[1]  # Columna B tiene el nombre del insumo
        unidad = row[2]  # Columna C tiene la unidad
        if pd.notna(insumo) and pd.notna(unidad):  # Verificar que no sean NaN
            unidades_insumos[str(insumo).strip()] = str(unidad).strip()
    
    # Crear diccionario de promociones
    promociones = {}
    for i, row in df_promociones.iterrows():
        nombre_promocion = row[0]  # Nombre de la promoción
        items = row[1:]  # Resto de las columnas
        promociones[nombre_promocion] = [item for item in items if pd.notna(item)]
    
    # Crear lista de items únicos
    items_unicos = set(df_insumos.iloc[:, 1])  # Ajustar la columna si es necesario
    for items in promociones.values():
        items_unicos.update(items)
    items_unicos = list(items_unicos)
    
    # Diccionario para el consumo total de insumos
    consumo_insumos_total = {}
    
    # Procesar ventas
    umbral_similitud = 85  # Umbral de similitud
    for i, row in df_ventas.iterrows():
        item_vendido = row["Nombre"]  # Ajustar nombre de la columna
        cantidad_vendida = row["Unidades vendidas"]  # Ajustar nombre de la columna

        try:
            cantidad_vendida = float(cantidad_vendida)
        except ValueError:
            st.warning(f"Advertencia: 'cantidad_vendida' no es numérico para la fila {i}, valor: {cantidad_vendida}")
            continue

        # Intentar encontrar el ítem en promociones
        mejor_match_promocion = encontrar_mejor_match(item_vendido, promociones.keys(), umbral_similitud)
        
        if mejor_match_promocion:  # Es una promoción
            for item in promociones[mejor_match_promocion]:
                mejor_match_item = encontrar_mejor_match(item, items_unicos, umbral_similitud)
                if mejor_match_item in df_insumos.iloc[:, 1].values:
                    for insumo, cantidad in df_insumos[df_insumos.iloc[:, 1] == mejor_match_item].iterrows():
                        cantidad = float(cantidad[6])  # Ajusta la columna de cantidad
                        consumo_insumos_total[insumo] = consumo_insumos_total.get(insumo, 0) + cantidad * cantidad_vendida
        else:  # No es una promoción
            mejor_match_item = encontrar_mejor_match(item_vendido, items_unicos, umbral_similitud)
            if mejor_match_item in df_insumos.iloc[:, 1].values:
                for insumo, cantidad in df_insumos[df_insumos.iloc[:, 1] == mejor_match_item].iterrows():
                    cantidad = float(cantidad[6])  # Ajusta la columna de cantidad
                    consumo_insumos_total[insumo] = consumo_insumos_total.get(insumo, 0) + cantidad * cantidad_vendida
    
    # Preparar los datos para exportar, incluyendo unidades
    datos_exportar = []
    for insumo, cantidad_total in consumo_insumos_total.items():
        unidad = unidades_insumos.get(insumo, "Sin unidad")  # Buscar la unidad, si no existe colocar "Sin unidad"
        datos_exportar.append({"Insumo": insumo, "Cantidad Total": cantidad_total, "Unidad": unidad})
    
    # Mostrar los resultados en Streamlit
    st.subheader("Consumo de Insumos Total")
    df_consumo_insumos_total = pd.DataFrame(datos_exportar)
    st.write(df_consumo_insumos_total)
    
    # Permitir exportar los resultados a un archivo Excel
    archivo_salida = st.download_button(
        label="Descargar archivo de consumo de insumos",
        data=df_consumo_insumos_total.to_excel(index=False, sheet_name="Consumo Insumos"),
        file_name="consumo_insumos_total.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.warning("Por favor sube todos los archivos necesarios.")
