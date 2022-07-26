# -*- coding: utf-8 -*-
"""NLU2_Model1_9_27.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1VDkkrcjm8tU3qti9n_I9bxbKYL3HrLl5
"""

from google.colab import drive
drive.mount('/content/drive')

!pip install seqeval

slots_dict = {'NoLabel': 0,
 'B-weather/noun': 1,
 'I-weather/noun': 2,
 'B-location': 3,
 'I-location': 4, 
 'B-datetime': 5, 
 'I-datetime': 6,
 'B-weather/attribute': 7,
 'I-weather/attribute': 8,
 'B-reminder/todo': 9, 
 'I-reminder/todo': 10, 
 'B-alarm/alarm_modifier': 11,
 'B-reminder/noun': 12,
 'B-reminder/recurring_period': 13,
 'I-reminder/recurring_period': 14,
 'B-reminder/reference': 15,
 'I-reminder/noun': 16,
 'B-reminder/reminder_modifier': 17,
 'B-timer/noun': 18,
 'I-reminder/reference': 19,
 'B-negation': 20,
 'B-timer/attributes': 21,
 'B-news/type': 22,
 'I-reminder/reminder_modifier': 23,
 'B-weather/temperatureUnit': 24,
 'I-alarm/alarm_modifier': 25,
 "B-demonstrative_reference":26,
 "I-demonstrative_reference":27,
 "PAD":28}
intents_dict = {'weather/find': 0,
                'alarm/set_alarm': 1,
                'alarm/show_alarms': 2,
                'reminder/set_reminder': 3,
                'alarm/modify_alarm': 4,
                'weather/checkSunrise': 5,
                'weather/checkSunset': 6,
                'alarm/snooze_alarm': 7,
                'alarm/cancel_alarm': 8,
                'reminder/show_reminders': 9,
                'reminder/cancel_reminder': 10,
                'alarm/time_left_on_alarm': 11}

index2slot_dict ={
   0: 'NoLabel',
   1:'B-weather/noun',
   2:'I-weather/noun',
   3:'B-location',
   4:'I-location', 
   5:'B-datetime', 
   6: 'I-datetime',
   7:'B-weather/attribute',
   8:'I-weather/attribute',
   9:'B-reminder/todo', 
   10:'I-reminder/todo', 
   11:'B-alarm/alarm_modifier',
   12:'B-reminder/noun',
   13:'B-reminder/recurring_period',
   14:'I-reminder/recurring_period',
   15:'B-reminder/reference',
   16:'I-reminder/noun',
   17:'B-reminder/reminder_modifier',
   18:'B-timer/noun',
   19:'I-reminder/reference',
   20:'B-negation',
   21:'B-timer/attributes',
   22:'B-news/type',
   23:'I-reminder/reminder_modifier',
   24:'B-weather/temperatureUnit',
   25:'I-alarm/alarm_modifier',
   26:"B-demonstrative_reference",
   27:"I-demonstrative_reference",
   28:"PAD" 
}

import torch 
import torch.nn as nn
import torch.nn.functional as F

# utils
import numpy as np
from matplotlib import pyplot as plt
import re
from collections import Counter
from seqeval.metrics import accuracy_score
from seqeval.metrics import classification_report
from seqeval.metrics import f1_score
from sklearn.metrics import confusion_matrix

class config_param:
  def __init__(self):
    self.max_len = 15
    self.learning_rate = 0.001
    self.total_epoch = 100
    self.batch = 256
    self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    self.DROPOUT = 0.2
    self.embedding_size = 200
    self.lstm_hidden_size = 100

cfg = config_param()

def convert_int(arr):
    try:
        a = int(arr)
    except:
        return None
    return a

