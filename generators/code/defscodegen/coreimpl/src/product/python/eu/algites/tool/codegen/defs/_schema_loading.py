"""Schema resource parsing preserving exact decimal facet values."""
from decimal import Decimal
import json
import yaml

class _ExactSchemaLoader(yaml.SafeLoader):
    pass

def _decimal(loader, node):
    text = loader.construct_scalar(node).replace('_', '')
    if ':' in text:
        result = Decimal(0)
        for component in text.split(':'):
            result = result * 60 + Decimal(component)
        return result
    return Decimal(text)

_ExactSchemaLoader.add_constructor('tag:yaml.org,2002:float', _decimal)

def load_schema(path):
    text = path.read_text(encoding='utf-8')
    return json.loads(text, parse_float=Decimal) if path.suffix.lower() == '.json' else yaml.load(text, Loader=_ExactSchemaLoader)
