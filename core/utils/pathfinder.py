import heapq
from typing import List, Optional

from api.material_base import MaterialType


def extract_vault_location(construction: List[dict]) -> Optional[List[int]]:
    for item in construction:
        material_type: Optional[str, MaterialType] = item["material_type"]
        if isinstance(material_type, MaterialType):
            material_type: str = item["material_type"].value
        if material_type == "Vault":
            return item["location"]
    return None


def is_solid(x: int, y: int, construction: List[dict]) -> int:
    for item in construction:
        location = item["location"]
        material_type: Optional[str, MaterialType] = item["material_type"]
        if isinstance(material_type, MaterialType):
            material_type: str = item["material_type"].value
        if location[0] == x and location[1] == y:
            return 0 if material_type == "Vault" else 1
    return 0


def deconstruct_house(construction: List[dict]):
    vault_location: List[int] = extract_vault_location(construction)
    door_location: List[int] = [0, 15]
    rows: List[List[int]] = []
    for y in range(0, 31):
        rows.append([
            is_solid(x, y, construction) for x in range(0, 31)
        ])
    return (
        (door_location[1], door_location[0]),
        (vault_location[1], vault_location[0]),
        rows
    )


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def get_neighbors(pos, maze, rows, cols):
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    neighbors = [(pos[0] + dr, pos[1] + dc) for dr, dc in directions]
    items = []
    for r, c in neighbors:
        if rows > r >= 0 and 0 <= c < cols:
            if maze[r][c] == 0:
                items.append((r, c))
    return items


def reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    return path[::-1]


def get_a_star_maze_solution(construction: List[dict]):
    """
    Get maze solution using the A* algorithm.

    https://en.wikipedia.org/wiki/A*_search_algorithm
    """
    start, end, maze = deconstruct_house(construction)
    rows, cols = len(maze), len(maze[0])
    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, end)}

    while open_set:
        current_f, current = heapq.heappop(open_set)
        if current == end:
            path = reconstruct_path(came_from, end)
            return path

        for neighbor in get_neighbors(current, maze, rows, cols):
            tentative_g_score = g_score[current] + 1

            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, end)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
                came_from[neighbor] = current

    return None  # No path found


def get_maze_solution(construction: List[dict]):
    solution = get_a_star_maze_solution(construction)
    if not solution:
        return None
    return [[c, r] for r, c in solution]
