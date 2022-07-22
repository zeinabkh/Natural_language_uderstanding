# -*- coding: utf-8 -*-
"""train_2_nlu3.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1WRQwAezbjOmqm0In7CU9Mep096VaXObH
"""

!pip install transformers
!pip install tokenizers

from google.colab import drive
drive.mount('/content/drive')

import json
from transformers import BertTokenizer, BertForMaskedLM,BertConfig

sentence = []
with open("/content/drive/MyDrive/NLU3/train_samples.json", "r", encoding='utf-8') as reader:
        input_data = json.load(reader)["data"][:300]
for i, entry in enumerate(input_data):
        for paragraph in entry["paragraphs"]:
            sentence.append(paragraph["context"])
            for qa in paragraph["qas"]:
                sentence.append(qa["question"])

tokenizer = BertTokenizer.from_pretrained("HooshvareLab/bert-fa-base-uncased")

import torch
labels = []
mask = []
for sent in sentence:
    
    tok = tokenizer(sent, padding='max_length', truncation=True,max_length= 256)
    labels.append(tok.input_ids)
    mask.append(tok.attention_mask)
labels = torch.tensor(labels)
mask = torch.tensor(mask)

del sentence

# make copy of labels tensor, this will be input_ids
input_ids = labels.detach().clone()
# create random array of floats with equal dims to input_ids
rand = torch.rand(input_ids.shape)
# mask random 15% where token is not 0 [PAD], 1 [CLS], or 2 [SEP]
mask_arr = (rand < .15) * (input_ids != 0) * (input_ids != 1) * (input_ids != 2)
# loop through each row in input_ids tensor (cannot do in parallel)
for i in range(input_ids.shape[0]):
    # get indices of mask positions from mask array
    selection = torch.flatten(mask_arr[i].nonzero()).tolist()
    # mask input_ids
    input_ids[i, selection] = 3  # our custom [MASK] token == 3
encodings = {'input_ids': input_ids, 'attention_mask': mask, 'labels': labels}

class Dataset(torch.utils.data.Dataset):
    def __init__(self, encodings):
        # store encodings internally
        self.encodings = encodings

    def __len__(self):
        # return the number of samples
        return self.encodings['input_ids'].shape[0]

    def __getitem__(self, i):
        # return dictionary of input_ids, attention_mask, and labels for index i
        return {key: tensor[i] for key, tensor in self.encodings.items()}

dataset = Dataset(encodings)
loader = torch.utils.data.DataLoader(dataset, batch_size=8, shuffle=True)

# from transformers import RobertaConfig

config = BertConfig( vocab_size=tokenizer.vocab_size,
                    hidden_size = 768,
                    num_hidden_layers = 3,
                    num_attention_heads = 3,
                    # intermediate_size = 3072,
                    hidden_act = 'gelu',
                    hidden_dropout_prob = 0.1,
                    attention_probs_dropout_prob = 0.1,
                    type_vocab_size = 2,
               
                   ) 


model = BertForMaskedLM(config)
model.parameters()

sum(p.numel() for p in model.parameters())

from tqdm.auto import tqdm
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
# and move our model over to the selected device
model.to(device)
epochs = 2
from transformers import AdamW
# activate training mode
model.train()
# initialize optimizer
optim = AdamW(model.parameters(), lr=1e-4)
for epoch in range(epochs):
    # setup loop with TQDM and dataloader
    loop = tqdm(loader, leave=True)
    for batch in loop:
        # initialize calculated gradients (from prev step)
        optim.zero_grad()
        # pull all tensor batches required for training
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)
        # process
        outputs = model(input_ids, attention_mask=attention_mask,
                        labels=labels)
        # extract loss
        loss = outputs.loss
        # calculate loss for every parameter that needs grad update
        loss.backward()
        # update parameters
        optim.step()
        # print relevant info to progress bar
        loop.set_description(f'Epoch {epoch}')
        loop.set_postfix(loss=loss.item())

model.save_pretrained("/content/drive/MyDrive/NLU3_s/train_model_large_10_15")