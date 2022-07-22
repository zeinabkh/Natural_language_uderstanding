# -*- coding: utf-8 -*-
"""new_nlu3__1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1If819A9QmWBS3i6T-qhUcIZu16Zpg7el
"""

from google.colab import drive
drive.mount('/content/drive')

!pip install datasets
!pip install transformers

# -*- coding: utf-8 -*-
"""NLU3_pretrain_bert_14.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1I4acc-cQiBEqacO81ksrYwLWnNWKVR-5
"""



import transformers

print(transformers.__version__)

model_checkpoint =  "HooshvareLab/bert-fa-base-uncased"
batch_size = 16

# Give the path for train data
from pathlib import Path
import json
path = Path('/content/drive/MyDrive/NLU3/train_samples.json')
#path = Path('squad/train-v2.0.json')
# Open .json file
with open(path, 'rb') as f:
    squad_dict = json.load(f)


texts = []
queries = []
answers = []
ID = []
title = []

# Search for each passage, its question and its answer
for group in squad_dict['data']:
    ti = group["title"]
    for passage in group['paragraphs']:
        context = passage['context']
        for qa in passage['qas']:
            question = qa['question']
            id = qa["id"]
            answer =  qa['answers']
            if len(answer ) == 0 :
              answer1 = {'text':[""] , 'answer_start':[]}
              answers.append(answer1)
            else:
              answer1 = {'text':[answer[0]['text']] , 'answer_start':[answer[0]['answer_start']]}
              answers.append(answer1)
            title.append(ti)
            texts.append(context)
            queries.append(question)
            ID.append(id)

train_context, train_question, train_answers, train_id, train_title = texts, queries, answers, ID, title

# Give the path for validation data
path = Path('/content/drive/MyDrive/NLU3/validation_samples.json')
#path = Path('squad/dev-v2.0.json')
# Open .json file
with open(path, 'rb') as f:
    squad_dict = json.load(f)

texts = []
queries = []
answers = []
ID = []
title = []

# Search for each passage, its question and its answer
for group in squad_dict['data']:
    ti = group["title"]
    for passage in group['paragraphs']:
        context = passage['context']
        for qa in passage['qas']:
            question = qa['question']
            id = qa["id"]
            answer =  qa['answers']
            if len(answer ) == 0 :
              answer1 = {'text':[""] , 'answer_start':[]}
              answers.append(answer1)
            else:
              answer1 = {'text':[answer[0]['text']] , 'answer_start':[answer[0]['answer_start']]}
              answers.append(answer1)
            title.append(ti)
            texts.append(context)
            queries.append(question)
            ID.append(id)
            # for answer in qa['answers']:
            #     # Store every passage, query and its answer to the lists
            #     #print(answer)
            #     answer1 = {'text':[answer['text']] , 'answer_start':[answer['answer_start']]}
            #     #print(answer1)
            #     title.append(ti)
            #     texts.append(context)
            #     queries.append(question)
            #     answers.append(answer1)
            #     ID.append(id)

val_context, val_question, val_answers, val_id, val_title = texts, queries, answers, ID, title

import pandas as pd
from datasets import Dataset
#['id', 'title', 'context', 'question', 'answers']
train_data = pd.DataFrame({'answers' : train_answers, 'context' : train_context, 'id' : train_id, 'question' : train_question, 'title' : train_title})
val_data = pd.DataFrame({'answers' : val_answers, 'context' : val_context, 'id' : val_id, 'question' : val_question, 'title' : val_title})

train_datasets = Dataset.from_pandas(train_data)
val_datasets = Dataset.from_pandas(val_data)
data = {"train" : train_datasets, "test" : val_datasets}
#vall_da = train_datasets('bookcorpus', split='train[:10')

train_datasets

from datasets import ClassLabel, Sequence
import random
import pandas as pd
from IPython.display import display, HTML

def show_random_elements(dataset, num_examples=10):
    assert num_examples <= len(dataset), "Can't pick more elements than there are in the dataset."
    picks = []
    for _ in range(num_examples):
        pick = random.randint(0, len(dataset)-1)
        while pick in picks:
            pick = random.randint(0, len(dataset)-1)
        picks.append(pick)
    
    df = pd.DataFrame(dataset[picks])
    for column, typ in dataset.features.items():
        if isinstance(typ, ClassLabel):
            df[column] = df[column].transform(lambda i: typ.names[i])
        elif isinstance(typ, Sequence) and isinstance(typ.feature, ClassLabel):
            df[column] = df[column].transform(lambda x: [typ.feature.names[i] for i in x])
    display(HTML(df.to_html()))

