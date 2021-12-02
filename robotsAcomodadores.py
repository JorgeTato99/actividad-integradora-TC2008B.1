# Librerías Necesarias para Mesa
from mesa import Agent, Model
from mesa.space import Grid
from mesa.time import RandomActivation
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter
from mesa.datacollection import DataCollector
from mesa.visualization.modules import ChartModule, TextElement
from mesa.space import MultiGrid

# Librerías Necesarias para el PathFinding
from pathfinding.core.grid import Grid as Gridd
from pathfinding.finder.a_star import AStarFinder
from tornado.ioloop import PeriodicCallback

# Clase para los Robots Limpiadores
class Robot(Agent):
    # Constructor
    def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.pos = pos
        self.model = model
        self.id = self.unique_id-1
        self.estado = 0
        self.monton = 0
        # print(self.unique_id)

    # Función de Paso
    def step(self):
        # print(len(self.model.CoorCajas)-1, " >= " ,self.id)
        if (len(self.model.CoorCajas)-1 >= self.id) or (self.estado == 1):
            # print(self.model.CoorCajas[self.id])

            if self.monton >= self.model.NumMontones-1:
                self.monton = self.model.NumMontones-1

            if self.estado == 0:
                # print("El estado es: ", self.estado, " y el id es: ", self.id)
                # Posición de la Caja a Recolectar
                BoxPos = self.model.CoorCajas[self.id]
                nueva_pos = self.moverse(BoxPos)
                if nueva_pos == self.pos:
                    for i in self.model.grid.iter_cell_list_contents([self.pos]):
                        if(type(i) is Caja):
                            if(not i.enTransporte):
                                i.enTransporte = True
                                BoxesPos = self.model.CoorMontones[self.monton]
                                self.model.crearCaja(BoxesPos, 0, True)
                                break
                    self.estado = 1
                    self.model.CoorCajas.remove(BoxPos)
            
            # Moviendose hacia un monton de cajas
            if self.estado == 1:
                # Posición del Monton de Cajas
                BoxesPos = self.model.CoorMontones[self.monton]
                nueva_pos = self.moverse(BoxesPos)
                if nueva_pos == self.pos:
                    for i in self.model.grid.iter_cell_list_contents([self.pos]):
                        if(type(i) is Caja):
                            i.nivel += 1
                            i.enTransporte = False
                            i.pos = nueva_pos
                            print("Robot: ", self.id, " entregó en montón: ", self.monton)
                            break
                    self.estado = 0
                    self.monton += 1
                    self.model.NumCajasAcomodadas += 1
        else:
            final_pos = (self.id, 2)
            nueva_pos = self.moverse(final_pos)

        self.model.grid.move_agent(self, nueva_pos)

    def moverse(self, BoxPos):
        # Variables
        x1, y1 = self.pos
        x2, y2 = BoxPos

        if y1 > y2:
            return(x1, y1-1)
        elif y1 < y2:
            return(x1, y1+1)
        elif x1 > x2:
            return(x1-1, y1)
        elif x1 < x2:
            return(x1+1, y1)
        else:
            return(x1, y1)


# Clase para las Cajas
class Caja(Agent):
    # Constructor
    def __init__(self, model, pos, nivel, enTransporte):
        super().__init__(model.next_id(), model)
        self.pos = pos
        self.enTransporte = enTransporte
        self.nivel = nivel

    # Función de Paso
    def step(self):
        pass

