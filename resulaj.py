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

n_trials = 1000
dot_density = 16.7      # measured in dots/(degree^2 * sec)
n_sets = 1 # each contains n_dots dots. cycle between them in round-robin fashion. for n_sets=2, set 1 in frame 1, set 2 in frame 2, set 1 in frame 3, etc.

dot_radius = 2              # Radius of each dot in pixels
dot_life = 20               # How many frames a dot follows its trajectory before redrawn. -1
                            # is infinite life
dot_speed = 7.1     # in visual degrees per second
noise_update_type = "reset_location"   #how to update noise dots --> options:
                                                    # "incoherent_direction_update"
                                                    # "random_walk_update"
                                                    # "reset_location"

dot_labels_fixed = False  # can coherent dots be reassigned as noise dots, and vice versa?

coherence_choices = [0, .016, .032, .064, .128, .256, .512]

risk_options = [0, 4, 5, 7, 8]

# trial timing parameters:
time_targets_only = [700, 1000] # in msec. from literature "before stimulus appears, targets displayed for some time in exponential distribution with mean 0.82s and range 0.7-1.0s"
time_stimulus_max = 2000 # in msec. from literature: "participants could view for as long as needed up to 2.0s"
time_movement = [300, 700] # in msec. from literature: "movement duration (time between leaving home position and selecting a target) required to be 500+/-200ms"
time_intertrial = 1000 # in msec
time_target_feedback = 200 # in msec, the length of time that correct/incorrect target choices are displayed
time_risk_displayed = 2000 # in msec


'''
safe choice score values = [none, correct, wrong, safe]
safe_choice_time_bounds = [min, max], where the time is selected randomly within that range
'''
safe_choice_scores = [-2, 1, -1, 0]

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

# target parameters
target_radius = 1.5 # in cm
target_dist_from_start = 20 # in cm
target_angle = 28 # angle of target relative to vertical


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
GREEN = (0,128,0)

dot_color = WHITE         #Color of the dots
background_color = GRAY   #Color of the background
initial_target_color = BLACK
selected_target_color = BLUE
correct_target_color = GREEN
incorrect_target_color = RED

aperture_center_x = x_screen_center      #NOTE: Aperture center is currently equal to center of
                                         #screen
aperture_center_y = y_screen_center      # (in pixels)

cwd = os.getcwd()

cursor_start_position = [0.5*monitor.current_w, .9*monitor.current_h]

start_color = BLUE
start_radius = 1
selected_start_color = BLUE


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

#check if cursor in start circle, return 1 if so and zero else
def check_cursor_in_start():
    x, y = pygame.mouse.get_pos()

    # check if it's in start
    x_dist_from_start = np.abs(x - cursor_start_position[0])
    y_dist_from_start = np.abs(y - cursor_start_position[1])
    if ((x_dist_from_start**2 + y_dist_from_start**2)**0.5 <= start_radius*37.8):
        return 1
    return 0

def draw_start():
    screen.fill(background_color)
    start_selected = check_cursor_in_start()
    if (start_selected==1):
        pygame.draw.circle(screen, selected_start_color, (cursor_start_position[0], cursor_start_position[1]), start_radius*37.8, 6)
        return 1
    else :
        pygame.draw.circle(screen, start_color, (cursor_start_position[0], cursor_start_position[1]), start_radius*37.8, 6)
        return 0

    pygame.display.update()

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

def cm_to_pixels(cm_value):
    return int(37.795*cm_value)
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
target_radius = cm_to_pixels(target_radius)

'''
@@@@@@@@@@@@@@@@@@@
CLASS DEFINITIONS @
@@@@@@@@@@@@@@@@@@@
'''

