# Venus External - ESP Overlay
# Transparent overlay window for rendering ESP using pygame

import pygame
import win32api
import win32con
import win32gui
import ctypes
import threading
import time

class Overlay:
    def __init__(self, features, entity_manager):
        self.features = features
        self.entity_manager = entity_manager
        self.running = False
        self.thread = None
        self.width = win32api.GetSystemMetrics(0)
        self.height = win32api.GetSystemMetrics(1)
        
        # Colors (RGB)
        self.color_enemy = (255, 71, 87)
        self.color_team = (46, 213, 115)
        self.color_health_high = (46, 213, 115)
        self.color_health_med = (255, 165, 2)
        self.color_health_low = (255, 71, 87)
        self.color_name = (255, 255, 255)
        self.color_transparent = (0, 0, 0)  # This will be made transparent
        
    def start(self):
        """Start the overlay in a separate thread"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop the overlay"""
        self.running = False
    
    def _run(self):
        """Main overlay loop"""
        # Initialize pygame
        pygame.init()
        pygame.font.init()
        
        # Get screen size
        self.width = win32api.GetSystemMetrics(0)
        self.height = win32api.GetSystemMetrics(1)
        
        # Update entity manager screen size
        self.entity_manager.screen_width = self.width
        self.entity_manager.screen_height = self.height
        
        # Create borderless window
        screen = pygame.display.set_mode((self.width, self.height), pygame.NOFRAME)
        pygame.display.set_caption("Venus ESP")
        
        # Get pygame window handle
        hwnd = pygame.display.get_wm_info()["window"]
        
        # Make window transparent and click-through
        # Extended window styles
        win32gui.SetWindowLong(
            hwnd, 
            win32con.GWL_EXSTYLE,
            win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) 
            | win32con.WS_EX_LAYERED 
            | win32con.WS_EX_TRANSPARENT
            | win32con.WS_EX_TOPMOST
        )
        
        # Set black as transparent color
        win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0, 0, 0), 0, win32con.LWA_COLORKEY)
        
        # Move to top-left and set always on top
        win32gui.SetWindowPos(
            hwnd, 
            win32con.HWND_TOPMOST, 
            0, 0, self.width, self.height,
            win32con.SWP_SHOWWINDOW
        )
        
        # Font for text
        try:
            font = pygame.font.SysFont("Segoe UI", 13)
            font_small = pygame.font.SysFont("Segoe UI", 11)
        except:
            font = pygame.font.Font(None, 16)
            font_small = pygame.font.Font(None, 14)
        
        clock = pygame.time.Clock()
        
        while self.running:
            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
            
            # Clear screen with transparent color
            screen.fill(self.color_transparent)
            
            # Draw ESP if enabled
            if self.features.get("esp_enabled", False):
                self._draw_esp(screen, font, font_small)
            
            # Draw crosshair if enabled
            if self.features.get("crosshair_enabled", False):
                self._draw_crosshair(screen)
            
            # Draw FOV circle if enabled
            if self.features.get("fov_circle", False):
                radius = int(self.features.get("fov_circle_radius", 100))
                pygame.draw.circle(
                    screen, 
                    (255, 255, 255), 
                    (self.width // 2, self.height // 2), 
                    radius, 
                    1
                )
            
            pygame.display.flip()
            clock.tick(60)  # 60 FPS
        
        pygame.quit()
    
    def _draw_esp(self, screen, font, font_small):
        """Draw ESP for all players"""
        for player in self.entity_manager.players:
            if player.is_local:
                continue
            
            if player.screen_pos is None:
                continue
            
            # Skip dead players
            if player.health <= 0:
                continue
            
            x = int(player.screen_pos[0])
            y = int(player.screen_pos[1])
            
            # Calculate box dimensions based on screen coordinates
            box_height = 0
            if player.screen_head_pos:
                # Delta between Root and Head (approx 1.5 - 2 studs)
                # Character is roughly 5-6 studs tall. 
                # Multiplier ~3.0 - 4.0 should cover full body
                head_y = player.screen_head_pos[1]
                pixel_delta = abs(y - head_y)
                box_height = max(20, int(pixel_delta * 3.8))
            else:
                # Fallback if head pos missing
                box_height = max(30, min(400, int(2000 / max(player.distance, 5))))
                
            box_width = int(box_height * 0.5)
            
            # Box position (centered on player)
            box_x = x - box_width // 2
            box_y = y - box_height // 2
            
            # Main color (enemy = red)
            color = self.color_enemy
            
            # Draw box ESP
            if self.features.get("esp_box", False):
                # Draw box outline
                pygame.draw.rect(
                    screen, 
                    color, 
                    (box_x, box_y, box_width, box_height), 
                    2
                )
                
                # Optional: corner style box
                corner_len = box_width // 4
                # Top-left
                pygame.draw.line(screen, color, (box_x, box_y), (box_x + corner_len, box_y), 2)
                pygame.draw.line(screen, color, (box_x, box_y), (box_x, box_y + corner_len), 2)
                # Top-right
                pygame.draw.line(screen, color, (box_x + box_width, box_y), (box_x + box_width - corner_len, box_y), 2)
                pygame.draw.line(screen, color, (box_x + box_width, box_y), (box_x + box_width, box_y + corner_len), 2)
                # Bottom-left
                pygame.draw.line(screen, color, (box_x, box_y + box_height), (box_x + corner_len, box_y + box_height), 2)
                pygame.draw.line(screen, color, (box_x, box_y + box_height), (box_x, box_y + box_height - corner_len), 2)
                # Bottom-right
                pygame.draw.line(screen, color, (box_x + box_width, box_y + box_height), (box_x + box_width - corner_len, box_y + box_height), 2)
                pygame.draw.line(screen, color, (box_x + box_width, box_y + box_height), (box_x + box_width, box_y + box_height - corner_len), 2)
            
            # Draw health bar
            if self.features.get("esp_health", False):
                health_pct = max(0, min(1, player.health / max(player.max_health, 1)))
                bar_width = 4
                bar_height = box_height
                bar_x = box_x - bar_width - 3
                bar_y = box_y
                
                # Background
                pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
                
                # Health fill
                if health_pct > 0.66:
                    health_color = self.color_health_high
                elif health_pct > 0.33:
                    health_color = self.color_health_med
                else:
                    health_color = self.color_health_low
                
                fill_height = int(bar_height * health_pct)
                pygame.draw.rect(
                    screen, 
                    health_color, 
                    (bar_x, bar_y + bar_height - fill_height, bar_width, fill_height)
                )
                
                # Border
                pygame.draw.rect(screen, (80, 80, 80), (bar_x, bar_y, bar_width, bar_height), 1)
            
            # Draw name
            if self.features.get("esp_name", False):
                name = player.name or "Player"
                # Render text with shadow
                text_shadow = font.render(name, True, (0, 0, 0))
                text = font.render(name, True, self.color_name)
                text_rect = text.get_rect(center=(x, box_y - 12))
                screen.blit(text_shadow, (text_rect.x + 1, text_rect.y + 1))
                screen.blit(text, text_rect)
                
                # Distance
                dist_text = f"[{int(player.distance)}m]"
                dist_shadow = font_small.render(dist_text, True, (0, 0, 0))
                dist = font_small.render(dist_text, True, (180, 180, 180))
                dist_rect = dist.get_rect(center=(x, box_y + box_height + 10))
                screen.blit(dist_shadow, (dist_rect.x + 1, dist_rect.y + 1))
                screen.blit(dist, dist_rect)
            
            # Draw snaplines
            if self.features.get("esp_snaplines", False):
                pygame.draw.line(
                    screen, 
                    color, 
                    (self.width // 2, self.height),  # Bottom center of screen
                    (x, box_y + box_height),  # Bottom of box
                    1
                )
    
    def _draw_crosshair(self, screen):
        """Draw custom crosshair"""
        cx = self.width // 2
        cy = self.height // 2
        size = 10
        gap = 4
        color = (0, 255, 170)
        
        # Horizontal lines
        pygame.draw.line(screen, color, (cx - size - gap, cy), (cx - gap, cy), 2)
        pygame.draw.line(screen, color, (cx + gap, cy), (cx + size + gap, cy), 2)
        
        # Vertical lines
        pygame.draw.line(screen, color, (cx, cy - size - gap), (cx, cy - gap), 2)
        pygame.draw.line(screen, color, (cx, cy + gap), (cx, cy + size + gap), 2)
        
        # Center dot
        pygame.draw.circle(screen, color, (cx, cy), 2)
