import asyncio
import random
from openai import OpenAI, AsyncOpenAI
from typing import List, Dict, Optional, Union, Any

class LLM:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model_name: str,
        generation_params: dict = None
    ):
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        self.model_name = model_name
        self.generation_params = generation_params or {}
    
    def generate_embeddings(
        self, input_texts: List[str],
    ):
        response = self.client.embeddings.create(
            model=self.model_name,
            input=input_texts
        )
        return [embedding_data.embedding for embedding_data in response.data]


    def generate(
        self, 
        messages: List[Dict[str, str]], 
        **params
    ) -> Union[str, Any]:
        """Generate completion from messages."""
        if self.client is not None and hasattr(self.client, 'chat') and hasattr(self.client.chat, 'completions'):
            try:
                response = self.client.chat.completions.create(
                    model = self.model_name,
                    messages = messages,
                    **{**self.generation_params, **params}
                )
                
                if hasattr(response, 'choices'):
                    return response.choices[0].message.content
                else:
                    return response
                    
            except Exception as e:
                if "Error code: 400" in str(e):
                    # Context too long
                    print(f"Generation exceeded context window with {len(messages)} messages. Removing the first assistant message.")
                    print(messages)
                    first_assistant_message_idx = None
                    for i, message in enumerate(messages):
                        if message["role"] == "assistant":
                            first_assistant_message_idx = i
                            break
                    if first_assistant_message_idx is not None:
                        messages.pop(first_assistant_message_idx)
                        return self.generate(messages, **params)
                # print(messages)
                raise Exception(f"API call failed: {str(e)}")
                
        else:
            raise NotImplementedError


class AsyncLLM:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model_name: Union[str, List[str]],
        generation_params: dict = None
    ):
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key
        )
        self.generation_params = generation_params or {}
        self.model_name = model_name
    
    async def generate_embeddings(
        self, input_texts: List[str],
    ):
        response = await self.client.embeddings.create(
            model=self.model_name,
            input=input_texts
        )
        return [embedding_data.embedding for embedding_data in response.data]

    async def generate(
        self, 
        messages: List[Dict[str, str]],
        max_retries_per_model: int = 5,
        include_stop_string=True,
        **params
    ) -> Union[str, Any]:
        if not (self.client and hasattr(self.client, 'chat') and hasattr(self.client.chat, 'completions')):
            raise NotImplementedError("Invalid async client provided.")

        last_exception = None
        
        
        for attempt in range(max_retries_per_model):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    **{**self.generation_params, **params}
                )
                if hasattr(response, 'choices') and response.choices:
                    output =  response.choices[0].message.content
                else:
                    output =  response
                try:
                    stop_reason = response.choices[0].provider_specific_fields['stop_reason']
                except:
                    stop_reason = None
                if include_stop_string and stop_reason is not None:
                    output += stop_reason
                    
                return output
            
            except Exception as e:
                last_exception = e
                error_str = str(e)
                print("Error in AsyncLLM.generate: ", e)
                
                if "Error code: 400" in error_str:
                    if 'Invalid max_tokens value' in error_str:
                        self.generation_params['max_tokens'] = 8192
                        break
                    print("Context length exceeded. Removing the first assistant message to shorten the prompt.")
                    
                    first_assistant_message_idx = -1
                    for i, message in enumerate(messages):
                        # drop the first user message
                        if i == 0 :
                            continue
                        if message["role"] == "user":
                            first_assistant_message_idx = i
                            break
                    
                    if first_assistant_message_idx != -1:
                        messages.pop(first_assistant_message_idx)
                        continue 
                    else:
                        print("No assistant message available to remove; skipping further retries for this model.")
                        break 
                
                # Exponential backoff with jitter for rate-limit (429)
                # and transient server errors (500, 502, 503, 529).
                base_delay = min(2 ** attempt, 32)  # 1, 2, 4, 8, 16, 32
                jitter = random.uniform(0, base_delay * 0.5)
                delay = base_delay + jitter
                print(f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries_per_model})")
                await asyncio.sleep(delay)

        
        raise Exception(f"All model attempts failed after retries. Last error: {last_exception}")
