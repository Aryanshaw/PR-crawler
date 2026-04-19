import os
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from config import GROQ_API_KEY

class LLMHelper:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in environment variables")
            
        # Using Llama 3 via Groq
        self.llm = ChatGroq(
            groq_api_key=GROQ_API_KEY, 
            model_name="llama-3.3-70b-versatile"
        )
        # Using local free embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

    def get_structured_output(self, prompt, pydantic_object, input_data=None):
        input_data = input_data or {}
        parser = JsonOutputParser(pydantic_object=pydantic_object)
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that extracts structured data. {format_instructions}"),
            ("user", "{prompt}")
        ])
        
        chain = prompt_template | self.llm | parser
        
        return chain.invoke({
            "format_instructions": parser.get_format_instructions(),
            "prompt": prompt,
            **input_data
        })

    def get_embeddings(self, text):
        return self.embeddings.embed_query(text)

    def simple_chat(self, system_msg, user_msg):
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("user", "{user_msg}")
        ])
        chain = prompt | self.llm
        return chain.invoke({"user_msg": user_msg}).content
