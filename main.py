from algo.dijkstra import dijkstra


graph = {
    "A": {
        "B": {"distance": 5, "cost": 10},
        "C": {"distance": 2, "cost": 5}
    },
    "B": {
        "D": {"distance": 4, "cost": 8}
    },
    "C": {
        "B": {"distance": 8, "cost": 12},
        "D": {"distance": 7, "cost": 15}
    },
    "D": {}
}

path, cost = dijkstra(graph, "A", "D", weight_type="distance")

print("Shortest Path:", path)
print("Total Distance:", cost)