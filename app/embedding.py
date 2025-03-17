# app/embedding.py
"""
Embedding işlemleri.
"""
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.document_loaders import TextLoader as LangChainTextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import PGVector
import os

from app.config import EMBEDDING_MODEL, DB_CONNECTION, COLLECTION_NAME


# Basit bir TextLoader sınıfı oluştur (unstructured bağımlılığı olmadan)
class TextLoader:
    def __init__(self, file_path):
        self.file_path = file_path

    def load(self):
        from langchain_core.documents import Document
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Dosya bulunamadı: {self.file_path}")

        with open(self.file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        return [Document(page_content=text, metadata={"source": self.file_path})]


def get_embeddings():
    """
    Embedding modelini döndür.
    """
    return SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)


def load_documents(path):
    """
    Belgeleri yükle, böl ve vektörleştir.
    """
    if os.path.isdir(path):
        documents = []
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.txt'):
                    file_path = os.path.join(root, file)
                    try:
                        loader = TextLoader(file_path)
                        documents.extend(loader.load())
                    except Exception as e:
                        print(f"Error loading file {file_path}")
                        print(e)
    else:
        loader = TextLoader(path)
        documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )

    chunks = text_splitter.split_documents(documents)

    if not chunks:
        print("Uyarı: Hiç belge parçası oluşturulmadı. Belgelerin içeriği boş olabilir.")
        return 0

    print(f"{len(chunks)} belge parçası oluşturuldu")

    embeddings = get_embeddings()

    db = PGVector.from_documents(
        documents=chunks,
        embedding=embeddings,
        connection_string=DB_CONNECTION,
        collection_name=COLLECTION_NAME,
        distance_strategy="cosine"
    )

    return len(chunks)