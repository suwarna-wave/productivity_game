# pg_game.py
import pygame, sys
from shared import load, save

WIDTH, HEIGHT = 640, 400
BG_COLOR = (24, 24, 36)
WHITE = (240, 240, 240)
BTN_COLOR = (60, 130, 220)
BTN_HOVER = (80, 150, 240)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Reward World")

font = pygame.font.SysFont(None, 28)
big  = pygame.font.SysFont(None, 36)
clock = pygame.time.Clock()

def draw_text(txt, x, y, fnt=font, color=WHITE):
    img = fnt.render(txt, True, color)
    screen.blit(img, (x, y))

class Button:
    def __init__(self, rect, label, cost, on_click):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.cost = cost
        self.on_click = on_click

    def draw(self, coins):
        mouse = pygame.mouse.get_pos()
        color = BTN_HOVER if self.rect.collidepoint(mouse) else BTN_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        text = f"{self.label} ({self.cost}c)"
        draw_text(text, self.rect.x+10, self.rect.y+10)

    def handle(self, event, coins):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()

def main():
    running = True
    avatar_x, avatar_y = WIDTH//2, HEIGHT//2 + 40
    btn_hat = Button((30, 300, 180, 40), "Buy Hat", 30, lambda: buy("hat", 30))
    btn_pet = Button((230, 300, 200, 40), "Buy Pet Slime", 50, lambda: buy("pet_slime", 50))

    while running:
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            # buttons see latest coins on click
            s = load()
            btn_hat.handle(e, s["coins"])
            btn_pet.handle(e, s["coins"])

        s = load()
        screen.fill(BG_COLOR)
        draw_text("Reward World", 20, 20, big)
        draw_text(f"Coins: {s['coins']}   XP: {s['xp']}   Sessions: {s['sessions_completed']}", 20, 60)

        # Avatar
        pygame.draw.circle(screen, (220, 200, 140), (avatar_x, avatar_y), 30)  # head
        # Hat cosmetic
        if s["inventory"].get("hat"):
            pygame.draw.polygon(screen, (180, 50, 50), [(avatar_x-35, avatar_y-10),
                                                        (avatar_x+35, avatar_y-10),
                                                        (avatar_x, avatar_y-50)])
        # Pet cosmetic
        if s["inventory"].get("pet_slime"):
            pygame.draw.circle(screen, (90, 200, 120), (avatar_x+60, avatar_y+25), 14)

        # Ground
        pygame.draw.rect(screen, (40, 90, 60), (0, HEIGHT-40, WIDTH, 40))

        # Buttons
        btn_hat.draw(s["coins"])
        btn_pet.draw(s["coins"])

        draw_text("Tip: finish a focus session in the Tk app to earn coins!", 20, HEIGHT-30)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

def buy(item_key, cost):
    s = load()
    if s["coins"] >= cost and not s["inventory"].get(item_key, False):
        s["coins"] -= cost
        s["inventory"][item_key] = True
        save(s)

if __name__ == "__main__":
    main()
