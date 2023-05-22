import requests
import time
import math

class WaterData:
    def __init__(self, cache_update_interval, db_update_interval, queue_path, local_cache_path):
      self.cache_update_interval = cache_update_interval
      self.db_update_interval = db_update_interval
      self.last_cache_update_attempt = time.time()
      self.last_db_update_attempt = time.time()
      self.queue_path = queue_path
      self.local_cache_path = local_cache_path
      self.force_cache_update = False
      self.database_update_pending = False
    
    def is_cache_outdated(self):
      if (self.force_cache_update):
        self.force_cache_update = False
        print("The cache is being forced to update")
        return True
      current_time = time.time()
      return current_time - self.last_cache_update_attempt > self.cache_update_interval
      
    def is_db_update_pending(self):
      return self.database_update_pending
      
    def get_force_cache_update(self):
      return self.force_cache_update

    def is_db_outdated(self):
      current_time = time.time()
      return current_time - self.last_db_update_attempt > self.db_update_interval

    def get_water_data(self):
      with open(self.local_cache_path, "r") as fileOpened:
            globalWaterBottleData = fileOpened.readline().strip()
            if (globalWaterBottleData == ""):
              globalWaterBottleData = 0
            fileOpened.close()
      
      return float(globalWaterBottleData)


    def update_cache(self):
      self.last_cache_update_attempt = time.time()
      global_water_dispensed = requests.get("https://8ndi1e.deta.dev/total_flow")
      with open(self.local_cache_path, "w") as fileOpened:
        fileOpened.write(str(global_water_dispensed.json()))
        fileOpened.close()



    def update_database(self):
      print("the database is being updated...")
      self.database_update_pending = True
    
      self.last_db_update_attempt = time.time()
      ounces = math.floor(self.get_data_from_queue())
      self.force_cache_update = True
      requests.post("https://8ndi1e.deta.dev/flow/station1/" + str(ounces))
      self.force_cache_update = True
      self.clear_queue()
      print("The database has been updated and queue cleared")
      self.database_update_pending = False

    def get_data_from_queue(self):
      with open(self.queue_path, "r") as fileOpened:
        data = fileOpened.readline().strip()
        if (data == ""):
          data = 0
        fileOpened.close()
      return math.floor(float(data))

    def add_to_queue(self, ounces):
      current = self.get_data_from_queue()
      with open(self.queue_path, "w") as fileOpened:
        fileOpened.write(str(float(current + ounces)))
        fileOpened.close()
        
        
    def clear_queue(self):
      with open(self.queue_path, 'w') as fileOpened:
        fileOpened.write(str(0.0))
        fileOpened.close()
      
