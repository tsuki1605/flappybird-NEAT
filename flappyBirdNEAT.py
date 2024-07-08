import pygame
import neat
import time
import os
import random
import visualize
import pickle

pygame.font.init()

WIDTH = 500
HEIGHT = 800
FLOOR = 730

GEN = 0

DRAW_LINES = False

#load images
BIRDS_IMG = [pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird1.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird2.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird3.png")))] #image two times biggger and load image
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("images", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("images", "base.png")))
BACKGROUND_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bg.png")))

#fonts
STAT_FONT = pygame.font.SysFont("arial", 50)
END_FONT = pygame.font.SysFont("arial", 70)

pygame.display.set_caption("Flappy Bird")

class Bird:
    """
    Bird class representing the flappy bird
    """
    IMGS = BIRDS_IMG
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        """
        Initilize object
        Parameters:
            x: starting x position (int)
            y: starting y position (int)
        Return:
            None
        """
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.velocity = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]
    
    def jump(self):
        """
        Makes the bird jump
        Return:
            None
        """
        self.velocity = -10.5 #negative since top left of screen is (0,0), going up means negative velocity
        self.tick_count = 0 #keep count of when last jumped
        self.height = self.y #keep track where bird jumped from
    
    def move(self):
        """
        Makes the bird move
        Return:
            None
        """
        self.tick_count += 1

        #downward acceleration
        displacement = self.velocity * self.tick_count + 1.5 * self.tick_count**2 #based on velocity, how much moving up or down

        #make sure velocity doesnt go too far up or down
        #terminal velocity
        if displacement >= 16:
            displacement = 16
        if displacement < 0:
            displacement -= 2 #fine tune movement
        
        self.y = self.y + displacement

        if displacement < 0 or self.y < self.height + 50:
            #tilt up
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            #tilt down
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL
    
    def draw(self, window):
        """
        Draws the bird
        Parameters:
            window: pygame window or surface
        Return:
            None
        """
        self.img_count += 1

        #check which image to use based on image count, loop through three images
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0
        
        #when bird tilted (nose diving), don't want it to be flapping wings
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2
        
        #rotate image around its center based on tilt
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
        window.blit(rotated_image, new_rect.topleft)
    
    def get_mask(self):
        """
        Gets mask for current image of bird
        Return:
            None
        """
        return pygame.mask.from_surface(self.img)

class Pipe:
    """
    Represents a pipe object
    """
    GAP = 200
    VELOCITY = 5

    def __init__(self, x):
        """
        Initialize pipe object
        Parameters:
            x: int
            y: int
        Return:
            None
        """
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0

        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOT = PIPE_IMG

        self.passed = False

        self.set_height()
    
    def set_height(self):
        """
        Set height of pipe from top of screen
        Return: 
            None
        """
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP
    
    def move(self):
        """
        Move pipe based on velocity
        Return: 
            None
        """
        self.x -= self.VELOCITY

    def draw(self, window):
        """
        Draw both top and bottom of pipe
        Parameters:
            pygame window/surface
        Return:
            None
        """
        #draw top pipe
        window.blit(self.PIPE_TOP, (self.x, self.top))
        #draw bottom pipe
        window.blit(self.PIPE_BOT, (self.x, self.bottom))

    def collide(self, bird, window):
        """
        Returns if bird collides with a pipe
        Parameters:
            bird: Bird object
        Return:
            Boolean
        """
        bird_mask = bird.get_mask()
        #mask for top and bottom height
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bot_mask = pygame.mask.from_surface(self.PIPE_BOT)

        #calculate offset
        top_offset = (self.x - bird.x, self.top - round(bird.y)) #bird to top_mask
        bot_offset = (self.x - bird.x, self.bottom - round(bird.y)) #top_mask to bot_mask

        #points of collision
        bot_point = bird_mask.overlap(bot_mask, bot_offset)
        top_point = bird_mask.overlap(top_mask, top_offset)

        #check if points of collision exist
        if top_point or bot_point:
            return True
        
        return False

