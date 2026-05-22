from nicegui import ui,app
import logout

def navigation_ui(title):
    
    #Make the header (blue bar on top)
    myheader=ui.header().classes('items-center')

    #Add the background stylesheet to the HTML header
    ui.add_head_html('<link rel="stylesheet" href="/static/backdrop.css">')

    #Edit header content
    with myheader:

        #Add the burger menu button (when clicked it toggles the drawer)
        ui.button(icon='menu', on_click=lambda: mydrawer.toggle()).props('flat color=white')
        
        #Add a label
        ui.label(title).classes('text-lg font-bold ml-4')

        #Add a space to move everything to the right side
        ui.space()

        with ui.button(app.storage.user.get('username'),icon='account_circle').props('flat color=white'):
            with ui.menu().classes('w-32'):
                ui.menu_item('Log out', on_click=logout.logout)

    #Make the drawer
    mydrawer=ui.left_drawer(value=False,bottom_corner=False).classes('bg-gray-100 p-4')

    #Edit drwaer content
    with mydrawer:

        #Conent
        with ui.column().classes('w-full gap-1'):
            ui.label('Navigation').classes('text-h6 font-bold mb-2')
            ui.separator().classes('mb-4')
            
            ui.button('Home', icon='home', on_click=lambda: ui.navigate.to('/')).classes('w-full text-lg').props('flat color=black align=left')
            ui.button('Dashboard', icon='liquor', on_click=lambda: ui.navigate.to('/dashboard')).classes('w-full text-lg').props('flat color=black align=left')
            ui.button('A*', icon='calculate', on_click=lambda: ui.navigate.to('/astar')).classes('w-full text-lg').props('flat color=black align=left')
            ui.button('Dijkstra', icon='route', on_click=lambda: ui.navigate.to('/dijkstra')).classes('w-full text-lg').props('flat color=black align=left')
            ui.button('Grassfire', icon='local_fire_department', on_click=lambda: ui.navigate.to('/grassfire')).classes('w-full text-lg').props('flat color=black align=left')
            ui.button('Settings', icon='settings', on_click=lambda: ui.navigate.to('/signup')).classes('w-full text-lg').props('flat color=black align=left')

        ui.space()

        with ui.column().classes('w-full'):
            ui.separator().classes('w-full mb-2')
            ui.button('About', icon='info', on_click=lambda: ui.navigate.to('/about')).classes('w-full text-lg').props('flat color=gray-700 align=left')

if __name__ in '__main__':
    print("Do not run this as a standalone script!")
