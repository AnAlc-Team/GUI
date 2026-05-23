#Import the JSON library
import json

#Import heapq
import heapq

#Import deque
from collections import deque

#Import the path library, used to get file paths
from pathlib import Path

#Import fastapi for authentication
from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from fastapi.responses import StreamingResponse

#Import starlette
from starlette.middleware.base import BaseHTTPMiddleware

#Import NiceGUI
from nicegui import app, ui, run
from nicegui import Client
from nicegui.page import page

#Import OpenCV for decoding the stream
import cv2

#Libraries for displaying the stream
import asyncio
import time
import threading
import numpy as np

#Import custom scripts
import navui
import logout

#Import the Tello script
from tello import Tello

#Get the base directory
base_dir = Path(__file__).parent

#Find file paths
favicon_path = base_dir / 'static' / 'avra.jpg'
passwords_path = base_dir / 'users.json'
unrestricted_path = base_dir / 'unrestricted.json'
protected_path = base_dir / 'protected.json'
admins_path = base_dir / 'admins.json'
image_path = base_dir / 'static' / 'photo.png'

#Add static files
app.add_static_files('/static', str(base_dir / 'static'))

#Read passwords from users.json and save them in passwords
with open(passwords_path, 'r') as file:
    passwords = json.load(file)

#Pages anyone can access, even without logging in
with open(unrestricted_path, 'r') as file:
    unrestricted_page_routes = json.load(file)

#Protected pages, only users with admin access
with open(protected_path, 'r') as file:
    protected = json.load(file)

#Read admin usernames and save them in admins
with open(admins_path, 'r') as file:
    admins = json.load(file)

#Set the URL prefix
prefix="https://avra-auth.web.app/"

#Get the base directory
base_dir = Path(__file__).parent

#Find file paths
updater_config_path = base_dir / "updater_config.json"
about_path = base_dir / "about.json"

#Read the config file
with open(updater_config_path,'r') as file:
    config = json.load(file)

#Get the config data
channel = config["channel"]
auto_update = config["auto_update"]

#Read the about file
with open(about_path,'r') as file:
    about = json.load(file)

#Get the about data
current_version = float(about["version"])

#Zip password
zip_password = "neverfind"

