#!/usr/bin/python3
import time
import sys
import pygame
import numpy as np

'''
@@@@@@@@@@@@@@@@@@
GLOBAL VARIABLES @
@@@@@@@@@@@@@@@@@@
'''

#NOTE: for now, I just copied these from the JS file --> not sure if we'll need all
#of them

n_dots = 300                #number of dots per set (equivalent to number of dots per
                             #frame)
n_sets = 1                  #number of sets to cycle through per frame
                            #TO-DO: we can probably just delete this ^ parameter
coherent_direction = 123;   #The direction of the coherentDots in degrees
                            #Starts at 3 o'clock and goes counterclockwise (0 ==
                            #90 == upwards, 180 == leftwards, 270 == downwards), range 0 - 360
coherence = 0.5             #Proportion of dots to move together, range from 0 to 1
dot_radius = 2               #Radius of each dot in pixels
dot_life = -1               # How many frames a dot follows its trajectory before redrawn. -1
                            # is infinite life
move_distance = 1          #How many pixels the dots move per frame
noise_update_type = "incoherent_direction_update"   #how to update noise dots --> options:
                                                    # "incoherent_direction_update"
                                                    # "random_walk_update"
                                                    # "reset_location"
'''
Out of Bounds Decision
How we reinsert a dot that has moved outside the edges of the aperture:
1 - Randomly appear anywhere in the aperture
2 - Randomly appear on the opposite edge of the aperture
'''
reinsert_type = 1


'''
@@@@@@@@@@@@@@@@@@
SET UP CANVAS, APERTURE @
@@@@@@@@@@@@@@@@@@
'''
pygame.init()

# Set task display to be full screen
monitor = pygame.display.Info()
screen = pygame.display.set_mode((monitor.current_w, monitor.current_h))
pygame.display.set_caption('RDM Task')
# X,Y coord of screen center = aperture center
x_screen_center = pygame.Rect((0,0),(monitor.current_w, monitor.current_h)).centerx
y_screen_center = pygame.Rect((0,0),(monitor.current_w, monitor.current_h)).centery

# Set our color constants
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)

dot_color = WHITE         #Color of the dots
background_color = GRAY   #Color of the background
aperture_width = 400;       #How many pixels wide the aperture is. For square aperture this
                            #will be the both height and width. For circle, this will be
                            #the diameter.
aperture_height = 300;      #How many pixels high the aperture is. Only relevant for ellipse
                            #and rectangle apertures. For circle and square, this is ignored.
aperture_center_x = x_screen_center      #NOTE: Aperture center is currently equal to center of
                                         #screen
aperture_center_y = y_screen_center      # (in pixels)

'''
Shape of aperture
 1 - Circle
 2 - Ellipse
 3 - Square
 4 - Rectangle
'''
aperture_type = 1

'''
@@@@@@@@@@@@@@@@@@@@@@
FUNCTION DEFINITIONS @
@@@@@@@@@@@@@@@@@@@@@@
'''

#calculates coherent_jump_size_x based on global variables coherent_direction and
#move_distance
def calculate_coherent_jump_size_x(coherent_direction):
    angle_in_radians = coherent_direction * np.pi / 180
    return move_distance * np.cos(angle_in_radians)

#calculates coherent_jump_size_y based on global variables coherent_direction and
#move_distance
def calculate_coherent_jump_size_y(coherent_direction):
    angle_in_radians = coherent_direction * np.pi / 180  #might need to be neg
    return move_distance * np.sin(angle_in_radians)

# Michelle: added
# initialize the parameters for the aperture for further calculation
def init_aperture_param():
    # For circle and square
    if (aperture_type == 1 or aperture_type == 3):
        horizontal_axis = vertical_axis = aperture_width / 2
    # For ellipse and rectangle
    elif (aperture_type == 2 or aperture_type == 4):
        horizontal_axis = aperture_width / 2
        vertical_axis = aperture_height / 2
    aperture_axis = [horizontal_axis, vertical_axis]
    return aperture_axis


'''
@@@@@@@@@@@@@@@@@@@@@@@
MORE GLOBAL VARIABLES @
@@@@@@@@@@@@@@@@@@@@@@@
'''

#TO-DO: update this based on pygame
#initialize aperture parameters --> horizontal = vertical because we are using a circle
aperture_axis = init_aperture_param();
horizontal_axis = aperture_axis[0]
vertical_axis = aperture_axis[1]
#  Was going to use to update portion of screen but dont see an increase in performance/ decrease in time
# aperture_section = pygame.Rect((aperture_center_x - horizontal_axis, aperture_center_y - vertical_axis),(aperture_width,aperture_height))


#calculate coherent jump sizes in x and y
coherent_jump_size_x = calculate_coherent_jump_size_x(coherent_direction)
coherent_jump_size_y = calculate_coherent_jump_size_y(coherent_direction)


#calculate the number of coherent and incoherent dots
n_coherent_dots = n_dots * coherence
n_incoherent_dots = n_dots - n_coherent_dots


