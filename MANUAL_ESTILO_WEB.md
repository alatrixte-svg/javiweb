# MANUAL DE ESTILO Y MANTENIMIENTO WEB
## Javier Gámez Martín — javiergamezmartin.com
**Versión 1.0 · 24 de junio de 2026**

---

## 1. Finalidad y rango de aplicación

Este documento es la referencia obligatoria para cualquier persona, asistente o agente que cree, modifique, revise o mantenga la web de Javier Gámez Martín.

Se aplica, como mínimo, a:

- `index.html`
- `libros.html`
- `prensa.html`
- `guia.html`
- `blog.html`
- `blog-articulo.html`
- `ELA.html`
- `ELA-research.html`
- `ELA-esporadica.html`
- `style.css`
- `script.js`
- contenidos y recursos vinculados a esas páginas

Cuando exista una discrepancia entre una propuesta puntual y este manual, prevalece este manual salvo instrucción expresa y concreta de Javier Gámez Martín.

---

## 2. Principio rector

La web debe transmitir una identidad personal, sólida y luminosa dentro de una estética sobria y elegante:

**Polilla · Policía · Abogado · Escritor.**

El sitio combina cuatro universos que deben convivir sin competir:

1. Trayectoria de servicio público, investigación y Derecho.
2. Autoría literaria, especialmente novela negra.
3. ELA, dependencia, dignidad, autonomía y defensa de derechos.
4. Amor, familia, humor, tecnología y voluntad de vivir.

La ELA forma parte esencial de la voz del sitio, pero no debe reducir la identidad de Javier a la enfermedad. La web habla de una persona completa, con historia, criterio, obra, familia y proyectos.

---

## 3. Paleta oficial

No crear colores nuevos sin una necesidad funcional clara y sin actualizar previamente este manual.

### Variables globales obligatorias

```css
:root {
  --gold: #d6b35a;
  --red: #b41d22;
  --ink: #070708;
  --soft: #f4ead8;
  --muted: #b9ad9b;
  --blue: #26c6da;
}
```

### Uso de cada color

| Variable o color | Uso autorizado |
|---|---|
| `--ink` | Fondo principal oscuro, encabezado, superficies profundas. |
| `--gold` | Color de marca: títulos destacados, botones principales, enlaces destacados, bordes y estados activos. |
| `--soft` | Texto principal claro sobre fondo oscuro. |
| `--muted` | Texto secundario, metadatos, pies, información de apoyo. |
| `--red` | Acento exclusivo de *Marquitos* y avisos de error. No usar como color dominante general. |
| `--blue` | Acento exclusivo de guía, tecnología, autonomía y contenidos funcionales relacionados. |
| `#74ad34` | Acento exclusivo de *Cuaderno de bitácora de un gladiador con ELA*. |
| `#e8dcc9` | Texto de lectura larga sobre fondos oscuros. |
| `#fff8ed` | Subtítulos y destacados claros. |
| `#ffffff` | Uso puntual para máxima legibilidad, nunca como fondo dominante de la web. |

### Fondos

- La web mantiene una atmósfera oscura, cálida y envolvente.
- El fondo general debe usar el gradiente oscuro establecido en `style.css`.
- Las tarjetas deben ser translúcidas, con fondos blancos de opacidad baja y bordes discretos.
- No introducir fondos blancos planos, azules corporativos, degradados chillones ni colores ajenos a la paleta.

---

## 4. Tipografía y jerarquía

### Familias tipográficas

- Tipografía principal: pila de sistema definida por la web:
  `system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif`.
- Citas, testimonios y textos con un tono íntimo: `Georgia, serif`.
- No añadir fuentes externas nuevas sin una razón editorial o visual clara.

### Jerarquía

- `h1`: título único y principal de cada página. Dorado. Gran tamaño, con una lectura limpia y sin frases excesivamente largas.
- `h2`: grandes bloques de contenido. Dorado.
- `h3`: subdivisiones o títulos de tarjeta. Claro o dorado según el componente.
- `h4`: uso limitado a tarjetas de noticia u organización interna.
- `.eyebrow`: etiqueta breve, en mayúsculas, dorada, con espaciado entre letras. Sirve para contextualizar una sección, no para repetir información.

### Normas de escritura tipográfica

- Un solo `h1` por página.
- No saltar niveles de encabezado.
- No usar mayúsculas sostenidas en párrafos.
- No abusar de negritas ni cursivas.
- Mantener líneas, párrafos y bloques respirables.
- Los títulos deben ser concretos, humanos y memorables; evitar fórmulas genéricas como “Bienvenido”, “Descubre más” o “Nuestro compromiso”.

