import re
from typing import List

import os
import sys
import re


class TextCapture():
    """
    针对一个句子：捕获一个句子中指定匹配格式/符号的数据，并获取该上下文。
    """
    def __init__(self, text: str, match_word, _context_length = 10, _orient = "all" ):
        self.text = text                                        # 要匹配的句子
        self.match_word = match_word                            # 匹配模式或符号
        self.context_length = _context_length
        self.orient = _orient

        if isinstance( match_word, re.Pattern):                 # 正则匹配
            self.matched_words = self.match_word_capture_re()
        else:
            raise Exception(f"当前不支持除正则匹配外的其他方式")
    
    def match_word_capture_re( self ):
        """正则匹配"""
        pattern_role = self.match_word
        matched_words = [match.group() for match in re.finditer(pattern_role, self.text)]
        return matched_words

    def get_context(self, symbol):
        """返回一个字符串在文中的内容：输出字符串列表"""
        pattern = re.compile(re.escape(symbol))                  # 编译正则表达式，使用非贪婪匹配来找到符号的位置  
        matches = [match.start() for match in pattern.finditer( self.text)]           # 查找所有符号的位置  
        contexts = []                                                           # 存储结果的列表  
        # 遍历每个匹配的位置  
        for match_index in matches:  
            # 计算上下文的起始和结束位置  
            start_index = max(0, match_index - self.context_length)  
            end_index = match_index + self.context_length + len(symbol)  # 加上符号的长度和额外的上下文长度  
            
            # 获取上下文内容  
            context = self.text[start_index:end_index]  
            # 将上下文内容添加到结果列表中  
            contexts.append(context)  
        
        return contexts  

class ParagraphSplit( ):
    """对一段文本而言"""
    def __init__(self, doc, _sep = [ "。", "；"]):
        self.seps = _sep
        self.sentence_doc = self.sentence_splitter( doc )

    def sentence_splitter( self, texts:list, index = 0) -> List[str]:
        """将一个长段落根据句号、分号进行递归分割
        index：当前使用的sep的索引
        texts：要分割的文本对象，以列表形式传入
        """
        if index < len( self.seps ):                                 # 如果还有分隔符可以用
            sep = self.seps[index]
        else:                                                       # 否则原样返回
            return texts
    
        ret_list = []
        for line in texts:
            lines = line.split( sep )
            for line in lines:
                line = line.strip()
                if line != "":
                    ret_list.append( line )
        return self.sentence_splitter( ret_list, index+1)

class CplParagraphSplit( ParagraphSplit ):
    """对一篇CPL文章分成三部分，每部分是最小字句的列表"""
    def __init__(self, 
                 doc, 
                 type_class,                # 实例化每个句子的类
                 context_length = 10,       # 实例化每个句子类需要的上下文情况
                 orient = "all",
                 _seps = [ "。"]      # 文章级别分隔符
                  ):
        super().__init__( doc, _seps)
        self.type_class = type_class
        self.context_length = context_length
        self.orient = orient
        # 对每个字句进行实例化
        self.sent_instance = self.capture_instantiate()

    def capture_instantiate( self ):
        """对全文每个Part的每个句子，都进行self.type_class实例化并存为字典"""
        ret = []
        # 遍历三个角色
        for sent in self.sentence_doc:
            ret.append( self.type_class( sent, self.context_length, self.orient ) )
        return ret

############################################### 日期 #############################################################################
class DateTextCapture( TextCapture ):
    """
    针对一个句子：捕获一个句子中所有年-月-日格式的数据，并根据上下文区分哪些是起始、截止、普通日期
    """
    def __init__(self, text: str, context_length = 10, orient = "all"):
        self.match_word = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")
        super().__init__( text, self.match_word, context_length, orient)
        self.start_date_dict = {}
        self.end_date_dict = {}
        self.normal_date_dict = {}
        self.all_time_capture()
    
    def all_time_capture( self ):
        date_set = set()
        for tup in self.matched_words:
            # date_set.add( f"{tup[0]}年{tup[1]}月{tup[2]}日")
            date_set.add(tup)
        for date_str in date_set:
            contexts = self.get_context( date_str )
            for context in contexts:
                if "自"+date_str in context or date_str+"起" in context:
                    # 起始日期
                    if date_str not in self.start_date_dict:
                        self.start_date_dict[ date_str ] = []
                    self.start_date_dict[ date_str ].append( context )
                elif "至"+date_str in context or date_str+"截止" in context or date_str+"止" in context:
                    # 截止日期
                    if date_str not in self.end_date_dict:
                        self.end_date_dict[ date_str ] = []
                    self.end_date_dict[ date_str ].append( context )
                else:
                    # 普通日期
                    if date_str not in self.normal_date_dict:
                        self.normal_date_dict[ date_str ] = []
                    self.normal_date_dict[ date_str ].append( context )

