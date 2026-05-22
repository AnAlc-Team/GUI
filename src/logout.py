from nicegui import ui,app

#Logout function
def logout() -> None:
    app.storage.user.clear()
    ui.navigate.to('/login')
    #app.shutdown()

if __name__ in '__main__':
    print("Do not run this as a standalone script!")