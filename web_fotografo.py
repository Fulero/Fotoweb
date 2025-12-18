# -*- coding: utf-8 -*-
"""
Versión Final Optimizada del Portafolio Fotográfico
- Sin indicadores molestos de optimización
- Carga más rápida y silenciosa
- Interface limpia y profesional
- Performance mejorada

@author: Office Agent - Versión Final
"""

import streamlit as st
import os
from PIL import Image
import io
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from pathlib import Path
import hashlib

# Configuración de la página
st.set_page_config(
    page_title="El Fotografo", 
    page_icon="📷", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== CONFIGURACIÓN DE OPTIMIZACIÓN ====================

# Configuración de thumbnails y compresión
THUMBNAIL_SIZE = (400, 300)  # Tamaño de thumbnails
PREVIEW_SIZE = (800, 600)    # Tamaño de vista previa
THUMBNAIL_QUALITY = 85       # Calidad de thumbnails (1-100)
PREVIEW_QUALITY = 90         # Calidad de vista previa
IMAGES_PER_PAGE = 8          # Más imágenes por página para menos clics
CACHE_DIR = "cache"          # Directorio de cache
THUMBNAILS_DIR = f"{CACHE_DIR}/thumbnails"
PREVIEWS_DIR = f"{CACHE_DIR}/previews"

# Crear directorios de cache silenciosamente
os.makedirs(THUMBNAILS_DIR, exist_ok=True)
os.makedirs(PREVIEWS_DIR, exist_ok=True)

# ==================== FUNCIONES DE OPTIMIZACIÓN SILENCIOSAS ====================

@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_image_hash(image_path):
    """Genera hash único para cada imagen para cache inteligente"""
    try:
        with open(image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return str(hash(image_path))

@st.cache_resource
def setup_thread_pool():
    """Configura pool de threads para procesamiento paralelo"""
    return ThreadPoolExecutor(max_workers=6)  # Más workers para mayor velocidad

def optimize_image_for_web(image_path, output_path, target_size, quality=85, format='WebP'):
    """
    Optimiza imagen para web con compresión y redimensionamiento - SILENCIOSO
    """
    try:
        with Image.open(image_path) as img:
            # Convertir a RGB si es necesario (para WebP)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Redimensionar manteniendo aspecto
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            # Guardar optimizado
            save_kwargs = {
                'format': format,
                'quality': quality,
                'optimize': True
            }
            
            if format.upper() == 'WEBP':
                save_kwargs['method'] = 6  # Mejor compresión WebP
            
            img.save(output_path, **save_kwargs)
            return True
    except Exception:
        return False

@st.cache_data(ttl=7200)  # Cache por 2 horas
def get_or_create_thumbnail(image_path):
    """
    Obtiene thumbnail existente o crea uno nuevo con cache inteligente - SILENCIOSO
    """
    try:
        image_hash = get_image_hash(image_path)
        thumbnail_name = f"{image_hash}_thumb.webp"
        thumbnail_path = os.path.join(THUMBNAILS_DIR, thumbnail_name)
        
        # Si el thumbnail ya existe, devolverlo
        if os.path.exists(thumbnail_path):
            return thumbnail_path
        
        # Crear thumbnail optimizado
        if optimize_image_for_web(image_path, thumbnail_path, THUMBNAIL_SIZE, THUMBNAIL_QUALITY):
            return thumbnail_path
        
        return image_path  # Fallback a imagen original
    except:
        return image_path

@st.cache_data(ttl=7200)
def get_or_create_preview(image_path):
    """
    Obtiene vista previa existente o crea una nueva - SILENCIOSO
    """
    try:
        image_hash = get_image_hash(image_path)
        preview_name = f"{image_hash}_preview.webp"
        preview_path = os.path.join(PREVIEWS_DIR, preview_name)
        
        if os.path.exists(preview_path):
            return preview_path
        
        if optimize_image_for_web(image_path, preview_path, PREVIEW_SIZE, PREVIEW_QUALITY):
            return preview_path
        
        return image_path
    except:
        return image_path

def batch_process_thumbnails_silent(image_paths):
    """
    Procesa thumbnails en lotes usando threading - COMPLETAMENTE SILENCIOSO
    """
    executor = setup_thread_pool()
    futures = []
    
    for image_path in image_paths:
        future = executor.submit(get_or_create_thumbnail, image_path)
        futures.append((future, image_path))
    
    results = []
    for future, original_path in futures:
        try:
            thumbnail_path = future.result(timeout=10)  # Timeout más corto
            results.append((original_path, thumbnail_path))
        except Exception:
            results.append((original_path, original_path))
    
    return results

# ==================== FUNCIONES DE GALERÍA OPTIMIZADAS ====================

@st.cache_data(ttl=1800)  # Cache por 30 minutos
def obtener_imagenes_galeria(nombre_galeria):
    """Obtiene todas las imágenes de una galería específica con cache"""
    ruta_galeria = f'imagenes/Galerias/{nombre_galeria}'
    imagenes = []
    
    if os.path.exists(ruta_galeria):
        extensiones = ['jpg', 'jpeg', 'png', 'webp', 'JPG', 'JPEG', 'PNG', 'WEBP']
        imagenes_set = set()
        
        for archivo in os.listdir(ruta_galeria):
            if any(archivo.lower().endswith(f'.{ext.lower()}') for ext in extensiones):
                ruta_imagen = os.path.join(ruta_galeria, archivo).replace('\\', '/')
                imagenes_set.add(ruta_imagen)
        
        imagenes = sorted(list(imagenes_set))
    
    return imagenes

def mostrar_galeria_optimizada_final(nombre_galeria):
    """
    Muestra galería con lazy loading optimizado
    """
    st.title(f"📸 {nombre_galeria.replace('_', ' ').title()}")
    
    # Obtener todas las imágenes
    imagenes = obtener_imagenes_galeria(nombre_galeria)
    
    if not imagenes:
        st.error(f"📁 No se encontraron imágenes en la galería '{nombre_galeria}'")
        st.info("Verifica que la carpeta contenga archivos JPG, PNG o WEBP")
        return
    
    total_imagenes = len(imagenes)
    st.info(f"🖼️ **{total_imagenes} fotografías** en esta galería.")
    
    # ==================== LAZY LOADING CON PAGINACIÓN ====================
    
    # Inicializar estado de paginación
    if f'page_{nombre_galeria}' not in st.session_state:
        st.session_state[f'page_{nombre_galeria}'] = 0
    
    current_page = st.session_state[f'page_{nombre_galeria}']
    total_pages = (total_imagenes + IMAGES_PER_PAGE - 1) // IMAGES_PER_PAGE
    
    # Controles de paginación superiores
    if total_pages > 1:
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⏮️", disabled=current_page == 0, help="Primera página"):
                st.session_state[f'page_{nombre_galeria}'] = 0
                st.rerun()
        
        with col2:
            if st.button("◀️", disabled=current_page == 0, help="Página anterior"):
                st.session_state[f'page_{nombre_galeria}'] = max(0, current_page - 1)
                st.rerun()
        
        with col3:
            st.markdown(f"<div style='text-align: center; padding: 8px;'><strong>Página {current_page + 1} de {total_pages}</strong></div>", unsafe_allow_html=True)
        
        with col4:
            if st.button("▶️", disabled=current_page >= total_pages - 1, help="Página siguiente"):
                st.session_state[f'page_{nombre_galeria}'] = min(total_pages - 1, current_page + 1)
                st.rerun()
        
        with col5:
            if st.button("⏭️", disabled=current_page >= total_pages - 1, help="Última página"):
                st.session_state[f'page_{nombre_galeria}'] = total_pages - 1
                st.rerun()
    
    # ==================== CARGA DE IMÁGENES ====================
    
    # Calcular rango de imágenes para la página actual
    start_idx = current_page * IMAGES_PER_PAGE
    end_idx = min(start_idx + IMAGES_PER_PAGE, total_imagenes)
    imagenes_pagina = imagenes[start_idx:end_idx]
    
    # Procesar thumbnails en background
    thumbnail_results = batch_process_thumbnails_silent(imagenes_pagina)
    
    # ==================== MOSTRAR IMÁGENES EN GRID OPTIMIZADO ====================
    
    st.markdown("---")
    
    # Mostrar imágenes en filas de 2 con thumbnails optimizados
    for i in range(0, len(thumbnail_results), 2):
        col1, col2 = st.columns(2)
        
        # Primera imagen de la fila
        with col1:
            if i < len(thumbnail_results):
                original_path, thumbnail_path = thumbnail_results[i]
                
                try:
                    # Mostrar thumbnail optimizado
                    thumbnail_img = Image.open(thumbnail_path)
                    st.image(
                        thumbnail_img, 
                        width='content', 
                        caption=f"Foto {start_idx + i + 1}"
                    )
                    
                    # Botón para vista completa
                    if st.button(f"🔍 Ver completa", key=f"view_{start_idx + i}"):
                        st.session_state[f'viewing_{nombre_galeria}'] = original_path
                        st.rerun()
                        
                except Exception:
                    # Fallback silencioso a imagen original
                    try:
                        original_img = Image.open(original_path)
                        original_img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                        st.image(
                            original_img, 
                            width='content', 
                            caption=f"Foto {start_idx + i + 1}"
                        )
                        
                        if st.button(f"🔍 Ver completa", key=f"view_{start_idx + i}"):
                            st.session_state[f'viewing_{nombre_galeria}'] = original_path
                            st.rerun()
                    except Exception:
                        st.error(f"Error cargando imagen {i+1}")
        
        # Segunda imagen de la fila
        with col2:
            if i + 1 < len(thumbnail_results):
                original_path, thumbnail_path = thumbnail_results[i + 1]
                
                try:
                    thumbnail_img = Image.open(thumbnail_path)
                    st.image(
                        thumbnail_img, 
                        width='content', 
                        caption=f"Foto {start_idx + i + 2}"
                    )
                    
                    if st.button(f"🔍 Ver completa", key=f"view_{start_idx + i + 1}"):
                        st.session_state[f'viewing_{nombre_galeria}'] = original_path
                        st.rerun()
                        
                except Exception:
                    # Fallback silencioso
                    try:
                        original_img = Image.open(original_path)
                        original_img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                        st.image(
                            original_img, 
                            width='content', 
                            caption=f"Foto {start_idx + i + 2}"
                        )
                        
                        if st.button(f"🔍 Ver completa", key=f"view_{start_idx + i + 1}"):
                            st.session_state[f'viewing_{nombre_galeria}'] = original_path
                            st.rerun()
                    except Exception:
                        st.error(f"Error cargando imagen {i+2}")
    
    # ==================== MODAL DE VISTA COMPLETA ====================
    
    if f'viewing_{nombre_galeria}' in st.session_state:
        viewing_path = st.session_state[f'viewing_{nombre_galeria}']
        
        st.markdown("---")
        st.markdown("### 🖼️ Vista Completa")
        
        # Generar vista previa
        preview_path = get_or_create_preview(viewing_path)
        
        try:
            preview_img = Image.open(preview_path)
            st.image(preview_img, width='content')
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("❌ Cerrar vista"):
                    del st.session_state[f'viewing_{nombre_galeria}']
                    st.rerun()
                    
        except Exception:
            # Fallback a imagen original
            try:
                original_img = Image.open(viewing_path)
                st.image(original_img, width='content')
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("❌ Cerrar vista"):
                        del st.session_state[f'viewing_{nombre_galeria}']
                        st.rerun()
            except Exception:
                st.error("Error mostrando vista completa")
    
    # ==================== CONTROLES INFERIORES SIMPLIFICADOS ====================
    
    st.markdown("---")
    
    # Botón de retroceso
    if st.button("← Volver a Galerías", key="back_button", type="primary"):
        st.session_state.current_gallery = None
        # Limpiar estados de la galería
        if f'page_{nombre_galeria}' in st.session_state:
            del st.session_state[f'page_{nombre_galeria}']
        if f'viewing_{nombre_galeria}' in st.session_state:
            del st.session_state[f'viewing_{nombre_galeria}']
        st.rerun()

# ==================== APLICACIÓN PRINCIPAL ====================

# Cargar CSS
with open('style/style.css', encoding='utf-8') as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Inicializar session state
if 'current_gallery' not in st.session_state:
    st.session_state.current_gallery = None

# CONTENIDO PRINCIPAL
with st.container():
    st.subheader("Fotografía, Arte y Visión")
    st.title("El Fotografo")
    st.write(
        "Soy un apasionado de la fotografía, busco captar la esencia de un presente que inevitablemente se convertirá en uno de los infinitos instantes del pasado."
    )

with st.container(border=True, vertical_alignment='top'):
    st.header('Sobre mí', divider='gray')
    left_column, right_column = st.columns(2)
    with left_column:
        st.subheader('Pasión por la Fotografía')
        st.write('''
                 Con más de 25 años de experiencia en el mundo de la fotografía, me especializo en capturar los momentos más importantes de tu vida con un enfoque artístico y profesional.
                 
                 Mi filosofía se basa en crear imágenes auténticas que cuenten historias, reflejen emociones y perduren en el tiempo.
                 
                 Cada sesión es única y personalizada según tus necesidades y visión.
                 ''')
    with right_column:
        image = Image.open('imagenes/dollar-gill-yqNRxWNrC04-unsplash.jpg')
        st.image(image, width='content')

with st.container(border=True, vertical_alignment='top'):
    st.header('Servicios', divider='gray')
    left_column, right_column = st.columns(2)
    with right_column:
        st.subheader('Excelencia profesional')
        st.write('''
                 📷 Bodas y Eventos - Documentando tu día especial. 
                 
                 📷 Retratos y Sesiones - Capturando tu esencia única.
                 
                 📷 Paisajes y Naturaleza - La belleza del mundo natural.
                 
                 📷 Fotografía de Producto - Resaltando los productos o servicios que ofrecen las tiendas físicas, tiendas online o emprendedores.
                 
                 📷 Fotografía Gastronómica - Retratando la belleza única de cada uno de tus platos.
                 
                 📷 Fotografía inmobiliaria - Enfocada en capturar las propiedades de manera atractiva para compradores e inquilinos. 
                 ''')

    with left_column:
        image = Image.open('imagenes/alexander-dummer-aS4Duj2j7r4-unsplash.jpg')
        st.image(image, width='content')

with st.container(border=True, vertical_alignment='top'):
    st.header('Mis trabajos', divider='gray')
    
    # Lógica de navegación optimizada
    if st.session_state.current_gallery is None:
        left_column, right_column = st.columns(2)
        with left_column:
            st.subheader('Galerías')
            ruta = 'imagenes/Galerias'
            
            if os.path.exists(ruta):
                for directorio in os.listdir(ruta):
                    if os.path.isdir(os.path.join(ruta, directorio)):
                        imagenes = obtener_imagenes_galeria(directorio)
                        cantidad = len(imagenes)
                        
                        if cantidad > 0:
                            if st.button(f"📸 {directorio.replace('_', ' ').title()} *({cantidad} fotografías)*", key=f"gallery_{directorio}"):
                                st.session_state.current_gallery = directorio
                                st.rerun() 
            else:
                st.warning("📁 Carpeta 'imagenes/Galerias' no encontrada")

        with right_column:
            image = Image.open('imagenes/alexander-wang-KjyrxSHwqTg-unsplash.jpg')
            st.image(image, width='content')
    else:
        mostrar_galeria_optimizada_final(st.session_state.current_gallery)

with st.container(border=True, vertical_alignment='top'):
    st.header('Contacto', divider='grey')
    right_column, left_column = st.columns(2)
    with left_column:
        st.subheader('Comunícate conmigo')        
        contactos = [
        ("Instagram", "https://www.instagram.com/tu_usuario/", "https://cdn-icons-png.flaticon.com/512/2111/2111463.png"),
        ("+34123456789", "tel:+34123456789", "https://cdn-icons-png.flaticon.com/512/724/724664.png"),
        ("+34123456789", "https://wa.me/34123456789", "https://cdn-icons-png.flaticon.com/512/733/733585.png")
        ]

        for nombre, url, icono in contactos:
            st.markdown(f"""
            <a href="{url}" target="_blank" rel="noopener noreferrer">
            <img src="{icono}" width="30" style="vertical-align:middle;margin-right:10px;">
            {nombre}
            </a>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
    with right_column:
        image = Image.open('imagenes/nordwood-themes-q8U1YgBaRQk-unsplash.jpg')
        st.image(image, width='content')