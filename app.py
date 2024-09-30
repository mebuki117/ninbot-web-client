import customtkinter as ctk
import requests
import server
import socket
import webbrowser

PORT = server.PORT
VERSION = 'v1.0.0'

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"Ninbot Local Overlay {VERSION}")
        self.geometry("400x300")

        link_label = ctk.CTkLabel(self, text=f"Server URL: {App.get_ninb_page_url()}", text_color="yellow", fg_color="transparent", cursor="hand2")
        link_label.pack(pady=10)
        link_label.bind("<Button-1>", lambda e: webbrowser.open(App.get_ninb_page_url()))
        
        self.var_use_chunk_coords = ctk.BooleanVar()
        
        self.entry_use_chunk_coords = ctk.CTkCheckBox(self, text="Use Chunk Coords", variable=self.var_use_chunk_coords)
        self.entry_use_chunk_coords.pack(pady=10)

        self.var_show_angle = ctk.BooleanVar()
        
        self.entry_show_angle = ctk.CTkCheckBox(self, text="Show angle", variable=self.var_show_angle)
        self.entry_show_angle.pack(pady=10)
        

        self.button_update = ctk.CTkButton(self, text="Update Options", command=self.update_options)
        self.button_update.pack(pady=20)

        self.fetch_initial_options()

    def fetch_initial_options(self):
        try:
            response = requests.get(f'http://localhost:{PORT}/get_options')
            if response.status_code == 200:
                options = response.json()

                self.var_use_chunk_coords.set(options.get('use_chunk_coords', False))
                self.var_show_angle.set(options.get('show_angle', False))
        except requests.RequestException as e:
            print(f"Error fetching options: {e}")

    def update_options(self):
        use_chunk_coords_value = True if self.entry_use_chunk_coords.get() == 1 else False
        show_angle_value = True if self.entry_show_angle.get() == 1 else False

        try:
            print('updating options....')
            requests.post(f'http://localhost:{PORT}/update_option', json={"option": "use_chunk_coords", "value": use_chunk_coords_value})
            requests.post(f'http://localhost:{PORT}/update_option', json={"option": "show_angle", "value": show_angle_value})
            print('updated options')
        except requests.RequestException as e:
            print(f"error updating options: {e}")
    
    @staticmethod
    def get_ninb_page_url():
        ip = App.get_local_ip()
        return f'http://{ip}:{PORT}'
    
    @staticmethod
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            print(f"error getting ip: {e}")

server.run_flask()

app = App()
app.mainloop()
