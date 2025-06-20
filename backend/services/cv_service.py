import os
import cv2
import numpy as np
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CVService:
    def __init__(self):
        """Initialize Computer Vision models"""
        try:
            # Load CLIP model for image understanding
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.clip_model.to(self.device)
        except Exception as e:
            logger.error(f"Error loading CLIP model: {e}")
            self.clip_model = None
            self.clip_processor = None
    
    def preprocess_image(self, image_path: str) -> Optional[np.ndarray]:
        """Preprocess image for analysis"""
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Resize if too large
            height, width = image_rgb.shape[:2]
            if height > 1024 or width > 1024:
                scale = min(1024 / height, 1024 / width)
                new_height = int(height * scale)
                new_width = int(width * scale)
                image_rgb = cv2.resize(image_rgb, (new_width, new_height))
            
            return image_rgb
        except Exception as e:
            logger.error(f"Error preprocessing image {image_path}: {e}")
            return None
    
    def generate_caption(self, image_path: str) -> Optional[str]:
        """Generate caption for image using CLIP"""
        if not self.clip_model or not self.clip_processor:
            return None
        
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert("RGB")
            
            # Prepare text prompts for captioning
            text_prompts = [
                "a photo of",
                "an image showing",
                "a picture of",
                "this is",
                "shows"
            ]
            
            # Process image and text
            inputs = self.clip_processor(
                text=text_prompts,
                images=image,
                return_tensors="pt",
                padding=True
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get embeddings
            with torch.no_grad():
                image_features = self.clip_model.get_image_features(inputs["pixel_values"])
                text_features = self.clip_model.get_text_features(inputs["input_ids"])
            
            # Calculate similarities
            similarities = torch.cosine_similarity(image_features, text_features)
            
            # Get best prompt
            best_idx = similarities.argmax().item()
            best_prompt = text_prompts[best_idx]
            
            # Simple caption generation (in a real implementation, you'd use a proper captioning model)
            return f"{best_prompt} content"
            
        except Exception as e:
            logger.error(f"Error generating caption for {image_path}: {e}")
            return None
    
    def extract_tags(self, image_path: str) -> List[str]:
        """Extract tags from image using CLIP"""
        if not self.clip_model or not self.clip_processor:
            return []
        
        try:
            # Common tags for social media images
            tag_candidates = [
                "person", "people", "face", "portrait", "selfie",
                "food", "meal", "restaurant", "cooking",
                "nature", "landscape", "mountain", "beach", "forest",
                "city", "building", "architecture", "street",
                "animal", "pet", "dog", "cat", "bird",
                "car", "vehicle", "transportation",
                "art", "painting", "drawing", "design",
                "fashion", "clothing", "style",
                "technology", "computer", "phone", "gadget",
                "sport", "fitness", "exercise", "gym",
                "music", "concert", "performance",
                "travel", "vacation", "tourism"
            ]
            
            # Load image
            image = Image.open(image_path).convert("RGB")
            
            # Process image and text
            inputs = self.clip_processor(
                text=tag_candidates,
                images=image,
                return_tensors="pt",
                padding=True
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get embeddings
            with torch.no_grad():
                image_features = self.clip_model.get_image_features(inputs["pixel_values"])
                text_features = self.clip_model.get_text_features(inputs["input_ids"])
            
            # Calculate similarities
            similarities = torch.cosine_similarity(image_features, text_features)
            
            # Get top tags (similarity > 0.3)
            threshold = 0.3
            top_indices = (similarities > threshold).nonzero(as_tuple=True)[0]
            
            tags = []
            for idx in top_indices:
                tags.append(tag_candidates[idx.item()])
            
            return tags[:10]  # Limit to top 10 tags
            
        except Exception as e:
            logger.error(f"Error extracting tags from {image_path}: {e}")
            return []
    
    def calculate_similarity(self, image_path: str, text: str) -> float:
        """Calculate similarity between image and text"""
        if not self.clip_model or not self.clip_processor:
            return 0.0
        
        try:
            # Load image
            image = Image.open(image_path).convert("RGB")
            
            # Process image and text
            inputs = self.clip_processor(
                text=[text],
                images=image,
                return_tensors="pt",
                padding=True
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get embeddings
            with torch.no_grad():
                image_features = self.clip_model.get_image_features(inputs["pixel_values"])
                text_features = self.clip_model.get_text_features(inputs["input_ids"])
            
            # Calculate cosine similarity
            similarity = torch.cosine_similarity(image_features, text_features).item()
            
            return max(0.0, similarity)  # Ensure non-negative
            
        except Exception as e:
            logger.error(f"Error calculating similarity for {image_path}: {e}")
            return 0.0
    
    def process_image(self, image_path: str, associated_text: str = "") -> Dict[str, Any]:
        """Complete image processing pipeline"""
        caption = self.generate_caption(image_path)
        tags = self.extract_tags(image_path)
        similarity_score = self.calculate_similarity(image_path, associated_text) if associated_text else 0.0
        
        return {
            "caption": caption,
            "tags": tags,
            "similarity_score": similarity_score
        }

# Global CV service instance
cv_service = CVService() 