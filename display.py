import pygame
import time


class Display:
  def __init__(self, main_background_image_path, dispensing_background_image_path, font, font_size_bottles, font_size_ounces, bg_color_dark, bg_color_light, text_color):
    self.setup()
    self.info = pygame.display.Info()
    self.windowWidth = self.info.current_w
    self.windowHeight = self.info.current_h
    self.display = self.create_display()
    self.main_background_image_path = main_background_image_path
    self.dispensing_background_image_path = dispensing_background_image_path
    #self.background_image = self.setup_background(background_image_path)
    self.font_bottles = pygame.font.SysFont(font,font_size_bottles)
    self.font_ounces = pygame.font.SysFont(font,font_size_ounces)
    self.bg_color_dark = bg_color_dark
    self.bg_color_light = bg_color_light
    self.text_color = text_color
    self.useMainBackground()


  def format_ounces_text(self, text):
    return "{:,}".format(float(text))
    
  def format_bottles_text(self, text):
    return "{:,}".format(text)

  def display_bottles_refilled(self, bottles):
#    print("bottles being displayed  " + str(bottles))
    half_window_height = self.windowHeight / 2
    self.create_label(self.font_bottles,self.format_bottles_text(int(bottles)), (500, half_window_height), self.bg_color_dark)
    self.update_display()

#  def display_pounds_of_plastic(self, pounds):
#    self.create_label(self.format_text(pounds), (640, 370))
#    self.update_display()

  def display_ounces_dispensed(self, ounces):
    #self.create_label(self.format_text(ounces), (910, 845))
    half_window_height = self.windowHeight / 2
    self.create_label(self.font_ounces, self.format_ounces_text(ounces), (1200, half_window_height), self.bg_color_light)
    self.update_display()

  def create_label(self, font_type, text, position, bg_color):
    label = font_type.render(text, 1, self.text_color, bg_color)
    label = pygame.transform.rotate(label, 90)
    text_rect = label.get_rect(center=(position))
    self.display.blit(label, text_rect)

  def setup(self):
    pygame.init()

  def shut_down(self):
    pygame.quit()
    exit()
  
  def check_for_termination_request(self):
    for event in pygame.event.get():
      if (self.did_escape_key_get_pressed(event)):
        return True
    return False

  def did_escape_key_get_pressed(self, event):
    if event.type == pygame.KEYDOWN:
      if event.key == pygame.K_ESCAPE:
        return True
    return False

  def update_display(self):
    pygame.display.update()

  def clear_current_ounces_dispensed(self):
    self.create_label(self.font_ounces, "            ", (910, 845), self.bg_color_light)
    self.update_display()


  def useMainBackground(self):
      self.setup_background(self.main_background_image_path)

  def useWaterDispensingBackground(self):
      self.setup_background(self.dispensing_background_image_path)

  def setup_background(self, image):
    main_surface = pygame.display.get_surface()
    UI_Image = pygame.image.load(image)
    UI_Image = pygame.transform.rotate(UI_Image,90)
    UI_Image = pygame.transform.scale(UI_Image, (self.windowWidth,self.windowHeight))
    main_surface.blit(UI_Image, (0, 0))
    self.update_display()
    
  
  def create_display(self):

    return pygame.display.set_mode((self.windowWidth,self.windowHeight), pygame.FULLSCREEN) #This function will create a display Surface.
#    return pygame.display.set_mode((self.windowWidth,self.windowHeight), pygame.RESIZABLE) #This function will create a display Surface.