#The A* algorithm
def astar(start, goal, obstacles, rows, cols):
    def manhattan(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    front = []
    heapq.heappush(front, (0, start))
    came_from = {start: None}
    cost = {start: 0}

    while front:
        _, current = heapq.heappop(front)
        if current == goal:
            break

        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            next_node = (current[0] + dx, current[1] + dy)

            if 0 <= next_node[0] < rows and 0 <= next_node[1] < cols and next_node not in obstacles:
                new_cost = cost[current] + 1
                if next_node not in cost or new_cost < cost[next_node]:
                    cost[next_node] = new_cost
                    priority = new_cost + manhattan(goal, next_node)
                    heapq.heappush(front, (priority, next_node))
                    came_from[next_node] = current
        
    path = []
    current = goal
    if current not in came_from:
        return []
    while current != start:
        path.append(current)
        current = came_from[current]
    path.reverse()

    return path[:-1] if path else []

#The Dijkstra algorithm
def dijkstra(Start, Goal, Obstacles, Rows, Cols):
    dist = {Start: 0}
    came_from = {Start: None}
    directions = ((0, 1), (1, 0), (0, -1), (-1, 0))
    
    queue = []
    heapq.heappush(queue, (0, Start))
    visited = set()
    
    while queue:
        _, current = heapq.heappop(queue)
        
        if current in visited:
            continue            
        if current == Goal:
            break
            
        visited.add(current)
        
        for dx, dy in directions:
            next_node = (current[0] + dx, current[1] + dy)
            
            if 0 <= next_node[0] < Rows and 0 <= next_node[1] < Cols and next_node not in Obstacles:          
                new_dist = dist[current] + 1
                
                if next_node not in dist or new_dist < dist[next_node]:
                    dist[next_node] = new_dist
                    came_from[next_node] = current
                    heapq.heappush(queue, (new_dist, next_node))
    
    if Goal not in came_from:
        return []
    
    path = []
    current = Goal
    while current != Start:
        path.append(current)
        current = came_from[current]
    path.reverse()
    
    return path[:-1] if path else []

#The Grassfire algorithm
def grassfire(Start, Goal, Obstacles, Rows, Cols):  
    queue = deque()
    queue.append(Goal)
    dist = {Goal: 0}
    visited = set()
    visited.add(Goal)
    
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
    
    while queue:
        current = queue.popleft()
        current_dist = dist[current]
        
        if current == Start:
            break
        
        for dx, dy in directions:
            next_node =(current[0] + dx, current[1] + dy)
            
            if 0 <= next_node[0] < Rows and 0 <= next_node[1] < Cols:
                if next_node not in dist and next_node not in Obstacles:
                    dist[next_node] = dist[current] + 1
                    queue.append(next_node)
    
    if Start not in dist:
        return []
    
    path = []
    current = Start
    path.append(current)
    
    while current != Goal:
        current_dist = dist[current]
        found = False
        
        for dx, dy in directions:
            next_node = (current[0] + dx, current[1] + dy)
            if 0 <= next_node[0] < Rows and 0 <= next_node[1] < Cols:
                if next_node in dist and dist[next_node] == current_dist - 1:
                    current = next_node
                    path.append(current)
                    found = True
                    break
        
        if not found:
            return []
    
    return path[1:-1] # συμβαινει συχνα

#Function to convert the path to a matrix representation
def create_path_matrix(rows, cols, start, goal, path):
    # Initialize an empty matrix with 0s (representing nothing)
    matrix = [[0 for _ in range(cols)] for _ in range(rows)]
    
    #Mark the path nodes with 3
    for r, c in path:
        if 0 <= r < rows and 0 <= c < cols:
            matrix[r][c] = 3
            
    #Mark the start node with 1 (overwrites path if they overlap)
    if start and 0 <= start[0] < rows and 0 <= start[1] < cols:
        matrix[start[0]][start[1]] = 1
        
    #Mark the goal node with 2 (overwrites path if they overlap)
    if goal and 0 <= goal[0] < rows and 0 <= goal[1] < cols:
        matrix[goal[0]][goal[1]] = 2
        
    commandgen(matrix)

step = 30 # Default step value, can be updated in the Step page

def commandgen(matrix, filename="command.txt"):
    global step
    start_x = -1
    start_y = -1
    rows = len(matrix)
    cols = len(matrix[0])
    
    # Find the starting position
    for i in range(rows):
        for j in range(cols):
            if matrix[i][j] == 1:
                start_x = j
                start_y = i

    cx = start_x
    cy = start_y
    
    with open(filename, 'w') as f:

        f.write("command\n")
        f.write("streamon\n")
        f.write("takeoff\n")
        #f.write("up 100\n")

        while True:
            matrix[cy][cx] = 0
            moved = False

            # 1. Search If we found the goal(2)
            if cy + 1 < rows and matrix[cy+1][cx] == 2:
                f.write(f"back {step}\n")
                break 
            elif cy - 1 >= 0 and matrix[cy-1][cx] == 2:
                f.write(f"forward {step}\n")
                break
            elif cx - 1 >= 0 and matrix[cy][cx-1] == 2:
                f.write(f"left {step}\n")
                break
            elif cx + 1 < cols and matrix[cy][cx+1] == 2:
                f.write(f"right {step}\n")
                break

            #2. Ιf 2 not found , search for 3 
            if cy + 1 < rows and matrix[cy+1][cx] == 3:
                f.write(f"back {step}\n")
                cy += 1
                moved = True
            elif cy - 1 >= 0 and matrix[cy-1][cx] == 3:
                f.write(f"forward {step}\n")
                cy -= 1
                moved = True
            elif cx - 1 >= 0 and matrix[cy][cx-1] == 3:
                f.write(f"left {step}\n")
                cx -= 1
                moved = True
            elif cx + 1 < cols and matrix[cy][cx+1] == 3:
                f.write(f"right {step}\n")
                cx += 1
                moved = True

            #3. Safety Check
            if not moved:
                print("Warning: commandgen got stuck. Breaking loop to prevent freeze.")
                break
        
        f.write("flip f\n")
        f.write("delay 5\n")
        f.write("land")
        
        


class VideoStreamer:
    def __init__(self):
        self.cap = None
        self.running = False
        
        # Create a 640x480 black placeholder frame
        blank_image = np.zeros((480, 640, 3), dtype=np.uint8)
        ret, buffer = cv2.imencode('.jpg', blank_image)
        self.blank_frame = buffer.tobytes()

    def start(self):
        # CRITICAL FIX: Prevent multiple threads from spawning on page refresh
        if self.running:
            return 
            
        self.running = True
        # Open the UDP stream in a background thread
        threading.Thread(target=self._init_capture, daemon=True).start()

    def _init_capture(self):
        # Keep trying to connect as long as the streamer is running
        while self.running and (self.cap is None or not self.cap.isOpened()):
            self.cap = cv2.VideoCapture("udp://@0.0.0.0:11111", cv2.CAP_FFMPEG)
            if not self.cap.isOpened():
                time.sleep(0.5) 

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None

    def generate_frames(self):
        try:
            # Yield the black frame immediately
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + self.blank_frame + b'\r\n')
                   
            while True:
                if self.running and self.cap and self.cap.isOpened():
                    success, frame = self.cap.read()
                    if success:
                        frame = cv2.resize(frame, (640, 480))
                        ret, buffer = cv2.imencode('.jpg', frame)
                        if ret:
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                            continue 
                
                time.sleep(0.1)
                
        except Exception:
            pass

