from hmcfg import loader
import pytest

datasets = {
  'virtual_machines': {
    'patterns': [
      "{team}/{env}/*vm.json"
      ,"{team}/*vm.json"
    ],
    'schema': loader.load_json_schema('tests/data.schema/vm.json'),
    'key': ['name']
  },
  'dns': {
    'patterns': [
      "{team}/{env}/*dns.json"
      ,"{team}/*dns.json"
    ],
    'schema': loader.load_json_schema('tests/data.schema/dns.json'),
    'key': ['dns', 'provider']
  }
}

def test_json_schema():
  schema = loader.load_json_schema('tests/data.schema/dns.json')
  loader.load_json_file("tests/data/team01/prd/dns.json", schema)

  #this shall not pass
  with pytest.raises(Exception):
    loader.load_json_file("tests/data/team01/prd/vm.json", schema)

def test_discover_files():
  files = loader.get_config_file_names("tests/data")

  assert set(files) == set(['vm.json',
    'team01/vm.json',
    'team01/prd/vm.json',
    'team01/dev/vm.json',
    'team02/dev/vm.json',
    'team01/prd/dns.json'
  ])

  matches = loader.match(files, datasets)

  print(matches)

  assert(matches) == {
    'virtual_machines': {
      'files': {
        'team01/vm.json': {'team': 'team01'}, 
        'team01/prd/vm.json': {'team': 'team01', 'env': 'prd'}, 
        'team01/dev/vm.json': {'team': 'team01', 'env': 'dev'}, 
        'team02/dev/vm.json': {'team': 'team02', 'env': 'dev'}
      },
      **datasets['virtual_machines']
    },
    'dns': {
      'files': {
        'team01/prd/dns.json': {'team': 'team01', 'env': 'prd'}
      }
      ,**datasets['dns']
    }, 
    None: {
      'files': {
        'vm.json': {}
      }
      ,'schema': None
      ,'patterns': []
      ,'key': []
    }
  }

def test_config_loading():
  data = loader.load_configs("tests/data", datasets)
  
  assert None in data
  assert 'dns' in data
  assert 'virtual_machines' in data

  assert data['dns'] == [
    {'_filename': 'team01/prd/dns.json', '_line': 1, 'dns': 'somehost.com', 'provider': 'azure'},
    {'_filename': 'team01/prd/dns.json', '_line': 2, 'dns': 'databricks.com', 'provider': 'aws'}
  ]

