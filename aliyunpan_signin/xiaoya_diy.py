import sqlite3
import logging
import time
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logging = logging.getLogger("__adrive__")

def get_xiaoya_data_version(max_retries=3):
    """
    获取指定URL的内容。
    
    参数:
    - url: 要获取的URL。
    
    返回:
    - URL的内容，或在出现错误时返回None。
    """
    url = "http://docker.xiaoya.pro/version.txt"
    new_version = ''
    try:
        for retry_count in range(1, max_retries + 1):
            response = requests.get(url)
            if response.status_code == 200:
                new_version = response.text.strip() # 使用strip()删除任何前导或尾随的空白字符
                break
            else:
                logging.error(f"「小雅自动更新」第 {retry_count} 次获取最新数据版本失败，原因: {e}")
                time.sleep(5)
    except requests.RequestException as e:
        logging.error(f"「小雅自动更新」获取最新数据版本内容时出错，原因: {e}")
    return new_version

def update_db_values(database_path, updates, max_retries=3):
    for retry_count in range(1, max_retries + 1):
        try:
            # 连接到数据库
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()
            for update_item in updates:
                table_name = update_item[0]
                if table_name == 'x_meta':
                    path, readme_value = update_item[1:]
                    if readme_value:  # 检查 readme_value 是否为空
                        update_query = f"UPDATE {table_name} SET readme = ? WHERE path = ?"
                        cursor.execute(update_query, (readme_value, path))
                else:
                    _, key_name, value = update_item
                    if value:  # 检查 value 是否为空
                        update_query = f"UPDATE {table_name} SET value = ? WHERE key = ?"
                        cursor.execute(update_query, (value, key_name))
            # 提交更改
            conn.commit()
            # 关闭连接
            conn.close()
            return "成功更新 DIY 美化数据"
        except sqlite3.Error as e:
            logging.error(f"第 {retry_count} 次重试 - 发生数据库错误: {e}")
            if retry_count < max_retries:
                continue
            else:
                return f"数据库错误，重试 {max_retries} 次后仍无法成功更新"
def xiaoya_diy(db_path,new_head_value,new_body_value,new_readme,new_pk_readme=''):
    # 使用示例
    new_logo = 'https://cdn.jsdelivr.net/gh/alist-org/logo@main/logo.svg'
    new_favicon = 'https://cdn.jsdelivr.net/gh/alist-org/logo@main/can_circle.svg'
    # 要更新的多个值的列表
    updates = [
        ('x_setting_items', 'customize_head', new_head_value),
        ('x_setting_items', 'logo', new_logo),
        ('x_setting_items', 'favicon', new_favicon),
        ('x_setting_items', 'customize_body', new_body_value),
        ('x_meta', '/', new_readme),  # 更新x_meta表中path为'/'的readme字段
        ('x_meta', '/每日更新/PikPak', new_pk_readme),  # 更新x_meta表中path为'/'的readme字段
    ]
    return update_db_values(db_path, updates)