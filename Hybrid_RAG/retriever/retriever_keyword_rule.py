import sys
import os
from wayne_utils import get_ROOT_PATH
_ROOT_PATH = get_ROOT_PATH( 2, __file__)
sys.path.insert(0, _ROOT_PATH)
from data_capture import CplDocumentRatioTextCapture, CplDocumentMoneyTextCapture, CplDocumentDateTextCapture


class CplKeywordRuleRetriever( ):
    def __init__(self, entity_scope:list, core_ruled_text):
        """
        params: entity_scope，例如["法院", "原告", "被告"]
        """
        self.entity_scope = entity_scope
        self.ratio_doc = CplDocumentRatioTextCapture( core_ruled_text )
        self.money_doc = CplDocumentMoneyTextCapture( core_ruled_text )
        self.date_doc = CplDocumentDateTextCapture( core_ruled_text )

    # 获得基于规则的context和相关提示
    def retrieve( self, entity, attr):
        # 获取当前角色类型和名称
        entity_name = None
        entity_type = None
        """"""
        for word in ["法院", "原告", "被告"]:
            if word in entity:
                entity_type = word
                entity_name = entity.split(" ")[1].replace("(", "").replace(")", "").strip()
                break
        # 获取ruled_text中对应的部分
        if "（百分比或元）" in attr:
            context = self.ratio_doc.get_related_context( entity_type, attr)
        elif "（元）" in attr:
            context = self.money_doc.get_related_context( entity_type, attr)
        elif "日期" in attr or "时间" in attr:
            context = self.date_doc.get_related_context( entity_type, attr)
        
        # 对于被告，所有声明必需有被告名
        if entity_type == "被告":
            new_context = []
            for line in context:
                if entity_name in line:
                    new_context.append( line )
            context = new_context
        return context
