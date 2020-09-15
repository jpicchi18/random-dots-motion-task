#!/usr/bin/python3
import sys
import pygame
import numpy as np
import os
import csv
import time

'''
@@@@@@@@@@@@@@@@@@
GLOBAL VARIABLES @
@@@@@@@@@@@@@@@@@@
'''

trial_choices = {"safe_choice": True, "continuing_evidence": False, "longer_stimulus": False, \
    "limit_COM": False}

n_trials = 2                #number of trials

n_dots = 300                #number of dots per set (equivalent to number of dots per
                             #frame)
n_sets = 1                  #number of sets to cycle through per frame
                            #TO-DO: we can probably just delete this ^ parameter
#coherent_direction = 0;   # OBSOLETE: The direction of the coherentDots in degrees
                            #Starts at 3 o'clock and goes counterclockwise (0 ==
                            #90 == upwards, 180 == leftwards, 270 == downwards), range 0 - 360
coherence = 1             #Proportion of dots to move together, range from 0 to 1
dot_radius = 3             #Radius of each dot in pixels
dot_life = 40               # How many frames a dot follows its trajectory before redrawn. -1
                            # is infinite life
move_distance = 3          #How many pixels the dots move per frame
noise_update_type = "incoherent_direction_update"   #how to update noise dots --> options:
                                                    # "incoherent_direction_update"
                                                    # "random_walk_update"
                                                    # "reset_location"

coherence_choices = [0, .032, .064, .128, .256, .512]
time_between_trials = 3 # in seconds
time_between_phases = 10 # in seconds; eg, the time between resulaj control and experiment

'''
safe choice score values = [none, correct, wrong, safe]
safe_choice_time_bounds = [min, max], where the time is selected randomly within that range
'''
safe_choice_scores = [-2, 1, -1, 0]
time_bounds = [5, 8]

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

frames_per_second = 30

directory_name = ""

target_angle = 30 # angle of target relative to vertical

target_persistence_time = 3 # seconds that targets remain displayed after stimulus gets hidden

change_mind_time = 3 # seconds that participant is given to change mind after initial target selection




'''
@@@@@@@@@@@@@@@@@@@@@@@@@
SET UP CANVAS, APERTURE @
@@@@@@@@@@@@@@@@@@@@@@@@@
'''
pygame.init()

# Set task display to be full screen
monitor = pygame.display.Info()
# screen = pygame.display.set_mode((monitor.current_w, monitor.current_h))
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption('RDM Task')
# X,Y coord of screen center = aperture center
x_screen_center = pygame.Rect((0,0),(monitor.current_w, monitor.current_h)).centerx
y_screen_center = pygame.Rect((0,0),(monitor.current_w, monitor.current_h)).centery

# Set our color constants --> NOTE: check background and dot colors
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

dot_color = WHITE         #Color of the dots
background_color = GRAY   #Color of the background
initial_target_color = BLACK
selected_target_color = BLUE
aperture_width = monitor.current_w/4;       #How many pixels wide the aperture is. For square aperture this
                            #will be the both height and width. For circle, this will be
                            #the diameter.
aperture_height = monitor.current_h/3;      #How many pixels high the aperture is. Only relevant for ellipse
                            #and rectangle apertures. For circle and square, this is ignored.
aperture_center_x = x_screen_center      #NOTE: Aperture center is currently equal to center of
                                         #screen
aperture_center_y = y_screen_center      # (in pixels)

cwd = os.getcwd()


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

def draw_text(surface, text, size, x, y, color):
    font_name = pygame.font.match_font('arial')
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, color)
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

