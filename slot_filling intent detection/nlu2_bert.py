# -*- coding: utf-8 -*-
"""NLU2_MODEL2_9_23.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ySlAGlZekTQUy1ulLqoro4WN1_JpZqtO
"""

!pip install seqeval
!pip install transformers
!pip install bertviz

from google.colab import drive
drive.mount('/content/drive')

import numpy as np
from collections import Counter
import copy
import json
from sklearn.metrics import accuracy_score 
from seqeval.metrics import f1_score
import torch
import  torch.nn as nn
from torch.utils.data import TensorDataset
from transformers import BertPreTrainedModel, BertModel, BertConfig, BertTokenizer,DistilBertConfig
from bertviz import head_view

class config_param:
  def __init__(self):
    self.max_len = 15
    self.learning_rate = 0.001
    self.total_epoch = 150
    self.batch = 16
    # self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # print(self.device)
    self.DROPOUT = 0.1
    self.embedding_size = 300
    self.lstm_hidden_size = 100

"""# **LABELS**"""

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

"""# **LOAD Dataset**"""

def convert_int(arr):
    try:
        a = int(arr)
    except:
        return None
    return a
def clean_Normalize(text):
    clean_text = re.sub(r"[0-9]+minutes|[0-9]+seconds|[0-9]+.[0-9]+|[0-9]+am|[0-9]+:[0-9]+|[0-9]+am|[0-9]+pm|[0-9]+PM|[0-9]+p|[0-9]+a|[0-9]+( )pm|[0-9]+( )am|[0-9]+( )AM|[0-9]+( )PM","time ",text)
    clean_text = clean_text.replace("."," .").replace("?"," ?").replace(";"," ;").replace(","," ,").replace(":"," :").replace("/"," /").replace('"',' " ').replace("th"," th")
    return clean_text


def load_data(path_data):
    cnfg = config_param()
    data_file = open(path_data, "r", encoding="utf-8")
    i = 0 
    data = []
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
        
            l= 0 
    # print(semantic_frames_list[:10])
    sentences_index,real_len, slots_label = [],[],[] 
    # int_test = []
    all_token_list = []
    zero_lable = 0
    for s_frame in semantic_frames_list:
        if len(s_frame) == 0:
            continue
        slots_tag = []
        sen = []
        for slot in s_frame[3:]:
              d = slot.split("\t")
              # slots_tag.append(intents_dict[d[-2]])
              slots_tag.append(slots_dict[d[-1]])
              all_token_list.append(d[1])
              if convert_int(d[1]) is not None:
                sen.append("digit_term")
              else:
                sen.append(d[1])
              intnt = d[-2]
              # if len(sen) > cnfg.max_len:
              #      real_len.append(cnfg.max_len)
              # else:
              #      real_len.append(len(sen))
              # while len(sen)< cnfg.max_len:
              #       sen.append("PAD")
              #       slots_tag.append(slots_dict['PAD'])
        semantic_frame_info ={
        "words":sen ,
        "slot_label":slots_tag,
        "intent_label" : intents_dict[d[-2]]
        }
        data.append(semantic_frame_info)

    return data

class InputExample(object):
    """
    A single training/test example for simple sequence classification.
    Args:
        guid: Unique id for the example.
        words: list. The words of the sequence.
        intent_label: (Optional) string. The intent label of the example.
        slot_labels: (Optional) list. The slot labels of the example.
    """

    def __init__(self, guid, words, intent_label=None, slot_labels=None):
        self.guid = guid
        self.words = words
        self.intent_label = intent_label
        self.slot_labels = slot_labels

    def __repr__(self):
        return str(self.to_json_string())

    def to_dict(self):
        """Serializes this instance to a Python dictionary."""
        output = copy.deepcopy(self.__dict__)
        return output

    def to_json_string(self):
        """Serializes this instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


class InputFeatures(object):
    """A single set of features of data."""

    def __init__(self, input_ids, attention_mask, token_type_ids, intent_label_id, slot_labels_ids):
        self.input_ids = input_ids
        self.attention_mask = attention_mask
        self.token_type_ids = token_type_ids
        self.intent_label_id = intent_label_id
        self.slot_labels_ids = slot_labels_ids

    def __repr__(self):
        return str(self.to_json_string())

    def to_dict(self):
        """Serializes this instance to a Python dictionary."""
        output = copy.deepcopy(self.__dict__)
        return output

    def to_json_string(self):
        """Serializes this instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