#Video Streamer object
streamer=VideoStreamer()

#FastAPI route for the MPEG stream
@app.get('/video_stream')
def video_stream():
    return StreamingResponse(streamer.generate_frames(), media_type='multipart/x-mixed-replace; boundary=frame')

#Autentication middleware
@app.add_middleware
class AuthMiddleware(BaseHTTPMiddleware):

    #Asynchronous function, DO NOT CHANGE THE NAME, IT MUST BE dispatch
    async def dispatch(self, request: Request, call_next):

        #If not logged in (looking for the 'authenticated' key, if not found it returns False)
        if not app.storage.user.get('authenticated', False):

            #URL checks
            if not request.url.path.startswith('/_nicegui') and not request.url.path.startswith('/static')and request.url.path not in unrestricted_page_routes:

                #Redirected to login
                return RedirectResponse(f'/login?redirect_to={request.url.path}')

        return await call_next(request)

#Admin access middleware
@app.add_middleware
class AdminMiddleware(BaseHTTPMiddleware):

    #Asynchronous function, DO NOT CHANGE THE NAME, IT MUST BE dispatch
    async def dispatch(self, request: Request, call_next):

        #Check if page is protected
        if request.url.path in protected:

            #Check if user is an not admin
            if not app.storage.user.get('admin', False):
                
                #Send user back to login (logged in users are redirected again to '/')
                return RedirectResponse(f'/login?redirect_to={request.url.path}')

        return await call_next(request)

@app.exception_handler(404)
async def custom_404_handler(request: Request, exception: Exception) -> Response:
    
    # Create a temporary NiceGUI page context for the error
    with Client(page(''), request=request) as client:
        
        # 1. Load your awesome new checkerboard background!
        ui.add_head_html('<link rel="stylesheet" href="/static/backdrop.css?v=1">')
        
        # 2. Build the Error UI
        with ui.card().classes('absolute-center items-center p-8'):
            ui.label('404').classes('text-6xl font-bold text-gray-800')
            ui.label('Oops! We could not find that page.').classes('text-xl mb-4')
            
            # 3. Give them a way back home
            ui.button('Go to Dashboard', on_click=lambda: ui.navigate.to('/'))
            
    # Return the fully built NiceGUI page with a 404 status code
    return client.build_response(request, 404)

