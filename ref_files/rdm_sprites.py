#!/usr/bin/python3
import sys
import pygame
import numpy as np
import os
import csv

'''
@@@@@@@@@@@@@@@@@@
GLOBAL VARIABLES @
@@@@@@@@@@@@@@@@@@
'''

trial_choices = {"safe_choice": True, "continuing_evidence": False, "longer_stimulus": False, \
    "limit_COM": False}

n_trials = 5                #number of trials

n_dots = 300                #number of dots per set (equivalent to number of dots per
                             #frame)
n_sets = 1                  #number of sets to cycle through per frame
                            #TO-DO: we can probably just delete this ^ parameter
#coherent_direction = 0;   # OBSOLETE: The direction of the coherentDots in degrees
                            #Starts at 3 o'clock and goes counterclockwise (0 ==
                            #90 == upwards, 180 == leftwards, 270 == downwards), range 0 - 360
coherence = 1             # OBSOLETE: Proportion of dots to move together, range from 0 to 1
dot_radius = 3             #Radius of each dot in pixels
dot_life = 300               # How many frames a dot follows its trajectory before redrawn. -1
                            # is infinite life
move_distance = 1          #How many pixels the dots move per frame
noise_update_type = "incoherent_direction_update"   #how to update noise dots --> options:
                                                    # "incoherent_direction_update"
                                                    # "random_walk_update"
                                                    # "reset_location"

coherence_choices = [0, .032, .064, .128, .256, .512]
time_between_trials = 700 # milliseconds

'''
Out of Bounds Decision
How we reinsert a dot that has moved outside the edges of the aperture:
1 - Randomly appear anywhere in the aperture
2 - appear on the opposite edge of the aperture
'''
reinsert_type = 2

'''
Shape of aperture
 1 - Circle
 2 - Ellipse
 3 - Square
 4 - Rectangle
'''
aperture_type = 1

directory_name = ""

# SAFE CHOICE TRIALS PARAMS
'''
safe choice score values = [none, correct, wrong, safe]
safe_choice_time_bounds = [min, max], where the time is selected randomly within that range
'''
safe_choice_scores = [-2, 1, -1, 0]
safe_choice_time_bounds = [6, 9]


