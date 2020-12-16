# LITERATURE VALUES:
# diameter of aperture = 10-14 degrees
# density = ~16.7 dots/(degree)^2/sec
# frequency (1/(time between frames)) = 75 Hz
# target = .8 deg diameter 10 deg from 

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

n_trials = 50
dot_density = 16.7      # measured in dots/(degree^2 * sec)
n_sets = 1 # each contains n_dots dots. cycle between them in round-robin fashion. for n_sets=2, set 1 in frame 1, set 2 in frame 2, set 1 in frame 3, etc.

coherence = .2             #Proportion of dots to move together, range from 0 to 1
dot_radius = 2             #Radius of each dot in pixels
dot_life = 20               # How many frames a dot follows its trajectory before redrawn. -1
                            # is infinite life
dot_speed = 7.1     # in visual degrees per second
noise_update_type = "reset_location"   #how to update noise dots --> options:
                                                    # "incoherent_direction_update"
                                                    # "random_walk_update"
                                                    # "reset_location"
dot_labels_fixed = False                                

coherence_choices = [0, .016, .032, .064, .128, .256]
time_between_trials = [0.7, 1.0] # time bounds, in seconds
time_between_phases = 10 # in seconds; eg, the time between resulaj control and experiment

'''
safe choice score values = [none, correct, wrong, safe]
safe_choice_time_bounds = [min, max], where the time is selected randomly within that range
'''
safe_choice_scores = [-2, 1, -1, 0]
trial_time = [20, 20]     # time length of a trial, where time is chosen randomly and uniformly between these these bounds

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
dist_of_eye_to_screen_cm = 43   # distance from the human eye to the stimulus, measured in in cm
aperture_radius = 7    # aperture radius in visual angles

frames_per_second = 75

directory_name = ""

target_angle = 28 # angle of target relative to vertical

target_persistence_time = 1 # seconds that targets remain displayed after stimulus gets hidden

change_mind_time = 3 # seconds that participant is given to change mind after initial target selection

target_radius = 1.5 # in cm

target_dist_from_start = 20 # in cm


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
background_color = BLACK   #Color of the background
initial_target_color = BLACK
selected_target_color = BLUE

aperture_center_x = x_screen_center      #NOTE: Aperture center is currently equal to center of
                                         #screen
aperture_center_y = y_screen_center      # (in pixels)

cwd = os.getcwd()

target_radius = int(target_radius * 37.8)

cursor_start_position = [0.5*monitor.current_w, .9*monitor.current_h]


'''
@@@@@@@@@@@@@@@@@@@@@@
FUNCTION DEFINITIONS @
@@@@@@@@@@@@@@@@@@@@@@
'''

#calculates number of dots in the field based on the radius of aperture and dot density
def find_ndots(visual_angle, density):
    radius = angle_to_pixel_radius(visual_angle)
    return np.rint(density*np.pi*radius*radius)