#Create a page with name '/' and title 'Home'
@ui.page('/',title = 'Home')
def main_page() -> None:

    navui.navigation_ui("Home")

    with ui.card():

        #Make a column
        with ui.column().classes('p-8'):
            ui.label('Welcome to the main content area!').classes('text-2xl')
            ui.label(f"You are logged in as: {app.storage.user.get('username')}")
            ui.label('Click the hamburger icon in the top left to open the menu.')

            #The log out button
            ui.button(on_click=logout.logout, icon='logout', text='Log out')

#Create a page with name 'subpage'
@ui.page('/subpage')
def test_page() -> None:
    ui.label('This is a sub page.')

#Create a page with name 'login' and title 'Log In'
@ui.page('/login', title = 'Log In')
def login(redirect_to: str = '/') -> RedirectResponse | None:

    with open(passwords_path, 'r') as file:
        passwords = json.load(file)

    #Login function
    def try_login() -> None:

        #Check if given password mathes the actual password
        if passwords.get(username.value) == password.value:

            #Check if user is an admin
            if username.value in admins:

                #Seve cookies
                app.storage.user.update({'username': username.value, 'authenticated': True, 'admin': True})

                #Redirect user where they wanted to go
                ui.navigate.to(redirect_to)
            else:

                #Seve cookies
                app.storage.user.update({'username': username.value, 'authenticated': True, 'admin': False})

                #Redirect user where they wanted to go
                ui.navigate.to(redirect_to)
        else:

            #Wrong username or password notification
            ui.notify('Wrong username or password', color='negative')

    #Add the background stylesheet to the HTML header
    ui.add_head_html('<link rel="stylesheet" href="/static/backdrop.css">')

    #Check wether the user is authenticated
    if app.storage.user.get('authenticated', False):
    
        #Is authenticated, redirect to '/'
        return RedirectResponse('/')
    
    #Make the card for the login imput boxes
    with ui.card().classes('absolute-center'):

        #Username input box
        username = ui.input('Username').on('keydown.enter', try_login)

        #Password input box
        password = ui.input('Password', password=True, password_toggle_button=True).on('keydown.enter', try_login)

        #Login button
        ui.button('Log in', on_click=try_login)
    
    return None

#Create page with name 'protected'
@ui.page('/protected')
def protected_page() -> None:
    ui.label("Hi admin!")

# Create a global instance so the socket isn't bound multiple times
tello_instance = None

