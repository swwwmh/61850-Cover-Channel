import random
import re

def modify_message_bytes(input_file, output_file, target_bit_string):
    """修改报文中指定位置的4字节数据，保持原始文件格式"""
    if len(target_bit_string) != 32:
        raise ValueError("目标比特串必须是32位")
    
    with open(input_file, 'r') as file:
        content = file.read()
    
    # 分割每个报文（分隔符前后可能有换行符）
    parts = re.split(r'(\n*\+---------\+---------------\+----------\+\n?)', content)
    valid_parts = [p for p in parts if p.strip()]
    
    modified_messages = []
    message_count = 0  # 新增：独立的报文计数器
    
    for i in range(0, len(valid_parts), 2):
        if i + 1 >= len(valid_parts):
            break
            
        delimiter = valid_parts[i]
        message = valid_parts[i + 1]
        
        if not message.strip():
            modified_messages.append(delimiter + message)
            continue
        
        lines = message.strip().split('\n')
        if len(lines) < 2:
            modified_messages.append(delimiter + message)
            continue
        
        timestamp = lines[0].split('   ')[0]
        print(f"处理报文 {message_count+1} - 时间戳: {timestamp}")
        
        # 提取十六进制数据
        hex_data = ''.join(
            c for line in lines[1:] if '|' in line
            for c in line.split('|', 1)[1].strip() 
            if c in '0123456789abcdefABCDEF'
        )
        
        if len(hex_data) < 168 * 2:
            print("  警告：报文数据长度不足，跳过修改")
            modified_messages.append(delimiter + message)
            message_count += 1
            continue
        
        # 修正：使用message_count作为比特串索引
        bit_index = message_count * 2
        bit_pair = target_bit_string[bit_index:bit_index+2] if bit_index < len(target_bit_string) else "00"
        if len(bit_pair) < 2:
            bit_pair = "00"
        
        # 定位并修改4字节（修正起始索引）
        start_idx = 164 * 2 +1  # 第165字节开始（索引从0计算，每个字节2个十六进制字符）
        original_hex = hex_data[start_idx:start_idx+8]
        if len(original_hex) != 8:
            print("  警告：字节长度异常，跳过修改")
            modified_messages.append(delimiter + message)
            message_count += 1
            continue
        
        # 执行修改
        new_hex, original_dec, new_dec = _modify_hex(original_hex, bit_pair)
        if new_hex:
            hex_list = list(hex_data)
            hex_list[start_idx:start_idx+8] = list(new_hex)
            new_hex_data = ''.join(hex_list)
            
            # 重建报文行
            new_lines = [lines[0]]
            hex_pos = 0
            for line in lines[1:]:
                if '|' not in line:
                    new_lines.append(line)
                    continue
                prefix, _, suffix = line.partition('|')
                line_hex = ''.join(c for c in suffix.strip() if c in '0123456789abcdefABCDEF')
                replace_len = min(len(line_hex), len(new_hex_data) - hex_pos)
                new_line_hex = new_hex_data[hex_pos:hex_pos+replace_len]
                hex_pos += replace_len
                
                new_suffix = ''
                hex_idx = 0
                for c in suffix.strip():
                    if c in '0123456789abcdefABCDEF' and hex_idx < len(new_line_hex):
                        new_suffix += new_line_hex[hex_idx]
                        hex_idx += 1
                    else:
                        new_suffix += c
                new_lines.append(f"{prefix}|{new_suffix}")
            
            new_message = '\n'.join(new_lines)
            modified_messages.append(delimiter + new_message)
            print(f"  原始: {original_hex}({original_dec}) → 修改: {new_hex}({new_dec}), 目标比特: {bit_pair}")
        else:
            modified_messages.append(delimiter + message)
            print(f"  跳过修改: {original_hex}, 目标比特: {bit_pair}")
        
        message_count += 1
        print("-" * 60)
    
    # 合并所有部分
    new_content = ''.join(modified_messages)
    
    # 保存文件
    with open(output_file, 'w') as file:
        file.write(new_content.rstrip() + '\n\n')
    print(f"处理完成，已保存至: {output_file}")
    print(f"共处理 {message_count} 条报文")

def _modify_hex(hex_str, bit_pair):
    """修改十六进制字节的奇偶性并返回新值"""
    try:
        dec = int(hex_str, 16)
        print(f"  原始十进制: {dec}")
        
        tens = (dec // 10) % 10
        units = dec % 10
        target_tens = int(bit_pair[0])
        target_units = int(bit_pair[1])
        
        if (tens % 2 == target_tens) and (units % 2 == target_units):
            print("  无需修改：奇偶性已匹配")
            return hex_str, dec, dec
        
        # 生成新值（仅修改十位和个位）
        new_tens = tens if tens % 2 == target_tens else (
            random.choice([1,3,5,7,9]) if target_tens else random.choice([0,2,4,6,8])
        )
        new_units = units if units % 2 == target_units else (
            random.choice([1,3,5,7,9]) if target_units else random.choice([0,2,4,6,8])
        )
        new_dec = (dec // 100) * 100 + new_tens * 10 + new_units
        new_hex = format(new_dec, '08x')
        
        print(f"  新十进制: {new_dec} (十位:{new_tens}, 个位:{new_units})")
        return new_hex, dec, new_dec
    except:
        print("  错误：修改失败")
        return None, None, None

if __name__ == "__main__":
    # 直接设置文件路径和比特串
    input_file = "ML1001_P3_2_IL1001.txt"
    output_file = "ML1001_P3_2_IL1001_mod.txt"
    bit_string = "11001100000000001111111100000000"  # 32位示例比特串
    
    print(f"开始处理文件: {input_file}")
    print(f"目标比特串: {bit_string}")
    print(f"输出文件: {output_file}\n")
    
    modify_message_bytes(input_file, output_file, bit_string)