show_random_elements(train_datasets)

from transformers import AutoTokenizer
    
tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)

import transformers
assert isinstance(tokenizer, transformers.PreTrainedTokenizerFast)

max_length = 201
doc_stride = 128

for i, example in enumerate(train_datasets):
  if len(tokenizer(example["question"], example["context"])["input_ids"]) > 201:
    break
example = train_datasets[i]

len(tokenizer(example["question"], example["context"])["input_ids"])

len(tokenizer(example["question"], example["context"], max_length=max_length, truncation="only_second")["input_ids"])

tokenized_example = tokenizer(
    example["question"],
    example["context"],
    max_length=max_length,
    truncation="only_second",
    return_overflowing_tokens=True,
    stride=doc_stride
)

[len(x) for x in tokenized_example["input_ids"]]

for x in tokenized_example["input_ids"][:2]:
    print(tokenizer.decode(x))

tokenized_example = tokenizer(
    example["question"],
    example["context"],
    max_length=max_length,
    truncation="only_second",
    return_overflowing_tokens=True,
    return_offsets_mapping=True,
    stride=doc_stride
)
print(tokenized_example["offset_mapping"][0][:100])

first_token_id = tokenized_example["input_ids"][0][1]
offsets = tokenized_example["offset_mapping"][0][1]
print(tokenizer.convert_ids_to_tokens([first_token_id])[0], example["question"][offsets[0]:offsets[1]])

sequence_ids = tokenized_example.sequence_ids()
print(sequence_ids)

answers = example["answers"]
answers

len(answers["text"])

answers = example["answers"]
start_char = answers["answer_start"][0]
end_char = start_char + len(answers["text"][0])

# Start token index of the current span in the text.
token_start_index = 0
while sequence_ids[token_start_index] != 1:
    token_start_index += 1

# End token index of the current span in the text.
token_end_index = len(tokenized_example["input_ids"][0]) - 1
while sequence_ids[token_end_index] != 1:
    token_end_index -= 1

# Detect if the answer is out of the span (in which case this feature is labeled with the CLS index).
offsets = tokenized_example["offset_mapping"][0]
if (offsets[token_start_index][0] <= start_char and offsets[token_end_index][1] >= end_char):
    # Move the token_start_index and token_end_index to the two ends of the answer.
    # Note: we could go after the last offset if the answer is the last word (edge case).
    while token_start_index < len(offsets) and offsets[token_start_index][0] <= start_char:
        token_start_index += 1
    start_position = token_start_index - 1
    while offsets[token_end_index][1] >= end_char:
        token_end_index -= 1
    end_position = token_end_index + 1
    print(start_position, end_position)
else:
    print("The answer is not in this feature.")

pad_on_right = tokenizer.padding_side == "right"

