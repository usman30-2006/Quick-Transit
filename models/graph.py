class Graph: 
    def __init__(self):
        self.nodes = {}
    
    def AddEdge (self, from_node, to_node, distance, cost):
        if from_node not in self.nodes:  # the from node doesnt exist
            self.nodes[from_node] = {}
        
        if to_node not in self.nodes:  # the to node doesnt exist
            self.nodes[to_node] = {}
        
        self.nodes[from_node][to_node] = {
            "distance" : distance,
            "cost" : cost
        }
    
    def GetGraph (self):
        return self.nodes
