# ===================================================================
#                      IMPORTAÇÃO DE BIBLIOTECAS
# ===================================================================
import os
import sys
import webbrowser
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, font
from PIL import Image, ImageTk, ImageEnhance, ImageOps

# ===================================================================
#                      ★ ÁREA DE CUSTOMIZAÇÃO DA MARCA ★
# ===================================================================
NOME_DO_APP = "PixelVista"
NOME_DO_AUTOR = "Lucas Henrique de Oliveira"
# ===================================================================

# --- Constantes de Estilo ---
BG_COLOR = "#2E2E2E"
TEXT_COLOR = "#FFFFFF"
LINK_COLOR = "#6495ED"
BTN_BG_COLOR = "#4A4A4A"
BTN_HOVER_COLOR = "#6E6E6E"
FONT_TUPLE = ("Segoe UI", 10)
FONT_TUPLE_BOLD = ("Segoe UI", 16, "bold")
FONT_ICON = ("Segoe UI", 12)

# ===================================================================
#                      CLASSE PRINCIPAL DO APLICATIVO
# ===================================================================
class ImageViewer(tk.Tk):
    def __init__(self, file_path=None): 
        super().__init__()
        self.title(NOME_DO_APP)
        self.geometry("1000x750")

        try:
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(base_path, 'icone.ico')
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Aviso: Arquivo 'icone.ico' não pôde ser carregado: {e}")

        self.configure(bg=BG_COLOR)
        
        # --- Variáveis de Estado ---
        self.image_list, self.folder_path = [], ""
        self.current_index = -1
        self.original_pil_image = None
        self.edited_pil_image = None
        self.tk_image_ref = None
        self.zoom_level = 1.0
        
        # --- Variáveis de Corte (Crop) ---
        self.cropping = False
        self.crop_start_x, self.crop_start_y = 0, 0
        self.crop_rect_id = None
        
        # --- Variáveis de Arrastar (Pan) ---
        self.pan_start_x, self.pan_start_y = 0, 0
        self.canvas_drag_start_x, self.canvas_drag_start_y = 0, 0

        self.image_on_canvas_id = None
        self.canvas_image_coords = (0, 0) # (x, y) do canto superior esquerdo da imagem no canvas
        
        # --- Interface ---
        self.top_frame = tk.Frame(self, bg=BG_COLOR)
        self.top_frame.pack(side='top', fill='x', pady=5)
        
        self.status_frame = tk.Frame(self, bg=BG_COLOR)
        self.status_frame.pack(side='bottom', fill='x', padx=10, pady=5)
        self.file_status_label = tk.Label(self.status_frame, text="Nenhuma pasta aberta.", fg=TEXT_COLOR, bg=BG_COLOR, anchor='w', font=FONT_TUPLE)
        self.file_status_label.pack(side='left')
        self.author_label = tk.Label(self.status_frame, text=NOME_DO_AUTOR, fg=TEXT_COLOR, bg=BG_COLOR, anchor='e', font=FONT_TUPLE)
        self.author_label.pack(side='right')
        
        self.canvas = tk.Canvas(self, bg=BG_COLOR, highlightthickness=0, cursor="arrow")
        self.canvas.pack(expand=True, fill='both')
        
        self.create_initial_button()
        self.create_nav_buttons()
        self.create_zoom_buttons()
        self.create_menu()
        self.bind_events()

        if file_path:
            self.load_from_file_path(file_path)

    def create_menu(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        
        # Menu Arquivo
        file_menu = tk.Menu(self.menu_bar, tearoff=0) 
        self.menu_bar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Abrir Pasta...", command=self.open_folder, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Salvar (Sobrescrever)", command=self.save_changes, accelerator="Ctrl+S")
        file_menu.add_command(label="Salvar Como...", command=self.save_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.quit, accelerator="Esc")
        
        # Menu Ver
        view_menu = tk.Menu(self.menu_bar, tearoff=0) 
        self.menu_bar.add_cascade(label="Ver", menu=view_menu)
        view_menu.add_command(label="Ajustar à Janela (Reset)", command=self.fit_image_to_window, accelerator="F")
        view_menu.add_command(label="Tamanho Real (100%)", command=lambda: self.set_zoom(1.0), accelerator="R")

        # Menu Editar
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0) 
        self.menu_bar.add_cascade(label="Editar", menu=self.edit_menu, state="disabled")
        self.edit_menu.add_command(label="Cortar Imagem (Seleção)", command=self.start_crop_mode)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Rotacionar 90° Direita", command=lambda: self.apply_edit(self.rotate_image, angle=-90))
        self.edit_menu.add_command(label="Rotacionar 90° Esquerda", command=lambda: self.apply_edit(self.rotate_image, angle=90))
        self.edit_menu.add_command(label="Inverter Horizontalmente", command=lambda: self.apply_edit(self.flip_image, method=Image.Transpose.FLIP_LEFT_RIGHT))
        self.edit_menu.add_command(label="Inverter Verticalmente", command=lambda: self.apply_edit(self.flip_image, method=Image.Transpose.FLIP_TOP_BOTTOM))
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Ajustar Imagem (Brilho, Contraste...)", command=self.open_adjustments_window)
        self.edit_menu.add_command(label="Redimensionar (Esticar)...", command=self.resize_image)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Filtro: Tons de Cinza", command=lambda: self.apply_edit(self.convert_grayscale))
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Desfazer Alterações", command=self.revert_changes)

        # Menu Ferramentas
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Ferramentas", menu=tools_menu, state="normal") 
        tools_menu.add_command(label="Padronizar Imagem Atual...", command=self.standardize_current_image)
        tools_menu.add_separator()
        tools_menu.add_command(label="Padronizar Pasta Inteira (Lote)...", command=self.batch_process_images)
        
        # Menu Ajuda
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label=f"Sobre {NOME_DO_APP}", command=self.show_about_window)

    def open_link(self, url):
        webbrowser.open_new_tab(url)

    def show_about_window(self):
        about_win = tk.Toplevel(self); about_win.title(f"Sobre {NOME_DO_APP}"); about_win.geometry("400x250")
        about_win.configure(bg=BG_COLOR); about_win.resizable(False, False); about_win.transient(self); about_win.grab_set()
        link_font = font.Font(family="Segoe UI", size=10, underline=True)
        tk.Label(about_win, text=NOME_DO_APP, fg=TEXT_COLOR, bg=BG_COLOR, font=("Segoe UI", 20, "bold")).pack(pady=(15, 5))
        tk.Label(about_win, text="Versão 1.5 (Smart Zoom)", fg=TEXT_COLOR, bg=BG_COLOR, font=FONT_TUPLE).pack()
        tk.Label(about_win, text=NOME_DO_AUTOR, fg=TEXT_COLOR, bg=BG_COLOR, font=FONT_TUPLE).pack(pady=10)
        tk.Label(about_win, text="(21) 9 9955-3685", fg=TEXT_COLOR, bg=BG_COLOR, font=FONT_TUPLE).pack()
        github_link = tk.Label(about_win, text="GitHub: LucasHO94", fg=LINK_COLOR, bg=BG_COLOR, font=link_font, cursor="hand2"); github_link.pack()
        github_link.bind("<Button-1>", lambda e: self.open_link("https://github.com/LucasHO94"))
        linkedin_link = tk.Label(about_win, text="LinkedIn: lucasho94", fg=LINK_COLOR, bg=BG_COLOR, font=link_font, cursor="hand2"); linkedin_link.pack()
        linkedin_link.bind("<Button-1>", lambda e: self.open_link("https://www.linkedin.com/in/lucasho94/"))
        tk.Button(about_win, text="OK", command=about_win.destroy, width=10).pack(pady=20)

    def update_status(self):
        if self.image_list:
            filename = os.path.basename(self.image_list[self.current_index])
            count = f"[{self.current_index + 1} de {len(self.image_list)}]"; zoom_percent = f"Zoom: {self.zoom_level:.2f}x ({int(self.zoom_level*100)}%)"
            self.file_status_label.config(text=f"{filename}  {count}  {zoom_percent}"); self.title(f"{filename} - {NOME_DO_APP}")
        else:
            self.file_status_label.config(text="Nenhuma imagem carregada."); self.title(NOME_DO_APP)

    def create_initial_button(self):
        self.open_folder_btn=tk.Button(self,text="Abrir Pasta",command=self.open_folder,bg=BTN_BG_COLOR,fg=TEXT_COLOR,font=FONT_TUPLE_BOLD,relief='flat',padx=20,pady=10,cursor="hand2",activebackground=BTN_HOVER_COLOR,activeforeground=TEXT_COLOR)
        self.open_folder_btn.place(relx=0.5,rely=0.5,anchor='center')
        
    def create_nav_buttons(self):
        self.prev_btn=tk.Button(self,text="<",command=self.show_previous_image,bg=BTN_BG_COLOR,fg=TEXT_COLOR,font=FONT_TUPLE_BOLD,relief='flat',activebackground=BTN_HOVER_COLOR,activeforeground=TEXT_COLOR)
        self.next_btn=tk.Button(self,text=">",command=self.show_next_image,bg=BTN_BG_COLOR,fg=TEXT_COLOR,font=FONT_TUPLE_BOLD,relief='flat',activebackground=BTN_HOVER_COLOR,activeforeground=TEXT_COLOR)
        
    def create_zoom_buttons(self):
        self.zoom_in_btn=tk.Button(self.top_frame,text="🔍+",command=self.zoom_in,bg=BTN_BG_COLOR,fg=TEXT_COLOR,font=FONT_ICON,relief='flat',activebackground=BTN_HOVER_COLOR,activeforeground=TEXT_COLOR)
        self.zoom_out_btn=tk.Button(self.top_frame,text="🔍-",command=self.zoom_out,bg=BTN_BG_COLOR,fg=TEXT_COLOR,font=FONT_ICON,relief='flat',activebackground=BTN_HOVER_COLOR,activeforeground=TEXT_COLOR)
        
    def bind_events(self):
        self.bind_all("<Control-o>",self.open_folder)
        self.bind_all("<Control-s>",self.save_changes)
        self.bind_all("<Control-S>",self.save_as)
        
        self.bind('<Left>',self.show_previous_image);self.bind('<Right>',self.show_next_image);self.bind('<Escape>',self.cancel_actions);self.bind('+',self.zoom_in);self.bind('-',self.zoom_out);self.bind('<f>',self.fit_image_to_window);self.bind('<r>',lambda e:self.set_zoom(1.0))
        self.canvas.bind("<ButtonPress-1>", self.on_crop_start);self.canvas.bind("<B1-Motion>", self.on_crop_drag);self.canvas.bind("<ButtonRelease-1>", self.on_crop_end)
        self.canvas.bind("<ButtonPress-2>", self.on_pan_start);self.canvas.bind("<B2-Motion>", self.on_pan_move);self.canvas.bind("<ButtonRelease-2>", self.on_pan_end)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel);self.bind("<MouseWheel>", self.on_mouse_wheel)
        
    def open_folder(self,event=None):
        path=filedialog.askdirectory(); 
        if not path: return
        self.load_from_file_path(path, is_folder=True)
        
    def load_from_file_path(self, path, is_folder=False):
        target_file = None
        if is_folder: self.folder_path = path
        else: self.folder_path = os.path.dirname(path); target_file = path
        image_extensions = ('.jpg','.jpeg','.png','.gif','.bmp','.tiff','.tif','.webp','.ppm','.pgm','.pbm','.pnm')
        try: self.image_list = sorted([os.path.join(self.folder_path, f) for f in os.listdir(self.folder_path) if f.lower().endswith(image_extensions)])
        except FileNotFoundError: messagebox.showerror("Erro", f"A pasta não foi encontrada:\n{self.folder_path}"); return

        if self.image_list:
            self.open_folder_btn.place_forget()
            self.prev_btn.place(relx=0.0,rely=0.5,anchor='w',x=10);self.next_btn.place(relx=1.0,rely=0.5,anchor='e',x=-10)
            self.zoom_out_btn.pack(side='right',padx=5);self.zoom_in_btn.pack(side='right')
            self.menu_bar.entryconfig("Editar",state="normal")
            if target_file and target_file in self.image_list: self.current_index = self.image_list.index(target_file)
            else: self.current_index = 0
            self.load_image()
        else:
            messagebox.showinfo("Nenhuma Imagem",f"Nenhum arquivo de imagem encontrado em:\n{self.folder_path}");self.menu_bar.entryconfig("Editar",state="disabled")

    def load_image(self):
        if not self.image_list: return
        image_path = self.image_list[self.current_index]
        try:
            self.original_pil_image = Image.open(image_path)
            if self.original_pil_image.mode not in ('RGB','RGBA'): self.original_pil_image = self.original_pil_image.convert('RGB')
            self.revert_changes()
        except Exception as e:
            messagebox.showerror("Erro",f"Não foi possível carregar a imagem:\n{image_path}\n\nErro: {e}")
            self.image_list.pop(self.current_index)
            if not self.image_list: self.canvas.delete("all"); self.create_initial_button()
            elif self.current_index >= len(self.image_list): self.current_index = 0
            self.load_image()

    def display_tk_image(self, pil_image, specific_position=None):
        """Exibe a imagem no canvas. Pode receber uma posição específica ou centralizar."""
        self.canvas.delete("all")
        
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        img_w, img_h = pil_image.size
        
        if specific_position:
            # Se uma posição foi passada (pelo zoom no cursor), usa ela
            x, y = specific_position
        else:
            # Se não (reset ou load inicial), centraliza
            x = (canvas_w - img_w) / 2
            y = (canvas_h - img_h) / 2
            
        self.canvas_image_coords = (x, y)
        
        tk_image = ImageTk.PhotoImage(pil_image)
        self.image_on_canvas_id = self.canvas.create_image(x, y, image=tk_image, anchor='nw')
        self.tk_image_ref = tk_image
        self.update_status()
        
    def fit_image_to_window(self, event=None):
        if not self.edited_pil_image:return
        img_w,img_h=self.edited_pil_image.size;win_w,win_h=self.canvas.winfo_width(),self.canvas.winfo_height()
        if win_w<50 or win_h<50:self.after(50,self.fit_image_to_window);return
        ratio=min(win_w/img_w,win_h/img_h);new_w,new_h=int(img_w*ratio),int(img_h*ratio)
        resized_image=self.edited_pil_image.resize((new_w,new_h),Image.Resampling.LANCZOS)
        self.zoom_level=ratio
        self.display_tk_image(resized_image) # Chama sem posição para centralizar
        
    def show_next_image(self,event=None):
        if self.image_list:self.current_index=(self.current_index+1)%len(self.image_list);self.load_image()
    def show_previous_image(self,event=None):
        if self.image_list:self.current_index=(self.current_index-1+len(self.image_list))%len(self.image_list);self.load_image()
    
    # --- Funções de Edição ---
    def apply_edit(self,edit_function,**kwargs):
        if not self.edited_pil_image:return
        self.edited_pil_image=edit_function(self.edited_pil_image,**kwargs);self.fit_image_to_window()
    def rotate_image(self,image,angle):return image.rotate(angle,expand=True)
    def flip_image(self,image,method):return image.transpose(method)
    def convert_grayscale(self,image):return image.convert("L")
    def revert_changes(self,event=None):
        if self.original_pil_image:self.edited_pil_image=self.original_pil_image.copy();self.fit_image_to_window()
    
    def resize_image(self):
        if not self.edited_pil_image:return
        dims=simpledialog.askstring("Redimensionar","Digite as novas dimensões (LarguraxAltura):",initialvalue=f"{self.edited_pil_image.width}x{self.edited_pil_image.height}")
        if dims:
            try:w,h=map(int,dims.lower().split('x'));self.apply_edit(lambda img:img.resize((w,h),Image.Resampling.LANCZOS))
            except(ValueError,IndexError):messagebox.showerror("Formato Inválido","Use o formato 'LarguraxAltura', por exemplo '800x600'.")
            
    def open_adjustments_window(self):
        if not self.edited_pil_image:return
        adj_win=tk.Toplevel(self);adj_win.title("Ajustes");adj_win.geometry("300x250");adj_win.configure(bg=BG_COLOR);adj_win.resizable(False,False);adj_win.transient(self)
        tk.Label(adj_win,text="Brilho",fg=TEXT_COLOR,bg=BG_COLOR).pack(pady=(10,0));brightness_slider=tk.Scale(adj_win,from_=0.5,to=1.5,resolution=0.05,orient='horizontal');brightness_slider.set(1.0);brightness_slider.pack(fill='x',padx=10)
        tk.Label(adj_win,text="Contraste",fg=TEXT_COLOR,bg=BG_COLOR).pack(pady=(10,0));contrast_slider=tk.Scale(adj_win,from_=0.5,to=1.5,resolution=0.05,orient='horizontal');contrast_slider.set(1.0);contrast_slider.pack(fill='x',padx=10)
        tk.Label(adj_win,text="Nitidez",fg=TEXT_COLOR,bg=BG_COLOR).pack(pady=(10,0));sharpness_slider=tk.Scale(adj_win,from_=0.0,to=2.0,resolution=0.1,orient='horizontal');sharpness_slider.set(1.0);sharpness_slider.pack(fill='x',padx=10)
        def apply_all_adjustments():
            base_image=self.edited_pil_image.copy()
            enhancer=ImageEnhance.Brightness(base_image);base_image=enhancer.enhance(brightness_slider.get())
            enhancer=ImageEnhance.Contrast(base_image);base_image=enhancer.enhance(contrast_slider.get())
            enhancer=ImageEnhance.Sharpness(base_image);base_image=enhancer.enhance(sharpness_slider.get())
            self.edited_pil_image=base_image;self.fit_image_to_window();adj_win.destroy()
        tk.Button(adj_win,text="Aplicar",command=apply_all_adjustments).pack(pady=10)
    
    # --- Padronização ---
    def batch_process_images(self):
        if not self.folder_path: messagebox.showwarning("Aviso", "Abra uma pasta primeiro."); return
        dims = simpledialog.askstring("Padronizar (Lote)", "Tamanho Alvo (LxA):\n(Adicionará bordas brancas)", initialvalue="900x900")
        if not dims: return
        try: target_w, target_h = map(int, dims.lower().split('x'))
        except: messagebox.showerror("Erro", "Formato inválido. Use ex: 900x900"); return
        output_dir = os.path.join(self.folder_path, "Padronizadas")
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        count = 0; image_extensions = ('.jpg','.jpeg','.png','.gif','.bmp','.tiff','.tif','.webp')
        files = [f for f in os.listdir(self.folder_path) if f.lower().endswith(image_extensions)]
        for f in files:
            try:
                img_path = os.path.join(self.folder_path, f)
                with Image.open(img_path) as img:
                    if img.mode != 'RGB': img = img.convert('RGB')
                    ratio = min(target_w/img.width, target_h/img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
                    final_img = Image.new("RGB", (target_w, target_h), (255, 255, 255))
                    paste_x = (target_w - new_size[0]) // 2; paste_y = (target_h - new_size[1]) // 2
                    final_img.paste(resized_img, (paste_x, paste_y))
                    save_path = os.path.join(output_dir, f); final_img.save(save_path); count += 1
            except Exception as e: print(f"Erro ao processar {f}: {e}")
        messagebox.showinfo("Concluído", f"Processamento finalizado!\n{count} imagens salvas em:\n{output_dir}")

    def standardize_current_image(self):
        if not self.edited_pil_image: return
        dims = simpledialog.askstring("Padronizar Imagem Atual", "Tamanho Alvo (LxA):\n(Adicionará bordas brancas)", initialvalue="900x900")
        if not dims: return
        try: target_w, target_h = map(int, dims.lower().split('x'))
        except: messagebox.showerror("Erro", "Formato inválido. Use ex: 900x900"); return
        try:
            img = self.edited_pil_image
            ratio = min(target_w/img.width, target_h/img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
            final_img = Image.new("RGB", (target_w, target_h), (255, 255, 255))
            paste_x = (target_w - new_size[0]) // 2; paste_y = (target_h - new_size[1]) // 2
            final_img.paste(resized_img, (paste_x, paste_y))
            self.edited_pil_image = final_img; self.fit_image_to_window()
        except Exception as e: messagebox.showerror("Erro", f"Erro ao padronizar imagem: {e}")

    # --- Funções de Corte ---
    def start_crop_mode(self):
        if not self.edited_pil_image:return
        self.cropping=True;self.config(cursor="crosshair")
    def end_crop_mode(self):
        self.cropping=False;self.config(cursor="arrow")
        if self.crop_rect_id:self.canvas.delete(self.crop_rect_id);self.crop_rect_id=None
    def cancel_actions(self,event=None):
        if self.cropping:self.end_crop_mode()
        else:self.quit()
    def on_crop_start(self,event):
        if self.cropping: 
            self.crop_start_x=self.canvas.canvasx(event.x);self.crop_start_y=self.canvas.canvasy(event.y);
            if self.crop_rect_id:self.canvas.delete(self.crop_rect_id)
            self.crop_rect_id=self.canvas.create_rectangle(self.crop_start_x,self.crop_start_y,self.crop_start_x,self.crop_start_y,outline='white',dash=(4,2))
    def on_crop_drag(self,event):
        if self.cropping and self.crop_rect_id:
            cur_x,cur_y=self.canvas.canvasx(event.x),self.canvas.canvasy(event.y)
            self.canvas.coords(self.crop_rect_id,self.crop_start_x,self.crop_start_y,cur_x,cur_y)
    def on_crop_end(self,event):
        if not self.cropping or not self.crop_rect_id:return
        end_x,end_y=self.canvas.canvasx(event.x),self.canvas.canvasy(event.y)
        x1,y1=min(self.crop_start_x,end_x),min(self.crop_start_y,end_y);x2,y2=max(self.crop_start_x,end_x),max(self.crop_start_y,end_y)
        img_offset_x, img_offset_y = self.canvas_image_coords
        if not self.tk_image_ref or self.tk_image_ref.width() == 0: return
        displayed_w = self.tk_image_ref.width(); actual_w = self.edited_pil_image.width
        ratio = actual_w / displayed_w
        box_x1 = (x1 - img_offset_x) * ratio; box_y1 = (y1 - img_offset_y) * ratio
        box_x2 = (x2 - img_offset_x) * ratio; box_y2 = (y2 - img_offset_y) * ratio
        box_x1 = max(0, box_x1); box_y1 = max(0, box_y1)
        box_x2 = min(actual_w, box_x2); box_y2 = min(self.edited_pil_image.height, box_y2)
        if box_x2 > box_x1 and box_y2 > box_y1:
            self.apply_edit(lambda img,box:img.crop(box),box=(box_x1,box_y1,box_x2,box_y2))
        self.end_crop_mode()

    # --- Funções de Arrastar (Pan) ---
    def on_pan_start(self, event):
        if not self.image_on_canvas_id: return
        self.canvas.config(cursor="fleur")
        self.pan_start_x = event.x; self.pan_start_y = event.y
        self.canvas_drag_start_x, self.canvas_drag_start_y = self.canvas.coords(self.image_on_canvas_id)

    def on_pan_move(self, event):
        if not self.image_on_canvas_id: return
        dx = event.x - self.pan_start_x; dy = event.y - self.pan_start_y
        self.canvas.coords(self.image_on_canvas_id, self.canvas_drag_start_x + dx, self.canvas_drag_start_y + dy)

    def on_pan_end(self, event):
        if not self.cropping: self.canvas.config(cursor="arrow")
        # Atualiza as coordenadas globais para que o crop/zoom funcionem na nova posição
        if self.image_on_canvas_id:
            self.canvas_image_coords = self.canvas.coords(self.image_on_canvas_id)
        
    # --- FUNÇÕES DE ZOOM (Com Zoom no Cursor) ---
    def set_zoom(self, zoom_level):
        self.zoom_level = zoom_level
        self.apply_zoom()
    
    def apply_zoom(self, specific_position=None):
        """Aplica o zoom. Se specific_position for passado, usa para calcular o offset."""
        if not self.original_pil_image: return
        
        new_w = int(self.original_pil_image.width * self.zoom_level)
        new_h = int(self.original_pil_image.height * self.zoom_level)
        
        if new_w < 1 or new_h < 1: return
        
        resized_image = self.edited_pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.display_tk_image(resized_image, specific_position)

    def on_mouse_wheel(self, event):
        """Zoom focado na posição do mouse."""
        if not self.original_pil_image: return
        
        # 1. Pega a posição do mouse no Canvas
        mouse_x = self.canvas.canvasx(event.x)
        mouse_y = self.canvas.canvasy(event.y)
        
        # 2. Determina o fator de escala
        scale_factor = 1.1 if event.delta > 0 else 0.9
        new_zoom_level = self.zoom_level * scale_factor
        
        # Limites de zoom
        if new_zoom_level > 10.0: new_zoom_level = 10.0
        if new_zoom_level < 0.1: new_zoom_level = 0.1
        
        # Se o zoom não mudou (atingiu limite), sai
        if new_zoom_level == self.zoom_level: return

        # 3. Pega a posição atual da imagem no canvas
        img_x, img_y = self.canvas_image_coords
        
        # 4. Calcula a nova posição (Matemática do Zoom no Ponto)
        # A ideia é: (mouse - img_pos) / zoom_antigo = (mouse - nova_img_pos) / novo_zoom
        # Isso mantém o ponto da imagem sob o mouse estático
        new_img_x = mouse_x - (mouse_x - img_x) * (new_zoom_level / self.zoom_level)
        new_img_y = mouse_y - (mouse_y - img_y) * (new_zoom_level / self.zoom_level)
        
        self.zoom_level = new_zoom_level
        self.apply_zoom(specific_position=(new_img_x, new_img_y))

    def zoom_in(self, event=None):
        """Zoom centralizado (botão da interface)."""
        self.zoom_level = min(10.0, self.zoom_level + 0.1)
        self.apply_zoom() # Sem posição específica = centralizado

    def zoom_out(self, event=None):
        """Zoom centralizado (botão da interface)."""
        self.zoom_level = max(0.1, self.zoom_level - 0.1)
        self.apply_zoom()
    
    def save_as(self, event=None):
        if not self.edited_pil_image: return
        image_to_save = self.edited_pil_image
        if image_to_save.mode in ('RGBA', 'P'): image_to_save = image_to_save.convert('RGB')
        file_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png"), ("Bitmap", "*.bmp")])
        if file_path:
            try:
                image_to_save.save(file_path)
                messagebox.showinfo("Sucesso", f"Imagem salva em:\n{file_path}")
            except Exception as e: messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def save_changes(self, event=None):
        if not self.edited_pil_image or not self.image_list: return
        current_file_path = self.image_list[self.current_index]
        if not messagebox.askyesno("Sobrescrever", f"Tem certeza que deseja salvar as alterações em:\n{os.path.basename(current_file_path)}?\n\nEssa ação não pode ser desfeita."): return
        try:
            image_to_save = self.edited_pil_image
            if image_to_save.mode in ('RGBA', 'P') and current_file_path.lower().endswith(('.jpg', '.jpeg', '.bmp')):
                image_to_save = image_to_save.convert('RGB')
            image_to_save.save(current_file_path)
            self.original_pil_image = self.edited_pil_image.copy()
            messagebox.showinfo("Salvo", "Imagem atualizada com sucesso!")
        except Exception as e: messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{e}")

if __name__ == "__main__":
    if len(sys.argv) > 1: file_path_arg = sys.argv[1]
    else: file_path_arg = None
    app = ImageViewer(file_path=file_path_arg)
    app.mainloop()