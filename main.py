# -*- coding: utf-8 -*-
"""main.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1iagXpnHJgynbWCpXPK-sl7vxzNm0R6_O

## **TrojAI Inc. Project**

![Status](https://img.shields.io/static/v1.svg?label=Status&message=Running&color=red)
[![Open In Collab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/12zKxVdXI6B8n27FWnwlYi_YdZaavCZyI?usp=sharing) 

![References](https://img.shields.io/static/v1.svg?label=Motivation&message=References&color=green)

# **Naturalistic Support Artifacts**
Utilize / Design supporting artifacts to boost the model's prediction 

## **Pytorch Implementation**

## **TorchGAN** 
Pytorch library to assist in GAN training

[![GitHub](https://img.shields.io/static/v1.svg?logo=github&label=GitHub&message=Repository&color=lightgrey)](https://github.com/torchgan/torchgan)

## **Dataset Link:** 
*Dataset for GAN training*:  **Birds-400** 

[![Dataset](https://img.shields.io/static/v1.svg?logo=kaggle&label=Source&message=Dataset&color=blue)](https://www.kaggle.com/datasets/gpiosenka/100-bird-species?datasetId=534640&sortBy=voteCount)

*Dataset for generating adversarial artifact*: **German Traffic Sign Recognition Benchmark**

[![Dataset](https://img.shields.io/static/v1.svg?logo=google&label=Source&message=Dataset&color=blue)](https://benchmark.ini.rub.de/)

## **Contributor:** 
*Implemented by: Abhijith Sharma*

(Not official, likely to have bugs/errors)

## **Setting up the environment**
"""

# Connecting to the drive
#from google.colab import drive
#drive.mount('/content/drive')

# Providing path to working/project directory
import sys
sys.path.append('/home/sharma86/NSA/Project')
sys.path.append('/home/sharma86/NSA/Project/Model/CNN')

"""## **Importing Libraries**"""

#import warnings
#warnings.filterwarnings('ignore')
#from __future__ import print_function, division

# Python Utility Library
import os
import sys
import cv2
import copy
import math
import time
import shutil
import tarfile
import timm
from tqdm import tqdm
from glob import glob
from pathlib import Path

from collections import defaultdict

# Import models
from resnet18 import ResNet18
from vgg16 import VGG

# Data Science Libraries
import numpy as np
import pandas as pd
import seaborn as sns
from PIL import Image
from matplotlib import rc
from pylab import rcParams
import matplotlib.pyplot as plt
from matplotlib.pyplot import *
from matplotlib.pyplot import figure
from matplotlib.ticker import MaxNLocator
plt.ion()   # interactive mode

# SciKit Learn Libraries 
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report

# Pytorch Generic Libraries
import torch
torch.cuda.empty_cache()
import torch.nn as nn
import torch.optim as optim
from torch.optim import Adam
import torch.nn.functional as F
from torch.optim import lr_scheduler
from torch.autograd import Variable
from torch.utils.data import DataLoader, Subset
from torch.utils.data import RandomSampler
from torch.utils.data.sampler import SubsetRandomSampler

# Pytorch Vision Libraries 
import torchvision
import torchvision.utils as vutils
import torchvision.transforms as T
from torchvision.utils import make_grid
from torchvision.datasets import ImageFolder
from torchvision.datasets.utils import download_url
from torchvision import datasets, models, transforms
from torchvision.models import resnet18, resnet

# Adversarial attack library in PyTorch
import torchattacks

# Intializing the GPU/CPU
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# Importing torchGAN Libraries
import torchgan
from torchgan.models import *
from torchgan.trainer import Trainer
from torchgan.losses import *

import utils
from utils import show_image, imshow_old, bg_remove_threshold, place_artifact, apply_artifact, embed_2_artifact, create_mask
from utils import natural_test, natural_train, training_loop, testing_loop, patch_attack_proc, attack_visual, result_log 

# Setting up the seed for consistent reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)

"""## **Parameters and Paths**"""

# Path to Train/Val/Test dataset
NUM_ARTIFACTS = 2
PATCH_SIZE = 64 # choose the desired size for generated output of GAN
IMAGE_SIZE = 224
CNN_MODEL_NAME = 'resnet18'
MAIN_DIR = '/home/sharma86/NSA/Project/'
GAN_MODEL_PATH = MAIN_DIR + 'Model/GAN_' + str(PATCH_SIZE) +'/'
CNN_MODEL_PATH = MAIN_DIR + 'Model/CNN/' + CNN_MODEL_NAME + '.pt'
EMBED_PATH = MAIN_DIR + 'Embed_Vec/' + str(PATCH_SIZE) +'/'

"""## **Recognizing traffic signs**

Downloading Dataset


"""