class CplDocumentDateTextCapture( CplParagraphSplit ):
    """对一篇文章中一个主体而言"""
    def __init__(self, doc, context_length = 10, orient = "all", _seps = [ "。", "；"]):
        super().__init__( doc, DateTextCapture, context_length, orient, _seps)

    def get_attr_context_dict( self, attr) -> List[dict]:
        """指定实体和属性，返回所有句子中的日期数据及其相关的上下文字典"""
        ret = []
        sub_list = self.sent_instance                   # 获得本文该对象名下所有含有日期的句子的字典：sent：instance
        # 遍历每个句子，获取日期字典
        for line in sub_list:
            text_capture = line                     # 句子对应的日期字符串字典
            if len(text_capture.start_date_dict) > 0 or len(text_capture.end_date_dict) > 0 or len(text_capture.normal_date_dict) > 0:
                if line.text not in ret:
                    ret.append( line.text )
        return ret
    
    def get_related_context( self, attr)-> List[dict]:
        """对该部分的所有字句都进行基于entity和attr的判断，返回对应的上下文"""
        part_dict_list = self.get_attr_context_dict( attr )
        # 遍历每个句子存放该篇文档针对entity实体的attr的属性的句子列表
        ret = []                                    
        for i in range( len(part_dict_list) ):
            contexts = part_dict_list[i]           # 获取针对一行的所有日期数据
            flag = 0
            if "约定的还款日期或借款期限" in attr and ("还" in contexts or "偿" in contexts or "限" in contexts or "至" in contexts):
                flag = 1
            elif "发生时间" in attr:
                flag = 1
            if flag == 1:
                ret.append( contexts )
        return ret

############################################ 金额 #########################################
class MoneyTextCapture( TextCapture ):
    """
    针对一个句子：捕获一个句子中所有xx元格式的数据
    """
    def __init__(self, text: str, context_length = 10, orient = "all"):
        self.match_word = re.compile(r'\d{1,3}(?:[，,]\d{3})*(?:\.\d+)?(?:万)?元')
        super().__init__( text, self.match_word, context_length, orient)
        self.money_dict = {}
        self.all_money_capture()
    
    # 获取一个句子所有金额要素及其上下文
    def all_money_capture( self ):
        for money in self.matched_words:
            contexts = self.get_context( money ) 
            if money not in self.money_dict:
                self.money_dict[ money ] = contexts
            else:
                self.money_dict[ money ].extend( contexts )

class CplDocumentMoneyTextCapture( CplParagraphSplit ):
    """（元）"""
    def __init__(self, doc, context_length = 10, orient = "all", _seps = [ "。", "；"]):
        super().__init__( doc, MoneyTextCapture, context_length, orient, _seps)

    def get_attr_context_dict( self ) -> List[dict]:
        """指定实体和属性，返回所有句子中的日期数据及其相关的上下文字典"""
        ret = []
        sub_list = self.sent_instance            # 获得本文该对象名下所有含有日期的句子的字典
        # 遍历每个句子，获取金额字典
        for i in range(len(sub_list)):
            text_capture = sub_list[ i ]            # 句子对应的金额字符串字典
            money_dict = text_capture.money_dict
            ret.append( money_dict )
        return ret
    
    def get_related_context( self, attr)-> List[dict]:
        """对该部分的所有字句都进行基于entity和attr的判断，返回对应的上下文"""
        part_dict_list = self.get_attr_context_dict( )
        # 遍历每个句子存放该篇文档针对entity实体的attr的属性的句子列表
        ret = []                                    
        for i in range( len(part_dict_list) ):
            date_dict = part_dict_list[i]           # 获取针对一行的所有金额数据
            flag = 0
            # 遍历当前句子中所有金额格式的数据：获取数据对应的上下文列表，
            for date in date_dict.keys():
                if flag == 1:                       # 若已经验证通过，提前退出
                    break
                contexts = date_dict[date]
                if len(contexts)==0:
                    continue
                else:
                    # 遍历列表判断是否符合要求
                    for context in contexts:
                        if len(context.strip()) > 0:
                            # 对不同的日期数据进行分类讨论
                            if "约定的借款金额" in attr and ("借" in context or "约定" in context):
                                flag = 1
                                break
            if flag == 1:
                ret.append( self.sentence_doc[i] )
        return ret