#converts visual angle into aperture radius in pixels
def angle_to_pixelRadius(visualangle, distanceFromScreen):
    radius = np.tan((visualangle * 3.14 / 180)/2) * distanceFromScreen
    return radius * 37.8

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
def init_aperture_param(aperture_width, aperture_height):
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
def resulaj_test(coherence, is_right, trial_num, time_between_trials):
    clock = pygame.time.Clock()
    trial_dict = {} # where we will record all data for this trial, including the following...
    dot_positions = {}
    cursor_positions = {}
    waiting_period = False
    stimulus_on = True
    target_selected = 0
    time_limit = np.random.uniform(trial_time[0], trial_time[1])
    trial_done_time = time_limit + target_persistence_time + time_between_trials # when to leave the function
    experiment_done_time = time_limit + target_persistence_time # when to turn off stimulus and targets
    end_time = 0
    filename = "resulaj.csv"

    # set the initial cursor position
    pygame.mouse.set_pos(cursor_start_position)
    pygame.mouse.get_rel()

    # get target parameters
    left_target_coords, right_target_coords = get_target_positions(cursor_start_position[1])

    #calculate the number of coherent and incoherent dots
    n_coherent_dots = n_dots * coherence
    n_incoherent_dots = n_dots - n_coherent_dots

    coherent_direction = 0
    if not is_right:
        coherent_direction = 180

    # create and group together all sprites
    dot_sets = set_of_dot_sets(coherent_direction)

    # Game loop
    running = True
    start_time = pygame.time.get_ticks() # in milliseconds
    while running:

        # keep apropriate loop speed
        clock.tick(frames_per_second)

        # get current time
        current_time = pygame.time.get_ticks()-start_time

        # check if user closed the window or pressed the "esc" key --> if so, exit the program
        # if user pressed the "n" key --> jump to the wait period before the next trial
        pressed = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: # check if user clicked the red x
                pygame.quit()
                print("user-initiated program termination", file = sys.stderr)
                exit(1)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    print("user-initiated program termination", file = sys.stderr)
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
            dot_positions[current_time] = dot_sets.get_dot_positions()
            cursor_positions[current_time] = pygame.mouse.get_pos()

        # Update
        screen.fill(background_color)
        if (not waiting_period):
            target_selected = draw_targets(left_target_coords, right_target_coords)
            if (target_selected):
                waiting_period = True
                stimulus_on = False
                trial_done_time = current_time/1000 + time_between_trials
                end_time = current_time
            
            if stimulus_on:
                dot_sets.update()
                dot_sets.draw()
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
def resulaj_test_experiment(coherence, is_right, trial_num, time_limit, time_between_trials):
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
    initial_cursor_position = [0.5*monitor.current_w, .9*monitor.current_h]
    pygame.mouse.set_pos(initial_cursor_position)
    pygame.mouse.get_rel()

    # get target parameters
    left_target_coords, right_target_coords = get_target_positions(initial_cursor_position[1])

    #calculate the number of coherent and incoherent dots
    n_coherent_dots = n_dots * coherence
    n_incoherent_dots = n_dots - n_coherent_dots

    coherent_direction = 0
    if not is_right:
        coherent_direction = 180

    # create and group together all sprites
    dot_set = dot_set(coherent_direction)

    # Game loop
    running = True
    start_time = pygame.time.get_ticks() # in milliseconds
    while running:

        # keep apropriate loop speed
        clock.tick(frames_per_second)

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
            dot_positions[current_time] = dot_set.get_dot_positions()
            cursor_positions[current_time] = pygame.mouse.get_pos()

        # Update
        screen.fill(background_color)
        if (not waiting_period):
            target_selected = draw_targets(left_target_coords, right_target_coords)
            if (target_selected):
                stimulus_on = False
                if (first_selection):
                    trial_done_time = current_time/1000 + change_mind_time + time_between_trials
                    experiment_done_time = current_time/1000 + change_mind_time
                    first_selection = False
                end_time = current_time
            
            if stimulus_on:
                dot_set.update()
                dot_set.draw()
            elif (not stimulus_on and not waiting_period):
                display_countdown(int(experiment_done_time*1000 - current_time))

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

def display_countdown(msec_remaining):
    msec_remaining = int(np.ceil(msec_remaining / 100) * 100)
    draw_text(screen, str(msec_remaining), 25, monitor.current_w/2, monitor.current_h/10, WHITE)

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
    for i in range(n_trials):
        resulaj_test(np.random.choice(coherence_choices), \
            np.random.choice([0,1]), i, \
                    np.random.uniform(time_between_trials[0], time_between_trials[1]))

    # for i in range(n_trials):
    #     safe_choice_score = resulaj_test_experiment(np.random.choice(coherence_choices), \
    #         np.random.choice([0,1]), i, score, \
    #             np.random.uniform(time_bounds[0], time_bounds[1]))

# calculate positions for the left and right targets
# return 2 lists, first one containing the left coordinates, second one with the right coordinates
def get_target_positions(cursor_start_position):
    # calculate target distance --> 20 cm from start position
    target_dist = target_dist_from_start * 38.7
    
    # calculate y vals
    height = target_dist*np.cos((np.pi/180) * target_angle)
    y_coord = cursor_start_position - height
    
    # calculate x vals
    x_offset = target_dist*np.sin((np.pi/180) * target_angle)
    left_x = 0.5 * monitor.current_w - x_offset
    right_x = 0.5 * monitor.current_w + x_offset

    return [int(left_x), int(y_coord)], [int(right_x), int(y_coord)]

# return 1 for cursor in left target, 2 for cursor in right target, 0 otherwise
def check_cursor_in_target(left_target_coords, right_target_coords):
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
def draw_targets(left_target_coords, right_target_coords):
    target_selected = check_cursor_in_target(left_target_coords, right_target_coords)
    
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