#!wget https://sid.erda.dk/public/archives/daaeac0d7ce1152aea9b61d9f1e19370/GTSRB_Final_Training_Images.zip
#!unzip -qq GTSRB_Final_Training_Images.zip

"""### Exploration

Let's start by getting a feel of the data. The images for each traffic sign are stored in a separate directory. How many do we have?
"""

train_folders = sorted(glob('/home/sharma86/Data/GTSRB/Training/*'))

overall_classes = { 0:'Speed limit (20km/h)',
            1:'Speed limit (30km/h)',      
            2:'Speed limit (50km/h)',       
            3:'Speed limit (60km/h)',      
            4:'Speed limit (70km/h)',    
            5:'Speed limit (80km/h)',      
            6:'End of speed limit (80km/h)',     
            7:'Speed limit (100km/h)',    
            8:'Speed limit (120km/h)',     
            9:'No passing',   
           10:'No passing veh over 3.5 tons',     
           11:'Right-of-way at intersection',     
           12:'Priority road',    
           13:'Yield',     
           14:'Stop',       
           15:'No vehicles',       
           16:'Veh > 3.5 tons prohibited',       
           17:'No entry',       
           18:'General caution',     
           19:'Dangerous curve left',      
           20:'Dangerous curve right',   
           21:'Double curve',      
           22:'Bumpy road',     
           23:'Slippery road',       
           24:'Road narrows on the right',  
           25:'Road work',    
           26:'Traffic signals',      
           27:'Pedestrians',     
           28:'Children crossing',     
           29:'Bicycles crossing',       
           30:'Beware of ice/snow',
           31:'Wild animals crossing',      
           32:'End speed + passing limits',      
           33:'Turn right ahead',     
           34:'Turn left ahead',       
           35:'Ahead only',      
           36:'Go straight or right',      
           37:'Go straight or left',      
           38:'Keep right',     
           39:'Keep left',      
           40:'Roundabout mandatory',     
           41:'End of no passing',      
           42:'End no passing veh > 3.5 tons' }

class_labels = ['Ahead only', 'General caution', 'Keep right', 'No entry', 'No passing', 'No passing veh over 3.5 tons', \
                'No vehicles', 'Priority road', 'Right-of-way at intersection', 'Road work', 'Speed limit (100km/h)', \
                'Speed limit (120km/h)', 'Speed limit (30km/h)', 'Speed limit (50km/h)', 'Speed limit (60km/h)', \
                'Speed limit (70km/h)', 'Speed limit (80km/h)', 'Stop', 'Turn right ahead', 'Wild animals crossing', \
                'Yield']

overall_class_names = list(overall_classes.values())
class_indices = list(overall_classes.keys())
n_classes=len(class_indices)
class_samp=[len(os.listdir(train_folders[i])) for i in range(n_classes)]

interest_class_idx=[1,2,3,4,5,7,8,9,10,11,12,13,14,15,17,18,25,31,33,35,38]

class_names = [overall_classes[i] for i in interest_class_idx]
class_indices = [i for i in range(len(interest_class_idx))]
n_classes=len(class_indices)

DATA_DIR = Path('data')

DATASETS = ['train', 'val', 'test']


"""## **Data Loading**

Image Augmentation for increasing dataset size
"""

mean = [0.485, 0.456, 0.406]
std = [0.229, 0.224, 0.225]

trans_totensor = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor()
])

#trans_norm = transforms.Compose([
#    transforms.Normalize((0.485, 0.456, 0.406),
#                         (0.229, 0.224, 0.225))
#])

trans_norm = transforms.Compose([
    transforms.Normalize((0.5, 0.5, 0.5),
                         (0.5, 0.5, 0.5))
])

inv_trans_patch = transforms.Compose([ transforms.Normalize(mean = [ 0., 0., 0. ], std = [ 1/0.5, 1/0.5, 1/0.5 ]),
                                transforms.Normalize(mean = [ -0.5, -0.5, -0.5 ], std = [ 1., 1., 1. ]),])

inv_trans_norm = transforms.Compose([ transforms.Normalize(mean = [ 0., 0., 0. ], std = [ 1/0.5, 1/0.5, 1/0.5 ]),
                                transforms.Normalize(mean = [ -0.5, -0.5, -0.5 ], std = [ 1., 1., 1. ]),])