@ui.page('/dashboard',title = 'Dashboard')
def robot_dashboard():
    
    navui.navigation_ui("Dashboard")

    with ui.card().classes('col-span-2 h-full items-center justify-center border border-gray-700 bg-black p-0 overflow-hidden'):
            #Pull from the FastAPI route
            ui.html('<img src="/video_stream" style="width: 100%; height: 100%; object-fit: contain;">')

    #Mission execution (function based on DJI's SDK example)
    #Mission execution (function based on DJI's SDK example)
    def execute_mission():
        global tello_instance
        #Only initialize the drone connection once
        if tello_instance is None:
            tello_instance = Tello()
            
        try:
            with open("command.txt", "r") as f:
                commands = f.readlines()
        except FileNotFoundError:
            #Replaced ui.notify with print. Calling ui elements in a background thread crashes the app.
            print("Error: command.txt not found! Please generate a path first.")
            return None # Επιστρέφει None αν υπάρξει σφάλμα

        for cmd in commands:
            cmd = cmd.strip()
            if cmd:
                # Intercept the 'delay' command locally so the drone doesn't error out
                if cmd.startswith("delay"):
                    try:
                        delay_time = float(cmd.split(" ")[1])
                        time.sleep(delay_time)
                    except (IndexError, ValueError):
                        time.sleep(5)
                else:
                    tello_instance.send_command(cmd)
        
        #BATTERY - METALLICA
        try:
            battery_level = tello_instance.get_battery()
            return battery_level
        except Exception as e:
            print(f"Couldn't Return The Battery Level: {e}")
            return None
    
    async def auto_start():

        #Notify user that the mission is starting
        ui.notify('Initializing mission...', color='warning')
        
        #Wait a few seconds
        await asyncio.sleep(3)
        
        #Start the streamer object
        streamer.start()
        ui.notify('Executing commands from command.txt', color='info')

        #Running mission in a background thread και αποθήκευση της μπαταρίας
        battery = await run.io_bound(execute_mission)
        
        #Stop streaming
        streamer.stop()

        # Βattery
        if battery:
            ui.notify(f'Mission Complete! Drone Battery: {battery}%', color='positive', timeout=8000)
        else:
            ui.notify('Mission Complete!', color='positive')
    
    # Added Start Mission Button
    with ui.row().classes('w-full justify-center mt-4 mb-4'):
        ui.button('Start mission', on_click=auto_start)

@ui.page('/signup', title='Sign Up')
def signup():

    navui.navigation_ui("Add user")
    
    def try_signup() -> None:

        if password.value != confirm_password.value:
            ui.notify('Passwords do not match!', color='negative')
            return
            
        if not username.value or not password.value:
            ui.notify('Please fill in all fields', color='negative')
            return

        with open(passwords_path, 'r') as file:
            current_users = json.load(file)

        if username.value in current_users:
            ui.notify('Username is already taken!', color='negative')
            return

        current_users[username.value] = password.value
        
        with open(passwords_path, 'w') as file:

            json.dump(current_users, file, indent=4)

        ui.notify('Account created successfully! You can now log in.', color='positive')
        ui.navigate.to('/login')

    # Add your awesome checkerboard background
    ui.add_head_html('<link rel="stylesheet" href="/static/backdrop.css">')

    # Build the Sign Up Card
    with ui.card().classes('absolute-center items-center p-6'):
        ui.label('Add new user').classes('text-2xl font-bold mb-4')
        
        username = ui.input('Username').on('keydown.enter', try_signup).classes('w-full')
        password = ui.input('Password', password=True, password_toggle_button=True).on('keydown.enter', try_signup).classes('w-full')
        confirm_password = ui.input('Confirm Password', password=True, password_toggle_button=True).on('keydown.enter', try_signup).classes('w-full mb-4')
        
        with ui.row().classes('w-full justify-between mt-2'):
            ui.button('Back to Homepage', on_click=lambda: ui.navigate.to('/')).props('flat')
            ui.button('Add', on_click=try_signup)

@ui.page('/about',title='About')
def about():
    
    navui.navigation_ui('About')

    with ui.column().classes('w-full items-center'):
    
        with ui.card().classes('w-[500px] items-center'):
            ui.label('AVRA AUTH GUI').classes('text-lg font-bold')
            ui.image(image_path).classes('w-full')

#Tello code
def build_commands_file(matrix):
    n=len(matrix)
    for i in range(n):
        print(matrix[i][:])

