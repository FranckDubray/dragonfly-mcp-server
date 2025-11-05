import os
import base64
import mimetypes
import requests
from typing import Any, Dict, Optional, List

# Thin wrapper around google genai client

class GoogleGenAIClient:
    def __init__(self) -> None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY non défini dans l'environnement")
        self.api_key = api_key
        # Lazy import at runtime
        from google import genai  # type: ignore
        self._genai_mod = genai
        try:
            self.client = genai.Client(api_key=api_key)  # type: ignore[attr-defined]
        except Exception:
            self.client = genai.Client()  # type: ignore

    def _upload_video(self, path: str) -> Any:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Fichier introuvable: {path}")
        with open(path, 'rb') as f:
            # Try with mime_type for SDK 1.48 compatibility
            try:
                return self.client.files.upload(file=f, mime_type='video/mp4')
            except TypeError:
                # Fallback without mime_type
                return self.client.files.upload(file=f)

    def start_generate(self, model: str, prompt: str, *,
                       negative_prompt: Optional[str] = None,
                       image_path: Optional[str] = None,
                       last_frame_path: Optional[str] = None,
                       reference_image_paths: Optional[List[str]] = None,
                       aspect_ratio: Optional[str] = None,
                       resolution: Optional[str] = None,
                       duration_seconds: Optional[int] = None,
                       person_generation: Optional[str] = None,
                       seed: Optional[int] = None,
                       number_of_videos: int = 1) -> Dict[str, Any]:
        from google.genai import types  # type: ignore

        cfg_kwargs: Dict[str, Any] = {}
        if negative_prompt:
            cfg_kwargs['negative_prompt'] = negative_prompt
        if aspect_ratio:
            cfg_kwargs['aspect_ratio'] = aspect_ratio
        if resolution:
            cfg_kwargs['resolution'] = resolution
        if duration_seconds:
            cfg_kwargs['duration_seconds'] = duration_seconds
        if person_generation:
            cfg_kwargs['person_generation'] = person_generation
        if seed is not None:
            cfg_kwargs['seed'] = seed
        if number_of_videos:
            cfg_kwargs['number_of_videos'] = number_of_videos

        gen_cfg = types.GenerateVideosConfig(**cfg_kwargs) if cfg_kwargs else None

        # For now, skip image support (version 1.48 compatibility issues)
        if image_path or last_frame_path or reference_image_paths:
            raise NotImplementedError("Image→vidéo temporairement désactivé pour compatibilité SDK 1.48")

        kwargs: Dict[str, Any] = dict(model=model, prompt=prompt)
        if gen_cfg is not None:
            kwargs['config'] = gen_cfg

        op = self.client.models.generate_videos(**kwargs)
        op_name = getattr(op, 'name', None) or getattr(getattr(op, 'operation', None), 'name', None)
        return {"operation_name": op_name or "", "raw": op}

    def extend_video(self, model: str, video_path: str, prompt: Optional[str], resolution: str) -> Dict[str, Any]:
        from google.genai import types  # type: ignore
        video_file = self._upload_video(video_path)
        cfg = types.GenerateVideosConfig(number_of_videos=1, resolution=resolution)
        op = self.client.models.generate_videos(model=model, video=video_file, prompt=prompt, config=cfg)
        op_name = getattr(op, 'name', None) or getattr(getattr(op, 'operation', None), 'name', None)
        return {"operation_name": op_name or "", "raw": op}

    def get_operation(self, operation_name: str) -> Any:
        from google.genai import types  # type: ignore
        op = types.GenerateVideosOperation(name=operation_name)
        return self.client.operations.get(op)

    def download_operation_result(self, operation_name: str, dest_path: str, overwrite: bool = False) -> Dict[str, Any]:
        op = self.get_operation(operation_name)
        if not getattr(op, 'done', False):
            raise RuntimeError("Opération non terminée: impossible de télécharger")
        resp = getattr(op, 'response', None)
        if not resp or not getattr(resp, 'generated_videos', None):
            raise RuntimeError("Réponse invalide: aucune vidéo")
        vid0 = resp.generated_videos[0]
        
        # Get video URI and download via HTTP
        video_uri = getattr(vid0.video, 'uri', None)
        if not video_uri:
            raise RuntimeError("Aucune URI de vidéo trouvée")
        
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        if os.path.exists(dest_path) and not overwrite:
            raise FileExistsError(f"Fichier existe déjà: {dest_path}")
        
        # Download via requests
        headers = {}
        if self.api_key:
            headers['x-goog-api-key'] = self.api_key
        
        response = requests.get(video_uri, headers=headers, stream=True)
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        size = os.path.getsize(dest_path)
        return {"saved_path": dest_path, "size_bytes": size}
