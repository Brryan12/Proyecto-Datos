import inspect
from src.game.stats_module import Stats

print("Archivo cargado:", inspect.getfile(Stats))
print("Código fuente de Stats._init_:\n")
import inspect
print(inspect.getsource(Stats.__init__))

s = Stats()
print("\nInstancia creada -> extras_clima:", s.extras_clima)