@ui.page('/astar',title='A*')
def astar_page():
    ui.add_head_html('<style>.q-btn .q-focus-helper { display: none !important; }</style>')
    state = {
    'start': None,
    'goal': None,
    'obstacles': set(),
    'path': []
    }

    cells = {}

    def update_grid():
        for (r, c), btn in cells.items():
            if (r, c) == state['start']:
                btn.props('color=green')
            elif (r, c) == state['goal']:
                btn.props('color=red')
            elif (r, c) in state['obstacles']:
                btn.props('color=dark')
            elif (r, c) in state['path']:
                btn.props('color=blue')
            else:
                btn.props('color=grey-4')

    def cell_clicked(r, c):
        mode=mode_toggle.value
        pos=(r, c)
        
        state['path']=[]
        
        if mode=='Start':
            if pos in state['obstacles']: state['obstacles'].remove(pos)
            if pos==state['goal']: state['goal']=None
            state['start'] = pos
            
        elif mode=='Goal':
            if pos in state['obstacles']: state['obstacles'].remove(pos)
            if pos==state['start']: state['start']=None
            state['goal'] = pos
            
        elif mode=='Obstacle':
            if pos==state['start']: state['start']=None
            if pos==state['goal']: state['goal']=None
            state['obstacles'].add(pos)
            
        elif mode=='Erase':
            if pos==state['start']: state['start']=None
            if pos==state['goal']: state['goal']=None
            if pos in state['obstacles']: state['obstacles'].remove(pos)
            
        update_grid()

    def solve():
        if not state['start'] or not state['goal']:
            ui.notify('Please set both a Start and a Goal!', type='warning')
            return
        
        state['path'] = astar(
            state['start'], 
            state['goal'], 
            state['obstacles'], 
            int(rows_input.value), 
            int(cols_input.value)
        )

        state['matrix'] = create_path_matrix(
            int(rows_input.value), 
            int(cols_input.value), 
            state['start'], 
            state['goal'], 
            state['path']
        )
        
        if not state['path']:
            ui.notify('No path found! Obstacles might be blocking the way.', type='negative')
        else:
            ui.notify('Optimal path found!', type='positive')
            
        update_grid()

    def clear_grid():
        state['start'] = None
        state['goal'] = None
        state['obstacles'].clear()
        state['path'].clear()
        update_grid()

    ui.label("A* Pathfinding Interface").classes('text-2xl font-bold mb-2 mt-4')

    with ui.row().classes('items-center mb-4'):
        mode_toggle=ui.toggle(['Start', 'Goal', 'Obstacle', 'Erase'], value='Obstacle').classes('mr-4')
        ui.button('Find Path', on_click=solve, color='green')
        ui.button('Clear Map', on_click=clear_grid, color='red').props('outline')

    def change_size():
        clear_grid()
        draw_grid.refresh()

    with ui.row().classes('items-center mb-4'):
        rows_input=ui.number(label='Number of rows', value=15).props('min=5 max=50 step=1')
        cols_input=ui.number(label='Number of columns', value=15).props('min=5 max=50 step=1')
        ui.button('Change size', on_click=change_size)

    @ui.refreshable
    def draw_grid():
        cells.clear()
        with ui.card().classes('p-2 bg-gray-50'):
            with ui.grid(columns=int(cols_input.value)).classes('gap-0.5'):
                for r in range(int(rows_input.value)):
                    for c in range(int(cols_input.value)):
                        btn = ui.button(on_click=lambda e, r=r, c=c: cell_clicked(r, c), color='grey-4')
                        btn.props('unelevated square padding="none" :ripple="false"').classes('w-8 h-8')
                        cells[(r, c)] = btn
        update_grid()

    draw_grid()