# normal resulaj implementation
def resulaj_test_control(coherence, is_right, trial_num, score, time_limit):
    clock = pygame.time.Clock()
    trial_dict = {} # where we will record all data for this trial, including the following...
    dot_positions = {}
    cursor_positions = {}
    waiting_period = False
    stimulus_on = True
    target_selected = 0
    trial_done_time = time_limit + target_persistence_time + time_between_trials # when to leave the function
    experiment_done_time = time_limit + target_persistence_time # when to turn off stimulus and targets
    end_time = 0
    filename = "resulaj_control.csv"

    # set the initial cursor position
    initial_cursor_position = [0.5*monitor.current_w, .8*monitor.current_h]
    pygame.mouse.set_pos(initial_cursor_position)
    pygame.mouse.get_rel()

    # get target parameters
    target_radius = int(.05*monitor.current_w)
    left_target_coords, right_target_coords = get_target_positions(initial_cursor_position[1])

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

        # get current time
        current_time = pygame.time.get_ticks()-start_time

        # check if user closed the window or pressed the "esc" key --> if so, exit the program
        # if user pressed the "n" key --> jump to the wait period before the next trial
        pressed = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: # check if user clicked the red x
                pygame.quit()
                print("early program termination", file = sys.stderr)
                exit(1)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    print("early program termination", file = sys.stderr)
                    exit(1)
                elif event.key == pygame.K_n:
                    experiment_done_time = current_time/1000

        # end the trial if we've passed the post-trial break
        if (current_time > trial_done_time*1000):
            running = False
            break

        # enter the post-trial break if it's time to do so
        if (current_time > experiment_done_time * 1000 and not waiting_period):
            waiting_period = True
            trial_done_time = current_time/1000 + time_between_trials
        
        # turn off stimulus (not targets) if it's time to do so
        if (current_time > time_limit*1000):
            stimulus_on = False

        # turn off stimulus if cursor moved
        if (pygame.mouse.get_rel() != (0,0)):
            if (stimulus_on):
                experiment_done_time = current_time/1000 + target_persistence_time
                stimulus_on = False

        # collect dot and cursor positions if stimulus is off and experiment isn't over yet
        if (not waiting_period and not stimulus_on):
            dot_positions[current_time] = get_dot_positions(dot_array)
            cursor_positions[current_time] = pygame.mouse.get_pos()

        # Update
        screen.fill(background_color)
        if (not waiting_period):
            target_selected = draw_targets(left_target_coords, right_target_coords, target_radius)
            if (target_selected):
                waiting_period = True
                stimulus_on = False
                trial_done_time = current_time/1000 + time_between_trials
                end_time = current_time
            
            if stimulus_on:
                all_sprites.update()
                all_sprites.draw(screen)
            elif (not stimulus_on and not waiting_period):
                display_countdown(int(experiment_done_time - current_time/1000))

         # *after* drawing everything, flip the display
        pygame.display.update()

    trial_str = "Trial " + str(trial_num)
    trial_dict[trial_str] = ""

    trial_dict['coherence'] = str(coherence) # float val of coherence messed up pandas
    trial_dict['dot_positions'] = dot_positions
    trial_dict['cursor_positions'] = cursor_positions
    trial_dict['end_time'] = end_time
    trial_dict['target_selected'] = target_selected
    trial_dict['is_right'] = is_right
    
    if (target_selected == is_right+1):
        trial_dict['is_correct'] = 1
    else:
        trial_dict['is_correct'] = 0

    export_csv(trial_dict, filename)

    # split data for different trials into different csv files?

    return 0

# participant has time after first target selection to change his/her mind
def resulaj_test_experiment(coherence, is_right, trial_num, score, time_limit):
    clock = pygame.time.Clock()
    trial_dict = {} # where we will record all data for this trial, including the following...
    dot_positions = {}
    cursor_positions = {}
    waiting_period = False
    stimulus_on = True
    first_selection = True
    target_selected = 0
    trial_done_time = time_limit + target_persistence_time + time_between_trials # when to leave the function
    experiment_done_time = time_limit + target_persistence_time # when to turn off stimulus and targets
    end_time = 0
    filename = "resulaj_experiment.csv"

    # set the initial cursor position
    initial_cursor_position = [0.5*monitor.current_w, .8*monitor.current_h]
    pygame.mouse.set_pos(initial_cursor_position)
    pygame.mouse.get_rel()

    # get target parameters
    target_radius = int(.05*monitor.current_w)
    left_target_coords, right_target_coords = get_target_positions(initial_cursor_position[1])

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

        # get current time
        current_time = pygame.time.get_ticks()-start_time

        # check if user closed the window or pressed the "esc" key --> if so, exit the program
        # if user pressed the "n" key --> jump to the wait period before the next trial
        pressed = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: # check if user clicked the red x
                pygame.quit()
                print("early program termination", file = sys.stderr)
                exit(1)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    print("early program termination", file = sys.stderr)
                    exit(1)
                elif event.key == pygame.K_n:
                    experiment_done_time = current_time/1000

        # end the trial if we've passed the post-trial break
        if (current_time > trial_done_time*1000):
            running = False
            break

        # enter the post-trial break if it's time to do so
        if (current_time > experiment_done_time * 1000 and not waiting_period):
            waiting_period = True
            trial_done_time = current_time/1000 + time_between_trials
        
        # turn off stimulus (not targets) if it's time to do so
        if (current_time > time_limit*1000):
            stimulus_on = False

        # turn off stimulus if cursor moved
        if (pygame.mouse.get_rel() != (0,0)):
            if (stimulus_on):
                experiment_done_time = current_time/1000 + target_persistence_time
                stimulus_on = False

        # collect dot and cursor positions if stimulus is off and experiment isn't over yet
        if (not waiting_period and not stimulus_on):
            dot_positions[current_time] = get_dot_positions(dot_array)
            cursor_positions[current_time] = pygame.mouse.get_pos()

        # Update
        screen.fill(background_color)
        if (not waiting_period):
            target_selected = draw_targets(left_target_coords, right_target_coords, target_radius)
            if (target_selected):
                stimulus_on = False
                if (first_selection):
                    trial_done_time = current_time/1000 + change_mind_time + time_between_trials
                    experiment_done_time = current_time/1000 + change_mind_time
                    first_selection = False
                end_time = current_time
            
            if stimulus_on:
                all_sprites.update()
                all_sprites.draw(screen)
            elif (not stimulus_on and not waiting_period):
                display_countdown(int(experiment_done_time - current_time/1000))

         # *after* drawing everything, flip the display
        pygame.display.update()

    trial_str = "Trial " + str(trial_num)
    trial_dict[trial_str] = ""

    trial_dict['coherence'] = str(coherence) # float val of coherence messed up pandas
    trial_dict['dot_positions'] = dot_positions
    trial_dict['cursor_positions'] = cursor_positions
    trial_dict['end_time'] = end_time
    trial_dict['target_selected'] = target_selected
    trial_dict['is_right'] = is_right
    
    if (target_selected == is_right+1):
        trial_dict['is_correct'] = 1
    else:
        trial_dict['is_correct'] = 0

    export_csv(trial_dict, filename)

    # split data for different trials into different csv files?

    return 0

