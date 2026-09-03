# NexTrace Configurator UI Style Guideline

Este documento define la paleta de colores y las especificaciones de diseño para los componentes y botones de la aplicación. Todos los desarrollos e implementaciones futuras deben regirse estrictamente bajo estas directrices visuales.

---

## 1. Paleta de Colores Principal

La aplicación utiliza un esquema minimalista y profesional restringido a **3 colores primarios** para evitar el ruido visual:

*   **Midnight Navy (`#0B192C`)**: Color institucional principal. Utilizado para textos destacados, estados activos principales, encabezados de diagnóstico, anillos de progreso clave y botones de acción secundaria/continuación.
*   **Slate Gray (`#64748B` / `#94A3B8`)**: Color neutro utilizado para textos secundarios, bordes sutiles, estados desactivados y fondos de elementos secundarios.
*   **Electric/Process Blue (`#0284C7` / `#0091FF`)**: Color de énfasis utilizado para acciones de creación primaria, botones destacados como el "Wizard" y resaltados interactivos.

---

## 2. Tipos de Botones Oficiales

A partir de ahora, la aplicación cuenta únicamente con **2 diseños de botones** permitidos:

### Tipo A: Botón de Acción Primaria (Electric/Process Blue)
*   **Propósito**: Creación de nuevos elementos, lanzamientos de asistentes (Wizards), o acciones positivas principales.
*   **Color de Fondo**: Electric Blue (`#0284C7` o `bg-sky-600` / `bg-blue-500`).
*   **Color de Texto**: Blanco Puro (`#FFFFFF`).
*   **Bordes**: Completamente redondeados (`rounded-full`).
*   **Clases Tailwind Clave**:
    ```html
    className="bg-sky-600 hover:bg-sky-700 text-white font-bold px-6 py-2.5 rounded-full transition-all shadow-md active:scale-95 cursor-pointer"
    ```

### Tipo B: Botón de Acción Secundaria y Continuación (Midnight Navy)
*   **Propósito**: Pasos de continuidad ("Continue Step"), confirmaciones de procesos y cierres/diagnósticos.
*   **Color de Fondo**: Midnight Navy (`#0B192C`).
*   **Color de Texto**: Blanco Puro o Muted Navy.
*   **Bordes**: Semi-redondeados a redondeados según contexto (`rounded-xl` o `rounded-full`).
*   **Clases Tailwind Clave**:
    ```html
    className="bg-[#0B192C] hover:bg-[#15253F] text-white font-bold px-6 py-2.5 rounded-xl transition-all shadow-md active:scale-95 cursor-pointer"
    ```

---

## 3. Directriz de Implementación
*   **Prohibición de Colores Extraños**: Queda estrictamente prohibido introducir colores adicionales (verdes, amarillos intensos, púrpuras, rosas) a las tarjetas de KPI superiores o botones, a menos que sean indicadores de advertencia o error críticos de sistema.
*   **Unificación**: Todas las pantallas nuevas (Dashboard, Configuración, Auditoría) deben apegarse a esta guía de estilo.