############################################ 比例 #########################################
class RatioTextCapture( TextCapture ):
    """
    针对一个句子：捕获一个句子中所有xx%格式的数据
    """
    def __init__(self, text: str, context_length = 10, orient = "all"):
        self.match_word = re.compile(
            r'(?<!\d)\d{1,2}(\.\d{1,2})?%|'  # 原有的百分比匹配
            r'[十百千万]?分之[零一二三四五六七八九十百千万两\d]+'  # 中文形式的“分之”匹配
        )
        super().__init__( text, self.match_word, context_length, orient)
        self.dict = {}
        self.all_capture()
    
    def all_capture( self ):
        for money in self.matched_words:
            if len( money.strip() )>0:
                contexts = self.get_context( money ) 
                if money not in self.dict:
                    self.dict[ money ] = contexts
                else:
                    self.dict[ money ].extend( contexts )

class CplDocumentRatioTextCapture( CplParagraphSplit ):
    """%"""
    def __init__(self, doc, context_length = 10, orient = "all", _seps = [ "。", "；"]):
        super().__init__( doc, RatioTextCapture, context_length, orient, _seps)

    def get_attr_context_dict( self) -> List[dict]:
        """指定实体和属性，返回所有句子中的比例数据及其相关的上下文字典"""
        ret = []
        sub_list = self.sent_instance            # 获得本文该对象名下所有含有日期的句子的字典
        # 遍历每个句子，获取金额字典
        for line in sub_list:
            text_capture = line         # 句子对应的金额字符串字典
            dict = text_capture.dict
            ret.append( dict )
        return ret
    
    def get_related_context( self, attr)-> List[dict]:
        """对该部分的所有字句都进行基于entity和attr的判断，返回对应的上下文"""
        part_dict_list = self.get_attr_context_dict( )
        # 遍历每个句子存放该篇文档针对entity实体的attr的属性的句子列表
        ret = []                                    
        for i in range( len(part_dict_list) ):
            date_dict = part_dict_list[i]           # 获取针对一行的所有金额数据
            flag = 0
            # 遍历当前句子中所有金额格式的数据：获取数据对应的上下文列表，
            for date in date_dict.keys():
                if flag == 1:                       # 若已经验证通过，提前退出
                    break
                contexts = date_dict[date]
                if len(contexts)==0:
                    continue
                else:
                    # 遍历列表判断是否符合要求
                    for context in contexts:
                        # 对不同的日期数据进行分类讨论
                        if "约定的利息" in attr and ("息" in context or "率" in context):
                            flag = 1
                            break
                        elif "约定的逾期利息" in attr and ( "利" in context or "率" in context or "约定" in context):
                            flag = 1
                            break
                        elif "约定的违约金" in attr and ( "违约" in context or "罚" in context or "约定" in context or "息" in context or "率" in context):
                            flag = 1
                            break
            if flag == 1:
                ret.append( self.sentence_doc[i] )
        return ret
    

#################################### 入口方法 ###########################

# 实体名
def entity_name_keyword_rag( entity, texts ):
    ret = []
    if entity == "法院":
        for line in texts["开头"]:
            if "法院" in line:
                ret.append( line.strip() )
        return ret
    else:
        procedure = texts['程序信息']
        sent_procedure = chunk_sentence( procedure )
        keywords_dict = {
            "原告": ["原告", "申请人"], 
            "被告": ["被告", "被申请人"]
        }
        keywords = keywords_dict[entity]
        not_keywords = keywords_dict["原告"][:-1] if entity == "被告" else keywords_dict["被告"]
        not_keywords.append( "代理人" )

        for line in sent_procedure:
            for keyword in keywords:
                if keyword in line:
                    flag = 0
                    for notword in not_keywords:
                        if notword in line:
                            flag = 1
                            break
                    if flag == 0:
                        ret.append( line.strip() )
        return ret

