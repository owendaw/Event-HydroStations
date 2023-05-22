import pygame
import time
import math
import fcntl


import RPi.GPIO as GPIO
import os
import board
import busio
import requests
#import adafruit_vl6180x
import adafruit_vl53l0x
import threading
from power_api import SixfabPower, Definition, Event
from subprocess import call
from water_data import WaterData
from display import *
water_data = WaterData(50, 50, "./WaterDataFiles/Water_Dispensed_Queue.txt", "./WaterDataFiles/GlobalWaterData_AWS.txt")
hope_display = Display('./UI_Background_V2_Idle_Screen.png', "./UI_Background_V2_Dispensing_Screen.png", "menlo", 200, 400, (11,35,65), (0,85,184), (246,243,241)) # ./UI_Background_V2_Idle_Screen.png #Dark Blue Color (R=11,G=35,B=65)
isWaterDispensing = False
display_needs_update = True # This variable is used to update the idle screen after a user fillup is cleared. This is to prevent constant updates from happening and slowing down processing.
                            # This will also be set to true in the condition that the "is_cache_outdated" returns true
sixfab_power_api = SixfabPower()
running_on_battery_power = False
max_sensor_range = 100
min_sensor_range = 20
tof_sensor_configurable_timeout_value = 30.0
tof_sensor_timed_out = False
solenoid_opened_time = 0.0
solenoid_initial_timed_out_time = 0.0

pygame.mouse.set_visible(False)

previous = 0
range_1 = 0
range_2 = 0
range_3 = 0
range_4 = 0
range_5 = 0
range_6 = 0
range_7 = 0
range_8 = 0

class myThread_1 (threading.Thread):
    global isWaterDispensing
    global previous
    global display_needs_update
    global sixfab_power_api
    global running_on_battery_power
    global tof_sensor_timed_out
    global solenoid_opened_time

    def thread_function_1(self):
        continue_running = True
        previous = 0
        last_time_heartbeat_1_was_updated = 0.0
        global display_needs_update
        while continue_running:
          
          curr_time = time.time()
          if ( (curr_time - last_time_heartbeat_1_was_updated) > 5.0 ):
              last_time_heartbeat_1_was_updated = curr_time
              with open("./heartbeat_monitor_thread_1.txt", "w") as fileOpened:
                  fileOpened.write(str(curr_time))
                  fileOpened.flush()
                  fileOpened.close()

          if (water_data.is_cache_outdated()):
            try:
              water_data.update_cache()
              display_needs_update = True
              continue
            except:
              print("There was a problem connecting to the database. Try again later.")
              continue

          else:
            try:
              global_water_data = water_data.get_water_data()
            except:
              print("There was a problem accessing the local cache..")
              continue
          
          try:
            queue_data = water_data.get_data_from_queue()
            global_water_data += queue_data
          except Exception as e:
            print(e)
            print("There was a problem accessing the data from the queue")
            
          #print("Global Water Data: " + str(global_water_data))
          
          if (water_data.get_force_cache_update()):

              continue

          if (not water_data.is_db_update_pending()):
              if (previous > int(global_water_data)):
                  global_water_data = previous
 #                 print("GUI flickering prevention engaged")
              Total_Bottles_Save = math.floor(float(global_water_data) / 1)
              pounds_of_plastic = round((float(Total_Bottles_Save) * 0.02039276), 1)
              
              if ((not isWaterDispensing) and (display_needs_update)):
                  hope_display.display_bottles_refilled(global_water_data/16.9)  #This line affects polling rate in idle state
#                  hope_display.display_pounds_of_plastic(pounds_of_plastic) #This line affects polling rate in idle state
                  display_needs_update = False
              previous = int(global_water_data)


          if(hope_display.check_for_termination_request()):
              continue_running = False
          elif (running_on_battery_power):
              continue_running = False
              print("brian! " + str(sixfab_power_api.get_working_mode()))