---

## 5. Cabecera y navegación

### Cabecera

La cabecera es una pieza de identidad y debe conservar:

- Fondo oscuro translúcido.
- Efecto de desenfoque.
- Borde inferior sutil dorado.
- Marca “Javier Gámez Martín” a la izquierda.
- Navegación horizontal en escritorio y adaptada a varias líneas en móvil.
- Botón de contacto como acción visual prioritaria.

En escritorio la cabecera debe permanecer visible al hacer scroll. En móvil puede dejar de ser fija para preservar espacio útil y legibilidad.

### Marca

- “Javier Gámez Martín” debe enlazar siempre a `index.html`.
- No subrayar visualmente la marca.
- No sustituirla por abreviaturas, logotipos improvisados o iconos.

### Navegación canónica

La navegación principal debe mantenerse coherente en todas las páginas:

1. Historia → `index.html#historia`
2. Libros → `libros.html`
3. Prensa → `prensa.html`
4. Guía gratuita → `guia.html`
5. Blog → `blog.html`
6. ELA → `ELA.html`
7. Contacto → `index.html#contacto`

Reglas:

- La página activa debe incorporar `aria-current="page"` cuando corresponda.
- “Contacto” debe conservar el estilo de botón principal.
- No eliminar, renombrar, reordenar ni añadir secciones del menú sin instrucción expresa.
- En páginas interiores, nunca usar enlaces relativos ambiguos que puedan romperse según la carpeta de origen.
- Los enlaces a secciones de la portada deben usar la ruta completa relativa: `index.html#id-de-seccion`.

---

## 6. Botones, enlaces y llamadas a la acción

### Botón principal

- Fondo: `--gold`.
- Texto: oscuro, próximo a `#111`.
- Peso alto.
- Debe reservarse para la acción principal de cada contexto: comprar, descargar, contactar, leer una sección clave o acceder a un recurso.

### Botón secundario

- Fondo transparente.
- Borde dorado.
- Texto dorado.
- Se utiliza para una alternativa relevante, pero secundaria.

### Enlaces de texto

- Dorados dentro de fondos oscuros cuando sean enlaces destacados.
- Enlace subrayado o cambio de color al pasar el cursor.
- No usar azul estándar de navegador ni enlaces sin estilo.
- Los enlaces externos deben usar `target="_blank"` y `rel="noopener"` cuando se abran en nueva pestaña.

### Criterio editorial de CTA

Usar verbos claros:

- “Comprar tapa blanda”
- “Comprar Kindle”
- “Descargar PDF”
- “Ver guía gratuita”
- “Leer el artículo”
- “Solicitar una entrevista”
- “Ver en YouTube”

Evitar:

- “Haz clic aquí”
- “Más información”
- “Ver más”, salvo en contextos muy evidentes
- Llamadas comerciales agresivas o impersonales

---

## 7. Tarjetas, bloques, imágenes y vídeo

### Tarjetas

Las tarjetas comparten una lógica visual:

- Fondo claro translúcido sobre fondo oscuro.
- Borde sutil.
- Esquinas redondeadas, aproximadamente entre 16 y 28 píxeles según tamaño.
- Sombra profunda y discreta.
- Separación interior generosa.
- Una jerarquía clara: etiqueta, título, texto y acción.

No crear tarjetas con bordes cuadrados, sombras duras, fondos blancos opacos o estilos que parezcan de otra web.

### Libros

Cada libro tiene un código cromático propio:

| Obra | Acento |
|---|---|
| *Marquitos, un monstruo entre nosotros* | Rojo `--red` |
| *Cuaderno de bitácora de un gladiador con ELA* | Verde `#74ad34` |
| *Guía para personas dependientes con espíritu guerrero* | Azul `--blue` |

Las portadas nunca deben recortarse. Deben usar `object-fit: contain`, estar centradas y mantener una presentación completa y digna.

### Imágenes

- Usar imágenes de alta calidad, bien encuadradas y con valor narrativo.
- Priorizar retratos, familia, libros, tecnología de apoyo, actos, naturaleza y momentos reales.
- Evitar imágenes de stock genéricas, melodramáticas o paternalistas.
- Todo `<img>` debe tener atributo `alt` descriptivo y útil.
- No usar nombres de archivo como texto alternativo.
- No deformar imágenes.
- Mantener bordes redondeados coherentes con el componente.

### Vídeo

- Las miniaturas deben respetar el estilo de tarjeta.
- Incluir texto claro de acción, por ejemplo “▶ Ver vídeo”.
- El contenido de vídeo debe complementar la narrativa, no sustituirla.