class Base:
    """
    Represents moving floor of game
    """
    VELOCITY = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        """
        Initialize object
        Parameter:
            y: int
        Return: 
            None
        """
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH
    
    def move(self):
        """
        Moves floor so it loooks like a continuous scrolling image
        Return:
            None
        """
        self.x1 -= self.VELOCITY
        self.x2 -= self.VELOCITY
        
        #move base image for one continuous image
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH
    
    def draw(self, window):
        """
        Draws the floor (two images that move together)
        Parameter:
            window: the pygame surface/window
        Return:
            None
        """
        window.blit(self.IMG, (self.x1, self.y))
        window.blit(self.IMG, (self.x2, self.y))

def draw_window(window, birds, pipes, base, score, GEN, pipe_ind):
    """
    Draws windows for main game loop
    Parameters:
        window: pygame window surface
        birds: list of Bird objects
        pipes: list of pipes
        base: Base object
        score: score of the game (int)
        gen: current generation
    Return:
        None
    """
    if GEN == 0:
        GEN = 1

    window.blit(BACKGROUND_IMG, (0,0))

    for pipe in pipes:
        pipe.draw(window)
    
    for bird in birds:
        # draw lines from bird to pipe
        if DRAW_LINES:
            try:
                pygame.draw.line(window, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width()/2, pipes[pipe_ind].height), 5)
                pygame.draw.line(window, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width()/2, pipes[pipe_ind].bottom), 5)
            except:
                pass
        # draw bird
        bird.draw(window)
    
    #score
    text = STAT_FONT.render("Score: " + str(score), 1, (255,255,255))
    window.blit(text, (WIDTH - 10 - text.get_width(), 10))

    #generations
    text = STAT_FONT.render("Gen: " + str(GEN), 1, (255,255,255))
    window.blit(text, (10, 10))

    #birds alive
    text = STAT_FONT.render("Alive: " + str(len(birds)), 1, (255,255,255))
    window.blit(text, (10, 50))
    
    base.draw(window)
    for bird in birds:
        bird.draw(window)

    pygame.display.update()

def main(genomes, config):
    """
    Runs simulation of current population of birds and sets fitness based on distance reached in game
    """
    global GEN
    GEN += 1

    nets = []
    ge =  []
    birds = []

    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        ge.append(genome)
        
    
    base = Base(FLOOR)
    pipes = [Pipe(600)]
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    score = 0

    run = True
    while run and len(birds) > 0:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break
        
        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        
        for x, bird in enumerate(birds):
            ge[x].fitness += 0.1
            bird.move()

            output = nets[birds.index(bird)].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()

        base.move()

        add_pipe = False
        rem = []
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird, window):
                    #remove bird that collides
                    ge[x].fitness -=1 #one removed from fitness score when bird hits pipe
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                # if not pipe.passed and pipe.x < bird.x:
                #     pipe.passed = True
                #     add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            
            if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True
            
            pipe.move()
        
        if add_pipe:
            score += 1
            for genome in ge:
                genome.fitness += 5
            pipes.append(Pipe(600))
        
        #removing passed pipes
        for r in rem:
            pipes.remove(r)
        
        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() - 10 >= FLOOR or bird.y < -50:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        #base.move()
        draw_window(window, birds, pipes, base, score, GEN, pipe_ind)
    
def run(config_file):
    """
    Runs NEAT algorithm to train neural network to play flappy bird
    Parameter:
        config_file: location of configuration file
    Return:
        None
    """
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_file)

    #create population, which is the top-level object for a NEAT run
    p = neat.Population(config)

    #add stdout reporter to show progress in terminal
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    #run for up to 50 generations
    winner = p.run(main,50)

    #show final stats
    print('\nBest genome:\n{!s}'.format(winner))
    

if __name__ == "__main__":
    #determine path to config file
    #script will run successfully regardless of current working directory
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)