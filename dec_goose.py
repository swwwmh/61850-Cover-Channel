import re
import random

def process_network_packets(input_file, output_file, bit_string):
    """处理网络报文文件，增强格式容错性并正确识别报文结构"""
    if len(bit_string) != 32:
        raise ValueError("bit_string必须是32位的二进制字符串")
    
    with open(input_file, 'r') as f:
        content = f.read()
    
    # 定义报文分隔符（兼容不同换行符）
    packet_separator = r'(\+---------\+---------------\+----------\+\s*\n.*?\n)'
    # 使用正则表达式查找所有报文，保留分隔符作为报文的一部分
    packets = re.findall(packet_separator + r'(.*?)(?=\+---------\+|$)', content, re.DOTALL)
    
    print(f"检测到{len(packets)}份报文，目标16份")
    
    if len(packets) != 16:
        print(f"警告：报文数量不符，期望16份，实际{len(packets)}份")
    
    modified_packets = []
    processed_count = 0

    for i, (header, packet) in enumerate(packets):
        print(f"===== 处理报文{i+1} =====")
        print(f"头部: {repr(header)}")
        print(f"数据部分前100字符: {repr(packet[:100])}")
        
        # 提取数据段（|0   |后的内容）
        data_match = re.search(r'\|0\s*\|\s*((?:[0-9a-fA-F]{2}\s*\|\s*)+[0-9a-fA-F]{2})\s*\|', packet, re.IGNORECASE)
        if not data_match:
            print(f"错误：报文{i+1}未找到数据段，格式异常，跳过")
            modified_packets.append(header + packet)
            continue
        
        original_data = data_match.group(1)
        # 提取有效字节及位置
        bytes_data = re.findall(r'([0-9a-fA-F]{2})', original_data, re.IGNORECASE)
        print(f"解析到{len(bytes_data)}个有效字节")
        
        if len(bytes_data) < 161:
            print(f"警告：报文{i+1}字节数不足，跳过")
            modified_packets.append(header + packet)
            continue
        
        target_indices = [157, 158, 159]
        if any(idx >= len(bytes_data) for idx in target_indices):
            print(f"错误：报文{i+1}目标索引超出范围，跳过")
            modified_packets.append(header + packet)
            continue
        
        # 获取目标字节及位置
        target_bytes = [bytes_data[idx] for idx in target_indices]
        original_hex = ''.join(target_bytes).upper()
        print(f"原始目标字节: {original_hex}")
        
        # 数值计算
        try:
            target_dec = int(original_hex, 16)
        except ValueError:
            print(f"错误：报文{i+1}目标字节无效，跳过")
            modified_packets.append(header + packet)
            continue
        
        # 除以16777216
        divided_value = target_dec / 16777216
        print(f"除以16777216后的值: {divided_value}")
        
        # 乘以10000000并取整
        scaled_value = int(divided_value * 10000000)
        print(f"乘以10000000并取整后的值: {scaled_value}")
        
        # 修改十位和个位的奇偶性
        bit_index = i * 2  # 每份报文对应两个bits
        if bit_index + 1 >= len(bit_string):
            print("错误：bit_string长度不足，跳过")
            modified_packets.append(header + packet)
            continue
        
        target_bit10 = bit_string[bit_index]    # 十位对应的bit
        target_bit1 = bit_string[bit_index + 1] # 个位对应的bit
        
        # 分解数值
        thousands_part = scaled_value // 1000 * 1000
        hundreds_part = (scaled_value % 1000) // 100 * 100
        tens_ones_part = scaled_value % 100
        
        # 调整十位和个位
        adjusted_tens_ones = tens_ones_part
        
        # 处理十位奇偶性
        current_tens = (tens_ones_part // 10) % 10
        if (target_bit10 == '1' and current_tens % 2 == 0) or \
           (target_bit10 == '0' and current_tens % 2 == 1):
            # 生成符合奇偶性要求的随机十位数字(0-9)
            new_tens = random.randrange(0, 10, 2) if target_bit10 == '0' else random.randrange(1, 10, 2)
            adjusted_tens_ones = (adjusted_tens_ones % 10) + (new_tens * 10)
        
        # 处理个位奇偶性
        current_ones = adjusted_tens_ones % 10
        if (target_bit1 == '1' and current_ones % 2 == 0) or \
           (target_bit1 == '0' and current_ones % 2 == 1):
            # 生成符合奇偶性要求的随机个位数字(0-9)
            new_ones = random.randrange(0, 10, 2) if target_bit1 == '0' else random.randrange(1, 10, 2)
            adjusted_tens_ones = (adjusted_tens_ones // 10) * 10 + new_ones
        
        # 确保在0-99范围内
        adjusted_tens_ones %= 100
        
        modified_scaled_value = thousands_part + hundreds_part + adjusted_tens_ones
        print(f"修改后的缩放值: {modified_scaled_value}")
        
        # 先除以10000000再乘以16777216
        final_value = (modified_scaled_value / 10000000) * 16777216
        print(f"除以10000000乘以16777216后的最终值: {final_value}")
        
        # 四舍五入取整并转换为十六进制
        modified_dec = round(final_value)
        print(f"四舍五入后的值: {modified_dec}")
        
        new_hex = hex(modified_dec)[2:].zfill(6).lower()  # 确保输出为小写
        new_target_bytes = [new_hex[0:2], new_hex[2:4], new_hex[4:6]]
        print(f"新目标字节: {new_target_bytes}")
        
        # 替换原始数据中的目标字节
        modified_data = original_data
        for idx, pos in zip(target_indices, target_indices):
            modified_data = modified_data[:pos*3] + new_target_bytes[idx - target_indices[0]] + modified_data[pos*3+2:]
        
        # 重建数据部分
        new_packet = packet.replace(original_data, modified_data)
        
        # 重建整个报文（包含头部）
        modified_packet = header + new_packet
        modified_packets.append(modified_packet)
        processed_count += 1
        
        print(f"报文{i+1}替换成功")
        print("===== 处理完成 =====")
    
    # 重建文件内容
    modified_content = ''.join(modified_packets)
    
    with open(output_file, 'w') as f:
        f.write(modified_content)
    
    print(f"处理完成：共{processed_count}份报文成功替换目标字节")

def extract_bit_string_from_packets(input_file):
    """从网络报文文件中提取比特串"""
    with open(input_file, 'r') as f:
        content = f.read()
    
    # 定义报文分隔符（兼容不同换行符）
    packet_separator = r'(\+---------\+---------------\+----------\+\s*\n.*?\n)'
    # 使用正则表达式查找所有报文，保留分隔符作为报文的一部分
    packets = re.findall(packet_separator + r'(.*?)(?=\+---------\+|$)', content, re.DOTALL)
    
    print(f"检测到{len(packets)}份报文，目标16份")
    
    if len(packets) != 16:
        print(f"警告：报文数量不符，期望16份，实际{len(packets)}份")
    
    extracted_bits = []
    
    for i, (header, packet) in enumerate(packets):
        print(f"===== 解析报文{i+1} =====")
        print(f"头部: {repr(header)}")
        print(f"数据部分前100字符: {repr(packet[:100])}")
        
        # 提取数据段（|0   |后的内容）
        data_match = re.search(r'\|0\s*\|\s*((?:[0-9a-fA-F]{2}\s*\|\s*)+[0-9a-fA-F]{2})\s*\|', packet, re.IGNORECASE)
        if not data_match:
            print(f"错误：报文{i+1}未找到数据段，格式异常，跳过")
            extracted_bits.extend(['0', '0'])  # 默认添加两个0
            continue
        
        original_data = data_match.group(1)
        # 提取有效字节及位置
        bytes_data = re.findall(r'([0-9a-fA-F]{2})', original_data, re.IGNORECASE)
        print(f"解析到{len(bytes_data)}个有效字节")
        
        if len(bytes_data) < 161:
            print(f"警告：报文{i+1}字节数不足，跳过")
            extracted_bits.extend(['0', '0'])  # 默认添加两个0
            continue
        
        target_indices = [157, 158, 159]
        if any(idx >= len(bytes_data) for idx in target_indices):
            print(f"错误：报文{i+1}目标索引超出范围，跳过")
            extracted_bits.extend(['0', '0'])  # 默认添加两个0
            continue
        
        # 获取目标字节及位置
        target_bytes = [bytes_data[idx] for idx in target_indices]
        hex_value = ''.join(target_bytes).upper()
        print(f"目标字节: {hex_value}")
        
        # 数值计算
        try:
            target_dec = int(hex_value, 16)
        except ValueError:
            print(f"错误：报文{i+1}目标字节无效，跳过")
            extracted_bits.extend(['0', '0'])  # 默认添加两个0
            continue
        
        # 除以16777216再乘以10000000
        scaled_value = (target_dec / 16777216) * 10000000
        print(f"缩放后的值: {scaled_value}")
        
        # 四舍五入取整
        rounded_value = round(scaled_value)
        print(f"四舍五入后的值: {rounded_value}")
        
        # 提取十位和个位
        tens_digit = (rounded_value // 10) % 10
        ones_digit = rounded_value % 10
        
        print(f"十位: {tens_digit}, 个位: {ones_digit}")
        
        # 根据奇偶性确定比特值
        bit10 = '0' if tens_digit % 2 == 0 else '1'
        bit1 = '0' if ones_digit % 2 == 0 else '1'
        
        print(f"提取的比特: {bit10}{bit1}")
        
        extracted_bits.extend([bit10, bit1])
    
    # 构建最终的比特串
    bit_string = ''.join(extracted_bits)
    
    print(f"提取的完整比特串: {bit_string}")
    print(f"比特串长度: {len(bit_string)}")
    
    return bit_string

if __name__ == "__main__":
    # 从修改后的文件中提取比特串
    modified_file = "IL001_P2_ML1001_mod.txt"
    extracted_bit_string = extract_bit_string_from_packets(modified_file)
    print(f"The covert bitstring: {extracted_bit_string}")