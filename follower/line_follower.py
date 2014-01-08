"""Logic for line follower."""

import sys
from time import time

import lib.lib as lib
import hardware.ir_hub as ir_hub_mod
import driver.mec_driver as mec_driver_mod
import lib.exceptions as ex
import follower
import pid as pid_mod

class LineFollower(follower.Follower):

    """Follow a line. Subclass for specific hardware/methods."""

    def __init__(self):
        """Build IR arrays, logger and driver"""
        super(LineFollower, self).__init__()
        self.front_pid = pid_mod.PID()
        self.back_pid = pid_mod.PID()

    def follow(self, state_table):
        """Used to update the motors speed and angler moation."""
        self.state_table = state_table
        # Get the intial condetion
        previous_time = time()
        # Init front_pid
        self.front_pid.set_k_values(1, 0, 0)
        # Inti back_pid
        self.back_pid.set_k_values(1, 0, 0)
        # Get current Heading
        self.heading = self.state_table.currentHeading
        # Continue untill an error condition
        while(1)
            # Assign the current states to the correct heading
            self.assign_states()
            # Check for error conditions        
            if(!(self.error == 0)):
                self.modify_run_state()
                return
            # Get the current time of the cpu
            current_time = time()
            # Call front PID
            self.sampling_time = current_time - previous_time
            # Call front PID
            front_error = self.front_pid.pid(0, self.front_state, self.sampling_time)
            # Call back PID
            back_error = self.back_pid.pid(0, self.back_state, self.sampling_time)
            # Update motors
            self.motors(front_error, back_error)
            # Take the current time set it equal to the privious time
            previous_time = current_time
       
        
    def modify_run_state(self):
        pass

    def motors(self, front_error, back_error):
        """Used to Update the motors speed and angler moation."""
        # Calculate translate_speed
        # MAX speed - error in the front sensor / total number
        # of states
        translate_speed =  100 - ( front_error / 16 )
        # Calculate rotate_speed
        # Max speed - Translate speed
        rotate_speed = 100 - translate_speed
        # Calculate translate_angle
        translate_angle = back_error * (180 / 16);
        if( translate_angle < 0 ):
            # Swift to the left
            translate_angle = 360 - translate_angle
        else:
            # swift to the right
            translate_angle = translate_angle   
        if( translate_speed > 100 ):
            # If translate_speed is greater than 100 set to 100
            translate_speed = 100
        elif( translate_speed < 0 ):
            # If translate_speed is greater than 100 set to 100
            translate_speed = 0
        if( rotate_speed > 100 ):
            # If rotate_speed is greater than 100 set to 100
            rotate_speed = 100
        elif( rotate_speed < 0 ):
            # If rotate_speed is greater than 100 set to 100
            rotate_speed = 0
        # Adjust motor speeds 
        mec_driver_mod.compound_move(translate_speed, translate_angle, rotate_speed)

    def assign_states(self):
        """Take 4x16 bit arrays and assigns the array to proper orientations.

        Note that the 'proper orientaitons are front, back, left and right.

        """
        # Get the current IR reaidngs
        current_ir_reading = self.ir_hub.read_all_arrays()
        # Heading west
        if self.heading == 0:
            # Forward is on the left side
            self.front_state = self.get_position_lr(
                current_ir_reading["left"])
            # Back is on the right side
            self.back_state = self.get_position_rl(
                current_ir_reading["right"])
            # Left is on the back
            self.left_state = self.get_position_lr(
                current_ir_reading["back"])
            # Right is on the fornt
            self.right_state = self.get_position_rl(
                current_ir_reading["front"])
        # Heading east
        elif self.heading == 180:
            # Forward is on the right side
            self.front_state = self.get_position_lr(
                current_ir_reading["right"])
            # Back is on the left side
            self.back_state = self.get_position_rl(
                current_ir_reading["left"])
            # Left is on the front
            self.left_state = self.get_position_lr(
                current_ir_reading["front"])
            # Right is on the back
            self.right_state = self.get_position_rl(
                current_ir_reading["back"])
        # Heading south
        elif self.heading == 270:
            # Forward is on the front side
            self.front_state = self.get_position_lr(
                current_ir_reading["front"])
            # Back is on the back side
            self.back_state = self.get_position_rl(
                current_ir_reading["back"])
            # Left is on the left
            self.left_state = self.get_position_lr(
                current_ir_reading["left"])
            # right is on the right
            self.right_state = self.get_position_rl(
                current_ir_reading["right"])
            # Heading nouth
        elif self.heading == 90:
            # Forward is on the right side
            self.front_state = self.get_position_lr(
                current_ir_reading["back"])
            # Back is on the left side
            self.back_state = self.get_position_rl(
                current_ir_reading["front"])
            # Left is on the front
            self.left_state = self.get_position_lr(
                current_ir_reading["right"])
            # Right is on the back
            self.right_state = self.get_position_rl(
                current_ir_reading["left"])
            if(!(self.left_state < 16) || !(self.right_state < 16)):
                self.error = -1
            if(!(self.front_state < 16)):
                if(self.front_state == 16):
                    # Front lost line
                    self.error = 1
                elif(self.front_state == 17):
                    self.error = 2
                elif(self.front_state == 18):
                    self.error = 3
                elif(self.front_state == 19):
                    self.error = 4
            else:
                self.error = 0;
            if(!(self.back_state < 16):
                if(self.back_state == 16):
                    # Back lost line
                    self.error = 5
                elif(self.back_state == 17):
                    self.error = 6
                elif(self.back_state == 18):
                    self.error = 7
                elif(self.back_state == 19):
                    self.error = 8
            else:
                self.error = 0;
            if(!(self.front_state < 16) && !(self.back_state < 16)):
                if((self.front_state == 16) && (self.front_state == 16)):
                    # line losted
                    self.error = 9
                else
                    # Intersection found
                    self.error = 10
            else:
                self.error = 0

    def get_position_lr(self, readings):
        """Reading the IR sensors from left to right
        
        Calculates the currrent state in refarencs to center from 
        left to right. States go form -15 to 15.
        """
        self.hit_position = []
        state = 0.0
        for index, value in enumerate(readings):
            if(value == 1):
               self.hit_position.append(index)
        if(len(self.hit_position) > 3):
            # Error: Intersection detected
            return 17
        if(len(self.hit_position) == 0):
            # Error: No line detected
            return 16
        if(len(self.hit_position) == 3):
            # Error: Bot at large error
            return 18
        state = self.hit_position[0] * 2
        if(len(self.hit_position) > 1):
            if(self.hit_position[1] > 0):
                state = state + 1
            if(abs(self.hit_position[0] - self.hit_position[1]) > 1):
                # Error: Discontinuity in sensors
                return 19
        state = state - 15;
        return state

    def get_position_rl(self, readings):
        """Reading the IR sensors from left to right   
        
        Calculates the currrent state in refarencs to center from 
        left to right. States go form -15 to 15.
        """
        self.hit_position = []
        state = 0.0
        for index, value in enumerate(readings):
            if(value == 1):
               self.hit_position.append(index)
        if(len(self.hit_position) > 3):
            # Error: Intersection detected
            return 17
        if(len(self.hit_position) == 0):
            # Error: No line detected
            return 16
        if(len(self.hit_position) == 3):
            # Error: Bot at large error
            return 18
        state = ( self.hit_position[0]) * 2
        if(len(self.hit_position) > 1):
            if(self.hit_position[1] > 0):
                state = state + 1
            if(abs(self.hit_position[0] - self.hit_position[1]) > 1):
                # Error: Discontinuity in sensors
                return 19
        state = (state - 15) * -1;
        return state
