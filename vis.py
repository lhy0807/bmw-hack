import pygame

pygame.init()
white = (255, 255, 255)

X = 1200
Y = 200

display_surface = pygame.display.set_mode((X, Y ))
pygame.display.set_caption('Image')

bmw530 = pygame.image.load('530.png')
bmw530 = pygame.transform.scale(bmw530, (240, 100))

while True :
  
    display_surface.fill(white)
    display_surface.blit(bmw530, (0, 0))
    display_surface.blit(bmw530, (240, 0))

    print(display_surface.get_view())
    for event in pygame.event.get() :
  
        if event.type == pygame.QUIT :
            pygame.quit()
            quit()
  
        # Draws the surface object to the screen.  
        pygame.display.update()

    