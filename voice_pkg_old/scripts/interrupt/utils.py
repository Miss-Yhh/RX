import os

def read_yaml_from_parent(config_filename, parent_levels=1):
    """
    读取位于上级目录中的YAML配置文件。

    :param config_filename: 配置文件的名称，例如 'y.yaml'。
    :param parent_levels: 获取父目录的次数。1代表当前脚本的同父目录的文件，2代表当前脚本的父目录的父目录的文件，以此类推。
    :return: 从YAML文件中读取的数据。
    """
    # 获取当前脚本的绝对路径
    script_path = os.path.abspath(__file__)
    
    # 根据parent_levels获取对应的父目录路径
    parent_dir = script_path
    for _ in range(parent_levels):
        parent_dir = os.path.dirname(parent_dir)
    
    # 构建配置文件的路径
    yaml_path = os.path.join(parent_dir, os.path.join('config', config_filename))

    return yaml_path