---

## 8. Estructura obligatoria por tipo de página

### Portada: `index.html`

Orden de referencia:

1. Cabecera.
2. Hero profesional con identidad, fotografía y llamadas a la acción.
3. Cita o manifiesto.
4. Historia personal y profesional.
5. Amor, familia y “doña ELA”.
6. Rasgos personales: esencia, mente y ojos.
7. Obras destacadas.
8. Tecnología, autonomía y guía.
9. Entrevistas y presentaciones.
10. Apariciones en medios.
11. Testimonios de lectores.
12. Vista previa del blog.
13. Contacto.
14. Pie.

No reordenar bloques principales sin solicitud expresa.

### Libros: `libros.html`

1. Cabecera.
2. Hero editorial breve.
3. Ficha completa de cada obra.
4. Portada, subtítulo, sinopsis, acciones y recursos asociados.
5. Pie.

Cada ficha debe distinguir claramente la naturaleza de la obra, sin repetición innecesaria.

### Prensa: `prensa.html`

1. Cabecera.
2. Hero explicativo.
3. Apariciones agrupadas o presentadas en tarjetas.
4. Medio, titular, fecha cuando exista y enlace.
5. Pie.

No inventar titulares, medios, fechas ni declaraciones.

### Guía gratuita: `guia.html`

1. Cabecera.
2. Hero con propósito, portada y acciones.
3. Beneficios o utilidad práctica.
4. Contenidos de la guía.
5. Bloque final de descarga.
6. Pie.

La guía debe presentarse como un recurso gratuito, práctico, accesible y orientado a recuperar autonomía.

### Blog: `blog.html`

1. Cabecera.
2. Hero o introducción de blog.
3. Índice y listado de artículos.
4. Tarjetas con fecha, título, extracto e imagen cuando exista.
5. Pie.

No ocultar artículos por motivos visuales. El orden debe responder al criterio editorial o cronológico definido por el sistema de datos.

### Artículo: `blog-articulo.html`

1. Enlace de vuelta al blog.
2. Metadatos.
3. Título.
4. Imagen principal, si existe.
5. Cuerpo legible.
6. Compartir.
7. Navegación entre artículos, cuando esté disponible.
8. Pie.

### ELA: `ELA.html`

1. Cabecera común.
2. Hero claro y respetuoso.
3. Noticias o contenidos contrastados.
4. Investigación, derechos, dependencia, autonomía y recursos.
5. Enlaces a contenidos específicos de investigación o exposoma cuando proceda.
6. Pie común.

La página ELA no debe usar una estética paralela. Debe compartir paleta, tipografía, cabecera, botones y pie con el resto de la web. No crear variables locales que contradigan `style.css`.

---

## 9. Pie de página

El pie debe ser común en todas las páginas.

Orden de navegación de referencia:

`Inicio · Libros · Blog · ELA · Prensa · Guía gratuita · Contacto`

Debe incluir:

- Redes sociales autorizadas.
- Enlaces de navegación.
- Contador de visitas, si está activo.
- Texto de copyright: `© Javier Gámez Martín`.

Reglas:

- Fondo integrado en la estética oscura.
- Texto secundario en `--muted`.
- Enlaces que pasan a dorado en interacción.
- No usar enlaces azules por defecto.
- No añadir páginas, iconos o servicios sin autorización.

---

## 10. Tono editorial y de marca

### Voz general

La voz debe ser:

- Cercana.
- Inteligente.
- Clara.
- Digna.
- Personal sin exhibicionismo.
- Combativa sin caer en la consigna.
- Emocional sin sentimentalismo.
- Humana, directa y con humor cuando encaje.

### Sí debe aparecer

- Amor y familia.
- Humor, tozudez, curiosidad e inconformismo.
- Trayectoria profesional y vocación de servicio.
- Literatura, investigación criminal y creación.
- ELA explicada desde la experiencia, el conocimiento y la dignidad.
- Tecnología como herramienta de autonomía.
- Defensa de derechos y vida independiente.

### Debe evitarse

- Victimismo.
- Tono paternalista o condescendiente.
- Frases grandilocuentes vacías.
- Uso constante de “superación”.
- Presentar a Javier exclusivamente como enfermo o como ejemplo inspiracional.
- Lenguaje frío institucional cuando se trate de vivencias personales.
- Promesas médicas, jurídicas o científicas sin respaldo.
- Sensacionalismo sobre la ELA, violencia o dependencia.

### Estilo de redacción