#          elif (3 == sixfab_power_api.get_working_mode()):
#              print("Brian")

          #Frames Per Second
          #clock.tick(30)

            
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
         
            
    def run(self):
        self.thread_function_1()  
        print("Starting " + self.name)
        threadLock.acquire()
        threadLock.release()

def thread_function_2():
    print("thread_function_2 entered")
    global current_fillup_value_in_oz, tot_current_cnt, isWaterDispensing, range_1, range_2, range_3, range_4, range_5, range_6, range_7, range_8
    global display_needs_update
    global sixfab_power_api
    global running_on_battery_power
    global max_sensor_range
    global min_sensor_range
    global tof_sensor_timed_out
    global solenoid_opened_time
    global solenoid_initial_timed_out_time
    global tof_sensor_configurable_timeout_value

    ###################################################
    ### TOF Sensor Setup
    ###################################################
    # Create I2C bus.
    i2c = busio.I2C(board.SCL, board.SDA)
     
    # Create sensor instance.
    #tof_sensor = adafruit_vl6180x.VL6180X(i2c)
    tof_sensor = adafruit_vl53l0x.VL53L0X(i2c)
#    tof_sensor.measurement_timing_budget = 200000
    tof_sensor.measurement_timing_budget = 25000
    last_time_heartbeat_2_was_updated = 0.0
    ###################################################
    ### Flow Sensor Setup
    ###################################################
    flowMeterPin = 27
    GPIO.setup(flowMeterPin, GPIO.IN)
    constant = 0.00046512
    current_fillup_value_in_oz = 0
    tot_current_cnt = 0

    def Pulse_cnt(flowMeterPin):
        global tot_current_cnt
        tot_current_cnt += 1

    GPIO.add_event_detect(flowMeterPin,GPIO.FALLING,
        callback=Pulse_cnt,bouncetime=10)
        

    ###################################################
    solenoidPin = 18

    GPIO.setup(solenoidPin, GPIO.OUT)
    GPIO.output(solenoidPin,GPIO.LOW)
    ###################################################
    PIN_IR_SENSOR = 31
    GPIO.setup(PIN_IR_SENSOR, GPIO.IN)
    ###################################################

                

    current_fillup_value_in_oz = 0
    tot_current_cnt = 0

    continue_running = True

    ###########################################################################
    ### Main Program Loop
    ###########################################################################
    last_time_solenoid_opened = 0.0
    previous_solenoid_state = False
    while continue_running:

        curr_time = time.time()
        if ( (curr_time - last_time_heartbeat_2_was_updated) > 5.0 ):
            last_time_heartbeat_2_was_updated = curr_time
            with open("./heartbeat_monitor_thread_2.txt", "w") as fileOpened:
                fileOpened.write(str(curr_time))
                fileOpened.flush()
                fileOpened.close()
        
        ###########################################################################
        ### TOF Sensor Main Loop
        ###########################################################################
        # Read the range in millimeters and print it.
        range_mm = tof_sensor.range
 #       print("Range: {0}mm".format(range_mm))
        
        tmp_range1 = range_1
        range_1 = range_mm
        
        tmp_range2 = range_2
        range_2 = tmp_range1
        
        tmp_range3 = range_3
        range_3 = tmp_range2
        
        tmp_range4 = range_4
        range_4 = tmp_range3
        
        tmp_range5 = range_5
        range_5 = tmp_range4
        
        tmp_range6 = range_6
        range_6 = tmp_range5
        
        tmp_range7 = range_7
        range_7 = tmp_range6
        
        tmp_range8 = range_8
        range_8 = tmp_range7
        
        
