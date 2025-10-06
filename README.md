# Proyecto de Estructuras de Datos - 05 de Octubre
[PDF con las instrucciones del proyecto](./Primer%20proyecto%20-%20Courier%20Quest.pdf)    

## Integrantes del Equipo
- Bryan Aguero Mata    
- Maria Blanco Sanchez   
- Andrey Solis Carvajal

## Descripción
Primer proyecto de Estructuras de Datos. 

## Objetivos
Implementar	y	justificar	el	uso	de	estructuras	de	datos	lineales
Practicar	el	manejo	de	archivos	en	múltiples	formatos (JSON,	texto,	binario)
Aplicar	algoritmos	de	ordenamiento en	escenarios	reales
Desarrollar	un	videojuego	con	Python	y	Arcade/Pygame/cocos2d
Integrar	un	API	real y	gestionar	caché	para	trabajar	en	modo	offline
Diseñar	un	bucle	de	juego	consistente	con	 reglas	cuantificables	(clima,	 reputación,	
resistencia)

Instrucciones generales:
Se debe instalar las siguientes librerías:
- Requests
- Pygame
- Pydantic

Se deben correr estos comandos en consola para instalar los paquetes que permiten correr el programa:
- pip install requests
- pip install pydantic
- pip install pygame

Estructura general del proyecto

Las estructuras de datos aplicadas fueron las siguientes:
En términos generales, se usan los dict y list que aplican de forma predeterminada por Python. En estos casos, almacena las relaciones clave-valor, las cuales han servido para almacenar las estadísticas, los estados de clima, el mapa y otros elementos. Todas sus operaciones utilizan una complejidad algorítmica en el mejor de los casos de O(1) y en el peor de O(n), tanto para insertar, buscar, eliminar y actualizar. 

Para el caso de los list, se aplica principalmente para la carga del API (mapa, pedidos y clima). Estos poseen una complejidad algorítmica similar, al ser 0(1) en el mejor de los casos (a excepción de búsqueda, que es O(n)), y O(n) en el peor de los casos (los accesos modificaciones son O(1)). Esto ocurre porque el tamaño de los datos no es tan grande. Además, las operaciones de acceso (que son las más aplicadas en el programa) funciona de forma rápida al ser el propósito de estas dos estructuras en python.

Por otro lado, se aplicó el uso de la estructura de datos queue de tipo FIFO, la cual se observa en el gestor de pedidos. Esto se aplicó pues estos se realizan según la prioridad que se requiera. Este maneja una complejidad algorítmica en el enqueue y dequeue de O(1) en el mejor de los casos, y en el peor de los casos O(1). Este tiene una complejidad espacial de O(n), pues debe ir guardando la cantidad de elementos n para poder cumplir su funcionamiento. 

Para el caso el stack de tipo LIFO, este fue aplicado en el undo, el cual se encarga de devolverse al punto de origen después de realizar una cantidad n de pasos. Este tiene la misma complejidad que el queue, aunque sus operaciones son distintas. 






