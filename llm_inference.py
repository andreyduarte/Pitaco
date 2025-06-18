from typing import Optional, Dict, Any, Type, cast, List
from pydantic import BaseModel, ValidationError
from google import genai # NÃO MODIFICAR / DO NOT MODIFY
import google.genai.types as genai_types
import logging
import json
import os
import time
import config

# Configure logging
logger = logging.getLogger(__name__)

def _make_llm_call(
    client: genai.Client,
    prompt_content: str,
    output_schema: Type[BaseModel],
    difficulty: str = "medium" # Adicionado parâmetro de dificuldade com default
) -> Optional[Dict[str, Any]]:
    """Função auxiliar para fazer uma chamada à API e processar a resposta com retries."""
    contents = [
        genai_types.Content( # NÃO MODIFICAR / DO NOT MODIFY
            role="user",
            parts=[genai_types.Part.from_text(text=prompt_content)],
        ),
    ]

    generation_config = genai_types.GenerateContentConfig( # NÃO MODIFICAR / DO NOT MODIFY
        response_mime_type="application/json",
        response_schema=output_schema,
        temperature=0.01
    )

    models_to_try = config.MODEL.get(difficulty, config.MODEL["medium"]) # Get models for difficulty, default to medium
    max_retries_per_model = config.MAX_TRIES
    parsed_json = None

    for model_name in models_to_try:
        logger.info(f"Tentando modelo: {model_name} para dificuldade: {difficulty}. Schema: {output_schema.__name__}")
        retries = 0
        success = False

        while retries < max_retries_per_model and not success:
            logger.info(f"Tentativa {retries + 1}/{max_retries_per_model} de chamar o modelo {model_name}. Schema: {output_schema.__name__}")
            logger.debug(f"Prompt para API (primeiros 500 chars): {prompt_content[:500]}...")

            full_response_text = ""
            try:
                response = client.models.generate_content(
                    model=model_name, # Usar o nome do modelo atual
                    contents=cast(List[genai_types.Content], contents), # type: ignore
                    config=generation_config,
                )
                if response.text:
                     full_response_text = response.text
                else:
                    logger.error(f"Resposta da API para {model_name} não contém o texto esperado ou estrutura de candidatos.")
                    retries += 1
                    time.sleep(2 ** retries) # Exponential backoff
                    continue # Try again

            except Exception as e_gc:
                logger.error(f"Falha ao chamar client.generate_content com {model_name} (Tentativa {retries + 1}): {e_gc}", exc_info=True)
                if hasattr(e_gc, 'response') and hasattr(e_gc.response, 'text'): # type: ignore
                    logger.error(f"Detalhes da resposta da API (erro) para {model_name}: {e_gc.response.text}") # type: ignore
                retries += 1
                time.sleep(2 ** retries) # Exponential backoff
                continue # Try again

            logger.info(f"Resposta recebida do modelo {model_name} para {output_schema.__name__} (Tentativa {retries + 1}).")

            if not full_response_text:
                logger.error(f"Resposta do modelo {model_name} está vazia.")
                retries += 1
                time.sleep(2 ** retries) # Exponential backoff
                continue # Try again

            # Limpeza do JSON (comum em respostas de LLMs)
            json_text = full_response_text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:-3].strip()
            elif json_text.startswith("```"):
                json_text = json_text[3:-3].strip()

            logger.debug(f"Texto JSON bruto recebido para {output_schema.__name__} com {model_name}: {json_text[:500]}...")

            try:
                parsed_json = json.loads(json_text)
                # Valida com o schema Pydantic após o parse
                output_schema(**parsed_json)
                logger.info(f"Raciocínio da Etapa: {parsed_json.get('raciocinio', 'N/A')}")
                success = True # JSON parsed and validated successfully
                break # Exit retry loop for this model
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar JSON para {output_schema.__name__} com {model_name} (Tentativa {retries + 1}): {e}. Resposta: {json_text}")
                retries += 1
                time.sleep(2 ** retries) # Exponential backoff
                # Continue loop to retry
            except ValidationError as e:
                logger.error(f"Erro de validação Pydantic para {output_schema.__name__} com {model_name} (Tentativa {retries + 1}): {e}. JSON: {json_text}")
                retries += 1
                time.sleep(2 ** retries) # Exponential backoff
                # Continue loop to retry
            except Exception as e:
                 logger.error(f"Erro inesperado ao processar resposta da API com {model_name} (Tentativa {retries + 1}): {e}", exc_info=True)
                 retries += 1
                 time.sleep(2 ** retries) # Exponential backoff
                 # Continue loop to retry

        if success:
            break # Exit model loop if successful

    if not success:
        logger.error(f"Falha final ao processar resposta da API para {output_schema.__name__} após tentar todos os modelos para dificuldade '{difficulty}'.")
        return None

    return parsed_json

def _make_embedding_call(text: str) -> Optional[List[List[float]]]:
    """Função auxiliar para fazer uma chamada à API de embedding com prevenção de erros."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    embeddings = None
    try:
        logger.info(f"Chamando API de embedding para texto (primeiros 50 chars): {text[:50]}...")
        result = client.models.embed_content(
            model="gemini-embedding-exp-03-07",
            contents=text,
            config=genai_types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")) # Use the input text

        if result and result.embeddings:
            embeddings = [e.values for e in result.embeddings]
            logger.info("Embeddings gerados com sucesso.")
        else:
            logger.error("Resposta da API de embedding não contém embeddings válidos.")

    except Exception as e:
        logger.error(f"Falha ao chamar a API de embedding: {e}", exc_info=True)

    return embeddings