#        print(" range_1 = " + str(range_1) + " range_2 = " + str(range_2) + " range_3 = " + str(range_3) + " range_4 = " + str(range_4) + " range_5 = " + str(range_5) + " range_6 = " + str(range_6) + " range_7 = " + str(range_7) + " range_8 = " + str(range_8)  )
        
        ###########################################################################
        ### Flow Sensor Main Loop
        ###########################################################################

        #current_fillup_value_in_oz = round((33.814 * (tot_current_cnt * constant)),1)
        
        liters_dispensed = tot_current_cnt/438
        ounces_dispensed = round((liters_dispensed*33.814),1)
        current_fillup_value_in_oz = ounces_dispensed

            
        ###########################################################################
        # 16 oz  = 0.473 liters
        ###########################################################################
        
        time_now_in_seconds = time.time()

        # This condition will reset the timeout.
        #if ( (time_now_in_seconds - solenoid_initial_timed_out_time) >= 10.0 ):
            #tof_sensor_timed_out = False
            #solenoid_initial_timed_out_time = 0.0

        if ( (tof_sensor_timed_out == False) and ((max_sensor_range >= range_1) and (max_sensor_range >= range_2) and (max_sensor_range >= range_3) and (max_sensor_range >= range_4) and (max_sensor_range >= range_5) and (max_sensor_range >= range_6) and (max_sensor_range >= range_7) and (max_sensor_range >= range_8)) and ((min_sensor_range < range_1) and (min_sensor_range < range_2) and (min_sensor_range < range_3) and (min_sensor_range < range_4) and (min_sensor_range < range_5) and (min_sensor_range < range_6) and (min_sensor_range < range_7) and (min_sensor_range < range_8)) ):
#        if (((100 >= range_1) and (100 >= range_2) and (100 >= range_3) and (100 >= range_4)) and ((20 < range_1) and (20 < range_2) and (20 < range_3) and (20 < range_4))):
            if (not isWaterDispensing):
                isWaterDispensing = True
                hope_display.useWaterDispensingBackground()
                solenoid_opened_time = time_now_in_seconds

            if ( (time_now_in_seconds - solenoid_opened_time) >= tof_sensor_configurable_timeout_value ):
                tof_sensor_timed_out = True
                solenoid_initial_timed_out_time = time_now_in_seconds

            last_time_solenoid_opened = time.time()
            GPIO.output(solenoidPin, GPIO.HIGH)
            hope_display.display_ounces_dispensed(str(current_fillup_value_in_oz))
            previous_solenoid_state = True
        elif( ((max_sensor_range < range_1) and (max_sensor_range < range_2) and (max_sensor_range < range_3) and (max_sensor_range < range_4)) or ((min_sensor_range > range_1) and (min_sensor_range > range_2) and (min_sensor_range > range_3) and (min_sensor_range > range_4)) ):
#        elif(((100 < range_1) and (100 < range_2) and (100 < range_3) and (100 < range_4) and (100 < range_5) and (100 < range_6) and (100 < range_7) and (100 < range_8)) or ((20 > range_1) and (20 > range_2) and (20 > range_3) and (20 > range_4) and (20 > range_5) and (20 > range_6) and (20 > range_7) and (20 > range_8))):    
            GPIO.output(solenoidPin, GPIO.LOW)
            # This condition will reset the timeout.
            tof_sensor_timed_out = False
            solenoid_initial_timed_out_time = 0.0
            if ( (time_now_in_seconds - last_time_solenoid_opened) >= 2.8 ):
                try:
                  water_data.add_to_queue(current_fillup_value_in_oz)
                except Exception as e:
                  print(e)  
                  print('There was a problem updating the queue')
                
                current_fillup_value_in_oz = 0
                tot_current_cnt = 0
#                hope_display.clear_current_ounces_dispensed()
                if (isWaterDispensing):
                    hope_display.useMainBackground()
                    isWaterDispensing = False  #when this line is uncommented, the reading becomes very slow (polling rate)
                    global_water_data = water_data.get_water_data()
                    if (previous > int(global_water_data)):
                        global_water_data = previous
                        print("GUI flickering prevention engaged")
                    Total_Bottles_Save = math.floor(float(global_water_data) / 1)
                    pounds_of_plastic = round((float(Total_Bottles_Save) * 0.02039276), 1)
                    hope_display.display_bottles_refilled(global_water_data/16.9)