# Make words dict	
words = []
data_file = open("/content/drive/MyDrive/NLU2/train-en.conllu", "r", encoding="utf-8")
i = 0 
data_sentences = data_file.read()
data_sentences_list = data_sentences.split("\n")
semantic_frame = []
semantic_frames_list = []
for sen in data_sentences_list:
         if len(sen)> 0 :
            semantic_frame.append(sen)
         else:
            semantic_frames_list.append(semantic_frame)
            semantic_frame = []
        
for frames in semantic_frames_list:
    # print(frames)
    for line in frames[3:]:
        line = line.strip().lower().split("\t")
        word = line[1]
        if convert_int(word) is not None:
                words.append('DIGIT' * len(word))
        else:        
                words.append(word)

words_vocab = sorted(set(words))
word_dict = {'UNK': 0, 'PAD': 1}

for i, item in enumerate(words_vocab):
    word_dict[item] = i + 2

def get_data(file_path):
  data_file = open(file_path, "r", encoding="utf-8")
  i = 0 
  data_sentences = data_file.read()
  data_sentences_list = data_sentences.split("\n")
  semantic_frame = []
  semantic_frames_list = []
  for sen in data_sentences_list:
         if len(sen)> 0 :
            semantic_frame.append(sen)
         else:
            semantic_frames_list.append(semantic_frame)
            semantic_frame = []
  return semantic_frames_list

word_dict

def makeindex(data_semantic_frames_list):
    train_data = []
    for frames in data_semantic_frames_list:
        for line in frames[3:]:
            line = line.strip().split("\t")
            word = line[1]
            sample_sentence = []
            sample_slot = []
            word = line[1]
            if word == '<=>':
                    real_length = index
                    break
            if convert_int(word) is not None:
                    word =  'DIGIT' * len(word)
            else:
                    pass
            slot = slots_dict[line[-1]]

            if word in word_dict:
                    sample_sentence.append(word_dict[word])
            else:
                    sample_sentence.append(word_dict['UNK'])

            sample_slot.append(slots_dict[line[-1]])

            train_intent = intents_dict[ line[-2] ]
            real_length = len(sample_sentence)
            while len(sample_sentence) < cfg.max_len:
                sample_sentence.append(word_dict['PAD'])
            while len(sample_slot) < cfg.max_len:
                sample_slot.append(slots_dict['NoLabel'])

        train_data.append([sample_sentence, real_length, sample_slot, train_intent])
    return train_data

semantic_frames_list_train = get_data("/content/drive/MyDrive/NLU2/train-en.conllu")
semantic_frames_list_test = get_data("/content/drive/MyDrive/NLU2/test-en.conllu")
semantic_frames_list_eval = get_data("/content/drive/MyDrive/NLU2/development-en.conllu")
train_data = makeindex(semantic_frames_list_train)
test_data = makeindex(semantic_frames_list_test)
eval_data = makeindex(semantic_frames_list_eval)
print(len(semantic_frames_list_train))
index2slot_dict = {}
for key in slots_dict:
    index2slot_dict[slots_dict[key]] = key


print('Number of training samples: ', len(train_data))
print('Number of test samples: ', len(test_data))
print('Number of words: ', len(word_dict))
print('Number of intent labels: ', len(intents_dict))
print('Number of slot labels', len(slots_dict))

import os
os.chdir("/content/drive/MyDrive/NLU2")

"""WORD Dictionary

data to index.

# **Utils Method.**
"""

import torch
import numpy as np

cnfg = config_param()
def make_mask(real_le, max_len=cnfg.max_len, label_size=len(slots_dict), batch=cnfg.batch):
    mask = torch.zeros(batch, max_len, label_size)
    for index, item in enumerate(real_le):
        mask[index, :item, :] = 1.0
    return mask

def masked_log_softmax(vector: torch.Tensor, mask: torch.Tensor, dim: int = -1) -> torch.Tensor:
    if mask is not None:
        mask = mask.float()
        while mask.dim() < vector.dim():
            mask = mask.unsqueeze(1)

        vector = vector + (mask + 1e-45).log()
    return torch.nn.functional.log_softmax(vector, dim=dim)