def convert_examples_to_features(examples, max_seq_len, tokenizer,
                                 pad_token_label_id=-100,
                                 cls_token_segment_id=0,
                                 pad_token_segment_id=0,
                                 sequence_a_segment_id=0,
                                 mask_padding_with_zero=True):
    # Setting based on the current model type
    cls_token = tokenizer.cls_token
    sep_token = tokenizer.sep_token
    unk_token = tokenizer.unk_token
    pad_token_id = tokenizer.pad_token_id

    features = []
    for (ex_index, example) in enumerate(examples):
        if ex_index % 5000 == 0:
            print("Writing example %d of %d" % (ex_index, len(examples)))

        # Tokenize word by word (for NER)
        tokens = []
        slot_labels_ids = []
        for word, slot_label in zip(example['words'], example['slot_label']):
            word_tokens = tokenizer.tokenize(word)
            if not word_tokens:
                word_tokens = [unk_token]  # For handling the bad-encoded word
            tokens.extend(word_tokens)
            # Use the real label id for the first token of the word, and padding ids for the remaining tokens
            slot_labels_ids.extend([int(slot_label)]+[pad_token_label_id]*(len(word_tokens) -1))
            # slot_labels_ids.extend([int(slot_label)] + [pad_token_label_id] * (len(word_tokens) - 1))

        # Account for [CLS] and [SEP]
        special_tokens_count = 2
        if len(tokens) > max_seq_len - special_tokens_count:
            tokens = tokens[:(max_seq_len - special_tokens_count)]
            slot_labels_ids = slot_labels_ids[:(max_seq_len - special_tokens_count)]
        # Add [SEP] token
        tokens += [sep_token]
        slot_labels_ids += [pad_token_label_id]
        token_type_ids = [sequence_a_segment_id] * len(tokens)
        # Add [SEP] token
        # tokens += [sep_token]
        # slot_labels_ids += [pad_token_label_id]
        # token_type_ids = [sequence_a_segment_id] * len(tokens)

        # Add [CLS] token
        tokens = [cls_token] + tokens
        slot_labels_ids = [pad_token_label_id] + slot_labels_ids
        token_type_ids = [cls_token_segment_id] + token_type_ids

        input_ids = tokenizer.convert_tokens_to_ids(tokens)

        # The mask has 1 for real tokens and 0 for padding tokens. Only real
        # tokens are attended to.
        attention_mask = [1 if mask_padding_with_zero else 0] * len(input_ids)

        # Zero-pad up to the sequence length.
        padding_length = max_seq_len - len(input_ids)
        input_ids = input_ids + ([pad_token_id] * padding_length)
        attention_mask = attention_mask + ([0 if mask_padding_with_zero else 1] * padding_length)
        token_type_ids = token_type_ids + ([pad_token_segment_id] * padding_length)
        slot_labels_ids = slot_labels_ids + ([pad_token_label_id] * padding_length)

        assert len(input_ids) == max_seq_len, "Error with input length {} vs {}".format(len(input_ids), max_seq_len)
        assert len(attention_mask) == max_seq_len, "Error with attention mask length {} vs {}".format(len(attention_mask), max_seq_len)
        assert len(token_type_ids) == max_seq_len, "Error with token type length {} vs {}".format(len(token_type_ids), max_seq_len)
        assert len(slot_labels_ids) == max_seq_len, "Error with slot labels length {} vs {}".format(len(slot_labels_ids), max_seq_len)

        intent_label_id = int(example['intent_label'])

      # [str(x) for x in slot_labels_ids]

        features.append(
            InputFeatures(input_ids=input_ids,
                          attention_mask=attention_mask,
                          token_type_ids=token_type_ids,
                          intent_label_id=intent_label_id,
                          slot_labels_ids=slot_labels_ids
                          ))

    return features