'''
@@@@@@@@@@@@@@@@@@@
CLASS DEFINITIONS @
@@@@@@@@@@@@@@@@@@@
'''

class dot(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface([dot_radius * 2, dot_radius * 2]).convert_alpha()
        self.image.fill(GRAY) # Set the dot to be transparent
        pygame.draw.circle(self.image, WHITE, (dot_radius, dot_radius), dot_radius)
        self.rect = self.image.get_rect() # Rect determines position the dot is drawn

        self.rect.centerx = 0                                      #x coordinate
        self.rect.centery = 0                                      #y coordinate
        self.vx = 0                                     #coherent x jumpsize
        self.vy = 0                                     #coherent y jumpsize
        self.vx2 = 0                                    #incoherent x jumpsize
        self.vy2 = 0                                    #incoherent y jumpsize
        self.latest_x_move = 0                          #latest x move direction
        self.latest_y_move = 0                          #latest y move direction
        self.life_count = np.floor(np.random.uniform(0, dot_life))    #counter for dot's life
        self.update_type = ""                           #string to determine how dot gets updated

        #create random x and y coordinates
        self.reset_location()
        self.setvxvy()
        self.setvx2vy2()

    # Michelle: Get functions for testing
    def get_xy(self):
        xy_coord = [self.rect.centerx, self.rect.centery]
        return xy_coord

    #Function to check if dot life has ended
    def life_ended(self):

        #If we want infinite dot life
        if (dot_life < 0):
            self.life_count = 0; #resetting to zero to save memory. Otherwise it might
                                 #increment to huge numbers.
            return False
        # Else if the dot's life has reached its end
        elif (self.life_count >= dot_life):
            self.life_count = 0
            return True
        #Else the dot's life has not reached its end
        else:
            return False

    # Function to check if dot is out of bounds
    def out_of_bounds(self):

        #for circle and ellipse:
        #equation of an ellipse centered at (h,k) with r_horiz=a and r_vert=b
        # (x-h)^2/a^2 + (y-k)^2/b^2 = 1
        if (aperture_type == 1 or aperture_type == 2):
            displacement_from_center = (((self.rect.centerx - aperture_center_x)**2)/(horizontal_axis**2)
                                        + ((self.rect.centery - aperture_center_y)**2)/(vertical_axis**2))
            if (displacement_from_center > 1):
                return True
            else:
                return False

        # For square and rectangle
        if (aperture_type == 3 or aperture_type == 4):
            if (self.rect.centerx < (aperture_center_x) - horizontal_axis
                or self.rect.centerx > (aperture_center_x) + horizontal_axis
                or self.rect.centery < (aperture_center_y) - vertical_axis
                or self.rect.centery > (aperture_center_y) + vertical_axis):
                return True
            else:
                return False


    #gives random (but legal) values to dot.x and dot.y
    def reset_location(self):
        #for a circle or ellipse
        if (aperture_type == 1 or aperture_type == 2):
            phi = np.random.uniform(-np.pi, np.pi)
            rho = np.random.random()                      # 0 <= rho <= 1

            centerx = np.sqrt(rho) * np.cos(phi)
            centery = np.sqrt(rho) * np.sin(phi)

            #TO-DO: FIND EQUIVALENT WAY TO MAP THESE 2 LINES USING PYGAME
            self.rect.centerx = centerx * horizontal_axis + aperture_center_x
            self.rect.centery = centery * vertical_axis + aperture_center_y

        #for a square or rectangle
        else:
            self.rect.centerx = np.random.uniform(-1, 1) * horizontal_axis + aperture_center_x
            self.rect.centery = np.random.uniform(-1, 1) * vertical_axis + aperture_center_y


    #sets dot.vx and dot.vy based on global variables coherent_jump_size
    def setvxvy(self):
        self.vx = coherent_jump_size_x
        self.vy = coherent_jump_size_y


    #set vx2 and vy2 based on a random angle
    def setvx2vy2(self):
        #generate random angle of movement
        theta = np.random.uniform(-np.pi, np.pi)

        #update vx2 and vy2 with the new angle
        self.vx2 = np.cos(theta) * move_distance
        self.vy2 = np.sin(theta) * move_distance  #NOTE: might have to make this negative


    #update x and y coordinates by moving it in x and y coherent directions
    def coherent_direction_update(self):
        self.rect.centerx += self.vx
        self.rect.centery += self.vy
        self.latest_move_x = self.vx
        self.latest_move_y = self.vy


    #update x and y coordinates with random move directions vx2 and vy2
    def incoherent_direction_update(self):
        self.rect.centerx += self.vx2
        self.rect.centery += self.vy2
        self.latest_x_move = self.vx2
        self.latest_y_move = self.vy2


    #create a new angle to move towards, and update the x and y coordinates based on that angle
    def random_walk_update(self):
        #generate a random angle of movement
        theta = np.random.uniform(-np.pi, np.pi)

        #genearte the movement from the angle
        self.latest_x_move = np.cos(theta) * move_distance
        self.latest_y_move = np.sin(theta) * move_distance

        #update x and y coordinates with new location
        self.rect.centerx += self.latest_x_move
        self.rect.centery += self.latest_y_move

    #TO-DO: create a "reinsert_on_opposite_edge(self)" function as an alternative to
    # "reset_location" when dot goes out of bounds

    def set_update_type(self, i):
        if i < n_coherent_dots:
            self.update_type = "coherent_direction_update"  #make it a coherent dot
        else:
            self.update_type = "incoherent_direction_update"  #make it a random dot

    def update(self):
        if self.update_type == "coherent_direction_update":
            self.coherent_direction_update()
        elif self.update_type == "random_walk_update":
            self.random_walk_update()
        elif self.update_type == "incoherent_direction_update":
            self.incoherent_direction_update()
        elif self.update_type == "reset_location":
            self.reset_location()
        else:
            print("error: update_type is invalid")
            exit(1);

        self.life_count += 1

        #TO-DO: check if dot goes out of bounds or if life ended, and update accordingly
        #TO-DO: if life ended, give it new random x and y directions, and update
        #vx, vy, vx2, vy2 if necessary

        if (self.life_ended()):
            self.reset_location()

	    # If it goes out of bounds, do what is necessary (reinsert randomly or reinsert on the opposite edge) based on the parameter chosen
        if (self.out_of_bounds()):
            if (reinsert_type == 1):
                self.reset_location()
            elif (reinsert_type == 2):
                #TO-DO: reinsert on opposite edge
                pass

'''
#contains a variable self.array, each of whose elements is a set (ie array) of dots, where
#the first n_coherent_dots are coherent dots and the rest are incoherent dots
class dotArray():
    def __init__(self):
        #initialize the array of dots
        self.dot_array = [];

        #create an n_sets sized array of dots where the first n_coherent_dots elements are
        #coherent dots and the rest are incoherent
        for i in range(n_dots):

            new_dot = dot()

            if i < n_coherent_dots:
                new_dot.update_type = "coherent_direction_update"  #make it a coherent dot
            else:
                new_dot.update_type = "incoherent_direction_update"  #make it a random dot

            self.dot_array.append(new_dot)

    # Michelle: Get functions for testing
    def get_xy_arr(self):
        dot_coord = np.empty(n_dots, dtype=list)
        for i in range(n_dots):
            xy_coord = self.dot_array[i].get_xy()
            dot_coord[i] = xy_coord
        return dot_coord

    #update dots with their new locations
    def update_dots(self):

        #loop through each dot and update them accordingly
        for i in range(len(self.dot_array)):
            update_dot = self.dot_array[i]

            if update_dot.update_type == "coherent_direction_update":
                update_dot.coherent_direction_update()
            elif update_dot.update_type == "random_walk_update":
                update_dot.random_walk_update()
            elif update_dot.update_type == "incoherent_direction_update":
                update_dot.incoherent_direction_update()
            elif update_dot.update_type == "reset_location":
                update_dot.reset_location
            else:
                print("error: update_type is invalid")
                exit(1);

            update_dot.life_count += 1

            #TO-DO: check if dot goes out of bounds or if life ended, and update accordingly
            #TO-DO: if life ended, give it new random x and y directions, and update
            #vx, vy, vx2, vy2 if necessary

            if (update_dot.life_ended()):
                dot = update_dot.reset_location()

    	    # If it goes out of bounds, do what is necessary (reinsert randomly or reinsert on the opposite edge) based on the parameter chosen
            if (update_dot.out_of_bounds()):
                if (reinsert_type == 1):
                    dot = update_dot.reset_location()
                elif (reinsert_type == 2):
                    #TO-DO: reinsert on opposite edge
                    pass

   #draw dots after they've been updated
    def draw(self):

        # Go through each dot in array and draw it
        for i in range(len(self.dot_array)):

            dot = self.dot_array[i]
            # TO-DO: Documentation says float can be passed for coords but compile error?
            dot_x = int(dot.x)
            dot_y = int(dot.y)
            pygame.draw.circle(screen, dot_color,(dot_x, dot_y), dot_radius)
'''


'''
@@@@@@@@@@@@@@@@@@@@@
MAIN IMPLEMENTATION @
@@@@@@@@@@@@@@@@@@@@@
'''

def main():

    # new_array = dotArray()
    all_sprites = pygame.sprite.RenderUpdates()
    for i in range(n_dots):
        new_dot = dot()
        new_dot.set_update_type(i)
        all_sprites.add(new_dot)

    clock = pygame.time.Clock()
    background = pygame.surface.Surface((monitor.current_w, monitor.current_h))
    background.fill(GRAY)
    screen.blit(background,(0,0))

    while True:
        clock.tick(60)
        # Handle closing the window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        # Draw screen
        all_sprites.update()
        circles = all_sprites.draw(screen)
        # Update a portion of the screen
        pygame.display.set_caption("{}".format(clock.get_fps()))
        pygame.display.update(circles)
        all_sprites.clear(screen,background)



if __name__=='__main__':
    main()