def one_hot(array, Num=len(slots_dict), maxlen=cnfg.max_len):

    shape = array.size()
    batch = shape[0]
    if len(shape) == 1:
        res = torch.zeros(batch, Num)
        for i in range(batch):
            res[i][array[i]] = 1
    else:
        res = torch.zeros(batch, maxlen, Num)
        for i in range(batch):
            for j in range(maxlen):
                if array[i, j] == Num:
                    pass
                else:
                    res[i][j][array[i, j]] = 1
    return res

import random

def get_batch(data, batch_size=cnfg.batch):
    random.shuffle(data)
    sindex = 0
    eindex = batch_size
    while eindex < len(data):

        sentence = []
        real_len = []
        slot_label = []
        intent_label = []
         
        batch = data[sindex:eindex]
        for m in range(sindex, eindex):
            sentence.append(data[m][0])
            real_len.append(data[m][1])
            slot_label.append(data[m][2])
            intent_label.append(data[m][3])

        temp = eindex
        eindex = eindex + batch_size
        sindex = temp

        yield (sentence, real_len, slot_label, intent_label)

"""#  Model"""

import torch 
import torch.nn as nn
import torch.nn.functional as F
cfg = config_param()
DROPOUT = cfg.DROPOUT
device = cfg.device
# Bi-model 
class slot_enc(nn.Module):
    def __init__(self, embedding_size, lstm_hidden_size, vocab_size=len(word_dict)):
        # print(vocab_size, embedding_size)
        super(slot_enc, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_size).to(device)
        self.lstm = nn.LSTM(input_size=embedding_size, hidden_size=lstm_hidden_size, num_layers=2, bidirectional=True, batch_first=True) 

    def forward(self, x):
        # print(x.size())
        x = self.embedding(x)
        # print(x.size())
        x = F.dropout(x, DROPOUT)       
        x, _ = self.lstm(x)
        x = F.dropout(x, DROPOUT)
        return x 

class slot_dec(nn.Module):
    def __init__(self, lstm_hidden_size, label_size=len(slots_dict)):
        super(slot_dec, self).__init__()
        self.lstm = nn.LSTM(input_size=lstm_hidden_size*5, hidden_size=lstm_hidden_size, num_layers=1)
        self.fc = nn.Linear(lstm_hidden_size, label_size)
        self.hidden_size = lstm_hidden_size

    def forward(self, x, hi):
        # print(x.size())
        batch = x.size(0)
        length = x.size(1)
        dec_init_out = torch.zeros(batch, 1, self.hidden_size).to(device)
        hidden_state = (torch.zeros(1, 1, self.hidden_size).to(device), \
                        torch.zeros(1, 1, self.hidden_size).to(device))
        x = torch.cat((x, hi), dim=-1)
        x = x.transpose(1, 0)  
        x = F.dropout(x, DROPOUT)
        all_out = []
        for i in range(length):
            # print(i,"##############")
            if i == 0:
                out, hidden_state = self.lstm(torch.cat((x[i].unsqueeze(1), dec_init_out), dim=-1), hidden_state)
            else:
                out, hidden_state = self.lstm(torch.cat((x[i].unsqueeze(1), out), dim=-1), hidden_state)
            all_out.append(out)
        output = torch.cat(all_out, dim=1)
        x = F.dropout(x, DROPOUT)
        res = self.fc(output)
        return res 

class intent_enc(nn.Module):
    def __init__(self, embedding_size, lstm_hidden_size, vocab_size=len(word_dict)):
        super(intent_enc, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_size).to(device)
        # self.embedding.weight.data.uniform_(-1.0, 1.0)
        self.lstm = nn.LSTM(input_size=embedding_size, hidden_size= lstm_hidden_size, num_layers=2,\
                            bidirectional= True, batch_first=True, dropout=DROPOUT)
    
    def forward(self, x):
        x = self.embedding(x)
        x = F.dropout(x, DROPOUT)
        x, _ = self.lstm(x)
        x = F.dropout(x, DROPOUT)
        return x


