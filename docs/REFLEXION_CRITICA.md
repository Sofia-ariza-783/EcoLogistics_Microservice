# Reflexión Crítica — Desarrollo Asistido por LLM del Carbon Tracker Service

Mirando el proceso completo con algo de distancia, lo que más me queda dando
vueltas es lo rápido que uno puede confiar en una fórmula que "suena bien".
El LLM propuso un modelo matemático razonable y hasta alineado con
estándares del sector, pero eso solo salió bien porque en algún momento se
frenó a preguntar en lugar de asumir — si no hubiera surgido esa pausa, el
error habría quedado enterrado en cada número reportado, sin que nadie lo
notara hasta mucho después. Algo parecido pasa con el código: en el papel
cumple SOLID, tiene sus capas bien separadas y su dosis de programación
defensiva, y sin embargo bastó una revisión con otros ojos para encontrar
algo tan básico como un campo sin límite superior que podía romper la
respuesta con un `Infinity`. Tres rondas de "refinamiento" y 84 pruebas
pasando, y ese hueco seguía ahí — lo cual dice bastante: las pruebas que uno
mismo genera tienden a cubrir justo lo que uno ya tenía en mente, no lo que
se le escapó, así que la cobertura real termina siendo un espejo de la
imaginación de quien pidió las pruebas, no del universo completo de cosas
que pueden salir mal. Y ahí es donde el Code Review deja de ser un trámite
y se vuelve el paso que realmente importa: fue la única instancia que no
estaba "enamorada" del diseño porque no lo había construido, y por eso pudo
ver lo que el resto no veía. Si algo me llevo de todo esto es que un LLM es
un compañero de trabajo rapidísimo y bastante competente, pero no es
alguien en quien uno deba confiar a ciegas en ninguna de sus tres promesas
—que el modelo de negocio esté bien pensado, que el código sea robusto, que
las pruebas alcancen—; conviene tratarlo como a un desarrollador junior muy
talentoso: se le puede delegar mucho, pero la revisión final sigue siendo
cosa de humanos (o de otro proceso igual de exigente).
