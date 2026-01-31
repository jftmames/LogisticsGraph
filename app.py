import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="LogisticsGraph Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏭 LogisticsGraph Pro: Supply Chain Risk Analysis")
st.caption("Herramienta de simulación de resiliencia y optimización de rutas NoSQL")

# --- 1. INICIALIZACIÓN DEL GRAFO (PERSISTENCIA) ---
if 'G' not in st.session_state:
    # Usamos DiGraph porque el flujo logístico es DIRIGIDO (Origen -> Destino)
    st.session_state.G = nx.DiGraph()
    
    # Nodos iniciales (Fábricas, Puertos, Almacenes, Tiendas)
    nodos_semilla = [
        ("Fabrica_Shanghai", {"tipo": "Fabrica"}),
        ("Puerto_Rotterdam", {"tipo": "Puerto"}),
        ("Puerto_Valencia", {"tipo": "Puerto"}),
        ("Almacen_Zaragoza", {"tipo": "Almacen"}),
        ("Tienda_Madrid", {"tipo": "Tienda"}),
    ]
    for nodo, attrs in nodos_semilla:
        st.session_state.G.add_node(nodo, **attrs)
    
    # Rutas iniciales (con peso de tiempo en días)
    rutas_semilla = [
        ("Fabrica_Shanghai", "Puerto_Rotterdam", 35),
        ("Fabrica_Shanghai", "Puerto_Valencia", 22),
        ("Puerto_Valencia", "Almacen_Zaragoza", 2),
        ("Almacen_Zaragoza", "Tienda_Madrid", 1),
    ]
    for u, v, t in rutas_semilla:
        st.session_state.G.add_edge(u, v, tiempo_dias=t)

# --- 2. BARRA LATERAL: GESTIÓN DE LA RED ---
with st.sidebar:
    st.header("🚚 Panel de Control")
    
    with st.expander("➕ Añadir Nodo"):
        nuevo_nodo = st.text_input("Nombre de ubicación")
        tipo_nodo = st.selectbox("Categoría", ["Fabrica", "Puerto", "Almacen", "Tienda"])
        if st.button("Registrar Ubicación"):
            if nuevo_nodo:
                st.session_state.G.add_node(nuevo_nodo, tipo=tipo_nodo)
                st.rerun()

    with st.expander("🔗 Crear Ruta"):
        nodos = list(st.session_state.G.nodes())
        origen = st.selectbox("Origen", nodos)
        destino = st.selectbox("Destino", nodos)
        tiempo = st.number_input("Tiempo (días)", min_value=1, value=1)
        if st.button("Conectar Ruta"):
            if origen != destino:
                st.session_state.G.add_edge(origen, destino, tiempo_dias=tiempo)
                st.success(f"Conectado: {origen} -> {destino}")
                st.rerun()

    st.divider()
    
    # --- SIMULADOR DE RIESGOS ---
    st.header("⚠️ Stress Test")
    st.caption("Simula la caída de un puerto o almacén")
    nodo_bloqueo = st.selectbox("Seleccionar nodo para bloquear:", nodos)
    
    if st.button("🔴 Ejecutar Stress Test"):
        # Calculamos descendientes ANTES del bloqueo
        # Asumimos que el suministro principal sale de Shanghai
        fabrica_raiz = "Fabrica_Shanghai"
        if fabrica_raiz in st.session_state.G:
            originales = nx.descendants(st.session_state.G, fabrica_raiz)
            
            # Copiamos el grafo y eliminamos el nodo bloqueado
            G_temp = st.session_state.G.copy()
            G_temp.remove_node(nodo_bloqueo)
            
            despues = nx.descendants(G_temp, fabrica_raiz)
            perdidos = (originales - despues) - {nodo_bloqueo}
            
            if perdidos:
                st.error(f"¡BLOQUEO CRÍTICO! {len(perdidos)} ubicaciones han perdido el suministro.")
                for p in perdidos:
                    st.write(f"❌ {p}")
            else:
                st.success("✅ Red Resiliente: No se han perdido conexiones finales.")

# --- 3. CUERPO PRINCIPAL ---
tab_viz, tab_opt = st.tabs(["🗺️ Mapa Logístico", "⏱️ Optimización de Tiempos"])

with tab_viz:
    col_map, col_info = st.columns([3, 1])
    
    with col_map:
        fig, ax = plt.subplots(figsize=(10, 7))
        # Colores por tipo de nodo
        colores_dict = {"Fabrica": "#e74c3c", "Puerto": "#f1c40f", "Almacen": "#3498db", "Tienda": "#2ecc71"}
        colores_nodos = [colores_dict.get(st.session_state.G.nodes[n].get('tipo', 'Tienda'), "#95a5a6") 
                         for n in st.session_state.G.nodes()]
        
        pos = nx.spring_layout(st.session_state.G, seed=42)
        nx.draw(st.session_state.G, pos, with_labels=True, node_color=colores_nodos, 
                node_size=2500, font_size=10, font_weight='bold', arrows=True, arrowsize=20)
        
        st.pyplot(fig)

    with col_info:
        st.write("**Leyenda:**")
        st.markdown("🔴 Fábrica\n\n🟡 Puerto\n\n🔵 Almacén\n\n🟢 Tienda")
        st.divider()
        st.metric("Total Rutas Activas", len(st.session_state.G.edges()))

with tab_opt:
    st.subheader("Buscador de Rutas Críticas")
    nodos_lista = list(st.session_state.G.nodes())
    
    c1, c2 = st.columns(2)
    with c1:
        start_node = st.selectbox("Punto de Partida", nodos_lista, index=0)
    with c2:
        end_node = st.selectbox("Punto de Entrega", nodos_lista, index=len(nodos_lista)-1)
    
    if st.button("Calcular Ruta Óptima"):
        try:
            # Algoritmo de Dijkstra para encontrar el camino más corto por tiempo
            camino = nx.shortest_path(st.session_state.G, source=start_node, target=end_node, weight='tiempo_dias')
            tiempo_total = nx.shortest_path_length(st.session_state.G, source=start_node, target=end_node, weight='tiempo_dias')
            
            st.info(f"📍 **Ruta Óptima:** {' ➡️ '.join(camino)}")
            st.metric("Tiempo Total de Tránsito", f"{tiempo_total} días")
        except nx.NetworkXNoPath:
            st.error("No existe una ruta conectada entre estos dos puntos.")
        except Exception as e:
            st.error(f"Error en el cálculo: {e}")