class intent_dec(nn.Module):
    def __init__(self, lstm_hidden_size, label_size=len(intents_dict)):
        super(intent_dec, self).__init__()
        self.lstm = nn.LSTM(input_size=lstm_hidden_size*4, hidden_size=lstm_hidden_size, batch_first=True, num_layers=1)#, dropout=DROPOUT)
        self.fc = nn.Linear(lstm_hidden_size, label_size)
        # print(label_size,"------------------------------------")
        
    def forward(self, x, hs, real_len):
        batch = x.size()[0]
        real_len = torch.tensor(real_len).to(device)
        x = torch.cat((x, hs), dim=-1)
        x = F.dropout(x, DROPOUT)
        x, _ = self.lstm(x)
        x = F.dropout(x, DROPOUT)

        index = torch.arange(batch).long().to(device)
        # print("++++++")
        # print(real_len-1)
        state = x[index, real_len-1, :]
        # print(state)
        res = self.fc(state.squeeze())
        return res
        
class Intent(nn.Module):
    def __init__(self):
        super(Intent, self).__init__()
        self.enc = intent_enc(cfg.embedding_size, cfg.lstm_hidden_size).to(device)
        self.dec = intent_dec(cfg.lstm_hidden_size).to(device)
        self.share_memory = torch.zeros(cfg.batch, cfg.max_len, cfg.lstm_hidden_size * 2).to(device)
    
class Slot(nn.Module):
    def __init__(self):
        super(Slot, self).__init__()
        self.enc = slot_enc(cfg.embedding_size, cfg.lstm_hidden_size).to(device)
        self.dec = slot_dec(cfg.lstm_hidden_size).to(device)
        self.share_memory = torch.zeros(cfg.batch, cfg.max_len, cfg.lstm_hidden_size * 2).to(device)

train_data

np.random.shuffle(train_data)

from torch import optim
import numpy as np
import torch
import random

"""# **Train**"""

