import sys
from PIL import Image, ImageOps, ImageDraw
import string
import random
import numpy as np
import cv2
import os

def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush() 


class DataCreator:
    def __init__(self, map_size, amount_maps, noise, amount_heros, ping, output_filename, noise_path, hero_list_path):
        self.map_size = map_size
        self.amount_maps = amount_maps
        self.noise = noise
        self.amount_heros = amount_heros
        self.ping = ping
        self.output_filename = output_filename
        self.noise_path = noise_path
        self.hero_list = self.convert_class2list(hero_list_path)
        self.baseMap = 'LOL_images/minimap/map916_inner.png'
        if self.map_size == "big":
            self.map_dimension = 920
            self.map_x_min = 80
            self.map_x_max = 870
            self.map_y_min = 80
            self.map_y_max = 870
            self.offset_dif = 70
            self.hero_size = 76
            self.hero_inner_size = 70
            self.cicrle_size = 3
        elif self.map_size == "medium":
            self.map_dimension = 425
            self.map_x_min = 21
            self.map_x_max = 403
            self.map_y_min = 21
            self.map_y_max = 403
            self.offset_dif = 45
            self.hero_size = 50
            self.hero_inner_size = 45
            self.cicrle_size = 2
        else:    
            self.map_dimension = 255
            self.map_x_min = 12
            self.map_x_max = 242
            self.map_y_min = 12
            self.map_y_max = 242
            self.offset_dif = 20
            self.hero_size = 25
            self.hero_inner_size = 23
            self.cicrle_size = 1

            
    def create_images(self):
        """
        Create maps with heroes and other elemenents inside
        """
        if self.amount_maps:
            for n in range(self.amount_maps):
                
                progress(n, self.amount_maps, status='Generating Maps')
              
                bckg = Image.open(self.baseMap).resize((self.map_dimension,self.map_dimension))
                labels = []

                if self.output_filename:
                    output_filename = self.output_filename + "_" + self.randomString(10)
                else: 
                    output_filename = randomString(15) 
                
                for i in range(10):
                    bckg, labels = self.put_heroes_group(bckg, labels)
                # print(labels)
                with open("output/"+output_filename+'.txt', 'w') as f:
                    for i, item in enumerate(labels):
                        if i>0: 
                            f.write('\n')
                        f.write("%s" % item)
                bckg = bckg.convert("RGB")
                bckg.save("output/"+output_filename+'.jpg', quality=95)
        


    def randomString(self, stringLength=10):
        """
        Generate a random string of fixed length 
        Necessary for create name of maps
        """
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(stringLength))


    def convert_class2list(self, file):
        """
        Search class name based on file name
        """
        with open(file) as f:
            hlist = f.read().splitlines()
        return hlist


    def put_image_on_map(self, img, bckg):
        pass


    def make_label(self, hero, offset, bckg, hero_num):
        """
        Create line for YOLOv3 label file
        1. Get hero its offset (position)
        2. Get map (bckg) needed for size 
        as we need position as % of map size
        3. Get hero_num - is number of line obtained from class file 
        """
        x = (offset[0]+(hero.size[0]/2))/bckg.size[0]
        y = (offset[1]+(hero.size[1]/2))/bckg.size[1]
        width = hero.size[0]/bckg.size[0]
        height = hero.size[1]/bckg.size[1]
        #zamien filename na numero klasy
        line = "{} {} {} {} {}".format(hero_num, x, y, width, height)
        # print(line)
        return line 


    def random_hero(self, directory):
        """
        Random select hero from heroes directory
        image_size for small minimap 30, for big minimap 70
        directory where heroes are ("LOL_images/heroes1x/")
        """
        # Random select hero
        filename = random.choice(os.listdir(directory))
        # Open hero
        # hero = Image.open(args.input_image)
        hero = Image.open(directory+filename).resize((self.hero_inner_size,self.hero_inner_size))
        return (hero, filename)


    def random_secondary_position(self, offset):
        """
        Define position of secondary heroes
        Based on offset of primary and size of hero image
        """
        img_x = np.random.randint(offset[0]-self.offset_dif, offset[0]+self.offset_dif)
        img_y = np.random.randint(offset[1]-self.offset_dif, offset[1]+self.offset_dif)
        return (img_x, img_y)


    def random_main_position(self, bckg):
        """
        Define position of primary heroe in group
        Based on size of map
        """
        # bg_w, bg_h = bckg.size
        img_x = np.random.randint(self.map_x_min, self.map_x_max)
        img_y = np.random.randint(self.map_y_min, self.map_y_max)
        # offset = ((bg_w - hero_w) // 2, (bg_h - hero_h) // 2)
        return (img_x,img_y)


    def insert_hero(self, bckg, offset, labels):
        """
        Insert hero in map
        Get image with circle "leblanc_fake_allyteam.png"m put in on the map
        Get image of hero and put it over image with circle (it is smaller)
        Create line of label for this hero
        Return updated data of labels lines and updated map
        """
        # Get Random file with hero
        hero, filename = self.random_hero("LOL_images/heroes1x/")
        # Extract hero_name from filename
        hero_name = filename.replace(".png", "")
        # Get number of class
        hero_num =  self.hero_list.index(hero_name)
        hero_w, hero_h = hero.size
        # Set hero in map
        if random.random() < .5:
            hero_base = Image.open(self.noise_path + "leblanc_fake_allyteam.png").resize((self.hero_size, self.hero_size))
        else:
            hero_base = Image.open(self.noise_path + "leblanc_fake_enemyteam.png").resize((self.hero_size, self.hero_size))
  
        a, b = offset
        offset_base = (a-self.cicrle_size, b-self.cicrle_size)
        bckg.paste(hero_base, offset_base, hero_base)
        bckg.paste(hero, offset, hero)
        
        # Create label line
        label = self.make_label(hero, offset, bckg, hero_num)
        labels.append(label)
        return bckg, labels


    def put_heroes_group(self, bckg, labels):
        """
        Create group of heros in map
        First put first hero in map, after random 
        number (from 0 to 4) of heros around him
        labels are all labels until now for this map
        hero_list is neccesary to get index number of hero.
        """
        offset = self.random_main_position(bckg)
        bckg, labels = self.insert_hero(bckg, offset, labels)
        num_heroes = np.random.randint(0, 4)
        for i in range(num_heroes):
            bckg, labels = self.insert_hero(bckg, self.random_secondary_position(offset), labels)
        return bckg, labels