# Train/Val/Test dataset
trans_patch = transforms.Compose([transforms.Resize((PATCH_SIZE, PATCH_SIZE)),transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

"""Class-specific dataloader"""

train_datasets = ImageFolder('./data/train', trans_totensor)
#train_loaders = DataLoader(train_datasets, batch_size=16, shuffle=True, num_workers=2)

#val_datasets = ImageFolder('./data/val', trans_totensor)
#val_loaders = DataLoader(val_datasets, batch_size=64, shuffle=True, num_workers=2)

#test_datasets = ImageFolder('./data/test', trans_totensor)
#test_loaders = DataLoader(test_datasets, batch_size=64, shuffle=True, num_workers=2)

#dataset_sizes = {'train': len(train_datasets), 'test': len(test_datasets)}


"""## **Import Model**

### CNN Model
"""

# Initialize the model
print("=> Loading model ")
# Model class must be defined somewhere
if CNN_MODEL_NAME == 'resnet18':
  cnn_model=ResNet18()
elif CNN_MODEL_NAME == 'vgg16':
  # Model class must be defined somewhere
  cnn_model=VGG('VGG16')

#PATH = CNN_MODEL_PATH
cnn_model.load_state_dict(torch.load(CNN_MODEL_PATH, map_location=torch.device(device)))
cnn_model.eval()

epochs=24
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(cnn_model.parameters(), lr=0.001)
scheduler = lr_scheduler.StepLR(optimizer, step_size=7, gamma=0.1)

SAVE_PATH = MAIN_DIR + CNN_MODEL_NAME + ".pt"
# Model Training
#cnn_model=natural_train(epochs, cnn_model, train_loaders, optimizer, scheduler, criterion, CNN_MODEL_PATH, trans_norm, norm=True)
# Model Testing
#natural_test(cnn_model, test_loaders, criterion, CNN_MODEL_PATH, trans_norm, norm=True)

"""### GAN Model"""

# Loading trained Generator
# Declare the GAN network
## Choose the desired size for generated output of GAN
dcgan_network = {
    "generator": {
        "name": DCGANGenerator,
        "args": {
            "encoding_dims": 128,
            "out_channels": 3,
            "out_size": PATCH_SIZE,  
            "step_channels": 64,
            "nonlinearity": nn.LeakyReLU(0.2),
            "last_nonlinearity": nn.Tanh(),
        },
        "optimizer": {"name": Adam, "args": {"lr": 0.001, "betas": (0.5, 0.999)}},
    },
    "discriminator": {
        "name": DCGANDiscriminator,
        "args": {
            "in_channels": 3,
            "in_size": PATCH_SIZE,
            "step_channels": 64,
            "nonlinearity": nn.LeakyReLU(0.2),
            "last_nonlinearity": nn.LeakyReLU(0.2),
        },
        "optimizer": {"name": Adam, "args": {"lr": 0.003, "betas": (0.5, 0.999)}},
    },
}

# Wasserstein Loss for training
wgangp_losses = [
    WassersteinGeneratorLoss(),
    WassersteinDiscriminatorLoss(),
    WassersteinGradientPenalty(),
]


# Training the network
trainer = Trainer(dcgan_network, wgangp_losses, sample_size=1, epochs=300, device=device, checkpoints=GAN_MODEL_PATH)
#trainer(train_dataloader)
model_path = GAN_MODEL_PATH + '4.model'
trainer.load_model(model_path)
netG = trainer.generator
netG.eval()

"""### Placing Artifact 1

#### Original
"""

# Import embedding for which Generator produces a relevant bird figure
# Matrix of the artifact embedding saved from GAN
NUM_ARTIFACTS = 2
embed_vec = torch.zeros((NUM_ARTIFACTS, 1, 128)).to(device)
# Array of the path of embedding 
FILE_PATH = [EMBED_PATH + 'yellow_2.pt', EMBED_PATH + 'yellow_2.pt']
# Initialize dummy artifact matrix
artifact_0_1 = torch.zeros((NUM_ARTIFACTS, 3, PATCH_SIZE, PATCH_SIZE))

for i in range(NUM_ARTIFACTS):
  embed_vec[i] = torch.load(FILE_PATH[i])
  # Produce artifacts out of imported embedding (netG is pre-trained Generator)
  artifact = netG(embed_vec[i])
  artifact = torchvision.transforms.functional.hflip(artifact)
  artifact_0_1[i] = artifact
#print(artifact.max(), artifact.min())
#artifact_0_1 = inv_trans_patch(artifact_0_1)
# Inverse standardisation for display (artifact_0_1 is in range 0 to 1)
artifact_0_1[0] = inv_trans_patch(artifact_0_1[0])
#plt.imshow(artifact_0_1[0].permute(1,2,0).detach().cpu().numpy())

"""#### Mask"""

# Convert artifact to numpy and then range 0 to 255 for background processing
artifact_0_255_numpy = artifact_0_1[0].permute(1,2,0).detach().cpu().numpy()*255
# Thresholding function for removing background to design the patch mask
patch_mask = bg_remove_threshold(artifact_0_255_numpy, 170, gauss_k=3)
# Display the mask generated
#plt.imshow(patch_mask, cmap='gray', vmin=0, vmax=1)
#plt.show()

"""## **Artifact Training**

### Training Initialization
"""

# Import embedding for which Generator produces a relevant bird figure
embed_vec = torch.zeros((NUM_ARTIFACTS, 1, 128)).to(device)
# Initialize the dummy mask
mask = np.zeros((IMAGE_SIZE, IMAGE_SIZE))
# Array of the path of embedding 
FILE_PATH = [EMBED_PATH + 'yellow_2.pt', EMBED_PATH + 'yellow_2.pt']

#orient = ['top_left']
orient = ['top_left', 'top_right']
#orient = ['top_left', 'top_right', 'bottom_left', 'bottom_right']

for i in range(NUM_ARTIFACTS):
  embed_vec[i] = torch.load(FILE_PATH[i])
  # Produce artifacts out of imported embedding (netG is pre-trained Generator)
  artifact = netG(embed_vec[i])
  if i==0:
    threshold = 170
    gauss_blur = 7
    if FILE_PATH[i]==FILE_PATH[i+1]:
      artifact = torchvision.transforms.functional.hflip(artifact)
  else:
    threshold = 170
    gauss_blur = 7
  # Inverse standardisation for display (artifact_0_1 is in range 0 to 1)
  artifact_0_1[i] = inv_trans_patch(artifact)
  location = orient[i]

  mask = mask + create_mask(artifact_0_1[i], IMAGE_SIZE, PATCH_SIZE, location, threshold, gauss_blur)

plt.imshow(mask[0], cmap='gray')
mask = torch.FloatTensor(mask)
mask = mask.to(device)

((mask[0] == 1).sum()/(IMAGE_SIZE*IMAGE_SIZE))*100

"""### Training Loop"""

# Trainloader for training (one image at a time)
#train_loaders = DataLoader(train_datasets, batch_size=1, shuffle=True, num_workers=2)
#norm_tol = 20/255
#tar_class = 7
#Epochs = 5
#bird_comb = 'yellow2_x_yellow2'
#patch_type = 'same'
#training_loop(MAIN_DIR, IMAGE_SIZE, PATCH_SIZE, embed_vec, bird_comb, patch_type, mask, orient, CNN_MODEL_NAME, cnn_model, netG, train_loaders, tar_class, Epochs, norm_tol)

"""### Testing Loop"""

bird_comb = 'yellow2_x_yellow2'
patch_type = 'same'
attack_mag = 4/255
steps = 20

NATURAL_CORRECT_W_NSA, ADVERSARIAL_CORRECT_W_NSA, NATURAL_CORRECT_WO_NSA, ADVERSARIAL_CORRECT_WO_NSA, TOTAL_NUM_PER_CLS = \
testing_loop(MAIN_DIR, IMAGE_SIZE, PATCH_SIZE, NUM_ARTIFACTS, n_classes, embed_vec, bird_comb, orient, patch_type, mask, CNN_MODEL_NAME, cnn_model, netG, attack_mag, steps)

"""### Result Logging"""

ROWS = ['Ahead only', 'General caution', 'Keep right', 'No entry', 'No passing', 'No passing veh over 3.5 tons', \
                'No vehicles', 'Priority road', 'Right-of-way at intersection', 'Road work', 'Speed limit (100km/h)', \
                'Speed limit (120km/h)', 'Speed limit (30km/h)', 'Speed limit (50km/h)', 'Speed limit (60km/h)', \
                'Speed limit (70km/h)', 'Speed limit (80km/h)', 'Stop', 'Turn right ahead', 'Wild animals crossing', \
                'Yield', 'OVERALL']

COLS = ['NATURAL_ACCURACY_W_NSA', 'ADVERSARIAL_ACCURACY_W_NSA', 'NATURAL_ACCURACY_WO_NSA', 'ADVERSARIAL_ACCURACY_WO_NSA', 'TOTAL_NUM_PER_CLS']

RES_SAVE_PATH = './pgd_4_result.csv'

OVERALL_NATURAL_ACCURACY_W_NSA, OVERALL_ADVERSARIAL_ACCURACY_W_NSA, OVERALL_NATURAL_ACCURACY_WO_NSA, OVERALL_ADVERSARIAL_ACCURACY_WO_NSA = result_log(RES_SAVE_PATH, ROWS, COLS, NATURAL_CORRECT_W_NSA, ADVERSARIAL_CORRECT_W_NSA, NATURAL_CORRECT_WO_NSA, ADVERSARIAL_CORRECT_WO_NSA, TOTAL_NUM_PER_CLS)

print(OVERALL_NATURAL_ACCURACY_W_NSA)
print(OVERALL_ADVERSARIAL_ACCURACY_W_NSA)
print(OVERALL_NATURAL_ACCURACY_WO_NSA)
print(OVERALL_ADVERSARIAL_ACCURACY_WO_NSA)
