import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk  # Asegúrate de agregar esta línea
import cv2
import threading
import json
import os

# Definir el archivo de cache donde se guardan las cámaras
CAMERAS_FILE = "cameras_cache.json"

# Comprobar si el archivo de cache existe, si no, crear uno con la estructura adecuada
if not os.path.exists(CAMERAS_FILE):
    with open(CAMERAS_FILE, 'w') as f:
        json.dump({"cameras": [], "grid_size": 1}, f)

# Cargar las cámaras y configuración desde el archivo de cache
def load_cameras_and_config():
    try:
        with open(CAMERAS_FILE, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):  # Si el archivo contiene una lista, convertirlo al formato esperado
                data = {"cameras": data, "grid_size": 1}
                save_cameras_and_config(data["cameras"], data["grid_size"])  # Actualizar el archivo
            cameras = data.get("cameras", [])
            grid_size = data.get("grid_size", 1)  # Valor predeterminado 1x1
            return cameras, grid_size
    except (json.JSONDecodeError, FileNotFoundError):
        # Si el archivo está corrupto o no existe, inicializar con valores predeterminados
        save_cameras_and_config([], 1)
        return [], 1

# Guardar las cámaras y configuración en el archivo de cache
def save_cameras_and_config(cameras, grid_size):
    with open(CAMERAS_FILE, 'w') as f:
        json.dump({"cameras": cameras, "grid_size": grid_size}, f)