# Commented out IPython magic to ensure Python compatibility.
# %%time
# from torch import optim
# import numpy as np
# import torch
# import random
# # from data2index_ver2 import train_data, test_data, index2slot_dict
# random.shuffle(train_data)
# train_data = train_data
# cfg = config_param()
# device = cfg.device
# epoch_num = cfg.total_epoch
# 
# slot_model = Slot().to(device)
# intent_model = Intent().to(device)
# 
# # print(slot_model)
# # print(intent_model)
# loss_intent = []
# loss_slot = []
# slot_optimizer = optim.Adam(slot_model.parameters(), lr=cfg.learning_rate)       # optim.Adamax
# intent_optimizer = optim.Adam(intent_model.parameters(), lr=cfg.learning_rate)   # optim.Adamax
# 
# best_correct_num = 0
# best_epoch = -1
# best_F1_score = 0.0
# best_epoch_slot = -1
# for epoch in range(epoch_num):
#     print(epoch)
#     slot_loss_history = []
#     intent_loss_history = []
#     for batch_index, data in enumerate(get_batch(train_data)):
#         sentence, real_len, slt_label, intent_label = data
#         
#         mask = make_mask(real_len).to(device)
#         x = torch.tensor(sentence).to(device)
#         
#         y_slot = torch.tensor(slt_label).to(device)
#         y_slot = one_hot(y_slot).to(device)
#       
#         y_intent = torch.tensor(intent_label).to(device)
#         y_intent = one_hot(y_intent,Num = 12).to(device)
#   
#         slot_optimizer.zero_grad()
#         intent_optimizer.zero_grad()
#     
#         hs = slot_model.enc(x)
#         slot_model.share_memory = hs.clone()
#        
#         hi = intent_model.enc(x)
#         intent_model.share_memory = hi.clone()
#     
#         slot_logits = slot_model.dec(hs, intent_model.share_memory.detach())
#         log_slot_logits = masked_log_softmax(slot_logits, mask, dim=-1)
#         slot_loss = -1.0 * torch.sum(y_slot*log_slot_logits)
#        
#         slot_loss_history.append(slot_loss.item())
#         slot_loss.backward()
#         torch.nn.utils.clip_grad_norm_(slot_model.parameters(), 5.0)
#         slot_optimizer.step()
#      
#         intent_logits = intent_model.dec(hi, slot_model.share_memory.detach(), real_len)
#      
#         log_intent_logits = F.log_softmax(intent_logits, dim=-1)
#         
#         intent_loss = -1.0*torch.sum(y_intent*log_intent_logits)
#       
#         intent_loss_history.append(intent_loss.item())
#         intent_loss.backward()
#         torch.nn.utils.clip_grad_norm_(intent_model.parameters(), 5.0)
#         intent_optimizer.step()
#         
# 		# Log
#         if batch_index % 100 == 0 and batch_index > 0:
#             loss_intent.append(sum(intent_loss_history[-100:])/100.0)
#             loss_slot.append(sum(slot_loss_history[-100:])/100.0)
#             print('Slot loss: {:.4f} \t Intent loss: {:.4f}'.format(sum(slot_loss_history[-100:])/100.0, \
#                 sum(intent_loss_history[-100:])/100.0))
#       
#     # Evaluation
#     y_true = []
#     y_pred = []
#     loss = 0
#     np.random.shuffle(eval_data)
#     total_test = len(eval_data)
#     correct_num = 0
#     F1_score = 0
#     slot_label_predict_list = []
#     slot_label_test_list = []
#     batch_data = get_batch(eval_data, batch_size=1)
#     for batch_index, data_test in enumerate(batch_data):
#         sentence_test, real_len_test, slot_label_test, intent_label_test = data_test
#         x_test = torch.tensor(sentence_test).to(device)
#         mask_test = make_mask(real_len_test, batch=1).to(device)
#         # Slot model generate hs_test and intent model generate hi_test
#         hs_test = slot_model.enc(x_test)
#         hi_test = intent_model.enc(x_test)
# 
#         # Slot
#         slot_logits_test = slot_model.dec(hs_test, hi_test)
#         log_slot_logits_test = masked_log_softmax(slot_logits_test, mask_test, dim=-1)
#         slot_pred_test = torch.argmax(log_slot_logits_test, dim=-1)
#         # Intent
#         intent_logits_test = intent_model.dec(hi_test, hs_test, real_len_test)
#         log_intent_logits_test = F.log_softmax(intent_logits_test, dim=-1)
#         res_test = torch.argmax(log_intent_logits_test, dim=-1)
#         y_true.append(intent_label_test[0])
#         y_pred.append(res_test.item())
#         y = one_hot(torch.tensor(intent_label_test),Num = 12).to(device)
#         loss += -1 * torch.sum(log_intent_logits_test* y ).detach()
#         if res_test.item() == intent_label_test[0]:
#             correct_num += 1
#         if correct_num > best_correct_num:
#             best_correct_num = correct_num
#             best_epoch = epoch
#             torch.save(intent_model, '/content/drive/MyDrive/model_intent_best.ckpt')
#             torch.save(slot_model, '/content/drive/MyDrive/model_slot_best.ckpt')
# 			 
#    
#     #     # Calc slot F1 score
#         
#         slot_pred_test = slot_pred_test[0][:real_len_test[0]]
#         slot_label_test = slot_label_test[0][:real_len_test[0]]
# 
#         slot_pred_test = [int(item) for item in slot_pred_test]
#         slot_label_test = [int(item) for item in slot_label_test]
# 
#         slot_pred_test = [index2slot_dict[item] for item in slot_pred_test]
#         slot_label_test = [index2slot_dict[item] for item in slot_label_test]
#         slot_label_predict_list.append(slot_pred_test)
#         slot_label_test_list.append(slot_label_test)
#     F1_score = f1_score(slot_label_test_list, slot_label_predict_list)
#     if F1_score > best_F1_score:
#         best_F1_score = F1_score
#         best_epoch_slot = epoch
#     print('*'*20)
#     print('Epoch: [{}/{}], Intent Val Acc: {:.4f} \t Slot F1 score: {:.4f}'.format(epoch+1, epoch_num, 100.0*correct_num/total_test, 100*F1_score))
#     print('*'*20)
#     # print(confusion_matrix(y_true,y_pred))
#     print(loss / total_test)
#     print('Best Intent Acc: {:.4f} at Epoch: [{}]'.format(100.0*best_correct_num/total_test, best_epoch+1))
#     print('Best F1 score: {:.4f} at Epoch: [{}]'.format(best_F1_score, best_epoch_slot+1))
#     print('#'*20)
# plt.plot(loss_intent)
# plt.plot(loss_slot,color="red")
# plt.show()
#