- Frases claras, con ritmo y propósito.
- Párrafos cortos o medios para facilitar la lectura.
- Información práctica antes que ornamentación.
- En contenidos sensibles, precisión y respeto.
- En contenidos literarios, permitir una mayor fuerza narrativa.
- Conservar expresiones identitarias cuando proceda: “Polilla”, “doña ELA”, “cariñito”, “gladiador”, siempre sin abuso.

---

## 11. Accesibilidad, rendimiento y calidad técnica

Toda modificación debe cumplir:

- HTML semántico.
- Jerarquía correcta de encabezados.
- `alt` útil en imágenes.
- Contraste suficiente entre texto y fondo.
- Navegación operable con teclado.
- Estados visibles de foco.
- Formularios con etiquetas y mensajes comprensibles.
- Diseño responsive sin desplazamiento horizontal.
- Imágenes optimizadas y sin deformación.
- Enlaces funcionales.
- No introducir dependencias innecesarias.
- No usar `!important` salvo corrección excepcional, justificada y documentada.

Se debe respetar Pico CSS y centralizar los estilos de la web en `style.css`.

---

## 12. Norma estricta de alcance: no tocar lo no solicitado

Esta norma es obligatoria.

Cuando se solicite un cambio:

1. Modificar únicamente los archivos necesarios para realizarlo.
2. No editar archivos no mencionados ni dependencias no imprescindibles.
3. No cambiar textos, imágenes, enlaces, orden de secciones, estilos, sangrías ni scripts ajenos a la petición.
4. No borrar código aparentemente redundante sin autorización expresa.
5. No sustituir un archivo completo cuando baste con una modificación localizada.
6. No reformatear masivamente el código solo por estilo.
7. No modificar datos, contenidos del blog, noticias, archivos JSON, recursos ni claves de configuración si no se ha pedido.
8. No hacer `commit`, `push`, publicación o despliegue sin autorización expresa.
9. Antes de una edición amplia o irreversible, crear copia de seguridad o trabajar en rama separada.
10. Si existe incertidumbre, priorizar conservar y pedir validación antes de cambiar.

---

## 13. Procedimiento obligatorio para ChatGPT, Codex o cualquier agente

### Antes de modificar

1. Leer este manual.
2. Identificar el objetivo exacto.
3. Localizar el archivo o archivos mínimos afectados.
4. Revisar la parte pertinente de `style.css`, `script.js` y el HTML afectado.
5. Explicar brevemente qué se modificará y qué no se tocará.
6. Mantener intacto todo lo no relacionado.

### Durante la modificación

1. Reutilizar clases y variables existentes.
2. Evitar CSS inline.
3. No duplicar estilos globales dentro de páginas.
4. No introducir colores, tipografías o componentes ajenos.
5. Mantener la estructura y rutas existentes salvo indicación contraria.
6. Añadir atributos de accesibilidad cuando corresponda.

### Después de modificar

1. Verificar visualmente escritorio y móvil.
2. Comprobar enlaces internos y externos afectados.
3. Confirmar que no hay desplazamiento horizontal.
4. Confirmar que se conserva cabecera y pie comunes.
5. Resumir los archivos tocados y los cambios exactos.
6. Indicar cualquier limitación, duda o comprobación pendiente.
7. No afirmar que algo funciona si no se ha podido comprobar.

---

## 14. Lista de validación previa a entrega

Antes de dar por terminado un cambio, responder internamente a estas preguntas:

- ¿He tocado solo los archivos estrictamente necesarios?
- ¿La cabecera coincide con el estándar?
- ¿El pie coincide con el estándar?
- ¿He usado exclusivamente la paleta oficial?
- ¿Los botones siguen la jerarquía principal/secundaria?
- ¿La tipografía y el tono son coherentes?
- ¿La página se verá correctamente en móvil?
- ¿Las imágenes conservan proporción y texto alternativo?
- ¿Los enlaces funcionan y tienen la ruta correcta?
- ¿No he alterado contenido o funcionalidades no solicitadas?
- ¿He explicado con exactitud qué he cambiado?

Si alguna respuesta es “no” o “no comprobado”, el trabajo no debe considerarse cerrado.

---

## 15. Regla de actualización del manual

Este documento debe actualizarse cuando Javier Gámez Martín decida cambiar de forma estable:

- Paleta.
- Tipografías.
- Estructura de navegación.
- Orden del pie.
- Estilo de botones.
- Arquitectura de páginas.
- Reglas editoriales.
- Procedimientos de mantenimiento.

Cada actualización debe indicar fecha, versión y resumen de los cambios.