class cursor_follower(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)


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
        self.life_count = np.floor(np.random.randint(0, dot_life))    #counter for dot's life
        self.update_type = ""                           #string to determine how dot gets updated

        # create random x and y coordinates
        self.reset_location()
        self.setvx2vy2()

        #set sprite-specific parameters
        self.image = pygame.Surface((2*dot_radius, 2*dot_radius))
        self.image.fill(background_color)
        pygame.draw.circle(self.image, dot_color, (dot_radius, dot_radius), dot_radius)
        self.rect = self.image.get_rect(center=(self.x, self.y)) # Rect determines position the dot is drawn

    # decrement life count, and reset location if dot life ended
    def life_check(self):
        
        self.life_count -= 1
        
        #If we want infinite dot life
        if (dot_life < 0):
            self.life_count = 0; #resetting to zero to save memory. Otherwise it might increment to huge numbers.
        
        # Else if the dot's life has reached its end
        elif (self.life_count < 0):
            self.life_count = dot_life
            self.reset_location()

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

        #TO-DO: check if dot goes out of bounds or if life ended, and update accordingly
        #TO-DO: if life ended, give it new random x and y directions, and update
        #vx, vy, vx2, vy2 if necessary

        self.life_check()

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
    def __init__(self, coherence, coherent_direction):
        self.set = []
        self.sprite_group = pygame.sprite.Group()
        self.coherence = coherence

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
                if (np.random.uniform() <= self.coherence):
                    dot.update_type = "coherent_direction_update"
                else:
                    dot.update_type = noise_update_type

        # update dot locations
        self.sprite_group.update()
    
    # returns an array of dot positions coordinates (x, y)
    def get_dot_positions(self):
        dot_positions = []
        for dot in self.set:
            dot_positions.append((dot.x, dot.y))
        
        return dot_positions

    def draw(self):
        self.sprite_group.draw(screen)

class set_of_dot_sets:
    def __init__(self, coherence, coherent_direction):
        self.set_of_dot_sets = []

        for i in range(n_sets):
            new_dot_set = dot_set(coherence, coherent_direction)
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