# Clase Laberinto
class Maze(Model):

    # Constructor
    def __init__(self, Ancho, Alto, NumRobots, NumCajas, Tiempo):
        super().__init__()
        
        self.Ancho = Ancho
        self.Alto = Alto
        self.NumRobots = NumRobots
        self.NumCajas = NumCajas
        self.Tiempo = Tiempo

        self.NumPasos = 0
        self.NumPasosRobots = 0
        self.NumCajasAcomodadas = 0

        # Sección pra los montones de cajas
        self.NumMontones = ((NumCajas-(NumCajas % 5)) / 5)+1
        self.NumMontones = int(self.NumMontones)
        self.CoorMontones = []
        self.CantMontones = []
        for i in range(self.NumMontones):
            self.CoorMontones.append((i,0))
        for i in range(self.NumMontones):
            self.CantMontones.append(0)
        # print(self.CoorMontones)
        
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(width= Ancho, height= Alto, torus=False)

        # Se crea la matrix
        matrix = []
        for x in range(Ancho):
            matrix.append([])
            for y in range(Alto):
                matrix[x].append(1)
        # print(matrix)

        # Listas de Coordenadas
        self.CoorCajas = []
        self.CoorRobots = []

        # Se crean los robots
        Aux = 0
        while Aux < self.NumRobots:
            x = self.random.randint(0,self.Ancho-1)
            y = self.random.randint(2,self.Alto-1)
            if (x,y) not in (self.CoorCajas and self.CoorRobots):
                robot = Robot(self, (x,y))
                self.grid.place_agent(robot, (x,y))
                self.schedule.add(robot)
                self.CoorRobots.append((x,y))
                Aux += 1
        # print(self.CoorRobots)

        # Se crean las cajas
        Aux = 0
        while Aux < self.NumCajas:
            x = self.random.randint(0,self.Ancho-1)
            y = self.random.randint(2,self.Alto-1)
            if (x,y) not in (self.CoorCajas and self.CoorRobots):
                caja = Caja(self, (x,y), 1, False)
                self.grid.place_agent(caja, (x,y))
                self.schedule.add(caja)
                self.CoorCajas.append((x,y))
                matrix[y][x] = 0
                Aux += 1
        # print(self.CoorCajas)

        # print("Matrix Final: \n", matrix)
        # print("matrix[1][1]: \n", matrix[1][1])
        
    def step(self):
        if (self.NumPasos < self.Tiempo) and (self.NumCajasAcomodadas < self.NumCajas):
            self.schedule.step()
            self.NumPasos += 1
            self.NumPasosRobots += self.NumRobots
        else:
            self.running = False

    def crearCaja(self, pos, nivel, enTransporte):
        caja = Caja(self, pos, nivel, enTransporte)
        self.grid.place_agent(caja, pos)
        self.schedule.add(caja)

class label(TextElement):
    def __init__(self, name, variable):
        self.name = name
        self.variable = variable
    
    def render(self, model):
        return str(self.name) + ": " + str(getattr(model, self.variable))

# Definimos como se van a ver los agentes
def agent_portrayal(agent):
    if(type(agent) is Robot):
        return {"Shape": "robot.png", "Layer": 0}
    elif(agent.nivel >= 5):
        return {"Shape": "caja_5.png", "Layer": 0}
    elif(agent.nivel == 4):
        return {"Shape": "caja_4.png", "Layer": 0}
    elif(agent.nivel == 3):
        return {"Shape": "caja_3.png", "Layer": 0}
    elif(agent.nivel == 2):
        return {"Shape": "caja_2.png", "Layer": 0}
    elif(agent.enTransporte):
        return {"Shape": "circle", "r": 1, "Filled": "true", "Color": "White", "Layer": 0}
    elif(agent.nivel == 1):
        return {"Shape": "caja_1.png", "Layer": 0}


# Se definen las variables de alto y ancho
Ancho = UserSettableParameter("slider", "Ancho", 15, 10, 30, 1)
Alto = UserSettableParameter("slider", "Alto", 15, 10, 30, 1)
# Se define los espacios del grid y el tamaño en px
grid = CanvasGrid(agent_portrayal, Ancho.value, Alto.value, 450, 450)

#Se inicia el Servidor
server = ModularServer(Maze, [
        grid,
        label("Tiempo Necesario: ", "NumPasos"), 
        label("Movimientos de Robots: ", "NumPasosRobots"),
        label("Cajas Acomodadas: ", "NumCajasAcomodadas"),
    ], 
    "Actividad Integradora - A01733616", 
    {
        "Ancho": Ancho,
        "Alto": Alto,
        "NumRobots": UserSettableParameter("number", "Número de Robots", 5),
        "NumCajas": UserSettableParameter("number", "Número de Cajas", 22),
        "Tiempo": UserSettableParameter("number", "Tiempo de Ejecución", 200)
    }
)
server.port = 8524
server.launch()