def prepare_train_features(examples):
    # Some of the questions have lots of whitespace on the left, which is not useful and will make the
    # truncation of the context fail (the tokenized question will take a lots of space). So we remove that
    # left whitespace
    examples["question"] = [q.lstrip() for q in examples["question"]]

    # Tokenize our examples with truncation and padding, but keep the overflows using a stride. This results
    # in one example possible giving several features when a context is long, each of those features having a
    # context that overlaps a bit the context of the previous feature.
    tokenized_examples = tokenizer(
        examples["question" if pad_on_right else "context"],
        examples["context" if pad_on_right else "question"],
        truncation="only_second" if pad_on_right else "only_first",
        max_length=max_length,
        stride=doc_stride,
        return_overflowing_tokens=True,
        return_offsets_mapping=True,
        padding="max_length",
    )

    # Since one example might give us several features if it has a long context, we need a map from a feature to
    # its corresponding example. This key gives us just that.
    sample_mapping = tokenized_examples.pop("overflow_to_sample_mapping")
    # The offset mappings will give us a map from token to character position in the original context. This will
    # help us compute the start_positions and end_positions.
    offset_mapping = tokenized_examples.pop("offset_mapping")

    # Let's label those examples!
    tokenized_examples["start_positions"] = []
    tokenized_examples["end_positions"] = []

    for i, offsets in enumerate(offset_mapping):
        # We will label impossible answers with the index of the CLS token.
        input_ids = tokenized_examples["input_ids"][i]
        cls_index = input_ids.index(tokenizer.cls_token_id)

        # Grab the sequence corresponding to that example (to know what is the context and what is the question).
        sequence_ids = tokenized_examples.sequence_ids(i)

        # One example can give several spans, this is the index of the example containing this span of text.
        sample_index = sample_mapping[i]
        answers = examples["answers"][sample_index]
        # If no answers are given, set the cls_index as answer.
        if len(answers["answer_start"]) == 0:
            tokenized_examples["start_positions"].append(cls_index)
            tokenized_examples["end_positions"].append(cls_index)
        else:
            # Start/end character index of the answer in the text.
            start_char = answers["answer_start"][0]
            end_char = start_char + len(answers["text"][0])

            # Start token index of the current span in the text.
            token_start_index = 0
            while sequence_ids[token_start_index] != (1 if pad_on_right else 0):
                token_start_index += 1

            # End token index of the current span in the text.
            token_end_index = len(input_ids) - 1
            while sequence_ids[token_end_index] != (1 if pad_on_right else 0):
                token_end_index -= 1

            # Detect if the answer is out of the span (in which case this feature is labeled with the CLS index).
            if not (offsets[token_start_index][0] <= start_char and offsets[token_end_index][1] >= end_char):
                tokenized_examples["start_positions"].append(cls_index)
                tokenized_examples["end_positions"].append(cls_index)
            else:
                # Otherwise move the token_start_index and token_end_index to the two ends of the answer.
                # Note: we could go after the last offset if the answer is the last word (edge case).
                while token_start_index < len(offsets) and offsets[token_start_index][0] <= start_char:
                    token_start_index += 1
                tokenized_examples["start_positions"].append(token_start_index - 1)
                while offsets[token_end_index][1] >= end_char:
                    token_end_index -= 1
                tokenized_examples["end_positions"].append(token_end_index + 1)

    return tokenized_examples

features = prepare_train_features(train_datasets[:5])
print(features)

tokenized_datasets = train_datasets.map(prepare_train_features, batched=True, remove_columns=train_datasets.column_names)
tokenized_datasets1 = val_datasets.map(prepare_train_features, batched=True, remove_columns=train_datasets.column_names)

from transformers import AutoModelForQuestionAnswering, TrainingArguments, Trainer

model = AutoModelForQuestionAnswering.from_pretrained(model_checkpoint)

model_name = model_checkpoint.split("/")[-1]
args = TrainingArguments(
    f"{model_name}-finetuned-squad",
    evaluation_strategy = "epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=batch_size,
    per_device_eval_batch_size=batch_size,
    num_train_epochs=3,
    weight_decay=0.01,
)

from transformers import default_data_collator

data_collator = default_data_collator

tokenized_datasets[0:15000]

trainer = Trainer(
    model,
    args,
    train_dataset=tokenized_datasets,
    eval_dataset=tokenized_datasets1,
    data_collator=data_collator,
    tokenizer=tokenizer,
)

trainer.train()

trainer.save_model("/content/drive/MyDrive/NLU3_s/test-pquad-trained1")

"""# **evaluate**"""

import torch

for batch in trainer.get_eval_dataloader():
    break
batch = {k: v.to(trainer.args.device) for k, v in batch.items()}
with torch.no_grad():
    output = trainer.model(**batch)
output.keys()

output.start_logits.shape, output.end_logits.shape

n_best_size = 20

import numpy as np

start_logits = output.start_logits[0].cpu().numpy()
end_logits = output.end_logits[0].cpu().numpy()
# Gather the indices the best start/end logits:
start_indexes = np.argsort(start_logits)[-1 : -n_best_size - 1 : -1].tolist()
end_indexes = np.argsort(end_logits)[-1 : -n_best_size - 1 : -1].tolist()
valid_answers = []
for start_index in start_indexes:
    for end_index in end_indexes:
        if start_index <= end_index: # We need to refine that test to check the answer is inside the context
            valid_answers.append(
                {
                    "score": start_logits[start_index] + end_logits[end_index],
                    "text": "" # We need to find a way to get back the original substring corresponding to the answer in the context
                }
            )

