class GlobalValuesClass1:
    # 其他成员和方法保持不变

    def __init__(self, 
                 # 其他参数不变
                 is_Navigating:bool=False,  # 注意，这里的初始化参数保持不变
                 # 其他参数不变
                 ):
        # 其他初始化代码不变
        self.__is_Navigating = is_Navigating  # 注意，这里改为使用私有变量

    # 其他方法保持不变

    def set_is_Navigating(self, is_Navigating:bool=False) -> None:
        self.__is_Navigating = is_Navigating  # 修改内部引用以影响私有变量
        
    @property
    def is_Navigatin(self) -> bool:
        """返回当前的导航状态"""
        return self.__is_Navigating
a = GlobalValuesClass1()

print(a.is_Navigatin)
print(vars(a))


class GlobalValuesClass1:
    def __init__(self, is_Navigating: bool = False):
        self.__is_Navigating = is_Navigating

    @property
    def is_Navigating(self) -> bool:
        return self.__is_Navigating

    # 假设还有其他@property装饰的属性

    # 方法来获取所有@property属性的值
    def get_dcit_attributes(self, ):
        properties = {}
        # dir(obj)会返回对象所有属性和方法的名称
        for name in dir(self):
            # 尝试获取属性的值，忽略任何不是@property的属性
            try:
                value = getattr(self, name)
                if isinstance(getattr(type(self), name, None), property):
                    properties[name] = value
            except AttributeError:
                # 如果属性访问出错，忽略这个属性
                continue
        return properties

# 创建类的实例
instance = GlobalValuesClass1(is_Navigating=True)

# 获取并打印所有@property属性的值
properties = instance.get_property_attributes()
print(properties)
