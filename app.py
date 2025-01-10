import streamlit as st
import pandas as pd
from fuzzywuzzy import process

# Función para encontrar el mejor match usando fuzzywuzzy
def encontrar_mejor_match(nombre, opciones, umbral):
    match, similitud = process.extractOne(nombre, opciones)
    if similitud >= umbral:
        return match
    return None

# Cargar los archivos de insumos y promociones desde la raíz del repositorio
archivo_insumos = "KENTO costo dosificaciones..xlsx"  # Archivo con los insumos
archivo_promociones = "promociones.xlsx"  # Archivo con el diccionario de promociones

# Configuración
umbral_similitud = 85  # Porcentaje mínimo de similitud para considerar un match

# Cargar el archivo de insumos para obtener las unidades
df_insumos = pd.read_excel(archivo_insumos, sheet_name=4)  # Ajusta el índice o nombre de la hoja
unidades_insumos = {}
for i, row in df_insumos.iterrows():
    insumo = row[1]  # Columna B tiene el nombre del insumo
    unidad = row[2]  # Columna C tiene la unidad
    if pd.notna(insumo) and pd.notna(unidad):  # Verificar que no sean NaN
        insumo = str(insumo).strip() if isinstance(insumo, str) else str(insumo)
        unidad = str(unidad).strip() if isinstance(unidad, str) else str(unidad)
        unidades_insumos[insumo] = unidad


# Cargar las promociones
df_promociones = pd.read_excel(archivo_promociones)
promociones = {}
for i, row in df_promociones.iterrows():
    nombre_promocion = row[0]  # Nombre de la promoción
    items = row[1:]  # Resto de las columnas
    promociones[nombre_promocion] = [item for item in items if pd.notna(item)]

# Crear una lista de todos los ítems únicos
items_unicos = set()
for item in promociones.values():
    items_unicos.update(item)

# Leer el archivo de ventas subido por el usuario
st.title('Análisis de Consumo de Insumos')

uploaded_file = st.file_uploader("Sube el archivo de ventas", type=["xlsx"])

if uploaded_file is not None:
    # Cargar las ventas desde el archivo de ventas subido
    df_ventas = pd.read_excel(uploaded_file, sheet_name=3)
    
    # Crear un diccionario para el consumo total de insumos
    consumo_insumos_total = {}

    # Procesar las ventas
    for i, row in df_ventas.iterrows():
        item_vendido = row["Nombre"]  # Nombre del ítem o promoción (ajustar nombre de la columna)
        cantidad_vendida = row["Unidades vendidas"]  # Cantidad vendida (ajustar nombre de la columna)

        # Asegurarse de que cantidad_vendida es un número
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
                if mejor_match_item and mejor_match_item in insumos:
                    for insumo, cantidad in insumos[mejor_match_item].items():
                        try:
                            cantidad = float(cantidad)
                        except ValueError:
                            st.warning(f"Advertencia: 'cantidad' no es numérico para el insumo {insumo}, valor: {cantidad}")
                            continue
                        consumo_insumos_total[insumo] = consumo_insumos_total.get(insumo, 0) + cantidad * cantidad_vendida
        else:  # No es una promoción
            mejor_match_item = encontrar_mejor_match(item_vendido, items_unicos, umbral_similitud)
            if mejor_match_item and mejor_match_item in insumos:
                for insumo, cantidad in insumos[mejor_match_item].items():
                    try:
                        cantidad = float(cantidad)
                    except ValueError:
                        st.warning(f"Advertencia: 'cantidad' no es numérico para el insumo {insumo}, valor: {cantidad}")
                        continue
                    consumo_insumos_total[insumo] = consumo_insumos_total.get(insumo, 0) + cantidad * cantidad_vendida

    # Preparar los datos para exportar, incluyendo unidades
    datos_exportar = []
    for insumo, cantidad_total in consumo_insumos_total.items():
        unidad = unidades_insumos.get(insumo, "Sin unidad")  # Buscar la unidad, si no existe colocar "Sin unidad"
        datos_exportar.append({"Insumo": insumo, "Cantidad Total": cantidad_total, "Unidad": unidad})

    # Convertir los datos a un DataFrame
    df_consumo_insumos_total = pd.DataFrame(datos_exportar)

    # Mostrar el DataFrame en Streamlit
    st.write(df_consumo_insumos_total)

    # Opción para descargar el archivo de resultados
    st.download_button(
        label="Descargar archivo de consumo de insumos",
        data=df_consumo_insumos_total.to_excel(index=False, sheet_name="Consumo Insumos"),
        file_name="consumo_insumos_total.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