@ui.page('/dijkstra',title='Dijkstra')
def dijkstra_page():
    ui.add_head_html('<style>.q-btn .q-focus-helper { display: none !important; }</style>')
    state = {
    'start': None,
    'goal': None,
    'obstacles': set(),
    'path': []
    }

    cells = {}
    def update_grid():
        for (r, c), btn in cells.items():
            if (r, c) == state['start']:
                btn.props('color=green')
            elif (r, c) == state['goal']:
                btn.props('color=red')
            elif (r, c) in state['obstacles']:
                btn.props('color=dark')
            elif (r, c) in state['path']:
                btn.props('color=blue')
            else:
                btn.props('color=grey-4')

    def cell_clicked(r, c):
        mode=mode_toggle.value
        pos=(r, c)
        
        state['path']=[]
        
        if mode=='Start':
            if pos in state['obstacles']: state['obstacles'].remove(pos)
            if pos==state['goal']: state['goal']=None
            state['start'] = pos
            
        elif mode=='Goal':
            if pos in state['obstacles']: state['obstacles'].remove(pos)
            if pos==state['start']: state['start']=None
            state['goal'] = pos
            
        elif mode=='Obstacle':
            if pos==state['start']: state['start']=None
            if pos==state['goal']: state['goal']=None
            state['obstacles'].add(pos)
            
        elif mode=='Erase':
            if pos==state['start']: state['start']=None
            if pos==state['goal']: state['goal']=None
            if pos in state['obstacles']: state['obstacles'].remove(pos)
            
        update_grid()

    def solve():
        if not state['start'] or not state['goal']:
            ui.notify('Please set both a Start and a Goal!', type='warning')
            return
        
        state['path'] = dijkstra(
            state['start'], 
            state['goal'], 
            state['obstacles'], 
            int(rows_input.value), 
            int(cols_input.value)
        )

        state['matrix'] = create_path_matrix(
            int(rows_input.value), 
            int(cols_input.value), 
            state['start'], 
            state['goal'], 
            state['path']
        )
        
        if not state['path']:
            ui.notify('No path found! Obstacles might be blocking the way.', type='negative')
        else:
            ui.notify('Optimal path found!', type='positive')
            
        update_grid()

    def clear_grid():
        state['start'] = None
        state['goal'] = None
        state['obstacles'].clear()
        state['path'].clear()
        update_grid()

    ui.label("Dijkstra Pathfinding Interface").classes('text-2xl font-bold mb-2 mt-4')

    with ui.row().classes('items-center mb-4'):
        mode_toggle=ui.toggle(['Start', 'Goal', 'Obstacle', 'Erase'], value='Obstacle').classes('mr-4')
        ui.button('Find Path', on_click=solve, color='green')
        ui.button('Clear Map', on_click=clear_grid, color='red').props('outline')

    def change_size():
        clear_grid()
        draw_grid.refresh()

    with ui.row().classes('items-center mb-4'):
        rows_input=ui.number(label='Number of rows', value=15).props('min=5 max=50 step=1')
        cols_input=ui.number(label='Number of columns', value=15).props('min=5 max=50 step=1')
        ui.button('Change size', on_click=change_size)

    @ui.refreshable
    def draw_grid():
        cells.clear()
        with ui.card().classes('p-2 bg-gray-50'):
            with ui.grid(columns=int(cols_input.value)).classes('gap-0.5'):
                for r in range(int(rows_input.value)):
                    for c in range(int(cols_input.value)):
                        btn = ui.button(on_click=lambda e, r=r, c=c: cell_clicked(r, c), color='grey-4')
                        btn.props('unelevated square padding="none" :ripple="false"').classes('w-8 h-8')
                        cells[(r, c)] = btn
        update_grid()

    draw_grid()