def load_and_cache_examples(args, tokenizer, mode):
    cached_features_file = os.path.join(
        args.data_dir,
        'matus_cached_{}_{}'.format(
            mode,
            args.max_seq_len
        )
    )
    if mode =="train":
          examples = load_data("/content/drive/MyDrive/NLU2/train-en.conllu")[:25000]
    elif mode =="test":
          examples = load_data("/content/drive/MyDrive/NLU2/test-en.conllu")
    else:
         examples = load_data("/content/drive/MyDrive/NLU2/development-en.conllu")[:2000]
        # Use cross entropy ignore index as padding label id so that only real label ids contribute to the loss later
    pad_token_label_id = args.ignore_index
    features = convert_examples_to_features(examples, args.max_seq_len, tokenizer,
                                                pad_token_label_id=pad_token_label_id)
    torch.save(features, cached_features_file)

    # Convert to Tensors and build dataset
    all_input_ids = torch.tensor([f.input_ids for f in features], dtype=torch.long)
    all_attention_mask = torch.tensor([f.attention_mask for f in features], dtype=torch.long)
    all_token_type_ids = torch.tensor([f.token_type_ids for f in features], dtype=torch.long)
    all_intent_label_ids = torch.tensor([f.intent_label_id for f in features], dtype=torch.long)
    all_slot_labels_ids = torch.tensor([f.slot_labels_ids for f in features], dtype=torch.long)

    dataset = TensorDataset(all_input_ids, all_attention_mask,
                            all_token_type_ids, all_intent_label_ids, all_slot_labels_ids)
    
    return dataset

"""# **MODEls**

**classifiers**
"""

class Intent_detection(nn.Module):
  def __init__(self,input_size, intent_class_num,dropout_rate ):
    super(Intent_detection, self).__init__()
    self.drop_out = nn.Dropout(dropout_rate)
    self.fully_connected = nn.Linear(input_size, intent_class_num )


  def forward(self,x):
    x = self.drop_out(x)
    y = self.fully_connected(x)
    return y
class Slot_filling(nn.Module):
  def __init__(self,input_size, slot_class_num,dropout_rate ):
    super(Slot_filling, self).__init__()
    self.drop_out = nn.Dropout(dropout_rate)
    self.fully_connected = nn.Linear(input_size, slot_class_num )


  def forward(self,x):
    x = self.drop_out(x)
    y = self.fully_connected(x)
    return y

"""# Joint Model"""

class Joint_Bert_Model(BertPreTrainedModel):

  def __init__(self,config, args,slot_class_num,intent_class_num):
    super(Joint_Bert_Model, self).__init__(config)
    self.bert =BertModel(config=config)
    self.num_slot_labels = slot_class_num
    self.args= args
    self.num_intent_labels = intent_class_num
    self.slot_filler = Slot_filling(config.hidden_size, self.num_slot_labels, args.dropout_rate)
    self.intent_detector = Intent_detection(config.hidden_size, self.num_intent_labels, args.dropout_rate)
    

  def forward(self,input_ids, attention_mask, token_type_ids, intent_label_ids, slot_labels_ids ):
    
      outputs = self.bert(input_ids, attention_mask=attention_mask,
                              token_type_ids=token_type_ids)  # sequence_output, pooled_output, (hidden_states), (attentions)
      sequence_output = outputs[0]
      pooled_output = outputs[1]  # [CLS]
      attention_output = outputs[-1]
      # print(sequence_output.size(),pooled_output.size(),"???????????")
      
      # print(sequence_output.size(),pooled_output.size(),"???????????")
      seq_input = torch.zeros((sequence_output.size()[0],sequence_output.size()[1],sequence_output.size()[2]))
      for i in range(self.args.max_seq_len):
            seq_input[:,i,:] +=sequence_output[:,i,:]+ pooled_output
      intent_logits = self.intent_detector(pooled_output)
      slot_logits = self.slot_filler(seq_input)
      total_loss = 0
      # print(cls_output.size(),intent_logits.view(-1, self.num_intent_labels).size(), intent_label_ids.view(-1).size())
      # get intent label
      if intent_label_ids is not None:
            if self.num_intent_labels == 1:
                intent_loss_fct = nn.BinaryCrossEntropyLoss()
                intent_loss = intent_loss_fct(intent_logits.view(-1), intent_label_ids.view(-1))
            else:
                intent_loss_fct = nn.CrossEntropyLoss()
                intent_loss = intent_loss_fct(intent_logits.view(-1, self.num_intent_labels), intent_label_ids.view(-1))
            total_loss += intent_loss
      if slot_labels_ids is not None:
            slot_loss_fct = nn.CrossEntropyLoss(ignore_index=self.args.ignore_index)
                # Only keep active parts of the loss
            if attention_mask is not None:
                    active_loss = attention_mask.view(-1) == 1
                    active_logits = slot_logits.view(-1, self.num_slot_labels)[active_loss]
                    active_labels = slot_labels_ids.view(-1)[active_loss]
                    slot_loss = slot_loss_fct(active_logits, active_labels)
            else:
                    slot_loss = slot_loss_fct(slot_logits.view(-1, self.num_slot_labels), slot_labels_ids.view(-1))
            total_loss += self.args.slot_loss_coef * slot_loss

      outputs = ((intent_logits, slot_logits),) + outputs[2:]  # add hidden states and attention if they are here

      outputs = (total_loss,) + outputs
    
      return outputs ,attention_output[0]

