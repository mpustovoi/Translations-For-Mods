import json
import re
import os

def get_template_structure(template_path):
    """
    Analyzes template structure, preserving information about empty lines between keys
    """
    with open(template_path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
    
    keys_order = []
    after_empty = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith('"') and ': ' in stripped:
            key = re.match(r'^\s*"([^"]+)"', line)
            if key:
                key_name = key.group(1)
                keys_order.append(key_name)
                j = i + 1
                empty_count = 0
                while j < len(lines) and lines[j].strip() == '':
                    empty_count += 1
                    j += 1
                after_empty.append(empty_count > 0)
                i = j - 1
        i += 1
    return keys_order, after_empty

def synchronize_json_with_deprecated(template_path, source_path, output_path):
    for path in [template_path, source_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
    
    def load_json(path):
        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                if not content.strip():
                    raise ValueError(f"File is empty: {path}")
                return json.loads(content)
        except json.JSONDecodeError as e:
            with open(path, 'r', encoding='utf-8-sig') as f:
                first_chars = f.read(50)
            raise ValueError(f"JSON parsing error in file {path}: {str(e)}\nFirst characters: '{first_chars}'") from None
    
    template_data = load_json(template_path)
    source_data = load_json(source_path)
    
    keys_order, after_empty = get_template_structure(template_path)
    
    deprecated_keys = sorted(set(source_data.keys()) - set(template_data.keys()))
    
    untranslated = []
    for key in keys_order:
        if key not in source_data:
            untranslated.append(key)
        elif key in template_data and source_data[key] == template_data[key] and not key.startswith("itemGroup."):
            untranslated.append(key)
    
    output_lines = ['{']
    
    for idx, key in enumerate(keys_order):
        value = source_data.get(key, template_data[key])
        needs_comma = (idx < len(keys_order) - 1) or bool(deprecated_keys)
        comma = ',' if needs_comma else ''
        output_lines.append(f'  "{key}": "{value}"{comma}')
        if idx < len(after_empty) and after_empty[idx]:
            output_lines.append('')
    
    if deprecated_keys:
        if output_lines and output_lines[-1].strip() != '':
            output_lines.append('')
        
        mod_id = keys_order[0].split('.')[0] if keys_order else "modid"
        header_key = f"deprecated_keys.{mod_id}"
        output_lines.append(f'  "{header_key}": "Deprecated Lines of {mod_id}",')
        output_lines.append('')
        
        for idx, key in enumerate(deprecated_keys):
            comma = ',' if idx < len(deprecated_keys) - 1 else ''
            output_lines.append(f'  "{key}": "{source_data[key]}"{comma}')
    
    output_lines.append('}')
    
    while len(output_lines) > 2 and output_lines[-2].strip() == '':
        output_lines.pop(-2)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    return untranslated, deprecated_keys

try:
    untranslated, deprecated = synchronize_json_with_deprecated(
        template_path='en_us_new.json',
        source_path='ru_ru_old.json',
        output_path='ru_ru.json'
    )

    print("\n" + "="*60)
    print("UNTRANSLATED STRINGS")
    print("="*60)
    for key in untranslated:
        print(f"  • {key}")
    print(f"\nTotal untranslated strings: {len(untranslated)}")
    
    print("\n" + "="*60)
    print("DEPRECATED KEYS")
    print("="*60)
    print(f"Total deprecated keys: {len(deprecated)}")
    if deprecated:
        print("\nFirst 5 deprecated keys:")
        for key in deprecated[:5]:
            print(f"  • {key}")
        if len(deprecated) > 5:
            print(f"  • ... and {len(deprecated) - 5} more")
    
    print("\n" + "="*60)
    print("SYNCHRONIZATION COMPLETED")
    print(f"Result saved to: {os.path.abspath('ru_ru.json')}")
    print("="*60)
    
    if untranslated:
        print("\n💡 Recommendations:")
        print("1. Translate the missing strings to complete localization")
        print("2. Check if untranslated strings should match English version")
        print("3. Verify itemGroup entries don't need translation")
    
except Exception as e:
    print(f"\n❌ ERROR DURING SYNCHRONIZATION: {str(e)}")
    import sys
    sys.exit(1)