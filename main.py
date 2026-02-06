# Venus External - Main UI
# Roblox External Cheat with Modern UI

import customtkinter as ctk
import threading
import time
from assets import Colors, Fonts
from memory import memory
from entity_manager import entity_manager
from overlay import Overlay

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Global Feature State
features = {
    # Visuals
    "esp_enabled": False,
    "esp_box": True,
    "esp_name": True,
    "esp_health": True,
    "esp_distance": True,
    "esp_snaplines": False,
    
    # Movement (Read-only display from memory)
    "show_speed": False,
    "show_position": False,
    
    # Misc
    "crosshair_enabled": False,
    "fov_circle": False,
    "fov_circle_radius": 100,
}

class TitleBar(ctk.CTkFrame):
    """Custom draggable title bar"""
    def __init__(self, master, app):
        super().__init__(master, height=32, fg_color=Colors.SIDEBAR, corner_radius=0)
        self.app = app
        self.pack(fill="x", side="top")
        
        # Icon & Title
        self.title = ctk.CTkLabel(
            self, text="  ⬡ Venus External", 
            font=("Segoe UI", 11, "bold"),
            text_color=Colors.PRIMARY
        )
        self.title.pack(side="left", padx=10)
        
        # Version
        self.version = ctk.CTkLabel(
            self, text="v1.0.0",
            font=("Segoe UI", 9),
            text_color=Colors.TEXT_MUTED
        )
        self.version.pack(side="left")
        
        # Window controls
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="right")
        
        self.minimize_btn = ctk.CTkButton(
            btn_frame, text="─", width=40, height=32,
            fg_color="transparent", hover_color=Colors.SURFACE,
            text_color=Colors.TEXT_SECONDARY, corner_radius=0,
            command=self.minimize
        )
        self.minimize_btn.pack(side="left")
        
        self.close_btn = ctk.CTkButton(
            btn_frame, text="✕", width=40, height=32,
            fg_color="transparent", hover_color=Colors.ERROR,
            text_color=Colors.TEXT_SECONDARY, corner_radius=0,
            command=self.app.on_close
        )
        self.close_btn.pack(side="left")
        
        # Drag bindings
        for widget in [self, self.title, self.version]:
            widget.bind("<Button-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.do_drag)
    
    def start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y
    
    def do_drag(self, event):
        x = self.app.winfo_x() + (event.x - self._drag_x)
        y = self.app.winfo_y() + (event.y - self._drag_y)
        self.app.geometry(f"+{x}+{y}")
    
    def minimize(self):
        self.app.iconify()


class FeatureToggle(ctk.CTkFrame):
    """Toggle switch for a feature"""
    def __init__(self, master, label, feature_key, features_dict):
        super().__init__(master, fg_color="transparent", height=36)
        self.features = features_dict
        self.feature_key = feature_key
        
        self.pack_propagate(False)
        
        self.label = ctk.CTkLabel(
            self, text=label,
            font=Fonts.BODY,
            text_color=Colors.TEXT_SECONDARY
        )
        self.label.pack(side="left", padx=(0, 10))
        
        self.toggle = ctk.CTkSwitch(
            self, text="", width=40,
            progress_color=Colors.PRIMARY,
            button_color=Colors.TEXT_MUTED,
            button_hover_color=Colors.PRIMARY_HOVER,
            command=self.on_toggle
        )
        if self.features.get(feature_key, False):
            self.toggle.select()
        self.toggle.pack(side="right")
    
    def on_toggle(self):
        self.features[self.feature_key] = bool(self.toggle.get())


class FeatureSlider(ctk.CTkFrame):
    """Slider for a numeric feature"""
    def __init__(self, master, label, feature_key, features_dict, min_val=0, max_val=100, suffix=""):
        super().__init__(master, fg_color="transparent")
        self.features = features_dict
        self.feature_key = feature_key
        self.suffix = suffix
        
        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x")
        
        self.label = ctk.CTkLabel(
            header, text=label,
            font=Fonts.BODY,
            text_color=Colors.TEXT_SECONDARY
        )
        self.label.pack(side="left")
        
        self.value_label = ctk.CTkLabel(
            header, text=f"{self.features.get(feature_key, 0):.0f}{suffix}",
            font=Fonts.BODY,
            text_color=Colors.PRIMARY
        )
        self.value_label.pack(side="right")
        
        # Slider
        self.slider = ctk.CTkSlider(
            self, from_=min_val, to=max_val,
            progress_color=Colors.PRIMARY,
            button_color=Colors.SECONDARY,
            button_hover_color=Colors.PRIMARY_HOVER,
            command=self.on_slide
        )
        self.slider.set(self.features.get(feature_key, 0))
        self.slider.pack(fill="x", pady=(5, 0))
    
    def on_slide(self, value):
        self.features[self.feature_key] = value
        self.value_label.configure(text=f"{value:.0f}{self.suffix}")


class FeatureCard(ctk.CTkFrame):
    """Card container for a group of features"""
    def __init__(self, master, title, icon=""):
        super().__init__(
            master, 
            fg_color=Colors.SURFACE,
            corner_radius=12,
            border_width=1,
            border_color=Colors.BORDER
        )
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 12))
        
        title_text = f"{icon}  {title}" if icon else title
        self.title = ctk.CTkLabel(
            header, text=title_text,
            font=Fonts.SUBHEADER,
            text_color=Colors.TEXT_PRIMARY
        )
        self.title.pack(side="left")
        
        # Content frame
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="x", padx=16, pady=(0, 16))


