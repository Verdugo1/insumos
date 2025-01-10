import streamlit as st
import pandas as pd
from fuzzywuzzy import process
import os

# Configuración inicial
st.title("Cálculo de Consumo de Insumos para Kento Sushi 🍣")

# Umbral de similitud ajustable desde la interfaz
umbral_similitud = st.slider("Umbral de similitud para fuzzy matching", min_value=50, max_value=100, value=85)

# Cargar archivos automáticamente desde el repositorio
archivo_ventas = st.file_uploader("Sube el archivo de Ventas Semanales", type=["xlsx"])
ruta_insumos = "./insumos.xlsx"
ruta_promociones = "./promociones.xlsx"

# Verificar si los archivos de insumos y promociones están en la raíz del proyecto
if not os.path.exists(ruta_insumos) or not os.path.exists(ruta_promociones):
    st.error("Los archivos 'insumos.xlsx' y/o 'promociones.xlsx' no se encuentran en la raíz del proyecto.")
else:
    # Cargar insumos
    try:
        data = pd.ExcelFile(ruta_insumos)
        hoja = data.sheet_names[4]  # Cambia al índice o nombre de la hoja que necesitas
        df = pd.read_excel(ruta_insumos, sheet_name=hoja)
        # Crear un diccionario para almacenar los consumos
        insumos = {}
        
        # Variable para guardar el ítem actual
        item_actual = None
        
        # Extraer información de las tablas
        for index, row in df.iterrows():
            # Detectar el inicio de una nueva sección (ítem del menú)
            if isinstance(row[0], str) and "***" in row[0]:  # Columna A contiene ***
                item_actual = row[1].strip()  # El nombre del ítem está en la columna B
                insumos[item_actual] = {}  # Inicializar su diccionario de insumos
        
            # Extraer los insumos y cantidades (si ya tenemos un ítem actual)
            elif item_actual and isinstance(row[1], str):  # Columna B tiene el insumo
                insumo = row[1].strip()  # Nombre del insumo
                cantidad = row[6]  # Columna donde está la cantidad (ajusta según tu archivo)
                if pd.notna(cantidad):  # Asegurarnos de que no sea NaN
                    insumos[item_actual][insumo] = cantidad
        
        # Mostrar el diccionario final
        print("Consumos por ítem:")
        for item, insumos_dict in insumos.items():
            print(f"\n{item}:")
            for insumo, cantidad in insumos_dict.items():
                print(f"  {insumo}: {cantidad}")
    except Exception as e:
        st.error(f"Error al procesar el diccionario de insumos: {e}")
        st.stop()

    # Cargar promociones
    try:
        df_promociones = pd.read_excel(ruta_promociones)
        promociones = {
            row[0]: [item for item in row[1:] if pd.notna(item)]
            for _, row in df_promociones.iterrows()
        }
    except Exception as e:
        st.error(f"Error al cargar el archivo de promociones: {e}")
        st.stop()

    # Procesar archivo de ventas solo si se sube
    if archivo_ventas:
        try:
            df_ventas = pd.read_excel(archivo_ventas, sheet_name=3)
        except Exception as e:
            st.error(f"Error al cargar el archivo de ventas: {e}")
            st.stop()

        # Crear el diccionario de insumos
        try:
            data = pd.ExcelFile(ruta_insumos)
            hoja = data.sheet_names[4]
            df = pd.read_excel(ruta_insumos, sheet_name=hoja)
            insumos = {}
            item_actual = None

            for _, row in df.iterrows():
                if isinstance(row[0], str) and "***" in row[0]:
                    item_actual = row[1].strip()
                    insumos[item_actual] = {}
                elif item_actual and isinstance(row[1], str):
                    insumo = row[1].strip()
                    cantidad = row[6]
                    if pd.notna(cantidad):
                        insumos[item_actual][insumo] = float(cantidad)
        except Exception as e:
            st.error(f"Error al procesar el diccionario de insumos: {e}")
            st.stop()

        # Función para encontrar el mejor match
        def encontrar_mejor_match(nombre, opciones, umbral):
            match, similitud = process.extractOne(nombre, opciones)
            return match if similitud >= umbral else None

        # Crear un diccionario para el consumo total de insumos
        consumo_insumos_total = {}

        # Procesar las ventas
        for _, row in df_ventas.iterrows():
            item_vendido = row["Nombre"]
            cantidad_vendida = row["Unidades vendidas"]

            try:
                cantidad_vendida = float(cantidad_vendida)
            except ValueError:
                continue

            mejor_match_promocion = encontrar_mejor_match(item_vendido, promociones.keys(), umbral_similitud)

            if mejor_match_promocion:
                for item in promociones[mejor_match_promocion]:
                    mejor_match_item = encontrar_mejor_match(item, insumos.keys(), umbral_similitud)
                    if mejor_match_item:
                        for insumo, cantidad in insumos[mejor_match_item].items():
                            consumo_insumos_total[insumo] = consumo_insumos_total.get(insumo, 0) + cantidad * cantidad_vendida
            else:
                mejor_match_item = encontrar_mejor_match(item_vendido, insumos.keys(), umbral_similitud)
                if mejor_match_item:
                    for insumo, cantidad in insumos[mejor_match_item].items():
                        consumo_insumos_total[insumo] = consumo_insumos_total.get(insumo, 0) + cantidad * cantidad_vendida

        # Crear el DataFrame final con unidades
        datos_exportar = [
            {"Insumo": insumo, "Cantidad Total": cantidad_total, "Unidad": unidades_insumos.get(insumo, "Sin unidad")}
            for insumo, cantidad_total in consumo_insumos_total.items()
        ]
        df_consumo_insumos_total = pd.DataFrame(datos_exportar)

        # Mostrar el resultado en la aplicación
        st.subheader("Consumo Total de Insumos")
        st.dataframe(df_consumo_insumos_total)

        # Botón para exportar el archivo
        if st.button("Exportar a Excel"):
            ruta_salida = "consumo_insumos_total.xlsx"
            df_consumo_insumos_total.to_excel(ruta_salida, index=False, sheet_name="Consumo Insumos")
            st.success(f"Archivo exportado exitosamente: {ruta_salida}")
            with open(ruta_salida, "rb") as file:
                st.download_button(
                    label="Descargar archivo",
                    data=file,
                    file_name="consumo_insumos_total.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    else:
        st.warning("Por favor, sube el archivo de ventas para continuar.")
