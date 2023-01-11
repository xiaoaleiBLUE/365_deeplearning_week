import torch
from torch import nn
import numpy as np
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import torch.nn.functional as F
from torch.utils.data import DataLoader
import torchvision
from torchvision.transforms import ToTensor, transforms
import glob
import os, PIL, random, pathlib
from PIL import Image

data_dir = r'/root/autodl-tmp/weather_photos'
data_dir = pathlib.Path(data_dir)
print(data_dir)                                         # weather_photos
data_path = list(data_dir.glob('*'))
print(data_path)


total_dir = r'/root/autodl-tmp/weather_photos/'
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

total_data = torchvision.datasets.ImageFolder(total_dir, transform)
print(total_data)
print(len(total_data))                                   # 1125

train_size = int(len(total_data) * 0.8)
test_size = len(total_data) - train_size

train_dataset, test_dataset = torch.utils.data.random_split(total_data, [train_size, test_size])

train_dataloader = DataLoader(train_dataset, batch_size=32)
test_dataloader = DataLoader(test_dataset, batch_size=32)


def printlog(info):
    nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("\n"+"=========="*8 + "%s"%nowtime)
    print(str(info)+"\n")


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv_1 = nn.Conv2d(in_channels=3, out_channels=12, kernel_size=5, stride=1)
        self.bn_1 = nn.BatchNorm2d(12)
        self.conv_2 = nn.Conv2d(in_channels=12, out_channels=12, kernel_size=5, stride=1)
        self.bn_2 = nn.BatchNorm2d(12)
        self.pool_1 = nn.MaxPool2d(2, 2)
        self.conv_3 = nn.Conv2d(in_channels=12, out_channels=24, kernel_size=5, stride=1)
        self.bn_3 = nn.BatchNorm2d(24)
        self.conv_4 = nn.Conv2d(in_channels=24, out_channels=24, kernel_size=5, stride=1)
        self.bn_4 = nn.BatchNorm2d(24)
        self.pool_2 = nn.MaxPool2d(2, 2)
        self.linear_1 = nn.Linear(60000, 10000)
        self.linear_2 = nn.Linear(10000, 4)

    def forward(self, x):
        x = F.relu(self.bn_1(self.conv_1(x)))
        x = F.relu(self.bn_2(self.conv_2(x)))
        x = self.pool_1(x)
        x = F.relu(self.bn_3(self.conv_3(x)))
        x = F.relu(self.bn_4(self.conv_4(x)))
        x = self.pool_2(x)
        x = x.view(-1, 24*50*50)
        x = F.relu(self.linear_1(x))
        x = self.linear_2(x)
        return x


device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(device)
model = Net().to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=0.0001)
loss_fn = nn.CrossEntropyLoss()


def train(train_dataloader, model, loss_fn, optimizer):
    size = len(train_dataloader.dataset)
    num_of_batch = len(train_dataloader)
    train_correct, train_loss = 0.0, 0.0
    for x, y in train_dataloader:
        x, y = x.to(device), y.to(device)
        pre = model(x)
        loss = loss_fn(pre, y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        with torch.no_grad():
            train_correct += (pre.argmax(1) == y).type(torch.float).sum().item()
            train_loss += loss.item()

    train_correct /= size
    train_loss /= num_of_batch
    return train_correct, train_loss


def test(test_dataloader, model, loss_fn):
    size = len(test_dataloader.dataset)
    num_of_batch = len(test_dataloader)
    test_correct, test_loss = 0.0, 0.0
    with torch.no_grad():
        for x, y in test_dataloader:
            x, y = x.to(device), y.to(device)
            pre = model(x)
            loss = loss_fn(pre, y)
            test_loss += loss.item()
            test_correct += (pre.argmax(1) == y).type(torch.float).sum().item()

    test_correct /= size
    test_loss /= num_of_batch
    return test_correct, test_loss


epochs = 100
train_acc = []
train_loss = []
test_acc = []
test_loss = []
for epoch in range(epochs):
    printlog("Epoch {0} / {1}".format(epoch, epochs))
    model.train()
    epoch_train_acc, epoch_train_loss = train(train_dataloader, model, loss_fn, optimizer)
    # if epoch % 5 == 0:
    #     for p in optimizer.param_groups:
    #         p['lr'] *= 0.9
    model.eval()
    epoch_test_acc, epoch_test_loss = test(test_dataloader, model, loss_fn)
    train_acc.append(epoch_train_acc)
    train_loss.append(epoch_train_loss)
    test_acc.append(epoch_test_acc)
    test_loss.append(epoch_test_loss)
    template = ("train_acc:{:.5f}, train_loss:{:.5f}, test_acc:{:.5f}, test_loss:{:.5f}")
    print(template.format(epoch_train_acc, epoch_train_loss, epoch_test_acc, epoch_test_loss))
print('done')
plt.plot(range(epochs), train_loss, label='train_loss')
plt.plot(range(epochs), train_acc, label='train_acc')
plt.plot(range(epochs), test_loss, label='test_loss')
plt.plot(range(epochs), test_acc, label='test_acc')
plt.legend()
plt.show()
print('done')