def prepare_validation_features(examples):
    # Some of the questions have lots of whitespace on the left, which is not useful and will make the
    # truncation of the context fail (the tokenized question will take a lots of space). So we remove that
    # left whitespace
    examples["question"] = [q.lstrip() for q in examples["question"]]

    # Tokenize our examples with truncation and maybe padding, but keep the overflows using a stride. This results
    # in one example possible giving several features when a context is long, each of those features having a
    # context that overlaps a bit the context of the previous feature.
    tokenized_examples = tokenizer(
        examples["question" if pad_on_right else "context"],
        examples["context" if pad_on_right else "question"],
        truncation="only_second" if pad_on_right else "only_first",
        max_length=max_length,
        stride=doc_stride,
        return_overflowing_tokens=True,
        return_offsets_mapping=True,
        padding="max_length",
    )

    # Since one example might give us several features if it has a long context, we need a map from a feature to
    # its corresponding example. This key gives us just that.
    sample_mapping = tokenized_examples.pop("overflow_to_sample_mapping")

    # We keep the example_id that gave us this feature and we will store the offset mappings.
    tokenized_examples["example_id"] = []

    for i in range(len(tokenized_examples["input_ids"])):
        # Grab the sequence corresponding to that example (to know what is the context and what is the question).
        sequence_ids = tokenized_examples.sequence_ids(i)
        context_index = 1 if pad_on_right else 0

        # One example can give several spans, this is the index of the example containing this span of text.
        sample_index = sample_mapping[i]
        tokenized_examples["example_id"].append(examples["id"][sample_index])

        # Set to None the offset_mapping that are not part of the context so it's easy to determine if a token
        # position is part of the context or not.
        tokenized_examples["offset_mapping"][i] = [
            (o if sequence_ids[k] == context_index else None)
            for k, o in enumerate(tokenized_examples["offset_mapping"][i])
        ]

    return tokenized_examples

validation_features = val_datasets.map(
    prepare_validation_features,
    batched=True,
    remove_columns=val_datasets.column_names
)

raw_predictions = trainer.predict(validation_features)

validation_features.set_format(type=validation_features.format["type"], columns=list(validation_features.features.keys()))

max_answer_length = 30

start_logits = output.start_logits[0].cpu().numpy()
end_logits = output.end_logits[0].cpu().numpy()
offset_mapping = validation_features[0]["offset_mapping"]
# The first feature comes from the first example. For the more general case, we will need to be match the example_id to
# an example index
context = val_datasets[0]["context"]

# Gather the indices the best start/end logits:
start_indexes = np.argsort(start_logits)[-1 : -n_best_size - 1 : -1].tolist()
end_indexes = np.argsort(end_logits)[-1 : -n_best_size - 1 : -1].tolist()
valid_answers = []
for start_index in start_indexes:
    for end_index in end_indexes:
        # Don't consider out-of-scope answers, either because the indices are out of bounds or correspond
        # to part of the input_ids that are not in the context.
        if (
            start_index >= len(offset_mapping)
            or end_index >= len(offset_mapping)
            or offset_mapping[start_index] is None
            or offset_mapping[end_index] is None
        ):
            continue
        # Don't consider answers with a length that is either < 0 or > max_answer_length.
        if end_index < start_index or end_index - start_index + 1 > max_answer_length:
            continue
        if start_index <= end_index: # We need to refine that test to check the answer is inside the context
            start_char = offset_mapping[start_index][0]
            end_char = offset_mapping[end_index][1]
            valid_answers.append(
                {
                    "score": start_logits[start_index] + end_logits[end_index],
                    "text": context[start_char: end_char]
                }
            )

valid_answers = sorted(valid_answers, key=lambda x: x["score"], reverse=True)[:n_best_size]
valid_answers

import collections

examples = val_datasets
features = validation_features

example_id_to_index = {k: i for i, k in enumerate(examples["id"])}
features_per_example = collections.defaultdict(list)
for i, feature in enumerate(features):
    features_per_example[example_id_to_index[feature["example_id"]]].append(i)

from tqdm.auto import tqdm

