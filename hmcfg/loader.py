import os
import hmcfg.simplematch as sm
import json
import jsonschema

_DATASET_SCHEMA = {
  "type": "object",
  "patternProperties": {
    ".*": { 
      "type": "object",
      "properties": {
        "patterns": { "type": "array", "items": { "type": "string" } },
        "key": { "type": "array", "items": { "type": "string" } },
        "schema": { "type": "object" }
      },
      "required": [ "patterns", "schema", "key" ]
    }
  }
}

def get_config_file_names(root_path:str):
  files = []

  for dirpath, dirnames, filenames in os.walk(root_path):
    for name in filenames:
      relpath = os.path.relpath(dirpath, root_path)
      if relpath == '.':
        relpath = ''

      files.append(os.path.join(relpath, name))

  return files

def match(files:list[str], datasets:dict[str,list[str]]):
  data = {}
  jsonschema.validate(datasets, _DATASET_SCHEMA)
  
  for f in files:
    for dataset_name, setup in datasets.items():
      patterns = setup['patterns']
      for p in patterns:
        labels = sm.match(pattern=p, string=f)
        
        if labels:
          if f in data:
            raise ValueError(f"file '{f}' already matches at least two patterns: '{p}' and '{data[f]['pattern']}'"
                            )
          data[f] = { 'dataset': dataset_name, 'labels': labels, 'pattern': p }
  
  for f in files:
    if f not in data:
      data[f] = { 'dataset': None, 'labels': {}, 'pattern': None}

  
  result = {}
  for filename, v in data.items():
    dataset = v['dataset']
    dataset_data = datasets[dataset] if dataset else { 'schema': None, 'patterns': [], 'key': [] }
    labels = v['labels']

    r = result[dataset] = result.get(dataset, { 
      'files': {},
      **dataset_data
    })
    files = r['files']
    files[filename] = labels

  return result

def load_json_schema(file_name:str, root_path=None):
  if root_path:
    file_name = os.path.join(root_path, file_name)

  schema = load_json_file(file_name)
  jsonschema.Validator.check_schema(schema)
  return schema

def load_json_file(file_name:str, json_schema:dict=None, root_path=None):
  if root_path:
    file_name = os.path.join(root_path, file_name)

  with open(file_name, 'r') as f:
    data = json.load(f)

  if json_schema:
    jsonschema.validate(data, json_schema)

  return data

def load_configs(root_path:str, datasets:list[dict], filter=None, metadata_prefix='_'):
  filter = filter or (lambda x, y: True)
  files = get_config_file_names(root_path)
  matches = match(files, datasets)

  res = {}
  pk_res= {}

  for dataset_name, m in matches.items():
    if not filter(dataset_name, m):
      continue

    data = res[dataset_name] = res.get(dataset_name, [])
    pk_data = pk_res[dataset_name] = pk_res.get(dataset_name, {})

    for f, labels in m['files'].items():
      records = load_json_file(f, m['schema'], root_path=root_path)
      key_columns = m['key']

      for idx, rec in enumerate(records):
        if metadata_prefix:
          rec[metadata_prefix + 'filename'] = f
          rec[metadata_prefix + 'line'] = idx+1
          for k, v in labels.items():
            res[metadata_prefix + k] = v

        if key_columns:
          key = tuple([rec[c] for c in key_columns])
          if key in pk_data:
            raise ValueError(f"Duplicated key {key} found in dataset {dataset_name}: files {f}:{idx+1} and {pk_data[key]} are having the same key")
          
          pk_data[key] = f"{f}:{idx+1}"

        data.append(rec)
  
  return res


  

  

