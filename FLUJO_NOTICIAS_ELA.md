# Flujo manual de noticias ELA

Este flujo se ejecuta solo cuando el usuario lo pida expresamente, por ejemplo:

> Ejecuta el flujo de noticias ELA.

No hacer commit ni push. El usuario subirá los cambios manualmente cuando los revise.

## Objetivo

Buscar noticias nuevas sobre ELA, revisar editorialmente las candidatas, depurar `candidate-news.json`, conservar un backup del candidate original y actualizar `ELA.html` con las noticias válidas.

## Pasos

1. Ejecutar la búsqueda local:

   ```powershell
   .\scripts\flujo_noticias_ela.cmd buscar
   ```

   La búsqueda combina Google News RSS, GDELT y RSS curados relacionados con
   ELA/ALS. `candidate-news.json` incluye el campo `provider` para identificar
   el origen de cada candidata. Si GDELT limita temporalmente las consultas,
   el flujo continúa con las demás fuentes disponibles.

2. Guardar una copia exacta del candidate recién generado:

   - `candidate-news.backup.json`

   También puede hacerse con:

   ```powershell
   .\scripts\flujo_noticias_ela.cmd backup
   ```

3. Revisar todas las noticias de `candidate-news.json` con criterio conservador:

   - Mantener solo noticias cuyo tema principal sea ELA, Ley ELA, investigación específica en ELA, cuidados de personas con ELA, testimonios, asociaciones, campañas o medidas públicas directamente vinculadas a ELA.
   - Excluir noticias donde ELA sea una mención secundaria, ambigua o no verificable.
   - No modificar los datos internos de las noticias válidas.
   - Actualizar `total` para que coincida con el número de noticias mantenidas.

4. Regla obligatoria para noticias dudosas:

   - Entrar siempre en la URL original antes de descartar.
   - Leer titular, entradilla y cuerpo disponible.
   - Si la URL original no es accesible, usar resultados indexados o fuentes secundarias fiables.
   - Si después de verificar sigue habiendo duda razonable, descartar.

5. Actualizar `ELA.html` con:

   ```powershell
   .\scripts\flujo_noticias_ela.cmd actualizar -Seleccion "1,2,3,..."
   ```

   La lista numérica debe incluir todas las noticias válidas del candidate depurado.

6. Al actualizar `ELA.html`, usar la opción mixta:

   - Añadir las nuevas noticias válidas.
   - Conservar noticias antiguas que ya estaban en `ELA.html`.
   - Eliminar de `ELA.html` cualquier noticia que estuviera en `candidate-news.backup.json` pero ya no esté en el `candidate-news.json` revisado.
   - Mantener el bloque de noticias de España limitado a 15 entradas.
   - Mantener bajo ese bloque una sección internacional con 6 noticias en inglés sobre ALS.

7. Verificar al final:

   - `candidate-news.json` es JSON válido.
   - `candidate-news.backup.json` es JSON válido.
   - `total` coincide con el número de elementos de `news`.
   - `ELA.html` contiene el array `newsData`.
   - Las noticias descartadas no aparecen en `ELA.html`.
   - Las noticias dudosas aceptadas tras verificación sí aparecen.

   Comprobación estática reutilizable:

   ```powershell
   .\scripts\flujo_noticias_ela.cmd validar
   ```

   Para comprobar también los enlaces de noticias por red:

   ```powershell
   .\scripts\flujo_noticias_ela.cmd validar -ComprobarEnlacesNoticias
   ```

   Para comprobación visual automatizada de escritorio y móvil:

   ```powershell
   .\scripts\flujo_noticias_ela.cmd visual
   ```

   Esta comprobación levanta un servidor local temporal en un puerto libre,
   verifica que `ELA.html` responde correctamente y, si encuentra Edge o Chrome,
   genera capturas reales en `.visual-checks/`. Si el navegador instalado no
   permite capturas headless, el comando lo informa con el error devuelto por
   el navegador y conserva la verificación de servidor y estructura.

   Para previsualización visual en navegador, iniciar un servidor local:

   ```powershell
   .\scripts\flujo_noticias_ela.cmd servir
   ```

   Y abrir:

   ```text
   http://127.0.0.1:8765/ELA.html
   ```

## Informe final esperado

Responder al usuario con:

1. Total de noticias analizadas.
2. Total de noticias mantenidas.
3. Total de noticias excluidas.
4. Tabla de descartadas con motivo concreto.
5. Confirmación de archivos modificados.
6. Cajetín numérico final, por ejemplo:

```text
1,2,3,4,5
```

El paso de actualización también devuelve un cajetín de texto para compartir
la actualización diaria. El mensaje usa las noticias más recientes finalmente
publicadas en `ELA.html`: toma los dos titulares que más se repitan en ese
bloque reciente y, si no detecta repeticiones, usa los dos primeros titulares
publicados más recientes.

## Archivos principales

- `scripts/buscar_noticias_ela.py`
- `scripts/actualizar_ela_html.py`
- `candidate-news.json`
- `candidate-news.backup.json`
- `ELA.html`
