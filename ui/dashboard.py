import pygame
import os

class Dashboard:
    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Professional Dark Theme Colors
        self.color_bg = (10, 10, 15, 200)
        self.color_accent = (0, 242, 255)
        self.color_text = (224, 224, 224)
        self.color_dim = (160, 160, 160)
        
        try:
            pygame.font.init()
            # Use standard font as fallback for robustness
            self.font_small = pygame.font.SysFont("Arial", 12)
            self.font_med = pygame.font.SysFont("Arial", 16)
            self.font_large = pygame.font.SysFont("Arial", 24, bold=True)
            
            # Try to load Geneva if on Mac
            font_path = "/System/Library/Fonts/Geneva.ttf"
            if os.path.exists(font_path):
                self.font_small = pygame.font.Font(font_path, 12)
                self.font_med = pygame.font.Font(font_path, 16)
                self.font_large = pygame.font.Font(font_path, 24)
        except:
            print("Dashboard Warning: Font initialization failed.")
            self.font_small = self.font_med = self.font_large = None
            
        self.sidebar_w = 300
        self.sidebar_rect = pygame.Rect(self.width - self.sidebar_w, 0, self.sidebar_w, self.height)
        
    def draw(self, sim_state):
        self.width = self.screen.get_width()
        self.height = self.screen.get_height()
        self.sidebar_rect.x = self.width - self.sidebar_w
        self.sidebar_rect.height = self.height
        
        self.draw_sidebar(sim_state)
        self.draw_controls_hint()

    def draw_sidebar(self, state):
        # Sidebar Panel (Glassmorphism Dark)
        surf = pygame.Surface((self.sidebar_w, self.height), pygame.SRCALPHA)
        pygame.draw.rect(surf, self.color_bg, (0, 0, self.sidebar_w, self.height))
        pygame.draw.line(surf, (255, 255, 255, 30), (0, 0), (0, self.height), 2)
        self.screen.blit(surf, (self.sidebar_rect.x, 0))
        
        y = 30
        self.draw_text("SIMULATION COMMAND", self.sidebar_rect.x + 20, y, self.color_accent, self.font_large)
        y += 60
        
        # System State
        self.draw_toggle("Status", "ONLINE" if not state.paused else "PAUSED", self.sidebar_rect.x + 20, y, (0, 255, 100) if not state.paused else (255, 80, 80))
        y += 50
        self.draw_toggle("Active Protocol", state.current_protocol, self.sidebar_rect.x + 20, y, self.color_accent)
        y += 100
        
        # Metrics Section
        self.draw_text("LIVE TELEMETRY", self.sidebar_rect.x + 20, y, self.color_dim, self.font_med)
        y += 40
        
        pdr = (state.total_packets_received / state.total_packets_sent * 100) if state.total_packets_sent > 0 else 0
        metrics = [
            ("Nodes", len(state.vehicles)),
            ("Transmissions", state.total_packets_sent),
            ("Successful", state.total_packets_received),
            ("PDR", f"{pdr:.1f}%")
        ]
        
        for label, val in metrics:
            self.draw_metric_line(label, str(val), self.sidebar_rect.x + 20, y)
            y += 40

    def draw_controls_hint(self):
        # Bottom left controls hint
        margin = 20
        y = self.height - 100
        hints = [
            "[DRAG] Pan View",
            "[SCROLL] Zoom In/Out",
            "[1,2,3] Switch Protocol",
            "[SPACE] Pause/Resume"
        ]
        for hint in hints:
            self.draw_text(hint, margin, y, (150, 150, 150), self.font_small)
            y += 18

    def draw_toggle(self, label, value, x, y, color):
        self.draw_text(label, x, y, self.color_dim, self.font_small)
        # Background box for value
        pygame.draw.rect(self.screen, (255, 255, 255, 10), (x, y+20, 260, 32), border_radius=5)
        self.draw_text(value, x + 12, y + 26, color, self.font_med)

    def draw_metric_line(self, label, val, x, y):
        self.draw_text(label, x, y, self.color_dim, self.font_small)
        self.draw_text(val, x + 160, y - 5, self.color_text, self.font_med)
        # Subtle separator
        pygame.draw.line(self.screen, (255, 255, 255, 10), (x, y + 25), (x + 260, y + 25))

    def draw_text(self, text, x, y, color=(255, 255, 255), font=None):
        if font:
            img = font.render(str(text), True, color)
            self.screen.blit(img, (x, y))