# 证据
def lending_evidence_rag( entity, texts ):
    docs = {
        "原告": texts['原告申诉'],
        "法院": texts['法院裁定']
    }
    ret = []
    keywords = [ "证据", "借条", "欠条", "借据", "收据", "物证", "证明", "协议", "收条", "合同"]
    banwords = [ "合同法"]
    and_words = [ "出具", "收到", "载", "签", "写", "约定", "内容"] 
    scopes = chunk_sentence( docs[ entity ] )
    for line in scopes:
        flag = 0
        for keyword in keywords:
            if flag == 1:
                break
            # 如果借款凭证关键字在
            if keyword in line:
                for banword in banwords:
                    if flag == 1:
                        break
                    # 且没有禁用词
                    if banword not in line:
                        for andword in and_words:
                            # 且有副助词
                            if andword in line:
                                ret.append( line )
                                flag = 1
                                break
    return ret


def type_recognizer( entity, key, texts ):
    text_pool = texts['法院裁定'] if entity == "法院" else texts['原告申诉']
    prefix = '法院认定：' if entity == "法院" else '原告主张：'
    ret = []
    if "姓名名称" in key:
        ret = entity_name_keyword_rag( entity, texts )
        prefix = "主体清单："
    elif "借款凭证" in key:
        ret = lending_evidence_rag( entity, texts )
    elif "借款金额" in key:
        capture = CplDocumentMoneyTextCapture(text_pool, context_length=30 )
        ret = capture.get_related_context( key )
    elif "还款日期或借款期限" in key:
        capture = CplDocumentDateTextCapture(text_pool, context_length=30 )
        ret = capture.get_related_context( key )
    elif "利息" in key or "违约金" in key:
        capture = CplDocumentRatioTextCapture(text_pool, context_length=30 )
        ret = capture.get_related_context( key ) 
    return f"{prefix}{ret}"

if __name__=="__main__":
    '''text = ['原告董光华、池昌概起诉称：被告杨小宝、王念安于农历2010年3月16日（即2010年4月29日）向原告借款39000元，约定月利率为2%，并出具借据。借款后，被告未偿还借款本息。现原告董光华、池昌概起诉要求：1.被告杨小宝、王念安共同偿还借款39000元及利息（从2010年4月29日起按月利率2%计算至判决确定支付之日止）；2.本案诉讼费由被告承担。',
 '原告在本院指定的举证期限内提供了如下证据：1.原告身份证，证明原告诉讼主体资格；2.被告人口信息、身份证，证明被告诉讼主体资格；3.借据，证明被告向原告借款及约定借款利率的事实。']
    capture = CplDocumentDateTextCapture(text, context_length=15 ) 
    ret = capture.get_related_context( "需返回利息计算起始日期" )
    print(ret)'''

    text = ['本院经审理认定：原告麻建海与被告林东升系朋友关系。2013年10月24日，被告林东升因经营需要向原告借款3万元，原告直接将现金3万元交付给被告，被告于同日向原告出具借据一张，约定借款期限从2013年10月24日起至2013年11月15日止。后还款期限届满，原告曾多次向被告催讨均未果。',
 '本院依照《中华人民共和国合同法》第一百零七条、第二百零六条，《中华人民共和国民事诉讼法》第一百四十四条、第一百四十八条的规定，判决如下：',
 '被告林东升于本判决生效之日起十日内偿还原告麻建海借款3万元并赔偿利息损失（从2016年4月5日起按年利率4.35%计算至判决确定的履行之日止）。',
 '如果未按本判决指定的期间履行给付金钱义务，应当依照《中华人民共和国民事诉讼法》第二百五十三条的规定，加倍支付迟延履行期间债务利息。']
    capture = CplDocumentDateTextCapture( text, context_length=30 )    
    capture.get_related_context( '第1次约定的还款日期或借款期限的还款日期' )