"""pygame / pygame-ce: HUD that keeps proportion from 720p to 4K and ultrawide."""
import pygame

import appdimens as ad
from appdimens.integrations import metrics_from_pygame

pygame.init()
screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
hud = ad.Dimens(metrics_from_pygame(screen))
clock = pygame.time.Clock()
running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type in (pygame.VIDEORESIZE, getattr(pygame, "WINDOWSIZECHANGED", -1)):
            hud.set_metrics(metrics_from_pygame(screen))
    screen.fill((12, 18, 32))
    font = pygame.font.Font(None, int(hud.ftsdp(28)))      # fit: never crops on ultrawide
    pad = int(hud.ftsdp(16))
    pygame.draw.rect(screen, (29, 78, 216), (pad, pad, int(hud.ftsdp(220)), int(hud.ftsdp(56))), border_radius=int(hud.ftsdp(10)))
    screen.blit(font.render("HP 100", True, (255, 255, 255)), (pad * 2, pad * 1.8))
    pygame.display.flip()
    clock.tick(60)
