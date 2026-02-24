import heapq

def dijkstra (graph, start, goal, weight_type = "distance"):
    queue = [(0, start, [])]
    visited = set()

    while queue:
        current_cost, current_node , path = heapq.heappop(queue) #declared variables from the first item from the heap

        if current_node in visited: # if current node is in visited move to the next node as it's already visited
            continue
            
        visited.add(current_node)
        path = path + [current_node]

        if current_node == goal:
            return path , current_cost
        
        for neighbor, weights in graph[current_node].items():
            if neighbor not in visited:
                weight = weights[weight_type]
                heapq.heappush(queue, (current_cost + weight, neighbor, path))
    
    return None, float("inf")
    