#                    hope_display.display_pounds_of_plastic(pounds_of_plastic)
                    display_needs_update = True
        elif( (tof_sensor_timed_out == True) ):
            GPIO.output(solenoidPin, GPIO.LOW)
            if ( (time_now_in_seconds - last_time_solenoid_opened) >= 2.8 ):
                try:
                  water_data.add_to_queue(current_fillup_value_in_oz)
                except Exception as e:
                  print(e)  
                  print('There was a problem updating the queue')
                
                current_fillup_value_in_oz = 0
                tot_current_cnt = 0
#                hope_display.clear_current_ounces_dispensed()
                if (isWaterDispensing):
                    hope_display.useMainBackground()
                    isWaterDispensing = False  #when this line is uncommented, the reading becomes very slow (polling rate)
                    global_water_data = water_data.get_water_data()
                    if (previous > int(global_water_data)):
                        global_water_data = previous
                        print("GUI flickering prevention engaged")
                    Total_Bottles_Save = math.floor(float(global_water_data) / 1)
                    pounds_of_plastic = round((float(Total_Bottles_Save) * 0.02039276), 1)
                    hope_display.display_bottles_refilled(global_water_data/16.9)
#                    hope_display.display_pounds_of_plastic(pounds_of_plastic)
                    display_needs_update = True

            if (water_data.is_db_outdated()): 
              try:
                water_data.update_database()
              except:
                print("There was a problem updating the database...")
            


#            if (previous_solenoid_state == True):
#                time.sleep(1)
            previous_solenoid_state = False
        
        ###########################################################################
        ### Read Global Data Periodically
        ###########################################################################
        ###########################################################################

        # NOTE: If the external battery pack is not connected (sixfab power pi hat).. this else if will make the polling rate of the sensor very slow (slows down the thread iteration rate)
        if (hope_display.check_for_termination_request()):
            continue_running = False
            GPIO.output(solenoidPin, GPIO.LOW)
            GPIO.cleanup()
            break
        elif (3 == sixfab_power_api.get_working_mode()):
            print("Brian")
            continue_running = False
            running_on_battery_power = True
            GPIO.output(solenoidPin, GPIO.LOW)
            GPIO.cleanup()
            break
                    
                
                
###########################################################################

        #Updates the entire surface (whole window) unless you add a parameter
        #pygame.display.update()

        #Frames Per Second
        #clock.tick(30)



if __name__ == "__main__":
    this_pid = os.getpid()

    with open("current_program_pid.txt", "w") as fileOpened:
        fileOpened.write(str(this_pid))
        fileOpened.close()
    print("pid = " + str(this_pid))

    threadLock = threading.Lock()
    threads = []
    thread1 = myThread_1(1, "Thread-1", 1)
    

    
#    thread_1 = threading.Thread(target=thread_function_1, name='thread_1')
    thread_2 = threading.Thread(target=thread_function_2, name='thread_2')

    thread1.start()
    thread_2.start()
    
    threads.append(thread1)
    threads.append(thread_2)

    
    
#    thread_1.join()
    thread1.join()
    thread_2.join()
    
    if(running_on_battery_power):
        call("sudo shutdown -h now", shell=True)

# Plan - every time user input occurs (receiving water) the program will push data to the DB
# and request the data for the machine's total bottle saved, directly after the update.
# Now the screen will be updated with what was pulled from the Database

# Plan 2 (This would store the water dispensed data locally, in which the AWS Database's purpose would be a backup to request from if the system crashes)
# I believe this could help update the numbers live on the screen with less requests to the DB
#Pygame's Quit
pygame.quit()

#Python's Quit
quit()
