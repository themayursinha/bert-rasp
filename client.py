import requests
from urllib.parse import unquote
from datasets import load_dataset
from tqdm import tqdm
from sklearn.metrics import confusion_matrix

dataset = load_dataset("b1nch3f/csic-dataset")

# URL where your server is hosted
SERVER_URL = "http://localhost:8000/api/userLogin"

def extract_payload(req, method):
  # print(req)
  payload = None

  if method == 'GET':
      if '?' in req.split('\n')[0]:
        query_params = req.split('\n')[0].split('?')[-1].replace(' HTTP/1.1', '')
        # print(query_params.split('&'))
        payload_lst = [item.split('=') for item in query_params.split('&')]
        # print(payload_lst)
        payload = {}
        for item in payload_lst:
            if len(item) == 2:
                payload[unquote(item[0], encoding='latin1').lower()] = unquote(item[1], encoding='latin1').lower()
        # payload = query_params

  else:
      query_params = req.split('\n')[-1]
      # print(query_params)

      payload_lst = [item.split('=') for item in query_params.split('&')]
      # print(payload_lst)
      payload = {}
      for item in payload_lst:
        if len(item) == 2:
            payload[item[0]] = item[1]

  return payload

# Initialize counters for both classes
label = []
label_hat = []

dataset = dataset['validation']

for index in tqdm(range(dataset.num_rows)):
    if dataset[index]['label'] == 'Normal':
       label.append(0)
    else:
       label.append(1)

    payload = extract_payload(dataset[index]['request'], dataset[index]['method'])

    # Send a POST request to the server
    if payload:
        response = requests.post(SERVER_URL, json=payload)

        if response.json()['detail']['message'] == 'Normal payload detected':
            label_hat.append(0)
        else:
            label_hat.append(1)
    else:
       label.pop()

cm = confusion_matrix(label, label_hat)
print(cm)

tn, fp, fn, tp = confusion_matrix(label, label_hat).ravel()

accuracy = (tp + tn)/(tp + tn + fp + fn)
print(f'accuracy: {accuracy}')