class Sidebar(ctk.CTkFrame):
    """Navigation sidebar"""
    def __init__(self, master, on_select):
        super().__init__(master, width=180, corner_radius=0, fg_color=Colors.SIDEBAR)
        self.on_select = on_select
        self.buttons = {}
        self.pack_propagate(False)
        
        # Logo
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(30, 40))
        
        self.logo = ctk.CTkLabel(
            logo_frame, text="VENUS",
            font=("Segoe UI", 28, "bold"),
            text_color=Colors.PRIMARY
        )
        self.logo.pack()
        
        self.subtitle = ctk.CTkLabel(
            logo_frame, text="EXTERNAL",
            font=("Segoe UI", 10),
            text_color=Colors.TEXT_MUTED
        )
        self.subtitle.pack()
        
        # Navigation buttons
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=12)
        
        categories = [
            ("◎", "Visuals"),
            ("⬡", "Player"),
            ("⚙", "Settings"),
        ]
        
        for icon, name in categories:
            btn = ctk.CTkButton(
                nav_frame,
                text=f" {icon}  {name}",
                height=40,
                corner_radius=8,
                fg_color="transparent",
                text_color=Colors.TEXT_MUTED,
                hover_color=Colors.SURFACE,
                font=Fonts.BODY,
                anchor="w",
                command=lambda n=name: self.select(n)
            )
            btn.pack(fill="x", pady=2)
            self.buttons[name] = btn
        
        # Status footer
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=12, pady=20)
        
        self.status_indicator = ctk.CTkLabel(
            footer, text="●",
            font=("Segoe UI", 10),
            text_color=Colors.ERROR
        )
        self.status_indicator.pack(side="left")
        
        self.status_label = ctk.CTkLabel(
            footer, text=" Not Attached",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED
        )
        self.status_label.pack(side="left")
    
    def select(self, name):
        for btn_name, btn in self.buttons.items():
            if btn_name == name:
                btn.configure(fg_color=Colors.SURFACE, text_color=Colors.PRIMARY)
            else:
                btn.configure(fg_color="transparent", text_color=Colors.TEXT_MUTED)
        self.on_select(name)
    
    def update_status(self, attached, text=""):
        if attached:
            self.status_indicator.configure(text_color=Colors.SUCCESS)
            self.status_label.configure(text=" " + text if text else " Attached")
        else:
            self.status_indicator.configure(text_color=Colors.ERROR)
            self.status_label.configure(text=" " + text if text else " Not Attached")


class VenusApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Venus External")
        self.geometry("850x550")
        self.configure(fg_color=Colors.BACKGROUND)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 850) // 2
        y = (self.winfo_screenheight() - 550) // 2
        self.geometry(f"+{x}+{y}")
        
        # Custom frameless window that still shows in taskbar
        self.overrideredirect(True)
        self.after(10, self._set_taskbar_icon)
        
        # Title bar
        self.titlebar = TitleBar(self, self)
        
        # Main container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        
        # Sidebar
        self.sidebar = Sidebar(self.container, self.switch_tab)
        self.sidebar.pack(side="left", fill="y")
        
        # Content area
        self.content = ctk.CTkFrame(self.container, fg_color="transparent")
        self.content.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        # Create views
        self.views = {}
        self.create_visuals_view()
        self.create_player_view()
        self.create_settings_view()
        
        # Default tab
        self.sidebar.select("Visuals")
        
        # Initialize overlay
        self.overlay = Overlay(features, entity_manager)
        
        # Start update loop
        self.running = True
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
        
        # Try to attach
        self.try_attach()
    
    def _set_taskbar_icon(self):
        """Make frameless window appear in taskbar using Windows API"""
        import ctypes
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080
        
        hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        
        # Get current style and add APPWINDOW, remove TOOLWINDOW
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = style & ~WS_EX_TOOLWINDOW
        style = style | WS_EX_APPWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        
        # Force window to refresh in taskbar
        self.withdraw()
        self.after(10, self.deiconify)
    
    
    def create_visuals_view(self):
        view = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        
        ctk.CTkLabel(
            view, text="Visuals",
            font=Fonts.HEADER,
            text_color=Colors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 20))
        
        # ESP Card
        esp = FeatureCard(view, "ESP", "◎")
        esp.pack(fill="x", pady=(0, 12))
        
        FeatureToggle(esp.content, "Enable ESP", "esp_enabled", features).pack(fill="x", pady=4)
        FeatureToggle(esp.content, "Box ESP", "esp_box", features).pack(fill="x", pady=4)
        FeatureToggle(esp.content, "Name ESP", "esp_name", features).pack(fill="x", pady=4)
        FeatureToggle(esp.content, "Health Bar", "esp_health", features).pack(fill="x", pady=4)
        FeatureToggle(esp.content, "Snaplines", "esp_snaplines", features).pack(fill="x", pady=4)
        
        # Crosshair Card
        crosshair = FeatureCard(view, "Crosshair", "✛")
        crosshair.pack(fill="x", pady=(0, 12))
        
        FeatureToggle(crosshair.content, "Enable Crosshair", "crosshair_enabled", features).pack(fill="x", pady=4)
        FeatureToggle(crosshair.content, "FOV Circle", "fov_circle", features).pack(fill="x", pady=4)
        FeatureSlider(crosshair.content, "FOV Radius", "fov_circle_radius", features, 50, 500, "px").pack(fill="x", pady=4)
        
        self.views["Visuals"] = view
    
    def create_player_view(self):
        view = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        
        ctk.CTkLabel(
            view, text="Player Info",
            font=Fonts.HEADER,
            text_color=Colors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 20))
        
        # Local Player Info Card
        info = FeatureCard(view, "Local Player", "⬡")
        info.pack(fill="x", pady=(0, 12))
        
        self.player_info_labels = {}
        info_items = ["Name", "UserID", "Health", "Position", "Speed"]
        
        for item in info_items:
            row = ctk.CTkFrame(info.content, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(
                row, text=f"{item}:",
                font=Fonts.BODY,
                text_color=Colors.TEXT_MUTED,
                width=80,
                anchor="w"
            ).pack(side="left")
            
            label = ctk.CTkLabel(
                row, text="--",
                font=Fonts.BODY,
                text_color=Colors.TEXT_PRIMARY
            )
            label.pack(side="left")
            self.player_info_labels[item] = label
        
        # Game Info Card
        game = FeatureCard(view, "Game Info", "🎮")
        game.pack(fill="x", pady=(0, 12))
        
        self.game_info_labels = {}
        game_items = ["PlaceID", "Players"]
        
        for item in game_items:
            row = ctk.CTkFrame(game.content, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(
                row, text=f"{item}:",
                font=Fonts.BODY,
                text_color=Colors.TEXT_MUTED,
                width=80,
                anchor="w"
            ).pack(side="left")
            
            label = ctk.CTkLabel(
                row, text="--",
                font=Fonts.BODY,
                text_color=Colors.TEXT_PRIMARY
            )
            label.pack(side="left")
            self.game_info_labels[item] = label
        
        self.views["Player"] = view
    
    def create_settings_view(self):
        view = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        
        ctk.CTkLabel(
            view, text="Settings",
            font=Fonts.HEADER,
            text_color=Colors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 20))
        
        # Connection Card
        conn = FeatureCard(view, "Connection", "🔗")
        conn.pack(fill="x", pady=(0, 12))
        
        btn_frame = ctk.CTkFrame(conn.content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=4)
        
        self.attach_btn = ctk.CTkButton(
            btn_frame, text="Attach to Roblox",
            height=36, corner_radius=8,
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
            text_color="#000000",
            font=Fonts.BODY,
            command=self.try_attach
        )
        self.attach_btn.pack(fill="x")
        
        # Overlay Card
        overlay_card = FeatureCard(view, "Overlay", "🖼")
        overlay_card.pack(fill="x", pady=(0, 12))
        
        overlay_btn_frame = ctk.CTkFrame(overlay_card.content, fg_color="transparent")
        overlay_btn_frame.pack(fill="x", pady=4)
        
        self.overlay_btn = ctk.CTkButton(
            overlay_btn_frame, text="Start Overlay",
            height=36, corner_radius=8,
            fg_color=Colors.SECONDARY,
            hover_color=Colors.PRIMARY_HOVER,
            text_color="#FFFFFF",
            font=Fonts.BODY,
            command=self.toggle_overlay
        )
        self.overlay_btn.pack(fill="x")
        
        # About Card
        about = FeatureCard(view, "About", "ℹ")
        about.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(
            about.content,
            text="Venus External v1.0.0\nRoblox External Cheat\n\nFeatures:\n• ESP (Box, Name, Health)\n• Visuals Only Build\n• Player Info Display",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
            justify="left"
        ).pack(anchor="w")
        
        self.views["Settings"] = view
    
    def switch_tab(self, name):
        for view in self.views.values():
            view.pack_forget()
        if name in self.views:
            self.views[name].pack(fill="both", expand=True)
    
    def try_attach(self):
        """Try to attach to Roblox process"""
        def attach_task():
            success = memory.attach()
            self.after(0, lambda: self.on_attach_result(success))
        
        self.sidebar.update_status(False, "Attaching...")
        threading.Thread(target=attach_task, daemon=True).start()
    
    def on_attach_result(self, success):
        if success:
            self.sidebar.update_status(True, f"PID: {memory.process_id}")
            self.attach_btn.configure(text="Attached ✓", fg_color=Colors.SUCCESS)
        else:
            self.sidebar.update_status(False, "Failed")
            self.attach_btn.configure(text="Attach to Roblox", fg_color=Colors.PRIMARY)
    
    def toggle_overlay(self):
        """Toggle ESP overlay"""
        if self.overlay.running:
            self.overlay.stop()
            self.overlay_btn.configure(text="Start Overlay", fg_color=Colors.SECONDARY)
        else:
            self.overlay.start()
            self.overlay_btn.configure(text="Stop Overlay", fg_color=Colors.ERROR)
    
    def update_loop(self):
        """Background thread for updating entity data"""
        while self.running:
            if memory.attached:
                try:
                    entity_manager.update_players()
                    
                    # Update UI (must be done on main thread)
                    self.after(0, self.update_player_info)
                except:
                    pass
            
            time.sleep(0.005)  # Minimize latency, rely on overlay vsync
    
    def update_player_info(self):
        """Update player info display"""
        if not memory.attached:
            return
        
        local = entity_manager.local_player
        if local:
            self.player_info_labels["Name"].configure(text=local.name or "--")
            self.player_info_labels["UserID"].configure(text=str(local.user_id) if local.user_id else "--")
            self.player_info_labels["Health"].configure(text=f"{local.health:.0f}/{local.max_health:.0f}")
            
            pos = local.position
            self.player_info_labels["Position"].configure(
                text=f"({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})"
            )
        
        # Game info
        self.game_info_labels["Players"].configure(text=str(len(entity_manager.players)))
    
    def on_close(self):
        """Clean shutdown"""
        self.running = False
        self.overlay.stop()
        memory.detach()
        self.destroy()


if __name__ == "__main__":
    app = VenusApp()
    app.mainloop()