@ui.page('/grassfire',title='Grassfire')
def grassfire_page():
    ui.add_head_html('<style>.q-btn .q-focus-helper { display: none !important; }</style>')
    state = {
    'start': None,
    'goal': None,
    'obstacles': set(),
    'path': []
    }

    cells = {}
    def update_grid():
        for (r, c), btn in cells.items():
            if (r, c) == state['start']:
                btn.props('color=green')
            elif (r, c) == state['goal']:
                btn.props('color=red')
            elif (r, c) in state['obstacles']:
                btn.props('color=dark')
            elif (r, c) in state['path']:
                btn.props('color=blue')
            else:
                btn.props('color=grey-4')

    def cell_clicked(r, c):
        mode=mode_toggle.value
        pos=(r, c)
        
        state['path']=[]
        
        if mode=='Start':
            if pos in state['obstacles']: state['obstacles'].remove(pos)
            if pos==state['goal']: state['goal']=None
            state['start'] = pos
            
        elif mode=='Goal':
            if pos in state['obstacles']: state['obstacles'].remove(pos)
            if pos==state['start']: state['start']=None
            state['goal'] = pos
            
        elif mode=='Obstacle':
            if pos==state['start']: state['start']=None
            if pos==state['goal']: state['goal']=None
            state['obstacles'].add(pos)
            
        elif mode=='Erase':
            if pos==state['start']: state['start']=None
            if pos==state['goal']: state['goal']=None
            if pos in state['obstacles']: state['obstacles'].remove(pos)
            
        update_grid()

    def solve():
        if not state['start'] or not state['goal']:
            ui.notify('Please set both a Start and a Goal!', type='warning')
            return
        
        state['path'] = grassfire(
            state['start'], 
            state['goal'], 
            state['obstacles'], 
            int(rows_input.value), 
            int(cols_input.value)
        )

        state['matrix'] = create_path_matrix(
            int(rows_input.value), 
            int(cols_input.value), 
            state['start'], 
            state['goal'], 
            state['path']
        )
        
        if not state['path']:
            ui.notify('No path found! Obstacles might be blocking the way.', type='negative')
        else:
            ui.notify('Optimal path found!', type='positive')
            
        update_grid()

    def clear_grid():
        state['start'] = None
        state['goal'] = None
        state['obstacles'].clear()
        state['path'].clear()
        update_grid()

    ui.label("Grassfire Pathfinding Interface").classes('text-2xl font-bold mb-2 mt-4')

    with ui.row().classes('items-center mb-4'):
        mode_toggle=ui.toggle(['Start', 'Goal', 'Obstacle', 'Erase'], value='Obstacle').classes('mr-4')
        ui.button('Find Path', on_click=solve, color='green')
        ui.button('Clear Map', on_click=clear_grid, color='red').props('outline')

    def change_size():
        clear_grid()
        draw_grid.refresh()

    with ui.row().classes('items-center mb-4'):
        rows_input=ui.number(label='Number of rows', value=15).props('min=5 max=50 step=1')
        cols_input=ui.number(label='Number of columns', value=15).props('min=5 max=50 step=1')
        ui.button('Change size', on_click=change_size)

    @ui.refreshable
    def draw_grid():
        cells.clear()
        with ui.card().classes('p-2 bg-gray-50'):
            with ui.grid(columns=int(cols_input.value)).classes('gap-0.5'):
                for r in range(int(rows_input.value)):
                    for c in range(int(cols_input.value)):
                        btn = ui.button(on_click=lambda e, r=r, c=c: cell_clicked(r, c), color='grey-4')
                        btn.props('unelevated square padding="none" :ripple="false"').classes('w-8 h-8')
                        cells[(r, c)] = btn
        update_grid()

    draw_grid()
    
@ui.page('/step',title='Step')
def step_page():
    
    navui.navigation_ui('Step')
    
    with ui.card().classes('absolute-center items-center p-6'):
        ui.label('Step (cm)').classes('text-xl font-bold mb-4')
        
        step_input = ui.number(value=step, min=20, max=500, step=5)
        
        def update_step():
            global step
            step = int(step_input.value) 
            ui.notify(f'Step Updated to: {step} [cm]', color='positive')
        
        with ui.row().classes('w-full justify-center mt-4 mb-4'):
            ui.button('Update', on_click=update_step)
        
if __name__ in {'__main__', '__mp_main__'}:

    #Run the GUI on localhost:8080
    ui.run(storage_secret='THIS_NEEDS_TO_BE_CHANGED',show=False,port=8080,favicon=favicon_path,uvicorn_reload_dirs=f"{base_dir},{base_dir / '.nicegui'}",uvicorn_reload_includes='*.py,*.css,*.html,*.js,*.vue')