def postprocess_qa_predictions(examples, features, raw_predictions, n_best_size = 20, max_answer_length = 30):
    
    all_start_logits, all_end_logits = raw_predictions
    # Build a map example to its corresponding features.
    example_id_to_index = {k: i for i, k in enumerate(examples["id"])}
    features_per_example = collections.defaultdict(list)
    for i, feature in enumerate(features):
        features_per_example[example_id_to_index[feature["example_id"]]].append(i)

    # The dictionaries we have to fill.
    predictions = collections.OrderedDict()
    # Logging.
    print(f"Post-processing {len(examples)} example predictions split into {len(features)} features.")
    # Let's loop over all the examples!
    print(len(examples))
    new_example = []
    ids = []
    for example_index, example in enumerate(tqdm(examples)):
        
        i += 1
        # Those are the indices of the features associated to the current example.
        feature_indices = features_per_example[example_index]

        min_null_score = None # Only used if squad_v2 is True.
        valid_answers = []
        
        context = example["context"]
        # Looping through all the features associated to the current example.
        for feature_index in feature_indices:
            # We grab the predictions of the model for this feature.
            start_logits = all_start_logits[feature_index]
            end_logits = all_end_logits[feature_index]
            # This is what will allow us to map some the positions in our logits to span of texts in the original
            # context.
            offset_mapping = features[feature_index]["offset_mapping"]

            # Update minimum null prediction.
            cls_index = features[feature_index]["input_ids"].index(tokenizer.cls_token_id)
            feature_null_score = start_logits[cls_index] + end_logits[cls_index]
            if min_null_score is None or min_null_score < feature_null_score:
                min_null_score = feature_null_score

            # Go through all possibilities for the `n_best_size` greater start and end logits.
            start_indexes = np.argsort(start_logits)[-1 : -n_best_size - 1 : -1].tolist()
            end_indexes = np.argsort(end_logits)[-1 : -n_best_size - 1 : -1].tolist()
            for start_index in start_indexes:
                for end_index in end_indexes:
                    # Don't consider out-of-scope answers, either because the indices are out of bounds or correspond
                    # to part of the input_ids that are not in the context.
                    if (
                        start_index >= len(offset_mapping)
                        or end_index >= len(offset_mapping)
                        or offset_mapping[start_index] is None
                        or offset_mapping[end_index] is None
                    ):
                        continue
                    # Don't consider answers with a length that is either < 0 or > max_answer_length.
                    if end_index < start_index or end_index - start_index + 1 > max_answer_length:
                        continue

                    start_char = offset_mapping[start_index][0]
                    end_char = offset_mapping[end_index][1]
                    valid_answers.append(
                        {
                            "score": start_logits[start_index] + end_logits[end_index],
                            "text": context[start_char: end_char]
                        }
                    )
        
        if len(valid_answers) > 0:
            best_answer = sorted(valid_answers, key=lambda x: x["score"], reverse=True)[0]
        else:
            # In the very rare edge case we have not a single non-null prediction, we create a fake prediction to avoid
            # failure.
            best_answer = {"text": "", "score": 0.0}
        
        # Let's pick our final answer: the best one or the null answer (only for squad_v2)
        # if not squad_v2:
        # print(example["id"],example["question"],example["answers"])
        # if example["id"] not in ids:
        #     predictions[example["id"]] = best_answer["text"]
        #     new_example.append(example)
        # ids.append(example["id"])
        # else:
        answer = best_answer["text"] if best_answer["score"] > min_null_score else ""
        predictions[example["id"]] = answer
    print(i)
    return predictions,new_example

validation_features

val_datasets

final_predictions,new_example = postprocess_qa_predictions(val_datasets, validation_features, raw_predictions.predictions)

new_example

from datasets import load_metric

metric = load_metric("squad_v2" )

len(final_predictions.items())

len(val_datasets)

formatted_predictions = [{"id": k, "prediction_text": v, "no_answer_probability": 0.0} for k, v in final_predictions.items()]
references = [{"id": ex["id"], "answers": ex["answers"]} for ex in val_datasets]
metric.compute(predictions=formatted_predictions, references=references)

"""**Test**"""

path = Path('/content/drive/MyDrive/NLU3/test_samples.json')
#path = Path('squad/dev-v2.0.json')
# Open .json file
with open(path, 'rb') as f:
    squad_dict = json.load(f)

texts = []
queries = []
answers = []
ID = []
title = []

# Search for each passage, its question and its answer
for group in squad_dict['data']:
    ti = group["title"]
    for passage in group['paragraphs']:
        context = passage['context']
        for qa in passage['qas']:
            question = qa['question']
            id = qa["id"]
            answer =  qa['answers']
            if len(answer ) == 0 :
              answer1 = {'text':[""] , 'answer_start':[]}
              answers.append(answer1)
            else:
              answer1 = {'text':[answer[0]['text']] , 'answer_start':[answer[0]['answer_start']]}
              answers.append(answer1)
            title.append(ti)
            texts.append(context)
            queries.append(question)
            ID.append(id)
      

val_context, val_question, val_answers, val_id, val_title = texts, queries, answers, ID, title

import pandas as pd
from datasets import Dataset
#['id', 'title', 'context', 'question', 'answers']

