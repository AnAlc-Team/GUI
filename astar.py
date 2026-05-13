from nicegui import ui
import heapq

ui.add_head_html('<style>.q-btn .q-focus-helper { display: none !important; }</style>')

#A* algorithm
def run_astar(start, goal, obstacles, rows, cols):
    """
    Placeholder A* algorithm. Replace this with your own function.
    Returns a list of (row, col) tuples representing the path.
    """
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) # Manhattan distance

    front = []
    heapq.heappush(front, (0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}

    while front:
        _, current = heapq.heappop(front)
        if current == goal:
            break
        
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
            next_node = (current[0] + dx, current[1] + dy)
            # Check bounds and obstacles
            if 0 <= next_node[0] < rows and 0 <= next_node[1] < cols and next_node not in obstacles:
                new_cost = cost_so_far[current] + 1
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + heuristic(goal, next_node)
                    heapq.heappush(front, (priority, next_node))
                    came_from[next_node] = current

    # Reconstruct the path
    path = []
    curr = goal
    if curr not in came_from: return [] # No path found
    while curr != start:
        path.append(curr)
        curr = came_from[curr]
    path.reverse()
    
    return path[:-1] if path else [] 

@ui.page('/astar')
def astar():
    #GUI
    ROWS, COLS = 15, 15

    # Dictionary to hold the grid state
    state = {
        'start': None,
        'goal': None,
        'obstacles': set(),
        'path': []
    }

    cells = {}

    def update_grid():
        """Updates the colors using Quasar's native color props."""
        for (r, c), btn in cells.items():
            if (r, c) == state['start']:
                btn.props('color=green')      # Start = Green
            elif (r, c) == state['goal']:
                btn.props('color=red')        # Goal = Red
            elif (r, c) in state['obstacles']:
                btn.props('color=dark')       # Obstacle = Dark Gray/Black
            elif (r, c) in state['path']:
                btn.props('color=blue')       # Path = Blue
            else:
                btn.props('color=grey-4')     # Empty = Light Gray

    def cell_clicked(r, c):
        """Handles logic when a user clicks a specific grid cell."""
        mode = mode_toggle.value
        pos = (r, c)
        
        # Clear any existing path since the user is modifying the map
        state['path'] = []
        
        if mode == 'Start':
            if pos in state['obstacles']: state['obstacles'].remove(pos)
            if pos == state['goal']: state['goal'] = None
            state['start'] = pos
            
        elif mode == 'Goal':
            if pos in state['obstacles']: state['obstacles'].remove(pos)
            if pos == state['start']: state['start'] = None
            state['goal'] = pos
            
        elif mode == 'Obstacle':
            if pos == state['start']: state['start'] = None
            if pos == state['goal']: state['goal'] = None
            state['obstacles'].add(pos)
            
        elif mode == 'Erase':
            if pos == state['start']: state['start'] = None
            if pos == state['goal']: state['goal'] = None
            if pos in state['obstacles']: state['obstacles'].remove(pos)
            
        update_grid()

    def solve():
        """Triggers the A* function using the UI's state variables."""
        if not state['start'] or not state['goal']:
            ui.notify('Please set both a Start and a Goal!', type='warning')
            return
        
        state['path'] = run_astar(state['start'], state['goal'], state['obstacles'], ROWS, COLS)
        
        if not state['path']:
            ui.notify('No path found! Obstacles might be blocking the way.', type='negative')
        else:
            ui.notify('Optimal path found!', type='positive')
            
        update_grid()

    def clear_grid():
        """Wipes the grid clean."""
        state['start'] = None
        state['goal'] = None
        state['obstacles'].clear()
        state['path'].clear()
        update_grid()

    # --- Page Layout ---
    ui.label("A* Pathfinding Interface").classes('text-2xl font-bold mb-2 mt-4')

    with ui.row().classes('items-center mb-4'):
        mode_toggle = ui.toggle(
            ['Start', 'Goal', 'Obstacle', 'Erase'], 
            value='Obstacle'
        ).classes('mr-4')
        
        ui.button('Find Path', on_click=solve, color='green')
        ui.button('Clear Map', on_click=clear_grid, color='red').props('outline')

    # The Grid Map
    with ui.card().classes('p-2 bg-gray-50'):
        # Changed 'gap-1' to 'gap-0' to remove all space between buttons
        with ui.grid(columns=COLS).classes('gap-0.5'):
            for r in range(ROWS):
                for c in range(COLS):
                    btn = ui.button(on_click=lambda e, r=r, c=c: cell_clicked(r, c), color='grey-4')
                    
                    # 'square' and ':ripple="false"' keep the buttons flat and rigid
                    btn.props('unelevated square padding="none" :ripple="false"').classes('w-8 h-8')
                    
                    cells[(r, c)] = btn