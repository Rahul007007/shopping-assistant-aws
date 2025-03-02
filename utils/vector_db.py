from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from utils.logger import CustomLogger
import time
import traceback

logger = CustomLogger('vector_db')

@dataclass
class VectorDBConfig:
    api_key: str
    batch_size: int = 96
    index_name: str = "expedite-assignment"
    dimension: int = 1024
    metric: str = "cosine"
    cloud: str = "aws"
    region: str = "us-east-1"

class VectorDB:
    def __init__(self, config: VectorDBConfig):
        self.config = config
        self.pc = Pinecone(api_key=config.api_key)
        self.index = None
        self.__initialize_index()

    def __initialize_index(self) -> None:
        """Initialize or connect to existing Pinecone index"""
        try:
            if not self.pc.has_index(self.config.index_name):
                self.pc.create_index(
                    name=self.config.index_name,
                    dimension=self.config.dimension,
                    metric=self.config.metric,
                    spec=ServerlessSpec(
                        cloud=self.config.cloud,
                        region=self.config.region
                    )
                )
                # Wait for index to be ready
                while not self.pc.describe_index(self.config.index_name).status['ready']:
                    time.sleep(1)

            self.index = self.pc.Index(self.config.index_name)
        except Exception as e:
            logger.error(f"Error initializing Pinecone index: {e}", level='ERROR')
            traceback.print_exc()
            raise e


    def upsert_data(self, data: List[Dict[str, Any]]) -> None:
        """
        Upsert data into the vector database
        Args:
            data: List of dictionaries containing product information
        """
        try:
            records = []
            for i in range(0, len(data), self.config.batch_size):
                batch = data[i:i+self.config.batch_size]
                embeddings = self.pc.inference.embed(
                    model="multilingual-e5-large",
                    inputs=[d["description"] for d in batch],
                    parameters={
                        "input_type": "passage",
                        "truncate": "END"
                    }
                )
                for doc, emb in zip(batch, embeddings):
                    doc_copy = doc.copy()
                    id = doc_copy.pop("id")
                    records.append({
                        "id": str(id),
                        "values": emb["values"],
                        "metadata": doc_copy
                    })
                time.sleep(2)

            # Batch upsert records
            def chunker(seq, batch_size):
                return (seq[pos:pos + batch_size] for pos in range(0, len(seq), batch_size))

            async_results = [
                self.index.upsert(vectors=chunk, async_req=True)
                for chunk in chunker(records, batch_size=200)
            ]

            # Wait for and retrieve responses
            [async_result.result() for async_result in async_results]
            logger.log_trace("Data upserted successfully", level='INFO')
        except Exception as e:
            logger.error(f"Error upserting data into Pinecone index: {e}", level='ERROR')
            traceback.print_exc()
            raise e

    def get_product_recommendations(self, query_text: str, top_k: int = 3, reformat_results=True, run_reranking=True) -> Dict[str, Any]:
        """
        Query the vector database for various products that similar to the query text
        Args:
            query_text: Text to search for
            top_k: Number of results to return
            reformat_results: Whether to reformat the results
        Returns:
            Dictionary containing search results
        """
        try:
            query_embedding = self.pc.inference.embed(
                model="multilingual-e5-large",
                inputs=[query_text],
                parameters={
                    "input_type": "query"
                }
            )

            results = self.index.query(
                vector=query_embedding[0].values,
                top_k=top_k,
                include_values=False,
                include_metadata=True
            )
            logger.log_trace(f"Search success", level='INFO')
            matches = results["matches"]
            if not run_reranking:
                if reformat_results:
                    return self.__reformat_results(matches)
            else:
                reranked_docs = self.__run_reranking(query_text, matches)
                if reformat_results:
                    return self.__reformat_reranked_results(reranked_docs)
                return reranked_docs

            return matches
        except Exception as e:
            logger.error(f"Error querying Pinecone index: {e}", level='ERROR')
            traceback.print_exc()
            raise e

    def __run_reranking(self, query_text: str, matches: Dict[str, Any]) -> Dict[str, Any]:
        """Run reranking on search results"""
        docs_for_rerank = []
        for match in matches:
            match_metadata = match['metadata'].copy()
            match_metadata['id'] = match['id']
            docs_for_rerank.append(match_metadata)
        try:
            reranked_docs = self.pc.inference.rerank(
                        model="bge-reranker-v2-m3",
                        query=query_text,
                        documents=docs_for_rerank,
                        top_n=3,
                        rank_fields=["description"],
                        return_documents=True,
                        parameters={
                            "truncate": "END"
                        }
                    )
            logger.log_trace(f"Reranking success", level='INFO')
            return reranked_docs
        except Exception as e:
            logger.error(f"Error reranking search results: {e}", level='ERROR')
            traceback.print_exc()
            raise e
    def __reformat_reranked_results(self, reranked_docs: List[Dict[str, Any]]) -> str:
        """Reformat reranked search results"""
        reformatted_str = ""
        for data in reranked_docs.data:
            result = data.document
            reformatted_str += f"Category: {result.root_category_name}\n"
            reformatted_str += f"Brand: {result.brand}\n"
            reformatted_str += f"Product ID: {result.product_id}\n"
            reformatted_str += f"Product Name: {result.product_name}\n"
            reformatted_str += f"Description: {result.description}\n"
            reformatted_str += f"Price: {result.final_price}\n"
            reformatted_str += f"Rating: {result.rating}\n"
            reformatted_str += f"Discount: {result.discount}\n"
            reformatted_str +="\n\n"

        return reformatted_str
    
    def __reformat_results(self, results: Dict[str, Any]) -> str:
        """Reformat search results"""

        reformatted_str = ""
        for result in results:
            metadata = result["metadata"]
            reformatted_str += f"Category: {metadata['root_category_name']}\n"
            reformatted_str += f"Brand: {metadata['brand']}\n"
            reformatted_str += f"Product ID: {metadata['product_id']}\n"
            reformatted_str += f"Product Name: {metadata['product_name']}\n"
            reformatted_str += f"Description: {metadata['description']}\n"
            reformatted_str += f"Price: {metadata['final_price']}\n"
            reformatted_str += f"Rating: {metadata['rating']}\n"
            reformatted_str += f"Discount: {metadata['discount']}\n"
            reformatted_str +="\n\n"
        return reformatted_str

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        return self.index.describe_index_stats()

    def delete_index(self) -> None:
        """Delete the index"""
        self.pc.delete_index(self.config.index_name)

# Example usage:
"""
from vector_db import VectorDB, VectorDBConfig
import os
from dotenv import load_dotenv

load_dotenv()
config = VectorDBConfig(api_key=os.getenv('PINECONE_API_KEY'))
vector_db = VectorDB(config)

# Query example
results = vector_db.get_product_recommendations("What are the lipsticks available?")
print(results)
"""