'''
@@@@@@@@@@@@@@@@@@@@@@@@@
SET UP CANVAS, APERTURE @
@@@@@@@@@@@@@@@@@@@@@@@@@
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
aperture_width = monitor.current_w/4;       #How many pixels wide the aperture is. For square aperture this
                            #will be the both height and width. For circle, this will be
                            #the diameter.
aperture_height = monitor.current_h/3;      #How many pixels high the aperture is. Only relevant for ellipse
                            #and rectangle apertures. For circle and square, this is ignored.
aperture_center_x = x_screen_center      #NOTE: Aperture center is currently equal to center of
                                         #screen
aperture_center_y = y_screen_center      # (in pixels)


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

def draw_text(surface, text, size, x, y):
    font_name = pygame.font.match_font('arial')
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surface.blit(text_surface, text_rect)

# add a row to the 2d matrix "position_record", which records the positions of dots at a given point
# in time
def get_dot_positions(dot_array):
    dot_positions = []
    for dot in dot_array:
        dot_positions.append([dot.x, dot.y])
    return dot_positions

def keypress_loop(coherence, is_right, trial_num):
    clock = pygame.time.Clock()
    trial_dict = {} # where we will record all data for this trial, including the following...
    dot_positions = {}
    left_click_times = []
    right_click_times = []
    filename = "keypress_loop.csv"

    #calculate the number of coherent and incoherent dots
    n_coherent_dots = n_dots * coherence
    n_incoherent_dots = n_dots - n_coherent_dots

    coherent_direction = 0
    if not is_right:
        coherent_direction = 180

    # create and group together all sprites
    all_sprites = pygame.sprite.Group()
    dot_array = []
    for i in range(n_dots):
        new_dot = dot(coherent_direction)

        if i < n_coherent_dots:
            new_dot.update_type = "coherent_direction_update"  #make it a coherent dot
        else:
            new_dot.update_type = "incoherent_direction_update"  #make it a random dot

        all_sprites.add(new_dot)
        dot_array.append(new_dot)

    # Game loop
    running = True
    start_time = pygame.time.get_ticks() # in milliseconds
    while running:
        # Process input (events)
        for event in pygame.event.get():
            # check for closing window
            if event.type == pygame.QUIT:
                running = False
                break
            
            keystate = pygame.key.get_pressed()
            if keystate[pygame.K_m]:
                current_time = pygame.time.get_ticks()-start_time
                dot_positions[current_time] = get_dot_positions(dot_array) # record dot positions
                right_click_times.append(current_time) # record time since start
                if (is_right):
                    running = False
            if keystate[pygame.K_z]:
                current_time = pygame.time.get_ticks()-start_time
                dot_positions[current_time] = get_dot_positions(dot_array) # record dot positions
                left_click_times.append(current_time) # record time since start
                if (not is_right):
                    running = False

        # Update
        all_sprites.update()

        # Draw / render
        screen.fill(background_color)
        all_sprites.draw(screen)

        # *after* drawing everything, flip the display
        pygame.display.flip()

    trial_str = "Trial " + str(trial_num+1)
    trial_dict[trial_str] = ""

    trial_dict['left_click_times'] = left_click_times
    trial_dict['right_click_times'] = right_click_times
    trial_dict['coherence'] = str(coherence) # float val of coherence messed up pandas
    trial_dict['dot_positions'] = dot_positions

    export_csv(trial_dict, filename)

    return trial_dict

def safe_choice(coherence, is_right, trial_num, score, time_limit, experiment):
    clock = pygame.time.Clock()
    trial_dict = {} # where we will record all data for this trial, including the following...
    dot_positions = {}
    left_click_times = []
    right_click_times = []
    space_click_times = []
    stimulus_on = True
    if experiment:
        filename = "safe_choice_experiment.csv"
    else:
        filename = "safe_choice_control.csv"
    last_choice = 0  # 0 for none; 1 for left; 2 for right; 3 for space

    #calculate the number of coherent and incoherent dots
    n_coherent_dots = n_dots * coherence
    n_incoherent_dots = n_dots - n_coherent_dots

    coherent_direction = 0
    if not is_right:
        coherent_direction = 180

    # create and group together all sprites
    all_sprites = pygame.sprite.Group()
    dot_array = []
    for i in range(n_dots):
        new_dot = dot(coherent_direction)

        if i < n_coherent_dots:
            new_dot.update_type = "coherent_direction_update"  #make it a coherent dot
        else:
            new_dot.update_type = "incoherent_direction_update"  #make it a random dot

        all_sprites.add(new_dot)
        dot_array.append(new_dot)

    # Game loop
    running = True
    start_time = pygame.time.get_ticks() # in milliseconds
    while running:

        # Process input (events)
        for event in pygame.event.get():
            # check for closing window
            if event.type == pygame.QUIT:
                running = False
                break

        # check timer
        current_time = pygame.time.get_ticks()-start_time
        if (current_time/1000 > time_limit):
            running = False
            break
            
        # track key presses
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_m]:
            last_choice = 2
            dot_positions[current_time] = get_dot_positions(dot_array) # record dot positions
            right_click_times.append(current_time) # record time since start
            turn_off_stimulus()
            stimulus_on = False

        if keystate[pygame.K_z]:
            last_choice = 1
            dot_positions[current_time] = get_dot_positions(dot_array) # record dot positions
            left_click_times.append(current_time) # record time since start
            turn_off_stimulus()
            stimulus_on = False

        if experiment:
            if keystate[pygame.K_SPACE]:
                last_choice = 3
                dot_positions[current_time] = get_dot_positions(dot_array)
                space_click_times.append(current_time)
                turn_off_stimulus()
                stimulus_on = False

        # Update
        if stimulus_on:
            all_sprites.update()

        # Draw / render
        screen.fill(background_color)
        if stimulus_on:
            all_sprites.draw(screen)
        draw_text(screen, 'SCORE: ' + str(score), 18, monitor.current_w/2, 10)

         # *after* drawing everything, flip the display
        pygame.display.flip()

    # update score
    if (last_choice == 0):
        score += safe_choice_scores[0]
    elif ((last_choice == 1 and not is_right) or (last_choice == 2 and is_right)):
        score += safe_choice_scores[1]
    elif (last_choice == 3):
        score += safe_choice_scores[3]
    else:
        # must be wrong
        score += safe_choice_scores[2]

    trial_str = "Trial " + str(trial_num+1)
    trial_dict[trial_str] = ""

    trial_dict['left_click_times'] = left_click_times
    trial_dict['right_click_times'] = right_click_times
    if experiment:
        trial_dict['space_click_times'] = space_click_times
    trial_dict['coherence'] = str(coherence) # float val of coherence messed up pandas
    trial_dict['dot_positions'] = dot_positions
    trial_dict['score'] = score

    export_csv(trial_dict, filename)

    return score

def limit_mind_changes(coherence, is_right, trial_num, score, time_limit, experiment, changes_limit):
    clock = pygame.time.Clock()
    trial_dict = {} # where we will record all data for this trial, including the following...
    dot_positions = {}
    left_click_times = []
    right_click_times = []
    filename = "limit_COM.csv"

    last_choice = 0  # 0 for none; 1 for left; 2 for right

    #calculate the number of coherent and incoherent dots
    n_coherent_dots = n_dots * coherence
    n_incoherent_dots = n_dots - n_coherent_dots

    coherent_direction = 0
    if not is_right:
        coherent_direction = 180

    # create and group together all sprites
    all_sprites = pygame.sprite.Group()
    dot_array = []
    for i in range(n_dots):
        new_dot = dot(coherent_direction)

        if i < n_coherent_dots:
            new_dot.update_type = "coherent_direction_update"  #make it a coherent dot
        else:
            new_dot.update_type = "incoherent_direction_update"  #make it a random dot

        all_sprites.add(new_dot)
        dot_array.append(new_dot)

    # Game loop
    running = True
    start_time = pygame.time.get_ticks() # in milliseconds
    while running:
        # Process input (events)
        for event in pygame.event.get():
            # check for closing window
            if event.type == pygame.QUIT:
                running = False
                break

        # check timer
        current_time = pygame.time.get_ticks()-start_time
        if (current_time/1000 > time_limit):
            running = False
            break
            
        # track key presses
        keystate = pygame.key.get_pressed()
        if (keystate[pygame.K_m] and changes_limit):
            changes_limit -= 1
            last_choice = 2
            dot_positions[current_time] = get_dot_positions(dot_array) # record dot positions
            right_click_times.append(current_time) # record time since start

        if (keystate[pygame.K_z] and changes_limit):
            changes_limit -= 1
            last_choice = 1
            dot_positions[current_time] = get_dot_positions(dot_array) # record dot positions
            left_click_times.append(current_time) # record time since start

        # Update
        all_sprites.update()

        # Draw / render
        screen.fill(background_color)
        all_sprites.draw(screen)
        draw_text(screen, 'SCORE: ' + str(score), 18, monitor.current_w/2, 10)
        draw_text(screen, 'REMAINING KEY PRESSES: ' + str(changes_limit), 18, monitor.current_w/2, 35)

        # *after* drawing everything, flip the display
        pygame.display.flip()

    # update score
    if (last_choice == 0):
        score += safe_choice_scores[0]
    elif ((last_choice == 1 and not is_right) or (last_choice == 2 and is_right)):
        score += safe_choice_scores[1]
    else:
        # must be wrong
        score += safe_choice_scores[2]

    trial_str = "Trial " + str(trial_num+1)
    trial_dict[trial_str] = ""

    trial_dict['left_click_times'] = left_click_times
    trial_dict['right_click_times'] = right_click_times
    trial_dict['coherence'] = str(coherence) # float val of coherence messed up pandas
    trial_dict['dot_positions'] = dot_positions
    trial_dict['score'] = score
    trial_dict['changes_left'] = changes_limit

    export_csv(trial_dict, filename)

    return score

def resulaj_test(coherence, is_right, trial_num, score, time_limit, experiment):
    clock = pygame.time.Clock()
    trial_dict = {} # where we will record all data for this trial, including the following...
    dot_positions = {}
    stimulus_on = True
    if experiment:
        filename = "resulaj_experiment.csv"
    else:
        filename = "resulaj_choice_control.csv"

    #calculate the number of coherent and incoherent dots
    n_coherent_dots = n_dots * coherence
    n_incoherent_dots = n_dots - n_coherent_dots

    coherent_direction = 0
    if not is_right:
        coherent_direction = 180

    # create and group together all sprites
    all_sprites = pygame.sprite.Group()
    dot_array = []
    for i in range(n_dots):
        new_dot = dot(coherent_direction)

        if i < n_coherent_dots:
            new_dot.update_type = "coherent_direction_update"  #make it a coherent dot
        else:
            new_dot.update_type = "incoherent_direction_update"  #make it a random dot

        all_sprites.add(new_dot)
        dot_array.append(new_dot)

    # create a cursor and put it in sprites group
    cursor_object = cursor()
    all_sprites.add(cursor_object)

    # Game loop
    running = True
    start_time = pygame.time.get_ticks() # in milliseconds
    while running:

        # Process input (events)
        for event in pygame.event.get():
            # check for closing window
            if event.type == pygame.QUIT:
                running = False
                break

        # check timer
        current_time = pygame.time.get_ticks()-start_time
        if (current_time/1000 > time_limit):
            running = False
            break

        # Update
        if stimulus_on:
            all_sprites.update()

        # Draw / render
        screen.fill(background_color)
        if stimulus_on:
            all_sprites.draw(screen)
        
        # draw targets
        pygame.draw.rect(screen,WHITE,(monitor.current_w*.2,monitor.current_h*.1,100,50))
        pygame.draw.rect(screen,WHITE,(monitor.current_w*.8,monitor.current_h*.1,100,50))

         # *after* drawing everything, flip the display
        pygame.display.flip()

    trial_str = "Trial " + str(trial_num+1)
    trial_dict[trial_str] = ""

    trial_dict['coherence'] = str(coherence) # float val of coherence messed up pandas
    trial_dict['dot_positions'] = dot_positions

    export_csv(trial_dict, filename)

    return 0


def export_csv(result_dict, filename):
    
    # Can adjust later to a customized file name
    if os.path.exists(directory_name + filename):
        with open(directory_name + filename, 'a') as f:
            w = csv.writer(f)
            w.writerows(result_dict.items())
    else:
        with open(directory_name + filename, 'w') as f:
            w = csv.writer(f)
            w.writerows(result_dict.items())

def make_data_dir():
    experiment_num = 0
    global directory_name
    
    # create parent "data" directory, if needed
    if not os.path.exists("./data"):
        os.mkdir("./data")

    while os.path.exists("./data/experiment_" + str(experiment_num)):
        experiment_num += 1
    directory_name = "./data/experiment_" + str(experiment_num) + "/"
    os.mkdir(directory_name)
    
def turn_off_stimulus():
    screen.fill(background_color)
    pygame.display.update()



'''
@@@@@@@@@@@@@@@@@@@@@@@
MORE GLOBAL VARIABLES @
@@@@@@@@@@@@@@@@@@@@@@@
'''

#TO-DO: update this based on pygame
#initialize aperture parameters --> horizontal = vertical because we are using a circle
aperture_axis = init_aperture_param()
horizontal_axis = aperture_axis[0]
vertical_axis = aperture_axis[1]
#  Was going to use to update portion of screen but dont see an increase in performance/ decrease in time
# aperture_section = pygame.Rect((aperture_center_x - horizontal_axis, aperture_center_y - vertical_axis),(aperture_width,aperture_height))


'''
@@@@@@@@@@@@@@@@@@@
CLASS DEFINITIONS @
@@@@@@@@@@@@@@@@@@@
'''

class dot(pygame.sprite.Sprite):
    def __init__(self, coherent_direction):
        pygame.sprite.Sprite.__init__(self)
        self.x = 0                                      #x coordinate
        self.y = 0                                      #y coordinate
        self.vx = calculate_coherent_jump_size_x(coherent_direction)
        self.vy = calculate_coherent_jump_size_y(coherent_direction)
        self.vx2 = 0                                    #incoherent x jumpsize
        self.vy2 = 0                                    #incoherent y jumpsize
        self.latest_x_move = 0                          #latest x move direction
        self.latest_y_move = 0                          #latest y move direction
        self.life_count = np.floor(np.random.uniform(0, dot_life))    #counter for dot's life
        self.update_type = ""                           #string to determine how dot gets updated

        #create random x and y coordinates
        self.reset_location()
        self.setvx2vy2()

        #set sprite-specific parameters
        self.image = pygame.Surface((2*dot_radius, 2*dot_radius))
        self.image.fill(background_color)
        pygame.draw.circle(self.image, dot_color, (dot_radius, dot_radius), dot_radius)
        self.rect = self.image.get_rect(center=(self.x, self.y)) # Rect determines position the dot is drawn

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
            displacement_from_center = (((self.x - aperture_center_x)**2)/(horizontal_axis**2)
                                        + ((self.y - aperture_center_y)**2)/(vertical_axis**2))
            if (displacement_from_center > 1):
                return True
            else:
                return False

        # For square and rectangle
        if (aperture_type == 3 or aperture_type == 4):
            if (self.x < (aperture_center_x) - horizontal_axis
                or self.x > (aperture_center_x) + horizontal_axis
                or self.y < (aperture_center_y) - vertical_axis
                or self.y > (aperture_center_y) + vertical_axis):
                return True
            else:
                return False

    #gives random (but legal) values to dot.x and dot.y
    def reset_location(self):

        # for a circle or ellipse
        if (aperture_type == 1):
            self.x = np.random.uniform(-1, 1) * horizontal_axis + aperture_center_x
            self.y = np.random.uniform(-1, 1) * vertical_axis + aperture_center_y
        
        elif (aperture_type == 2):
            NotImplemented

            # while ((self.x**2)/(horizontal_axis**2) + (self.y**2)/(vertical_axis**2)) > 1:
            #     self.x = np.random.uniform(-1, 1) * horizontal_axis + aperture_center_x
            #     self.y = np.random.uniform(-1, 1) * vertical_axis + aperture_center_y
        #     # x_coord_from_center = np.random.uniform(-horizontal_axis, horizontal_axis)
        #     # ymax = (horizontal_axis**2 - self.x**2)**0.5
        #     # y_coord_from_center = np.random.uniform(-ymax, ymax)

        #     # self.x = aperture_center_x + x_coord_from_center
        #     # self.y = aperture_center_y + y_coord_from_center
            
        #     phi = np.random.uniform(0, 2*np.pi)
        #     rho = np.random.random()

        #     self.x = rho * horizontal_axis * np.cos(phi)
        #     self.y = rho * vertical_axis * np.sin(phi)

        #     #TO-DO: FIND EQUIVALENT WAY TO MAP THESE 2 LINES USING PYGAME
        #     self.x = self.x + aperture_center_x
        #     self.y = self.y + aperture_center_y

        #for a square or rectangle
        else:
            self.x = np.random.uniform(-1, 1) * horizontal_axis + aperture_center_x
            self.y = np.random.uniform(-1, 1) * vertical_axis + aperture_center_y

    #set vx2 and vy2 based on a random angle
    def setvx2vy2(self):
        #generate random angle of movement
        theta = np.random.uniform(-np.pi, np.pi)

        #update vx2 and vy2 with the new angle
        self.vx2 = np.cos(theta) * move_distance
        self.vy2 = np.sin(theta) * move_distance  #NOTE: might have to make this negative

    #update x and y coordinates by moving it in x and y coherent directions
    def coherent_direction_update(self):
        self.x += self.vx
        self.y += self.vy
        self.latest_move_x = self.vx
        self.latest_move_y = self.vy

    #update x and y coordinates with random move directions vx2 and vy2
    def incoherent_direction_update(self):
        self.x += self.vx2
        self.y += self.vy2
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
        self.x += self.latest_x_move
        self.y += self.latest_y_move

    def update(self):
        
        if self.update_type == "coherent_direction_update":
            self.coherent_direction_update()
        elif self.update_type == "random_walk_update":
            self.random_walk_update()
        elif self.update_type == "incoherent_direction_update":
            self.incoherent_direction_update()
        elif self.update_type == "reset_location":
            self.reset_location
        else:
            print("error: update_type is invalid")
            exit(1);

        self.life_count += 1

        #TO-DO: check if dot goes out of bounds or if life ended, and update accordingly
        #TO-DO: if life ended, give it new random x and y directions, and update
        #vx, vy, vx2, vy2 if necessary

        if (self.life_ended()):
            dot = self.reset_location()

    	# If it goes out of bounds, do what is necessary (reinsert randomly or reinsert on the opposite edge) based on the parameter chosen
        if (self.out_of_bounds()):
            if (reinsert_type == 1):
                dot = self.reset_location()
            elif (reinsert_type == 2):
                #TO-DO: reinsert on opposite edge
                self.reinsert_on_opposite_edge()

        #update sprite-specific parameter
        self.rect.x = self.x
        self.rect.y = self.y

    # called when dot goes out of bounds and reinsert_type == 2
    def reinsert_on_opposite_edge(self):
        #for a circle or ellipse
        if (aperture_type == 1 or aperture_type == 2):

            phi = None
            pi = np.pi
            if (self.x > aperture_center_x):
                if (self.y > aperture_center_y):
                    # we're in the first quadrant --> move to the fourth
                    phi = np.random.uniform(-pi/2, -pi)
                else:
                    # we're in the fourth quadrant --> move to the second
                    phi = np.random.uniform(pi/2, pi)
            else:
                if (self.y > aperture_center_y):
                    # we're in the second quadrant --> move to the fourth
                    phi = np.random.uniform(0, -pi/2)
                else:
                    # we're in the third quadrant --> move to the first
                    phi = np.random.uniform(0, pi/2)

            # update dot location
            self.x = aperture_center_x + horizontal_axis * np.cos(phi)
            self.y = aperture_center_y + vertical_axis * np.sin(phi)

        #for a square or rectangle
        else:
            random_x_offset = np.random.uniform(0,1)
            random_y_offset = np.random.uniform(0,1)

            if (self.x > aperture_center_x):
                random_x_offset = np.random.uniform(-1, 0)
            if (self.y > aperture_center_y):
                random_y_offset = np.random.uniform(-1,0)

            self.x = random_x_offset * horizontal_axis + aperture_center_x
            self.y = random_y_offset * vertical_axis + aperture_center_y

class cursor(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        # initial cursor position
        self.x, self.y = pygame.mouse.get_pos()

        # cursor image
        self.image = pygame.Surface((2*dot_radius, 2*dot_radius))
        self.image.fill(WHITE)
        pygame.draw.circle(self.image, WHITE, (dot_radius, dot_radius), dot_radius)
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def update(self):
        self.x, self.y = pygame.mouse.get_pos()
        self.rect.x = self.x
        self.rect.y = self.y

    def get_xy_coords(self):
        return self.x, self.y

'''
@@@@@@@@@@@@@@@@@@@@@
MAIN IMPLEMENTATION @
@@@@@@@@@@@@@@@@@@@@@
'''

def main():

    make_data_dir()
    # all_data = []
    #
    # for i in range(n_trials):
    #     all_data.append(keypress_loop(np.random.rand(), np.random.choice([0, 1])))
    #
    # print(all_data)

    pygame.time.delay(1000)

    safe_choice_score = 0
    for i in range(n_trials):
        safe_choice_score = resulaj_test(np.random.choice(coherence_choices), \
            np.random.choice([0,1]), i, safe_choice_score, \
                np.random.uniform(safe_choice_time_bounds[0], safe_choice_time_bounds[1]), False)
        pygame.time.delay(time_between_trials)

    # pygame.time.delay(5)
    # safe_choice_score = 0
    # for i in range(n_trials):
    #     safe_choice_score = safe_choice(np.random.choice(coherence_choices), \
    #         np.random.choice([0,1]), i, safe_choice_score, \
    #             np.random.uniform(safe_choice_time_bounds[0], safe_choice_time_bounds[1]), False)
    #     pygame.time.delay(time_between_trials)

    # pygame.time.delay(5)

    # safe_choice_score = 0
    # for i in range(n_trials):
    #     safe_choice_score = limit_mind_changes(np.random.choice(coherence_choices), \
    #         np.random.choice([0,1]), i, safe_choice_score, \
    #             np.random.uniform(safe_choice_time_bounds[0], safe_choice_time_bounds[1]), False, 3)
    #     pygame.time.delay(time_between_trials)

    pygame.quit()


if __name__=='__main__':
    main()