class resulaj:
    def __init__(self):
        self.directory_name = ""
        self.make_data_dir()
        self.clock = None
        self.left_target_coords, self.right_target_coords = self.get_target_positions()
        self.is_right = 1

        # data collection parameters
        self.start_time = 0
        self.stimulus_start_time = 0
        self.stimulus_end_time = 0
        self.movement_end_time = 0
        self.feedback_end_time = 0
        self.trial_end_time = 0

        # trial-specific parameters
        self.intertrial_period_over = False
        self.stimulus_over = False
        self.movement_over = False
        self.intertrial_period_over_event = pygame.USEREVENT + 1
        self.stimulus_over_event = pygame.USEREVENT + 2
        self.movement_over_event = pygame.USEREVENT + 3

    def make_data_dir(self):
        experiment_num = 0
        
        # create parent "data" directory, if needed
        if not os.path.exists(cwd + "/data"):
            os.mkdir(cwd + "/data")

        while os.path.exists(cwd + "/data/experiment_" + str(experiment_num)):
            experiment_num += 1
        self.directory_name = cwd + "/data/experiment_" + str(experiment_num)
        os.mkdir(self.directory_name)

    # run however many resulaj_trials we want
    def run(self):
        for i in range(n_trials):
            self.resulaj_trial(i)
    
    def resulaj_trial(self, trial_num):
        # prepare variables for the trial`
        self.initialize_member_variables()
        get_rel_bool = False
        coherence = np.random.choice(coherence_choices)
        target_selected = 0
        trial_dict = {} # where we will record all data for this trial, including the following...
        dot_positions = {}
        cursor_positions = {}
        filename = "resulaj_" + str(trial_num) + ".csv"

        # decide on the coherent direction
        coherent_direction = 0
        if not self.is_right:
            coherent_direction = 180

        # create and group together all sprites
        dot_sets = set_of_dot_sets(coherence, coherent_direction)

        # before stimulus appears, targets are displayed for some time
        self.display_risk_phase()
        self.only_targets_phase()
        self.stimulus_start_time = self.current_time()

        # set the initial cursor position again
        pygame.mouse.set_pos(cursor_start_position)
        pygame.mouse.get_rel()
        
        # schedule when the stimulus should stop
        pygame.time.set_timer(self.stimulus_over_event, time_stimulus_max, True)

        while not self.intertrial_period_over:
            # keep apropriate loop speed
            self.clock.tick(frames_per_second)

            # check for early program termination or if the stimulus should stop due to time limits
            self.check_events()

            # turn off stimulus if cursor moved and set time limit to select a target
            if (pygame.mouse.get_rel() != (0,0) and get_rel_bool):
                # turn off stimulus
                pygame.time.set_timer(self.stimulus_over_event, 1, True)
            get_rel_bool = True
            
            # collect dot and cursor positions if stimulus is on, else collect cursor positions while movement phase is active
            if (not self.stimulus_over):
                dot_positions[self.current_time()] = dot_sets.get_dot_positions()
            elif (self.stimulus_over and not self.movement_over):
                cursor_positions[self.current_time()] = pygame.mouse.get_pos()

            # Update
            screen.fill(background_color)
            if (not self.intertrial_period_over):
                target_selected = self.draw_targets()
                if (target_selected):
                    pygame.time.set_timer(self.movement_over_event, 1, True)
                
                if not self.stimulus_over:
                    dot_sets.update()
                    dot_sets.draw()

            # *after* drawing everything, flip the display
            pygame.display.update()

        # rate confidence
        self.rate_confidence_phase()

        trial_str = "Trial " + str(trial_num)
        trial_dict[trial_str] = ""

        trial_dict['left_target_coord'] = self.left_target_coords
        trial_dict['right_target_coord'] = self.right_target_coords
        trial_dict['cursor_start_position'] = cursor_start_position
        trial_dict['coherence'] = str(coherence) # float val of coherence messed up pandas
        trial_dict['dot_positions'] = dot_positions
        trial_dict['cursor_positions'] = cursor_positions
        trial_dict['target_selected'] = target_selected
        trial_dict['is_right'] = self.is_right
        trial_dict['start_time'] = self.start_time
        trial_dict['stimulus_start_time'] = self.stimulus_start_time
        trial_dict['stimulus_end_time'] = self.stimulus_end_time
        trial_dict['movement_end_time'] = self.movement_end_time
        trial_dict['feedback_end_time'] = self.feedback_end_time
        trial_dict['trial_end_time'] = self.trial_end_time

        if (target_selected == self.is_right+1):
            trial_dict['is_correct'] = 1
        else:
            trial_dict['is_correct'] = 0

        self.export_csv(trial_dict, filename)

    # exit the program if user closed the window or pressed the "esc" key, or if the stimulus should stop
    def check_events(self):
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
            elif event.type == self.stimulus_over_event and not self.stimulus_over:
                self.stimulus_over = True
                self.stimulus_end_time = self.current_time()
                pygame.time.set_timer(self.movement_over_event, time_movement[1], True)
            elif event.type == self.movement_over_event and not self.movement_over:
                self.movement_over = True
                self.movement_end_time = self.current_time()
                self.target_feedback()
                self.feedback_end_time = self.current_time()
                # perform the intertrial period
                self.intertrial_period()
                self.intertrial_period_over = True
                self.trial_end_time = self.current_time()

    # calculate positions for the left and right targets
    # return 2 lists, first one containing the left coordinates, second one with the right coordinates
    def get_target_positions(self):
        # calculate target distance --> 20 cm from start position
        target_dist = target_dist_from_start * 38.7
    
        # calculate y vals
        height = target_dist*np.cos((np.pi/180) * target_angle)
        y_coord = cursor_start_position[1] - height

        if (cursor_start_position[1] - height - target_radius) < 0:
            y_coord = 0.15 * monitor.current_h
    
        # calculate x vals
        x_offset = target_dist*np.sin((np.pi/180) * target_angle)
        left_x = 0.5 * monitor.current_w - x_offset
        right_x = 0.5 * monitor.current_w + x_offset

        return [int(left_x), int(y_coord)], [int(right_x), int(y_coord)]

    # draw targets for resulaj experiment, returning 1 if a left target is selected, 2 for right target, 0 if none selected
    def draw_targets(self):
        target_selected = self.check_cursor_in_target()
        
        # choose colors for left and right targets
        left_color = initial_target_color
        right_color = initial_target_color
        if self.movement_over and self.is_right:
            left_color = incorrect_target_color
            right_color = correct_target_color
        elif self.movement_over and not self.is_right:
            left_color = correct_target_color
            right_color = incorrect_target_color
        
        # draw targets:
        pygame.draw.circle(screen, left_color, (self.left_target_coords[0], self.left_target_coords[1]), \
            target_radius, 6)
        pygame.draw.circle(screen, right_color, (self.right_target_coords[0], self.right_target_coords[1]), \
            target_radius, 6)
        
        # return values:
        if (target_selected == 1):
            return 1
        elif (target_selected == 2):
            return 2
        else:
            return 0

    # return 1 for cursor in left target, 2 for cursor in right target, 0 otherwise
    def check_cursor_in_target(self):
        x, y = pygame.mouse.get_pos()

        # check if it's in left target
        x_dist_from_left = np.abs(x - self.left_target_coords[0])
        y_dist_from_left = np.abs(y - self.left_target_coords[1])
        if ((x_dist_from_left**2 + y_dist_from_left**2)**0.5 <= target_radius):
            return 1

        # check if it's in right target
        x_dist_from_right = np.abs(x - self.right_target_coords[0])
        y_dist_from_right = np.abs(y - self.right_target_coords[1])
        if ((x_dist_from_right**2 + y_dist_from_right**2)**0.5 <= target_radius):
            return 2

        return 0

    def display_countdown(self, msec_remaining):
        msec_remaining = int(np.ceil(msec_remaining / 100) * 100)
        draw_text(screen, str(msec_remaining), 25, monitor.current_w/2, monitor.current_h/10, WHITE)

    def export_csv(self, result_dict, filename):
    
        # Can adjust later to a customized file name
        file_path = os.path.join(self.directory_name, filename)
        if os.path.exists(file_path):
            with open(file_path, 'a') as f:
                w = csv.writer(f)
                w.writerows(result_dict.items())
        else:
            with open(file_path, 'w') as f:
                w = csv.writer(f)
                w.writerows(result_dict.items())

    # only display the targets and nothing else for a certain period of time
    def only_targets_phase(self):
        # set the initial cursor position
        pygame.mouse.set_pos(cursor_start_position)
        
        # display only the targets
        screen.fill(background_color)
        self.draw_targets()
        pygame.display.update()

        # wait for this period to end
        tm_targets_only = np.random.randint(time_targets_only[0], time_targets_only[1])
        pygame.time.wait(tm_targets_only)
 
    # state the risk value for this trial. keep it displayed for "time_risk_displayed" msecs
    def display_risk_phase(self):
        # display only the targets
        screen.fill(background_color)
        draw_text(screen, "risk value: " + str(np.random.choice(risk_options)), 40, monitor.current_w/2, monitor.current_h/2, WHITE)
        pygame.display.update()
        pygame.time.wait(time_risk_displayed)

    def rate_confidence_phase(self):
        line_height = monitor.current_h/2
        left_endpoint = monitor.current_w*0.15
        right_endpoint = monitor.current_w*0.85
        line_width = right_endpoint - left_endpoint
        confidence = 0

        while True:
            self.clock.tick(frames_per_second * 2)

            # check for exit command
            for event in pygame.event.get():
                if event.type == pygame.QUIT: # check if user clicked the red x
                    pygame.quit()
                    print("user-initiated program termination", file = sys.stderr)
                    exit(1)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        return(confidence)

            # get mouse position
            x, y = pygame.mouse.get_pos()
            if (x < left_endpoint):
                x = left_endpoint
            elif (x > right_endpoint):
                x = right_endpoint
            original_x = x

            # calculate confidence value
            confidence = round( (x - left_endpoint)/line_width * 100 )

            # draw out everything
            screen.fill(background_color)
            draw_text(screen, "click spacebar when finished selecting confidence", 25, monitor.current_w/2, 9*monitor.current_h/10, WHITE)
            draw_text(screen, "confidence selection: " + str(confidence), 25, monitor.current_w/2, monitor.current_h/8, WHITE)
            pygame.draw.line(screen, WHITE, (left_endpoint, line_height), (right_endpoint, line_height))
            pygame.draw.circle(screen, WHITE, (original_x, line_height), 20)
            pygame.display.update()
        

    def target_feedback(self):
        screen.fill(background_color)
        self.draw_targets()
        pygame.display.update()

        pygame.time.wait(time_target_feedback)

    def intertrial_period(self):
        screen.fill(background_color)
        pygame.display.update()
        pygame.time.wait(time_intertrial)

    def cancel_scheduled_events(self):
        pygame.time.set_timer(self.intertrial_period_over_event, 0)
        pygame.time.set_timer(self.stimulus_over_event, 0)
        pygame.time.set_timer(self.movement_over_event, 0)

    def initialize_member_variables(self):
        self.clock = pygame.time.Clock()
        self.is_right = np.random.choice([0,1])

        self.stimulus_over = False
        self.movement_over = False
        self.intertrial_period_over = False

        self.stimulus_start_time = 0
        self.stimulus_end_time = 0
        self.movement_end_time = 0
        self.feedback_end_time = 0
        self.trial_end_time = 0

        # clear the event queue to prepare for the trial
        self.cancel_scheduled_events()
        pygame.event.clear()

        # set the start time
        self.start_time = pygame.time.get_ticks() # in milliseconds

    def current_time(self):
        return pygame.time.get_ticks()-self.start_time

'''
@@@@@@@@@@@@@@@@@@@@@
MAIN IMPLEMENTATION @
@@@@@@@@@@@@@@@@@@@@@
'''

def main():

    test_driver = resulaj()
    test_driver.run()

    pygame.quit()


if __name__=='__main__':
    main()
