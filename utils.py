import hashlib
import json

def generate_verify_code(secret_key, timestamp, data):
    data_str = json.dumps(data, separators=(',', ':'))
    original_str = f'{secret_key}{timestamp}{data_str}'
    md5_hash = hashlib.md5(original_str.encode('utf-8')).hexdigest().upper()
    return md5_hash

#用于把buffer里面的json数据正确的取出，用于解决粘包问题
def parse_complete_json(buffer):
    try:
        json_str = buffer.decode('utf-8')
        start_idx = json_str.index('{')

        # 计数括号
        bracket_count = 0
        end_idx = start_idx

        for i in range(start_idx, len(json_str)):
            if json_str[i] == '{':
                bracket_count += 1
            elif json_str[i] == '}':
                bracket_count -= 1

            if bracket_count == 0:
                end_idx = i + 1
                break

        complete_json = json_str[start_idx:end_idx]
        return json.loads(complete_json), end_idx  # 返回解析的JSON和结束索引

    except (ValueError, IndexError):
        return None, 0