test_data = pd.DataFrame({'answers' : val_answers, 'context' : val_context, 'id' : val_id, 'question' : val_question, 'title' : val_title})

test_datasets = Dataset.from_pandas(test_data)
data = {"train" : train_datasets, "test" : val_datasets}

validation_features = val_datasets.map(
    prepare_validation_features,
    batched=True,
    remove_columns=test_datasets.column_names
)

! pip install bertviz

def prepare_validation_features(examples):
    # Some of the questions have lots of whitespace on the left, which is not useful and will make the
    # truncation of the context fail (the tokenized question will take a lots of space). So we remove that
    # left whitespace
    examples["question"] = [q.lstrip() for q in examples["question"]]

    # Tokenize our examples with truncation and maybe padding, but keep the overflows using a stride. This results
    # in one example possible giving several features when a context is long, each of those features having a
    # context that overlaps a bit the context of the previous feature.
    tokenized_examples = tokenizer(
        examples["question" if pad_on_right else "context"],
        examples["context" if pad_on_right else "question"],
        truncation="only_second" if pad_on_right else "only_first",
        max_length=max_length,
        stride=doc_stride,
        return_overflowing_tokens=True,
        return_offsets_mapping=True,
        padding="max_length",
    )

    # Since one example might give us several features if it has a long context, we need a map from a feature to
    # its corresponding example. This key gives us just that.
    sample_mapping = tokenized_examples.pop("overflow_to_sample_mapping")

    # We keep the example_id that gave us this feature and we will store the offset mappings.
    tokenized_examples["example_id"] = []

    for i in range(len(tokenized_examples["input_ids"])):
        # Grab the sequence corresponding to that example (to know what is the context and what is the question).
        sequence_ids = tokenized_examples.sequence_ids(i)
        context_index = 1 if pad_on_right else 0

        # One example can give several spans, this is the index of the example containing this span of text.
        sample_index = sample_mapping[i]
        tokenized_examples["example_id"].append(examples["id"][sample_index])

        # Set to None the offset_mapping that are not part of the context so it's easy to determine if a token
        # position is part of the context or not.
        tokenized_examples["offset_mapping"][i] = [
            (o if sequence_ids[k] == context_index else None)
            for k, o in enumerate(tokenized_examples["offset_mapping"][i])
        ]

    return tokenized_examples

from transformers import AutoTokenizer, AutoModel, utils,BertForPreTraining,BertForQuestionAnswering,PreTrainedTokenizerFast
utils.logging.set_verbosity_error()  # Suppress standard warnings
tokenizer = AutoTokenizer.from_pretrained("HooshvareLab/bert-fa-base-uncased")
model = BertForQuestionAnswering.from_pretrained("/content/drive/MyDrive/train_model_large_10_15", output_attentions=True)
assert isinstance(tokenizer, PreTrainedTokenizerFast)

features_test = prepare_validation_features(test_datasets[:15])

features_test.keys()

for ids, tok, example in zip(features_test ["input_ids"],features_test["token_type_ids"],test_datasets[:10]):
  inputs = ids
  outputs = model(torch.tensor([inputs]),token_type_ids = torch.tensor([tok]))
  # print(outputs.start_logits)
  attention = outputs[-1]  # Output includes attention weights when output_attentions=True
  lenq = len([0 for k in tok if k ==0 ])
  len_a = len([1 for k in tok if k== 1])
  t1 = tokenizer.convert_ids_to_tokens(ids)
  t2 = tokenizer.convert_ids_to_tokens(ids[lenq:])
  at1 = ()
  from bertviz import model_view, head_view
  head_view(attention,t1,lenq)

print(test_datasets)

for  i in range(25,30):
  # print(test_datasets["answers"])
  answer = test_datasets["answers"][i]["text"][0]
  question = test_datasets["question"][i]
  inputs = idsinputs = tokenizer.encode_plus(question, answer, return_tensors = "pt", add_special_tokens=True)
  input_ids = inputs ["input_ids"]
  token_type_ids = inputs["token_type_ids"]
  outputs = model(input_ids,token_type_ids = token_type_ids)
  # print(outputs.start_logits)
  attention = outputs[-1]  # Output includes attention weights when output_attentions=True
  b = token_type_ids[0].tolist().index(1)
  input_id_list = input_ids[0].tolist()
  t1 = tokenizer.convert_ids_to_tokens(input_id_list)
  
  from bertviz import model_view, head_view
  head_view(attention,t1,b)