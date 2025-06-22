from ollama import Client
from ollama import ChatResponse
from ollama import _types
from typing import List, Optional, Dict
import logging, time
from typing import Dict, AsyncGenerator
from openai import OpenAI


class OllamaModels:
    def __init__(self, config, default_model: str = None):
        self.config = config
        self.default_model = default_model
        self.active_pulls = {}
        self.client = Client(
            host=f'http://{config.endpoint_url}:{config.endpoint_port}',
        )
        verifyLocalModels = self.list_local_models()
        if verifyLocalModels:
            pass
        
    def generate_response(self, prompt: str, model: Optional[str] = None) -> str:
        """generate a one off response."""
        response = self.client.generate(
            model=model or self.default_model,
            prompt=prompt,
        )
        return response["response"]

    def chat_response(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> ChatResponse:
        """chat session with memory."""
        return self.client.generate(
            model=model or self.default_model,
            messages=messages,
        )

    def pull_new_model_sync(self, model_name: str, client_id: str):
        """model pull that updates progress in client_progress."""
        try:
            self.active_pulls[client_id] = {"model": model_name, "active": True}

            # ollama.pull returns a generator that yields progress updates
            pull_stream = self.client.pull(model_name, stream=True)
            
            for progress_data in pull_stream:
                if not self.active_pulls.get(client_id, {}).get("active", False):
                    break  

                status = getattr(progress_data, 'status', 'downloading')
                completed = getattr(progress_data, 'completed', 0) or 0
                total = getattr(progress_data, 'total', 0) or 0
                digest = getattr(progress_data, 'digest', '')
                
                progress_info = {
                    "status": status,
                    "completed": completed,
                    "total": total,
                    "digest": digest,
                    "model": model_name,
                    "timestamp": time.time()
                }

                if total is not None and total > 0 and completed is not None:
                    progress_info["percentage"] = (completed / total) * 100
                else:
                    progress_info["percentage"] = 0
            
                # see if download is complete
                if status == "success" or (total > 0 and completed >= total):
                    self.active_pulls[client_id]["progress"]["status"] = "success"
                    

                self.active_pulls[client_id]["progress"] = progress_info
                
        except _types.ResponseError as e:
            return {"error": True, "message": f"Invalid model name or internal error: {str(e)}"}
        except Exception as e:
            return {"error": True, "message": f"Unexpected error: {str(e)}"}
        finally:
            # Clean up
            if client_id in self.active_pulls:
                del self.active_pulls[client_id]

    def cancel_pull(self, client_id: str):
        """cancel an active pull operation."""
        if client_id in self.active_pulls:
            self.active_pulls[client_id]["active"] = False
        
    def list_local_models(self) -> List[str]:
        """list all models downloaded locally."""
        try:
            response = self.client.list()
            models = response.get("models", [])
            return [model.model for model in models]
        except ConnectionError as e:
            print(f"[ ERROR ] - Ollama instance not started or issue contacting it. | {self.config.endpoint_url}:{self.config.endpoint_port}")
            logging.info(f"[ ERROR ] - Ollama instance not started or issue contacting it. | {self.config.endpoint_url}:{self.config.endpoint_port}")
            return False
        
    def delete_model(self, model_name: str) -> Dict:
        """delete a local model."""
        return self.client.delete(model_name)


# soon to come
class chatGPT():
    def __init__(self, config):
        self.config = config
        self.client = OpenAI(
            api_key=config.openai_api_key,
        )
        self.model = config.modal_name


    def generate_response(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
        )
        
