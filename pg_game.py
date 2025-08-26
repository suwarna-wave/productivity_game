# pg_game.py
import pygame, sys
from shared import load, save

WIDTH, HEIGHT = 640, 400
BG = (30, 36, 42)
WHITE = (240, 240, 240)
BTN = (70, 130, 220)
BTN2 = (90, 150, 240)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Reward World")
font = pygame.font.SysFont(None, 28)
big  = pygame.font.SysFont(None, 36)
clock = pygame.time.Clock()

def txt(t, x, y, f=font, c=WHITE): screen.blit(f.render(t, True, c), (x,y))

class Button:
    def __init__(self, rect, label, cost, key):
        self.rect = pygame.Rect(rect); self.label = label; self.cost = cost; self.key = key
    def draw(self):
        mouse = pygame.mouse.get_pos()
        pygame.draw.rect(screen, BTN2 if self.rect.collidepoint(mouse) else BTN, self.rect, border_radius=8)
        txt(f"{self.label} ({self.cost}c)", self.rect.x+10, self.rect.y+10)
    def click(self):
        s = load()
        if s["coins"] >= self.cost and not s["inventory"].get(self.key, False):
            s["coins"] -= self.cost
            s["inventory"][self.key] = True
            save(s)

def main():
    hat = Button((30, 320, 160, 40), "Buy Hat", 30, "hat")
    pet = Button((210, 320, 200, 40), "Buy Pet Slime", 50, "pet_slime")

    running = True
    while running:
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if hat.rect.collidepoint(e.pos): hat.click()
                if pet.rect.collidepoint(e.pos): pet.click()

        s = load()
        screen.fill(BG)
        txt("Reward World", 20, 20, big)
        txt(f"Coins: {s['coins']}   XP: {s['xp']}   Sessions: {s['sessions_completed']}", 20, 60)

        # Avatar
        cx, cy = WIDTH//2, HEIGHT//2 + 30
        pygame.draw.circle(screen, (220,200,140), (cx, cy), 28)
        if s["inventory"].get("hat"):
            pygame.draw.polygon(screen, (180,60,60), [(cx-32, cy-8), (cx+32, cy-8), (cx, cy-44)])
        if s["inventory"].get("pet_slime"):
            pygame.draw.circle(screen, (90,200,120), (cx+50, cy+20), 12)

        # Ground
        pygame.draw.rect(screen, (40, 90, 60), (0, HEIGHT-40, WIDTH, 40))

        # Shop
        hat.draw(); pet.draw()
        txt("Tip: Earn coins by finishing focus sessions in the Timer tab.", 20, HEIGHT-28)

        pygame.display.flip()

    pygame.quit(); sys.exit()

if __name__ == "__main__":
    main()
