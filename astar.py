""" A* Pathfinding """

class Node:
    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position

        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.position == other.position

def heuristic(node, goal, D1=1, D2=2 ** 0.5):  
    dx = abs(node.position[0] - goal.position[0])
    dy = abs(node.position[1] - goal.position[1])
    return D1 * (dx + dy) + (D2 - 2 * D1) * min(dx, dy)


def astar(layout, start, end):
    start_node = Node(None, start)
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, end)
    end_node.g = end_node.h = end_node.f = 0

    open_list = []
    closed_list = []

    open_list.append(start_node)

    while len(open_list) > 0:

        current_node = open_list[0]
        current_index = 0
        for index, item in enumerate(open_list):
            if item.f < current_node.f:
                current_node = item
                current_index = index

        open_list.pop(current_index)
        closed_list.append(current_node)

        if current_node == end_node: # if 구문을 만족을 못함
            path = []
            current = current_node
            
            while current is not None:
                # x, y = current.position
                # layout[x][y] = 7 
                path.append(current.position)
                current = current.parent
            
            return path[::-1]  

        children = []
        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:  

            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

            if node_position[0] > (len(layout) - 1) or node_position[0] < 0 or node_position[1] > (
                    len(layout[len(layout) - 1]) - 1) or node_position[1] < 0:
                continue

            if layout[node_position[0]][node_position[1]] != 0:
                # print("node -", node_position[0],node_position[1], "is blocked")
                continue

            new_node = Node(current_node, node_position)

            children.append(new_node)

        for child in children:

            is_in_closed = False
            for closed_child in closed_list:
                if child == closed_child:
                    is_in_closed = True
                    break
            if is_in_closed:
                continue

            child.g = current_node.g + 1
            child.h = 10000*heuristic(child, end_node)
            child.f = child.g + child.h

            is_in_open = False
            for open_node in open_list:
                if child == open_node and child.g > open_node.g:
                    is_in_open = True
                    break
            if is_in_open:
                continue

            open_list.append(child)