# Crear la ventana principal
class CameraApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Monitoreo de Cámaras IP")
        self.state('zoomed')  # Maximizar la ventana al iniciar
        self.resizable(False, False)  # Deshabilitar el cambio de tamaño de la ventana

        # Bloquear la barra de título para que no se pueda mover
        self.overrideredirect(True)

        # Establecer el color de fondo a oscuro
        self.configure(bg="black")

        # Contenedor de cámaras
        self.cameras, self.grid_size_override = load_cameras_and_config()
        self.current_camera_index = 0  # Índice de la cámara actual para 1x1
        self.running_threads = []  # Keep track of running threads

        # Crear la interfaz
        self.create_widgets()

        # Aplicar el tamaño del grid cargado
        self.set_grid_size(self.grid_size_override)

    def create_widgets(self):
        # Crear el menú superior
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar, bg="black")  # Fondo oscuro para el menú

        # Menú de opciones
        options_menu = tk.Menu(menu_bar, tearoff=0, bg="gray", fg="white")  # Fondo oscuro y texto claro
        menu_bar.add_cascade(label="Opciones", menu=options_menu)
        options_menu.add_command(label="Agregar Cámara", command=self.add_camera)
        options_menu.add_command(label="Eliminar Cámara", command=self.delete_camera_prompt)

        # Menú para cambiar el tamaño del grid
        grid_menu = tk.Menu(menu_bar, tearoff=0, bg="gray", fg="white")  # Fondo oscuro y texto claro
        menu_bar.add_cascade(label="Diseño", menu=grid_menu)
        grid_menu.add_command(label="1x1", command=lambda: self.set_grid_size(1))
        grid_menu.add_command(label="2x2", command=lambda: self.set_grid_size(2))
        grid_menu.add_command(label="3x3", command=lambda: self.set_grid_size(3))

        # Navegación entre cámaras (solo para 1x1)
        navigation_menu = tk.Menu(menu_bar, tearoff=0, bg="gray", fg="white")
        menu_bar.add_cascade(label="Navegación", menu=navigation_menu)
        navigation_menu.add_command(label="Siguiente Cámara", command=self.next_camera)
        navigation_menu.add_command(label="Anterior Cámara", command=self.previous_camera)

        # Salir de la aplicación
        menu_bar.add_command(label="Salir", command=self.confirm_exit)

        # Contenedor para las cámaras
        self.grid_frame = tk.Frame(self, bg="black")  # Fondo oscuro para el contenedor
        self.grid_frame.pack(fill=tk.BOTH, expand=True)

        self.update_camera_grid()

    def set_grid_size(self, size):
        # Establecer el tamaño del grid
        self.grid_size_override = size
        save_cameras_and_config(self.cameras, self.grid_size_override)  # Guardar configuración
        self.update_camera_grid()

    def update_camera_grid(self):
        # Detener todos los hilos antes de actualizar el grid
        self.stop_all_threads()

        # Asegurarse de que el tamaño del grid respete el valor guardado
        grid_size = self.grid_size_override
        if grid_size > 3:
            grid_size = 3  # Limitar el grid a un máximo de 3x3
        elif grid_size < 1:
            grid_size = 1  # Asegurar un mínimo de 1x1

        self.grid_size_override = grid_size  # Actualizar el valor en caso de ajustes

        # Limpiar el grid frame antes de redibujar
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        # Obtener el tamaño de la ventana
        self.update_idletasks()  # Asegurarse de que las dimensiones de la ventana sean correctas
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        camera_width = window_width // grid_size
        camera_height = window_height // grid_size

        # Configurar las filas y columnas del grid
        for row in range(grid_size):
            self.grid_frame.grid_rowconfigure(row, weight=1, minsize=camera_height)
        for col in range(grid_size):
            self.grid_frame.grid_columnconfigure(col, weight=1, minsize=camera_width)

        # Crear un frame para cada cámara
        for i, camera in enumerate(self.cameras[:grid_size * grid_size]):
            row = i // grid_size
            col = i % grid_size

            # Crear un frame para cada cámara
            camera_frame = tk.Frame(self.grid_frame, width=camera_width, height=camera_height, bg="black")  # Fondo oscuro
            camera_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            camera_frame.grid_propagate(False)  # Deshabilitar la propagación del tamaño

            # Label con el nombre de la cámara
            camera_label = tk.Label(camera_frame, text=camera['name'], bg="black", fg="white")  # Fondo oscuro y texto claro
            camera_label.pack()

            # Video panel para mostrar la transmisión
            video_panel = tk.Label(camera_frame, width=camera_width, height=camera_height, bg="black")  # Fondo oscuro
            video_panel.pack(fill=tk.BOTH, expand=True)

            # Iniciar un hilo para capturar video de la cámara
            threading.Thread(target=self.show_camera_stream, args=(camera['rtsp_url'], video_panel), daemon=True).start()

        # Si el grid es 1x1, mostrar solo una cámara
        if grid_size == 1 and self.cameras:
            camera = self.cameras[self.current_camera_index]
            # Crear un frame para la cámara actual
            camera_frame = tk.Frame(self.grid_frame, width=camera_width, height=camera_height, bg="black")
            camera_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
            camera_frame.grid_propagate(False)

            # Label con el nombre de la cámara
            camera_label = tk.Label(camera_frame, text=camera['name'], bg="black", fg="white")
            camera_label.pack()

            # Video panel para mostrar la transmisión
            video_panel = tk.Label(camera_frame, width=camera_width, height=camera_height, bg="black")
            video_panel.pack(fill=tk.BOTH, expand=True)

            # Iniciar un hilo para capturar video de la cámara
            threading.Thread(target=self.show_camera_stream, args=(camera['rtsp_url'], video_panel), daemon=True).start()

    def next_camera(self):
        # Cambiar a la siguiente cámara en 1x1
        if self.grid_size_override == 1 and self.cameras:
            self.current_camera_index = (self.current_camera_index + 1) % len(self.cameras)
            self.update_camera_grid()

    def previous_camera(self):
        # Cambiar a la cámara anterior en 1x1
        if self.grid_size_override == 1 and self.cameras:
            self.current_camera_index = (self.current_camera_index - 1) % len(self.cameras)
            self.update_camera_grid()

    def stop_all_threads(self):
        # Stop all threads by setting their running flag to False
        for thread in self.running_threads:
            thread["running"] = False
        self.running_threads.clear()

    def show_camera_stream(self, rtsp_url, video_panel):
        # Create a thread control flag
        thread_control = {"running": True}
        self.running_threads.append(thread_control)

        cap = cv2.VideoCapture(rtsp_url)
        if not cap.isOpened():
            messagebox.showerror("Error", f"No se pudo conectar a la cámara: {rtsp_url}")
            return

        while thread_control["running"]:
            try:
                ret, frame = cap.read()
                if ret:
                    # Check if the widget still exists
                    if not video_panel.winfo_exists():
                        break

                    # Obtener las dimensiones del panel
                    panel_width = video_panel.winfo_width()
                    panel_height = video_panel.winfo_height()

                    # Redimensionar el frame manteniendo la proporción
                    frame_height, frame_width, _ = frame.shape
                    aspect_ratio = frame_width / frame_height

                    if panel_width / panel_height > aspect_ratio:
                        new_height = panel_height
                        new_width = int(panel_height * aspect_ratio)
                    else:
                        new_width = panel_width
                        new_height = int(panel_width / aspect_ratio)

                    resized_frame = cv2.resize(frame, (new_width, new_height))

                    # Convertir la imagen a formato que Tkinter pueda mostrar
                    frame_rgb = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                    frame_image = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))

                    # Actualizar el video en la interfaz
                    video_panel.config(image=frame_image)
                    video_panel.image = frame_image
                else:
                    messagebox.showwarning("Advertencia", "No se pudo leer el frame de la cámara.")
                    break

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except tk.TclError:
                # Handle widget destruction gracefully
                break

        cap.release()

    def add_camera(self):
        # Mostrar un formulario para agregar una cámara
        camera_info = simpledialog.askstring(
            "Agregar Cámara",
            "Ingresa el nombre de la cámara y la URL RTSP separados por una coma (Ejemplo: Cámara 1, rtsp://url):"
        )

        if camera_info:
            try:
                name, rtsp_url = map(str.strip, camera_info.split(',', 1))
                if name and rtsp_url:
                    # Validar la URL RTSP
                    if not rtsp_url.startswith("rtsp://"):
                        messagebox.showerror("Error", "La URL debe comenzar con 'rtsp://'.")
                        return

                    # Guardar la cámara en la lista y actualizar el cache
                    new_camera = {'name': name, 'rtsp_url': rtsp_url}
                    self.cameras.append(new_camera)
                    save_cameras_and_config(self.cameras, self.grid_size_override)  # Guardar configuración
                    self.update_camera_grid()
                else:
                    messagebox.showerror("Error", "Ambos campos son obligatorios.")
            except ValueError:
                messagebox.showerror("Error", "Formato incorrecto. Usa una coma para separar el nombre y la URL.")

    def delete_camera_prompt(self):
        # Mostrar un formulario para seleccionar una cámara a eliminar
        if not self.cameras:
            messagebox.showinfo("Eliminar Cámara", "No hay cámaras para eliminar.")
            return

        camera_names = [camera['name'] for camera in self.cameras]
        selected_camera = simpledialog.askstring(
            "Eliminar Cámara",
            f"Selecciona la cámara a eliminar:\n{', '.join(camera_names)}"
        )

        if selected_camera:
            for index, camera in enumerate(self.cameras):
                if camera['name'] == selected_camera:
                    self.delete_camera(index)
                    break
            else:
                messagebox.showerror("Error", "Cámara no encontrada.")

    def delete_camera(self, index):
        # Eliminar la cámara seleccionada
        confirm = messagebox.askyesno("Eliminar cámara", "¿Estás seguro de que deseas eliminar esta cámara?")
        if confirm:
            del self.cameras[index]
            save_cameras_and_config(self.cameras, self.grid_size_override)  # Guardar configuración
            self.update_camera_grid()
        else:
            messagebox.showinfo("Eliminar cámara", "Operación cancelada.")

    def toggle_fullscreen(self):
        # Alternar entre pantalla completa y ventana normal
        is_fullscreen = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not is_fullscreen)

    def on_close(self):
        # Stop all threads and close the application
        self.stop_all_threads()
        self.destroy()

    def confirm_exit(self):
        # Confirm before exiting the application
        if messagebox.askyesno("Salir", "¿Estás seguro de que deseas salir?"):
            self.on_close()

if __name__ == "__main__":
    app = CameraApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)  # Handle window close event
    app.mainloop()
