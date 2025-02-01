
# 基础包
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.schema import TextNode
from llama_index.core import StorageContext
# 模型包
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.huggingface import HuggingFaceLLM

# 检索器包
from llama_index.core.retrievers import KeywordTableSimpleRetriever, VectorIndexRetriever 
from .retriever.retriever_bm25 import Rank_BM25_Retriever, Llamaindex_BM25_Retriever

# 其他包
from .data_capture import ParagraphSplit
import os

embed_model = None
llm = None

class HybridRAG( ):
    def __init__(self, text, embedding_model_path, llm_path = None, top_k = 3, threshold = 0.7, gpu_id = 0):
        """
        param text: 单个文本
        param top_k: 检索器返回个数
        param threshold: vector_retriever的返回值门槛
        param gpu_id: 使用的GPU编号
        """
        self.text = text
        self.top_k = top_k
        self.threshold = threshold

        os.environ["CUDA_VISIBLE_DEVICES"]  = str(gpu_id)
        # 制定embedding模型和LLM
        global embed_model, llm
        if embed_model == None:
            embed_model = HuggingFaceEmbedding(
                model_name = embedding_model_path
            )
        Settings.embed_model = embed_model
        if llm_path != None and llm == None:
            '''llm = HuggingFaceLLM(
                model_name = llm_path,
                tokenizer_name  = llm_path,
                model_kwargs={"trust_remote_code":True},
                tokenizer_kwargs={"trust_remote_code":True}
            )'''
            Settings.llm = llm

        # 构建单文本检索器
        self.nodes = self.rule_text_to_nodes( text )
        storage_context = StorageContext.from_defaults()
        storage_context.docstore.add_documents(self.nodes)
        # keyword_index = KeywordTableIndex(nodes, storage_context=storage_context)
        vector_index = VectorStoreIndex(self.nodes, storage_context=storage_context)
        self.vector_retriever = VectorIndexRetriever(index=vector_index, similarity_top_k=self.top_k, score = self.threshold)
        self.rank_bm25_retriever = Llamaindex_BM25_Retriever( vector_index, self.top_k)


    def rule_text_to_nodes( self, rule_text ):
        # 句子级分割
        new_text_list = []
        for key in rule_text:
            _list = rule_text[key]
            if key == '开头':
                new_text_list.append( "".join( _list ) )
            else:
                spliter = ParagraphSplit( _list )
                new_text_list.extend( spliter.sentence_doc )

        # 变成Node list
        nodes = []
        for i in range(len(new_text_list)):
            metadata={ }
            ids = str( len(nodes) )
            node = TextNode( text=new_text_list[i], id_=  ids, metadata=metadata)
            nodes.append( node )
        return nodes
    
    def hybrid_retrive( self, query ):
        auto_results_list = []
        vector_results = self.vector_retriever.retrieve( query )
        for i in range(len(vector_results)):
            auto_results_list.append( vector_results[i].text )
        rank_bm25_results = self.rank_bm25_retriever.retrieve( query ) 
        for i in range(len(rank_bm25_results)):
            if rank_bm25_results[i].text not in auto_results_list:
                auto_results_list.append( rank_bm25_results[i].text )
        return auto_results_list
    

if __name__ == "__main__":
    embedding_model_path = ""
    llm_path = None
    text = ""
    top_k = 3
    threshold = 0.6
    gpu_id = 0
    retriever = HybridRAG( text, embedding_model_path, llm_path, top_k, threshold, gpu_id)