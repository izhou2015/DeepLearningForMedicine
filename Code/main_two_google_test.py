
###################################
########## import library #########
###################################

import numpy as np
import pandas as pd

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from torchvision import transforms
from torch.utils.data import Dataset, DataLoader
import torch.optim as optim

from sklearn import metrics

from skimage import io, color

import time
import os
import pickle

import matplotlib.pyplot as plt
import scikitplot as skplt

from dataset import ChestXray
from train_valid import train, validation


###################################
########### load device ###########
###################################

# If there's a GPU available...
if torch.cuda.is_available():

    # Tell PyTorch to use the GPU.
    device = torch.device("cuda")

    print('There are %d GPU(s) available.' % torch.cuda.device_count())

    print('We will use the GPU:', torch.cuda.get_device_name(0))

# If not...
else:
    print('No GPU available, using the CPU instead.')
    device = torch.device("cpu")


###################################
############ def path #############
###################################

# # local
# train_df_path = '../../chest_xray_origin/train.csv'
# val_df_path = '../../chest_xray_origin/val.csv'
# root_dir = '../../chest_xray_origin/all/'

# hpc
train_df_path = 'chest_xray_origin/train.csv'
val_df_path = 'chest_xray_origin/val.csv'
test_df_path = 'chest_xray_origin/test.csv'

root_dir = 'chest_xray_origin/all/'

bs = 10
epochs = 1


###################################
############ load data ############
###################################

train_transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize([364, 364]),
        transforms.RandomResizedCrop(320),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

validation_transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize([364,364]),
        transforms.CenterCrop(320),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

test_transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize([364,364]),
        transforms.CenterCrop(320),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

train_loader = DataLoader(ChestXray(train_df_path, root_dir, transform=train_transform), batch_size=bs, shuffle=True)
valid_loader = DataLoader(ChestXray(val_df_path, root_dir, transform=validation_transform), batch_size=bs, shuffle=False)
test_loader = DataLoader(ChestXray(test_df_path, root_dir, transform=test_transform), batch_size=bs, shuffle=False)


###################################
######### optim & criter ##########
###################################

# weighted cross entropy loss: normal, pneumonia
train_weights = train_loader.dataset.data_frame.shape[0] / np.array(train_loader.dataset.data_frame['class'].value_counts())[::-1]
valid_weights = valid_loader.dataset.data_frame.shape[0] / np.array(valid_loader.dataset.data_frame['class'].value_counts())[::-1]
test_weights = test_loader.dataset.data_frame.shape[0] / np.array(test_loader.dataset.data_frame['class'].value_counts())[::-1]

train_weights = torch.FloatTensor(train_weights).to(device)
valid_weights = torch.FloatTensor(valid_weights).to(device)
test_weights = torch.FloatTensor(test_weights).to(device)

train_criterion = nn.CrossEntropyLoss(weight=train_weights)
valid_criterion = nn.CrossEntropyLoss(weight=valid_weights)
test_criterion = nn.CrossEntropyLoss(weight=test_weights)


###################################
###### pretrained GoogLeNet #######
###################################
print('###################################')
print('############ GoogLeNet ############')
print('###################################')

googlenet = models.googlenet(pretrained=True)
googlenet.fc = nn.Linear(1024, 2)

# training process
model = googlenet

# change model path here
model.load_state_dict(torch.load(''))

model.to(device)

start_epoch = 1

history = {# "train_loss":[], "train_acc":[],
           "test_loss":[], "test_acc":[], "test_preds_list":[],
           "test_truelabels_list":[], "test_probas_list":[], "test_auc_score":[]}
optimizer = optim.Adam(model.parameters())

start_time = time.time()

for epoch in range(start_epoch, epochs + 1):

    test_loss, test_acc, test_preds_list, test_truelabels_list, test_probas_list, test_auc_score = validation(epoch, model, optimizer, test_criterion, test_loader, device)
    history["test_loss"].append(test_loss)
    history["test_acc"].append(test_acc)
    history["test_preds_list"].append(test_preds_list)
    history["test_truelabels_list"].append(test_truelabels_list)
    history["test_probas_list"].append(test_probas_list)
    history["test_auc_score"].append(test_auc_score)

    print('{}: loss: {:.4f} acc: {:.4f} auc: {:.4f}'.format('test', test_loss, test_acc, test_auc_score))
    print()



print('time elapsed:', time.time() - start_time)

# save results
with open("history_googlenet_test.pkl", "wb") as fout:
    pickle.dump(history, fout)
