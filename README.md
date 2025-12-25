# Practica Final Diseño y Mantenmiento de Software

# 📊 RepoAnalyzer - Analizador de Métricas de Software

¡Bienvenido a **RepoAnalyzer**!

Esta es una aplicación web construida con **Flask** diseñada para analizar repositorios de GitHub (proyectos en Python) y extraer métricas de calidad de software automáticamente.

El objetivo principal de este proyecto no es solo calcular datos, sino demostrar la implementación correcta de **Patrones de Diseño de Software** para crear una arquitectura desacoplada, mantenible y robusta.

---

## 🚀 Características

* **Análisis de Repositorios:** Clona y analiza repositorios remotos de GitHub.
* **Métricas Soportadas:**
    * Líneas de Código (LOC).
    * Complejidad Ciclomática (CC) Promedio.
    * Índice de Mantenibilidad (Maintainability Index).
    * Ratio de Duplicación de Código.
    * Conteo de funciones, clases, imports y comentarios "TODO".
* **Sistema de Caché:** Utiliza una base de datos SQLite para guardar análisis previos y evitar recálculos innecesarios.
* **Historial:** Visualización de análisis anteriores.

---

## 🏗️ Arquitectura y Patrones de Diseño

Este proyecto es un ejemplo práctico de la asignatura **Diseño y Mantenimiento del Software**. Hemos implementado los siguientes patrones:

1.  **Mediator (Mediador):** Desacopla la interfaz web (Flask) de la lógica de negocio. El `UIMediator` coordina los componentes visuales (`Input`, `Output`, `History`) con el sistema.
2.  **Proxy:** `ProxySubject` actúa como intermediario. Gestiona el acceso a la base de datos (caché) y decide cuándo llamar al cálculo real.
3.  **Facade (Fachada):** `MetricsFacade` simplifica la complejidad del subsistema de métricas, ofreciendo una única función `compute_all` para analizarlo todo.
4.  **Strategy (Estrategia):** Cada métrica (`Lines`, `Functions`, `Duplication`, etc.) es una estrategia independiente intercambiable.
5.  **Singleton:** `ConfigSingleton` asegura una configuración centralizada y única para toda la app.
6.  **Visitor:** Usado internamente (via `ast.NodeVisitor`) para recorrer el árbol sintáctico de Python.

---

## 🛠️ Requisitos Previos

* **Python 3.10** o superior.
* **Git** instalado en tu sistema (necesario para clonar los repositorios a analizar).

---

## ⚙️ Instalación y Ejecución

Sigue estos pasos para ponerlo en marcha en tu máquina local:

### 1. Clonar o descargar
Descarga este repositorio y abre una terminal en la carpeta raíz (`repo_analyzer`).

### 2. Crear entorno virtual (Recomendado)
Es buena práctica no ensuciar tu Python global.

# En Linux/Mac
`python3 -m venv venv`
`source venv/bin/activate`

# En Windows
`python -m venv venv`
`venv\Scripts\activate`

### 3. Instalar dependencias

El proyecto es ligero. Principalmente necesitamos Flask y Pytest.
Bash

`pip install flask pytest`

### 4. Ejecutar la aplicación

Arranca el servidor de desarrollo:
Bash

`python3 app.py`

Verás un mensaje indicando que el sistema está listo en http://127.0.0.1:5000.

## 🖥️ Manual de Uso

    Abre tu navegador web y ve a http://127.0.0.1:5000.

    Repo URL: Introduce la URL de un repositorio público y de Python.

        Ejemplo para probar: https://github.com/kennethreitz/samplemod

    Opciones:

        Forzar recálculo: Si lo marcas, borrará la caché de ese repo, lo volverá a descargar y calculará todo de cero. Si no lo marcas y ya existe en la BD, te mostrará el resultado guardado al instante.

        Dup Window: Tamaño de la ventana para detectar código duplicado (por defecto es 4 líneas).

    Pulsa "Analizar".

    Nota: La primera vez que analices un repo grande puede tardar unos segundos o minutos dependiendo de tu conexión a internet, ya que tiene que clonarlo.

## 🧪 Ejecutar los Tests

El proyecto cuenta con una suite de tests robusta (Unitarios y de Integración) para asegurar que las métricas y la arquitectura funcionan bien.

Para lanzarlos, simplemente ejecuta desde la raíz:

`pytest -v`

Deberías ver todos los tests en verde (PASSED), cubriendo desde las estrategias de cálculo (test_functions.py, etc.) hasta la coordinación del mediador (test_mediator.py).
## ⚠️ Solución de Problemas Comunes

    "Num Files: 0": Asegúrate de que el repositorio que estás analizando es de Python. El sistema filtra automáticamente y solo analiza archivos .py.

    Error de permisos: Verifica que tienes permisos de escritura en la carpeta del proyecto, ya que la aplicación necesita crear las carpetas repo_cache/ (para descargas) y analysis.db (base de datos).

    Error "Git not found": Asegúrate de tener Git instalado y añadido al PATH de tu sistema.

## ✒️ Autores

    Igor & Nicolás

    Practica Final Diseño y Mantenimiento de Software - Curso 2024/2025