def display_countdown(sec_remaining):
    draw_text(screen, str(sec_remaining), 25, monitor.current_w/2, monitor.current_h/10, WHITE)

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
    if not os.path.exists(cwd + "/data"):
        os.mkdir(cwd + "/data")

    while os.path.exists(cwd + "/data/experiment_" + str(experiment_num)):
        experiment_num += 1
    directory_name = cwd + "/data/experiment_" + str(experiment_num) + "/"
    os.mkdir(directory_name)

def initialize_experiment():
    make_data_dir()

def run_resulaj_test():
    score = 0
    for i in range(n_trials):
        safe_choice_score = resulaj_test_control(np.random.choice(coherence_choices), \
            np.random.choice([0,1]), i, score, \
                np.random.uniform(time_bounds[0], time_bounds[1]))

    for i in range(n_trials):
        safe_choice_score = resulaj_test_experiment(np.random.choice(coherence_choices), \
            np.random.choice([0,1]), i, score, \
                np.random.uniform(time_bounds[0], time_bounds[1]))

# calculate positions for the left and right targets
# return 2 lists, first one containing the left coordinates, second one with the right coordinates
def get_target_positions(cursor_start_position):
    # calculate target distance 
    target_dist = cursor_start_position - 0.1*monitor.current_h
    
    # calculate y vals
    height = target_dist*np.cos((np.pi/180) * target_angle)
    y_coord = cursor_start_position - height
    
    # calculate x vals
    x_offset = target_dist*np.sin((np.pi/180) * target_angle)
    left_x = 0.5 * monitor.current_w - x_offset
    right_x = 0.5 * monitor.current_w + x_offset

    return [int(left_x), int(y_coord)], [int(right_x), int(y_coord)]

# return 1 for cursor in left target, 2 for cursor in right target, 0 otherwise
def check_cursor_in_target(left_target_coords, right_target_coords, target_radius):
    x, y = pygame.mouse.get_pos()

    # check if it's in left target
    x_dist_from_left = np.abs(x - left_target_coords[0])
    y_dist_from_left = np.abs(y - left_target_coords[1])
    if ((x_dist_from_left**2 + y_dist_from_left**2)**0.5 <= target_radius):
        return 1

    # check if it's in right target
    x_dist_from_right = np.abs(x - right_target_coords[0])
    y_dist_from_right = np.abs(y - right_target_coords[1])
    if ((x_dist_from_right**2 + y_dist_from_right**2)**0.5 <= target_radius):
        return 2

    return 0

# draw targets for resulaj experiment, returning 1 if a left target is selected, 2 for right target,
# 0 if none selected
def draw_targets(left_target_coords, right_target_coords, target_radius):
    target_selected = check_cursor_in_target(left_target_coords, right_target_coords, target_radius)
    
    if (target_selected == 1):
        pygame.draw.circle(screen, selected_target_color, (left_target_coords[0], left_target_coords[1]), target_radius, 6)
        pygame.draw.circle(screen, initial_target_color, (right_target_coords[0], right_target_coords[1]), target_radius, 6)
        return 1
    elif (target_selected == 2):
        pygame.draw.circle(screen, initial_target_color, (left_target_coords[0], left_target_coords[1]), target_radius, 6)
        pygame.draw.circle(screen, selected_target_color, (right_target_coords[0], right_target_coords[1]), target_radius, 6)
        return 2
    else:
        pygame.draw.circle(screen, initial_target_color, (left_target_coords[0], left_target_coords[1]), target_radius, 6)
        pygame.draw.circle(screen, initial_target_color, (right_target_coords[0], right_target_coords[1]), target_radius, 6)
        return 0

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

        # create random x and y coordinates
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

    # create a new angle to move towards, and update the x and y coordinates based on that angle
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


'''
@@@@@@@@@@@@@@@@@@@@@
MAIN IMPLEMENTATION @
@@@@@@@@@@@@@@@@@@@@@
'''

def main():

    initialize_experiment()
    # all_data = []
    #
    # for i in range(n_trials):
    #     all_data.append(keypress_loop(np.random.rand(), np.random.choice([0, 1])))
    #
    # print(all_data)

    # pygame.time.delay(5)
    # safe_choice_score = 0
    # for i in range(n_trials):
    #     safe_choice_score = safe_choice(np.random.choice(coherence_choices), \
    #         np.random.choice([0,1]), i, safe_choice_score, \
    #             np.random.uniform(safe_choice_time_bounds[0], safe_choice_time_bounds[1]), False)
    #     pygame.time.delay(time_between_trials)

    run_resulaj_test()
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