test_data = test_data
total_test = len(test_data)
correct_num = 0
F1_score = 0
slot_label_predict_list = []
slot_label_test_list = []
y_pred = []
y_true = []
intent_model =torch.load( '/content/drive/MyDrive/model_intent_best.ckpt')
slot_model = torch.load( '/content/drive/MyDrive/model_slot_best.ckpt')
batch_data = get_batch(test_data, batch_size=1)
for batch_index, data_test in enumerate(batch_data):
        sentence_test, real_len_test, slot_label_test, intent_label_test = data_test
        x_test = torch.tensor(sentence_test).to(device)
        mask_test = make_mask(real_len_test, batch=1).to(device)
        # Slot model generate hs_test and intent model generate hi_test
        hs_test = slot_model.enc(x_test)
        hi_test = intent_model.enc(x_test)

        # Slot
        slot_logits_test = slot_model.dec(hs_test, hi_test)
        log_slot_logits_test = masked_log_softmax(slot_logits_test, mask_test, dim=-1)
        slot_pred_test = torch.argmax(log_slot_logits_test, dim=-1)
        # Intent
        intent_logits_test = intent_model.dec(hi_test, hs_test, real_len_test)
        log_intent_logits_test = F.log_softmax(intent_logits_test, dim=-1)
        res_test = torch.argmax(log_intent_logits_test, dim=-1)
        y_true.append(intent_label_test[0])
        y_pred.append(res_test.item())

        if res_test.item() == intent_label_test[0]:
            correct_num += 1


        slot_pred_test = slot_pred_test[0][:real_len_test[0]]
        slot_label_test = slot_label_test[0][:real_len_test[0]]

        slot_pred_test = [int(item) for item in slot_pred_test]
        slot_label_test = [int(item) for item in slot_label_test]

        slot_pred_test = [index2slot_dict[item] for item in slot_pred_test]
        slot_label_test = [index2slot_dict[item] for item in slot_label_test]
        # print(slot_pred_test)
        # print(slot_label_test)
        slot_label_predict_list.append(slot_pred_test)
        slot_label_test_list.append(slot_label_test)
        y = one_hot(torch.tensor(intent_label_test),Num = 12).to(device)
        # intent_loss = -1.0*torch.sum(intent_label_test[0]*log_intent_logits_test)
        # slot_loss = -1.0 * torch.sum(slot_label_test[0][:real_len_test[0]] * log_slot_logits_test)
        # print(res_test.item() , intent_label_test[0])
        # print(-1 * torch.sum(log_intent_logits_test* y ).detach())
F1_score = f1_score(slot_label_test_list, slot_label_predict_list)
from sklearn.metrics import confusion_matrix
print(F1_score)
print(correct_num/ len(test_data))
print(confusion_matrix(y_true, y_pred))