#check if cursor in start circle, return 1 if so and zero else
def check_cursor_in_start(start_coords):
    x, y = pygame.mouse.get_pos()

    # check if it's in start
    x_dist_from_start = np.abs(x - start_coords[0])
    y_dist_from_start = np.abs(y - start_coords[1])
    if ((x_dist_from_start**2 + y_dist_from_start**2)**0.5 <= start_radius):
        return 1
    return 0

def draw_start(start_coords):
    start_selected= check_cursor_in_start(start_coords)
    if (start_selected==1):
        pygame.draw.circle(screen, selected_start_color, (start_coords[0], start_coords[1]), start_radius*37.8, 6)
        return 1
    else :
        pygame.draw.circle(screen, start_color, (start_coords[0], start_coords[1]), start_radius*37.8, 6)
        return 0

def visual_degrees_to_pixels(visual_degrees):
    return int(dist_of_eye_to_screen_cm * np.tan(visual_degrees * np.pi/180) * 37.795)

def angles_per_second_to_pixels_per_second(dot_speed):
    return dot_speed * (n_sets/frames_per_second) * (visual_degrees_to_pixels(dot_speed)/dot_speed)

# only works for circular apertures!!
def density_to_ndots(density, aperture_width_in_pixels):
   new_density = density * (1/(visual_degrees_to_pixels(1)**2))
   total_n_dots = new_density * (np.pi * (aperture_width_in_pixels/2)**2)
   dots_per_frame = total_n_dots/frames_per_second
   return int(dots_per_frame)

'''
@@@@@@@@@@@@@@@@@@@@@@@
MORE GLOBAL VARIABLES @
@@@@@@@@@@@@@@@@@@@@@@@
'''

# aperture_height gets ignored if circular aperture shape is selected
aperture_width = aperture_height = 2*visual_degrees_to_pixels(aperture_radius)

#initialize aperture parameters --> horizontal = vertical because we are using a circle
aperture_axis = init_aperture_param(aperture_width, aperture_height)
horizontal_axis = aperture_axis[0]
vertical_axis = aperture_axis[1]
#  Was going to use to update portion of screen but dont see an increase in performance/ decrease in time
# aperture_section = pygame.Rect((aperture_center_x - horizontal_axis, aperture_center_y - vertical_axis),(aperture_width,aperture_height))

move_distance = angles_per_second_to_pixels_per_second(dot_speed)   # How many pixels the dots move per frame

n_dots = density_to_ndots(dot_density, aperture_width)      # number of dots per set

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
            self.reset_location()
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

class dot_set:
    def __init__(self, coherent_direction):
        self.set = []
        self.sprite_group = pygame.sprite.Group()

        n_coherent_dots = n_dots * coherence
        n_incoherent_dots = n_dots - n_coherent_dots

        for i in range(n_dots):
            new_dot = dot(coherent_direction)

            if i < n_coherent_dots:
                new_dot.update_type = "coherent_direction_update"  #make it a coherent dot
            else:
                new_dot.update_type = noise_update_type  #make it a random dot

            self.set.append(new_dot)
            self.sprite_group.add(new_dot)
    
    def update(self):
        # change the noise/coherent designation if labels are not fixed
        if not dot_labels_fixed:
            for dot in self.set:
                if (np.random.uniform() <= coherence):
                    dot.update_type = "coherent_direction_update"
                else:
                    dot.update_type = noise_update_type

        # update dot locations
        self.sprite_group.update()
    
    # returns an array of dot positions coordinates (x, y)
    def get_dot_positions(self):
        return get_dot_positions(self.set)

    def draw(self):
        self.sprite_group.draw(screen)

class set_of_dot_sets:
    def __init__(self, coherent_direction):
        self.set_of_dot_sets = []

        for i in range(n_sets):
            new_dot_set = dot_set(coherent_direction)
            self.set_of_dot_sets.append(new_dot_set)

        self.current_set_index = 0

    def update(self):
        # cycle to the next set
        self.current_set_index += 1
        if (self.current_set_index >= len(self.set_of_dot_sets)):
            self.current_set_index = 0
        
        self.set_of_dot_sets[self.current_set_index].update()
    
    def get_dot_positions(self):
        return self.set_of_dot_sets[self.current_set_index].get_dot_positions()
    
    def draw(self):
        # draw all dot sets
        self.set_of_dot_sets[self.current_set_index].draw()


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
