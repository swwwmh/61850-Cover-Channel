
def extract_and_process_data(file_path):
    """从文件中提取十六进制报文并处理，生成指定位置字节的比特串，包含时间戳"""
    with open(file_path, 'r') as file:
        content = file.read()
    
    # 分割每个报文，每个报文以'+---------'开始
    messages = []
    parts = content.split('+---------+---------------+----------+')
    
    # 跳过第一个空元素
    for part in parts[1:]:
        if not part.strip():
            continue
            
        # 分割报文的各行
        lines = part.strip().split('\n')
        if len(lines) < 2:
            continue
            
        # 提取时间戳（第一行）
        timestamp_line = lines[0].strip()
        timestamp = timestamp_line.split('   ')[0] if '   ' in timestamp_line else timestamp_line
        
        # 提取所有十六进制数据行（从第二行开始）
        hex_lines = [line for line in lines[1:] if '|' in line]
        if not hex_lines:
            continue
            
        # 合并所有十六进制数据并清洗
        hex_data = ''
        for line in hex_lines:
            # 提取竖线后的部分并去除非十六进制字符
            line_data = line.split('|', 1)[1].strip() if '|' in line else ''
            hex_data += ''.join(c for c in line_data if c in '0123456789abcdefABCDEF')
        
        # 处理当前报文
        process_message(timestamp, hex_data)

# 定义一个全局变量来存储所有比特串
global_bit_string = ''

def process_message(timestamp, hex_data):
    """处理单个报文，包含时间戳，提取指定字节并生成比特串"""
    global global_bit_string  # 声明使用全局变量
    print(f"处理报文 - 时间戳: {timestamp}")
    
    # 确保数据长度足够（至少167字节）
    if len(hex_data) < 167 * 2:  # 每个字节2个十六进制字符
        print("  警告：报文数据长度不足，无法提取指定字节")
        print("-" * 60)
        return
    
    # 提取字节（索引从1开始）
    start_idx = (164 * 2) + 1  # 转换为十六进制字符索引
    end_idx = (168 * 2) + 1
    target_hex = hex_data[start_idx:end_idx]
    
    if len(target_hex) != 8:  # 4字节需要8个十六进制字符
        print("  警告：提取的字节长度异常")
        print("-" * 60)
        return
    
    # 转换为十进制
    try:
        decimal_num = int(target_hex, 16)
    except ValueError:
        print(f"  错误：无法将{target_hex}转换为十进制")
        print("-" * 60)
        return
    
    # 提取十位和个位
    tens_digit = (decimal_num // 10) % 10
    units_digit = decimal_num % 10
    
    # 生成比特串（奇数为1，偶数为0）
    bit_string = ''
    bit_string += '1' if tens_digit % 2 == 1 else '0'
    bit_string += '1' if units_digit % 2 == 1 else '0'
    
    # 将当前比特串追加到全局比特串中
    global_bit_string += bit_string
    
    # 输出结果
    print(f"  提取的4字节十六进制: {target_hex}")
    print(f"  十进制值: {decimal_num}")
    print(f"  十位数字: {tens_digit}, 个位数字: {units_digit}")
    print(f"  生成的比特串: {bit_string}")
    print("-" * 60)

if __name__ == "__main__":
    file_path = "ML1001_P3_2_IL1001_mod.txt"  # 替换为实际文件路径
    print(f"开始处理文件: {file_path}")
    extract_and_process_data(file_path)
    
    # 打印所有比特串
    print(f"The covert bitstring:")
    print(global_bit_string)