MODEL_CLASSES = {
    'bert': (BertConfig, Joint_Bert_Model, BertTokenizer),
    # 'bert': (BertConfig, Joint_Bert_Model, BertTokenizer),
    # 'distilbert': (DistilBertConfig, JointDistilBERT, DistilBertTokenizer),
    # 'albert': (AlbertConfig, JointAlbert, AlbertTokenizer)
}

MODEL_PATH_MAP = {
    'bert': 'bert-base-uncased',
    # 'bert':'distilbert-base-uncased',
    'distilbert': 'distilbert-base-uncased',
    'albert': 'albert-xxlarge-v1'
}

"""#F score """

def f_score_metric(predict_slots, true_slots):
  F_score  = f1_score(true_slots, predict_slots,average="micro")
  return F_score

"""# ***Train Model*** """

import os
import logging
from tqdm import tqdm, trange

import numpy as np
import torch
from torch.utils.data import DataLoader, RandomSampler, SequentialSampler
from transformers import BertConfig, AdamW, get_linear_schedule_with_warmup

# from utils import MODEL_CLASSES, compute_metrics, get_intent_labels, get_slot_labels

logger = logging.getLogger(__name__)

class Trainer(object):
    def __init__(self, args, train_dataset=None, dev_dataset=None, test_dataset=None,model_type = 'bert'):
        torch.autograd.set_detect_anomaly(True)
        self.args = args
        self.train_dataset = train_dataset
        self.dev_dataset = dev_dataset
        self.test_dataset = test_dataset
        self.intent_label_lst = list(intents_dict.items())
        self.slot_label_lst = list(slots_dict.items())
        # Use cross entropy ignore index as padding label id so that only real label ids contribute to the loss later
        self.pad_token_label_id = args.ignore_index
        self.config_class, self.model_class,_ = MODEL_CLASSES[model_type]
        self.config = self.config_class.from_pretrained(args.model_name_or_path, finetuning_task=args.task,output_attentions=True,)
        self.model = self.model_class.from_pretrained(args.model_name_or_path,
                                                      config = self.config,
                                                      args = args,
                                                      slot_class_num=len(self.slot_label_lst),
                                                      intent_class_num=len(self.intent_label_lst))

        # GPU or CPU
        self.device = "cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu"
        self.model.to(self.device)

    def train(self,tokenizer):
        train_sampler = RandomSampler(self.train_dataset)
        train_dataloader = DataLoader(self.train_dataset, sampler=train_sampler, batch_size=self.args.train_batch_size)
       
        if self.args.max_steps > 0:
            t_total = self.args.max_steps
            self.args.num_train_epochs = self.args.max_steps // (len(train_dataloader) // self.args.gradient_accumulation_steps) + 1
        else:
            t_total = len(train_dataloader) // self.args.gradient_accumulation_steps * self.args.num_train_epochs
    
        # Prepare optimizer and schedule (linear warmup and decay)
        no_decay = ['bias', 'LayerNorm.weight']
        optimizer_grouped_parameters = [
            {'params': [p for n, p in self.model.named_parameters() if not any(nd in n for nd in no_decay)],
             'weight_decay': self.args.weight_decay},
            {'params': [p for n, p in self.model.named_parameters() if any(nd in n for nd in no_decay)], 'weight_decay': 0.0}
        ]
        optimizer = AdamW(optimizer_grouped_parameters, lr=self.args.learning_rate, eps=self.args.adam_epsilon)
        scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=self.args.warmup_steps, num_training_steps=t_total)
        global_step = 0
        tr_loss = 0.0
        self.model.zero_grad()
        for epoch in range(int(self.args.num_train_epochs)):
            print(epoch)
            # epoch_iterator = tqdm(train_dataloader, desc="Iteration")
            for step, batch in enumerate(train_dataloader):
                self.model.train()
                batch = tuple(t.to(self.device) for t in batch)  # GPU or CPU
                inputs = {'input_ids': batch[0],
                          'attention_mask': batch[1],
                          'intent_label_ids': batch[3],
                          'slot_labels_ids': batch[4]}
                if self.args.model_type != 'distilbert':
                    inputs['token_type_ids'] = batch[2]
                outputs,_ = self.model(**inputs)
                # print("out puts",outputs)
                loss = outputs[0]
                if self.args.gradient_accumulation_steps > 1:
                    loss = loss / self.args.gradient_accumulation_steps

                loss.backward()

                tr_loss += loss.item()
                if (step + 1) % self.args.gradient_accumulation_steps == 0:
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.args.max_grad_norm)

                    optimizer.step()
                    scheduler.step()  # Update learning rate schedule
                    self.model.zero_grad()
            global_step += 1

            if self.args.logging_steps > 0 and global_step % self.args.logging_steps == 0:
                        self.evaluate("dev",tokenizer)

            # if self.args.save_steps > 0 and global_step % self.args.save_steps == 0:
                        

            if 0 < self.args.max_steps < global_step:
                    epoch_iterator.close()
                    break

            if 0 < self.args.max_steps < global_step:
                train_iterator.close()
                break
        self.save_model()
        return global_step, tr_loss / global_step

    def evaluate(self, mode,tokenizer):
        if mode == 'test':
            dataset = self.test_dataset
        elif mode == 'dev':
            dataset = self.dev_dataset
        else:
            raise Exception("Only dev and test dataset available")

        eval_sampler = SequentialSampler(dataset)
        eval_dataloader = DataLoader(dataset, sampler=eval_sampler, batch_size=self.args.eval_batch_size)

        # Eval!
        # logger.info("***** Running evaluation on %s dataset *****", mode)
        # logger.info("  Num examples = %d", len(dataset))
        # logger.info("  Batch size = %d", self.args.eval_batch_size)
        eval_loss = 0.0
        nb_eval_steps = 0
        intent_preds = None
        slot_preds = None
        out_intent_label_ids = None
        out_slot_labels_ids = None

        self.model.eval()

        for batch in eval_dataloader:
            batch = tuple(t.to(self.device) for t in batch)
            with torch.no_grad():
                inputs = {'input_ids': batch[0],
                          'attention_mask': batch[1],
                          'intent_label_ids': batch[3],
                          'slot_labels_ids': batch[4]}
                if self.args.model_type != 'distilbert':
                    inputs['token_type_ids'] = batch[2]
                outputs,attention_output = self.model(**inputs)
                tmp_eval_loss, (intent_logits, slot_logits) = outputs[:2]

                eval_loss += tmp_eval_loss.mean().item()
            nb_eval_steps += 1
           
            # Intent prediction
            if intent_preds is None:
                intent_preds = intent_logits.detach().cpu().numpy()
                out_intent_label_ids = inputs['intent_label_ids'].detach().cpu().numpy()
            else:
                intent_preds = np.append(intent_preds, intent_logits.detach().cpu().numpy(), axis=0)
                out_intent_label_ids = np.append(
                    out_intent_label_ids, inputs['intent_label_ids'].detach().cpu().numpy(), axis=0)

            # Slot prediction
            if slot_preds is None:
               
                slot_preds = slot_logits.detach().cpu().numpy()

                out_slot_labels_ids = inputs["slot_labels_ids"].detach().cpu().numpy()
            else:
               
                slot_preds = np.append(slot_preds, slot_logits.detach().cpu().numpy(), axis=0)

                out_slot_labels_ids = np.append(out_slot_labels_ids, inputs["slot_labels_ids"].detach().cpu().numpy(), axis=0)

        eval_loss = eval_loss / nb_eval_steps
        results = {
            "loss": eval_loss
        }

        # Intent result
        intent_preds = np.argmax(intent_preds, axis=1)
        
        # Slot result
        slot_preds = np.argmax(slot_preds, axis=2)
        out_slot_label_list = [[] for _ in range(out_slot_labels_ids.shape[0])]
        slot_preds_list = [[] for _ in range(out_slot_labels_ids.shape[0])]

        for i in range(out_slot_labels_ids.shape[0]):
            for j in range(out_slot_labels_ids.shape[1]):
                if out_slot_labels_ids[i, j] != self.pad_token_label_id:
                    out_slot_label_list[i].append(index2slot_dict[out_slot_labels_ids[i][j]])
                    slot_preds_list[i].append(index2slot_dict[slot_preds[i][j]])
        # attention view
        tokens = tokenizer.convert_ids_to_tokens(list(inputs['input_ids'][-1]))
        # print(attention_output[-2:-1].size())
        # head_view(attention_output, tokens)
        print("accuracy score intent detection", accuracy_score(intent_preds, out_intent_label_ids))
       
        f_score = f_score_metric( slot_preds_list, out_slot_label_list)
        print('slot fscore',f_score)
        results['slot fscore'] = f_score
        return results

    def save_model(self):
        # Save model checkpoint (Overwrite)
        if not os.path.exists(self.args.model_dir):
            os.makedirs(self.args.model_dir)
        model_to_save = self.model.module if hasattr(self.model, 'module') else self.model
        model_to_save.save_pretrained(self.args.model_dir)

        # Save training arguments together with the trained model
        torch.save(self.args, os.path.join(self.args.model_dir, 'training_args.bin'))
        print("Saving model checkpoint to %s", self.args.model_dir)

    def load_model(self):
        # Check whether model exists
        if not os.path.exists(self.args.model_dir):
            raise Exception("Model doesn't exists! Train first!")

        try:
            self.model = self.model_class.from_pretrained(self.args.model_dir,
                                                          args=self.args, 
                                                      config = self.config,
                          
                                                      slot_class_num=len(self.slot_label_lst),
                                                      intent_class_num=len(self.intent_label_lst))
            self.model.to(self.device)
           
        except:
            raise Exception("Some model files might be missing...")

