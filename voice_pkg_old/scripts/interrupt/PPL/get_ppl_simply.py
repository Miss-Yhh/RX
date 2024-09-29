# ==============
# Author: hsong
# ==============

from typing import Union, List, Dict 
from ppl_mydata import get_ppl_for

if __name__=='__main__':
    
    test2 =      [
                "介绍一下化工大在航天领域的科研成果",
                "介绍一下哈工大在航天的一份科研成果",
                "介绍一下杭州大厦王天岭的科研厂"
                ],
    
    test = "介绍一些哈工大在航天领域的科研成果"
    ppl = get_ppl_for(test)