"""# **RUN**"""

class config_param:
  def __init__(self):
    self.max_seq_len = 15
    self.learning_rate = 5e-5
    self.num_train_epochs = 4
    self.train_batch_size = 32
    self.eval_batch_size = 64
    # self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # print(self.device)
    self.dropout_rate = 0.1
    self.embedding_size = 200
    self.lstm_hidden_size = 100
    self.weight_decay  = 0
    self.gradient_accumulation_steps = 1
    self.adam_epsilon = 1e-8
    self.max_grad_norm = 1.0
    self.max_steps = -1
    self.warmup_steps = 0
    self.save_steps = 200
    self.do_train = 'store-true'
    self.do_eval = 'store-true'
    self.no_cuda = 'store-true'
    self.slot_loss_coef = 1
    self.model_type = "bert"
    self.seed = 1234
    self.ignore_index = 0
    self.data_dir = "/content/drive/MyDrive"
    self.task = None
    self.model_name_or_path = None
    self.logging_steps = 1
    self.model_dir = "/content/drive/MyDrive"

args = config_param()
args.model_name_or_path = MODEL_PATH_MAP[args.model_type]
tokenizer = MODEL_CLASSES[args.model_type][2].from_pretrained(args.model_name_or_path)

train_dataset = load_and_cache_examples(args, tokenizer, mode="train")
dev_dataset = load_and_cache_examples(args, tokenizer, mode="dev")
test_dataset = load_and_cache_examples(args, tokenizer, mode="test")

trainer = Trainer(args, train_dataset, dev_dataset, test_dataset)

if args.do_train:
        trainer.train(tokenizer)

if args.do_eval:
        trainer.load_model()
        trainer.evaluate("test",tokenizer)