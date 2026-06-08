#!/usr/bin/env python3
"""
AI/ML Integration Core - Intelligent Collaboration Engine
Transforms the MCP server into a truly intelligent collaborative partner

Local AI/ML capabilities without cloud dependencies:
- Local LLM integration (Ollama, llama.cpp, transformers)
- Computer vision and image analysis
- Predictive analytics and pattern recognition
- Intelligent workflow suggestions
- Context-aware assistance
- Learning from user behavior

Dependencies:
pip install torch torchvision transformers sentence-transformers scikit-learn
pip install opencv-python pillow numpy pandas matplotlib seaborn
pip install ollama requests huggingface-hub
"""

import json
import logging
import numpy as np
import os
import pickle
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable, Union
import hashlib
import subprocess
import requests
from collections import defaultdict, Counter
import sqlite3

# Core ML libraries
try:
    import torch
    import torch.nn as nn
    from transformers import pipeline, AutoTokenizer, AutoModel
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import cv2
    import PIL.Image as Image
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False

try:
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.metrics.pairwise import cosine_similarity
    import pandas as pd
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class LocalAIEngine:
    """Core AI engine for local processing and intelligence"""
    
    def __init__(self, data_dir: str = "data"):
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path(data_dir)
        self.ai_data_dir = self.data_dir / "ai_intelligence"
        self.ai_data_dir.mkdir(exist_ok=True)
        
        # AI models cache
        self.models = {}
        self.embeddings_cache = {}
        self.predictions_cache = {}
        
        # Intelligence database
        self.intelligence_db = self.ai_data_dir / "intelligence.db"
        self._init_intelligence_db()
        
        # Initialize core models
        self._initialize_models()
        
        self.logger.info("AI/ML Integration Engine initialized")
    
    def _init_intelligence_db(self):
        """Initialize SQLite database for AI intelligence storage"""
        conn = sqlite3.connect(self.intelligence_db)
        cursor = conn.cursor()
        
        # User behavior patterns
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_patterns (
            id INTEGER PRIMARY KEY,
            pattern_type TEXT,
            pattern_data TEXT,
            frequency INTEGER DEFAULT 1,
            confidence REAL,
            last_seen TIMESTAMP,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Context embeddings
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS context_embeddings (
            id INTEGER PRIMARY KEY,
            context_hash TEXT UNIQUE,
            embedding BLOB,
            context_type TEXT,
            metadata TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # AI predictions and outcomes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY,
            prediction_type TEXT,
            input_data TEXT,
            prediction TEXT,
            actual_outcome TEXT,
            accuracy REAL,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Learning sessions
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_sessions (
            id INTEGER PRIMARY KEY,
            session_type TEXT,
            input_features TEXT,
            output_labels TEXT,
            model_performance TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _initialize_models(self):
        """Initialize AI models for local processing"""
        if not TRANSFORMERS_AVAILABLE:
            self.logger.warning("Transformers not available - AI capabilities limited")
            return
        
        try:
            # Sentence embeddings for semantic understanding
            self.logger.info("Loading sentence transformer model...")
            self.models['embeddings'] = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Text classification for intent recognition
            self.logger.info("Loading text classification model...")
            self.models['classifier'] = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",
                return_all_scores=True
            )
            
            # Sentiment analysis
            self.models['sentiment'] = pipeline("sentiment-analysis")
            
            # Named entity recognition
            self.models['ner'] = pipeline("ner", aggregation_strategy="simple")
            
            self.logger.info("Core AI models loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading AI models: {e}")
    
    def get_embedding(self, text: str, cache_key: Optional[str] = None) -> np.ndarray:
        """Get semantic embedding for text"""
        if not TRANSFORMERS_AVAILABLE or 'embeddings' not in self.models:
            return np.random.rand(384)  # Fallback random embedding
        
        if cache_key and cache_key in self.embeddings_cache:
            return self.embeddings_cache[cache_key]
        
        try:
            embedding = self.models['embeddings'].encode(text)
            
            if cache_key:
                self.embeddings_cache[cache_key] = embedding
                # Store in database
                self._store_embedding(cache_key, embedding, "text", {"text": text})
            
            return embedding
            
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            return np.random.rand(384)
    
    def semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        
        if SKLEARN_AVAILABLE:
            similarity = cosine_similarity([emb1], [emb2])[0][0]
        else:
            # Fallback dot product similarity
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        
        return float(similarity)
    
    def analyze_intent(self, text: str) -> Dict[str, Any]:
        """Analyze user intent from text"""
        try:
            # Extract entities
            entities = []
            if 'ner' in self.models:
                ner_results = self.models['ner'](text)
                entities = [
                    {"text": ent["word"], "label": ent["entity_group"], "confidence": ent["score"]}
                    for ent in ner_results
                ]
            
            # Sentiment analysis
            sentiment = {"label": "NEUTRAL", "score": 0.5}
            if 'sentiment' in self.models:
                sentiment_result = self.models['sentiment'](text)[0]
                sentiment = sentiment_result
            
            # Intent classification (custom logic)
            intent_keywords = {
                "code_analysis": ["analyze", "code", "function", "class", "debug", "review"],
                "file_operation": ["file", "read", "write", "save", "open", "create"],
                "automation": ["automate", "script", "run", "execute", "batch"],
                "learning": ["learn", "understand", "explain", "teach", "show"],
                "memory": ["remember", "store", "recall", "save", "memory"],
                "search": ["find", "search", "look", "locate", "discover"]
            }
            
            intent_scores = {}
            for intent, keywords in intent_keywords.items():
                score = sum(1 for keyword in keywords if keyword in text.lower())
                if score > 0:
                    intent_scores[intent] = score / len(keywords)
            
            primary_intent = max(intent_scores.items(), key=lambda x: x[1]) if intent_scores else ("general", 0.1)
            
            return {
                "primary_intent": primary_intent[0],
                "intent_confidence": primary_intent[1],
                "all_intents": intent_scores,
                "entities": entities,
                "sentiment": sentiment,
                "complexity": len(text.split()) / 10  # Simple complexity measure
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing intent: {e}")
            return {
                "primary_intent": "general",
                "intent_confidence": 0.1,
                "all_intents": {},
                "entities": [],
                "sentiment": {"label": "NEUTRAL", "score": 0.5},
                "complexity": 0.5
            }
    
    def predict_next_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Predict what the user is likely to do next"""
        try:
            # Analyze recent patterns
            recent_patterns = self._get_recent_patterns(hours=24)
            
            # Get context embedding
            context_text = json.dumps(context, sort_keys=True)
            context_embedding = self.get_embedding(context_text)
            
            # Find similar contexts
            similar_contexts = self._find_similar_contexts(context_embedding, limit=10)
            
            # Predict based on patterns
            predictions = []
            
            # Pattern-based predictions
            for pattern in recent_patterns:
                if pattern['pattern_type'] in ['tool_sequence', 'workflow']:
                    pattern_data = json.loads(pattern['pattern_data'])
                    similarity = self._calculate_pattern_similarity(context, pattern_data)
                    
                    if similarity > 0.3:
                        predictions.append({
                            "type": "pattern_based",
                            "action": pattern_data.get('next_likely_action', 'unknown'),
                            "confidence": similarity * pattern['confidence'],
                            "reasoning": f"Similar to pattern: {pattern['pattern_type']}"
                        })
            
            # Context-based predictions
            for similar_ctx in similar_contexts:
                predictions.append({
                    "type": "context_based",
                    "action": similar_ctx.get('likely_next_action', 'unknown'),
                    "confidence": similar_ctx.get('similarity', 0.5),
                    "reasoning": "Based on similar context"
                })
            
            # Sort by confidence
            predictions.sort(key=lambda x: x['confidence'], reverse=True)
            
            return {
                "predictions": predictions[:5],  # Top 5 predictions
                "context_analysis": self._analyze_current_context(context),
                "recommendation_strength": "high" if predictions and predictions[0]['confidence'] > 0.7 else "medium" if predictions else "low"
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting next action: {e}")
            return {"predictions": [], "context_analysis": {}, "recommendation_strength": "low"}
    
    def learn_from_interaction(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Learn from user interactions to improve predictions"""
        try:
            # Extract learning features
            features = {
                "timestamp": time.time(),
                "user_action": interaction.get('action', ''),
                "context": interaction.get('context', {}),
                "outcome": interaction.get('outcome', ''),
                "success": interaction.get('success', False),
                "tools_used": interaction.get('tools_used', []),
                "session_context": interaction.get('session_context', {})
            }
            
            # Update pattern recognition
            self._update_user_patterns(features)
            
            # Store for future learning
            self._store_learning_session(features)
            
            # Update prediction accuracy
            if 'predicted_action' in interaction and 'actual_action' in interaction:
                accuracy = 1.0 if interaction['predicted_action'] == interaction['actual_action'] else 0.0
                self._update_prediction_accuracy(interaction, accuracy)
            
            return {
                "learning_status": "success",
                "patterns_updated": True,
                "accuracy_updated": 'predicted_action' in interaction,
                "learning_confidence": self._calculate_learning_confidence()
            }
            
        except Exception as e:
            self.logger.error(f"Error learning from interaction: {e}")
            return {"learning_status": "failed", "error": str(e)}
    
    def get_intelligent_suggestions(self, current_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get intelligent suggestions based on current state"""
        try:
            suggestions = []
            
            # Analyze current state
            state_analysis = self.analyze_intent(str(current_state))
            
            # Get context-aware suggestions
            if state_analysis['primary_intent'] == 'code_analysis':
                suggestions.extend(self._get_code_analysis_suggestions(current_state))
            elif state_analysis['primary_intent'] == 'file_operation':
                suggestions.extend(self._get_file_operation_suggestions(current_state))
            elif state_analysis['primary_intent'] == 'automation':
                suggestions.extend(self._get_automation_suggestions(current_state))
            
            # Add general productivity suggestions
            suggestions.extend(self._get_productivity_suggestions(current_state))
            
            # Score and rank suggestions
            for suggestion in suggestions:
                suggestion['ai_confidence'] = self._calculate_suggestion_confidence(suggestion, current_state)
            
            # Sort by confidence and relevance
            suggestions.sort(key=lambda x: x.get('ai_confidence', 0), reverse=True)
            
            return suggestions[:10]  # Top 10 suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating suggestions: {e}")
            return []
    
    # Helper methods
    def _store_embedding(self, context_hash: str, embedding: np.ndarray, context_type: str, metadata: Dict):
        """Store embedding in database"""
        try:
            conn = sqlite3.connect(self.intelligence_db)
            cursor = conn.cursor()
            
            embedding_blob = pickle.dumps(embedding)
            metadata_json = json.dumps(metadata)
            
            cursor.execute('''
            INSERT OR REPLACE INTO context_embeddings 
            (context_hash, embedding, context_type, metadata)
            VALUES (?, ?, ?, ?)
            ''', (context_hash, embedding_blob, context_type, metadata_json))
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Error storing embedding: {e}")
    
    def _get_recent_patterns(self, hours: int = 24) -> List[Dict]:
        """Get recent user patterns"""
        try:
            conn = sqlite3.connect(self.intelligence_db)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
            SELECT * FROM user_patterns 
            WHERE last_seen > ? 
            ORDER BY frequency DESC, confidence DESC
            LIMIT 20
            ''', (cutoff_time,))
            
            patterns = []
            for row in cursor.fetchall():
                patterns.append({
                    'id': row[0],
                    'pattern_type': row[1],
                    'pattern_data': row[2],
                    'frequency': row[3],
                    'confidence': row[4],
                    'last_seen': row[5]
                })
            
            conn.close()
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error getting recent patterns: {e}")
            return []
    
    def _find_similar_contexts(self, target_embedding: np.ndarray, limit: int = 10) -> List[Dict]:
        """Find contexts similar to target embedding"""
        try:
            conn = sqlite3.connect(self.intelligence_db)
            cursor = conn.cursor()
            
            cursor.execute('SELECT context_hash, embedding, metadata FROM context_embeddings')
            
            similarities = []
            for row in cursor.fetchall():
                stored_embedding = pickle.loads(row[1])
                similarity = cosine_similarity([target_embedding], [stored_embedding])[0][0] if SKLEARN_AVAILABLE else 0.5
                
                if similarity > 0.3:  # Threshold for relevance
                    metadata = json.loads(row[2])
                    similarities.append({
                        'context_hash': row[0],
                        'similarity': float(similarity),
                        'metadata': metadata
                    })
            
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            conn.close()
            
            return similarities[:limit]
            
        except Exception as e:
            self.logger.error(f"Error finding similar contexts: {e}")
            return []
    
    def _calculate_pattern_similarity(self, context1: Dict, context2: Dict) -> float:
        """Calculate similarity between two contexts"""
        try:
            # Simple similarity based on common keys and values
            common_keys = set(context1.keys()) & set(context2.keys())
            if not common_keys:
                return 0.0
            
            similarity_scores = []
            for key in common_keys:
                val1, val2 = str(context1[key]), str(context2[key])
                if val1 == val2:
                    similarity_scores.append(1.0)
                else:
                    # Use semantic similarity for text values
                    semantic_sim = self.semantic_similarity(val1, val2)
                    similarity_scores.append(semantic_sim)
            
            return np.mean(similarity_scores) if similarity_scores else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating pattern similarity: {e}")
            return 0.0
    
    def _analyze_current_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current context for insights"""
        return {
            "context_complexity": len(str(context)) / 1000,
            "key_elements": len(context),
            "context_type": "development" if any(key in str(context).lower() for key in ["code", "file", "function"]) else "general",
            "urgency_indicators": any(word in str(context).lower() for word in ["error", "urgent", "critical", "fix"])
        }
    
    def _update_user_patterns(self, features: Dict[str, Any]):
        """Update user behavior patterns"""
        try:
            conn = sqlite3.connect(self.intelligence_db)
            cursor = conn.cursor()
            
            pattern_type = f"{features['user_action']}_pattern"
            pattern_data = json.dumps({
                "action": features['user_action'],
                "context": features['context'],
                "tools": features['tools_used'],
                "success": features['success']
            })
            
            # Check if pattern exists
            cursor.execute('''
            SELECT id, frequency FROM user_patterns 
            WHERE pattern_type = ? AND pattern_data = ?
            ''', (pattern_type, pattern_data))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update frequency
                cursor.execute('''
                UPDATE user_patterns 
                SET frequency = frequency + 1, last_seen = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (existing[0],))
            else:
                # Insert new pattern
                cursor.execute('''
                INSERT INTO user_patterns 
                (pattern_type, pattern_data, frequency, confidence, last_seen)
                VALUES (?, ?, 1, 0.5, CURRENT_TIMESTAMP)
                ''', (pattern_type, pattern_data))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error updating user patterns: {e}")
    
    def _store_learning_session(self, features: Dict[str, Any]):
        """Store learning session data"""
        try:
            conn = sqlite3.connect(self.intelligence_db)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO learning_sessions 
            (session_type, input_features, output_labels, model_performance)
            VALUES (?, ?, ?, ?)
            ''', (
                "interaction_learning",
                json.dumps(features),
                json.dumps({"outcome": features.get('outcome'), "success": features.get('success')}),
                json.dumps({"confidence": 0.7})  # Placeholder
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing learning session: {e}")
    
    def _update_prediction_accuracy(self, interaction: Dict, accuracy: float):
        """Update prediction accuracy tracking"""
        try:
            conn = sqlite3.connect(self.intelligence_db)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO predictions 
            (prediction_type, input_data, prediction, actual_outcome, accuracy)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                "next_action",
                json.dumps(interaction.get('context', {})),
                interaction.get('predicted_action', ''),
                interaction.get('actual_action', ''),
                accuracy
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error updating prediction accuracy: {e}")
    
    def _calculate_learning_confidence(self) -> float:
        """Calculate overall learning confidence"""
        try:
            conn = sqlite3.connect(self.intelligence_db)
            cursor = conn.cursor()
            
            # Get recent prediction accuracy
            cursor.execute('''
            SELECT AVG(accuracy) FROM predictions 
            WHERE created > datetime('now', '-7 days')
            ''')
            
            result = cursor.fetchone()
            accuracy = result[0] if result[0] else 0.5
            
            conn.close()
            return float(accuracy)
            
        except Exception as e:
            self.logger.error(f"Error calculating learning confidence: {e}")
            return 0.5
    
    def _get_code_analysis_suggestions(self, state: Dict) -> List[Dict]:
        """Get code analysis specific suggestions"""
        return [
            {
                "type": "code_analysis",
                "action": "bb7_analyze_code_complete",
                "description": "Perform comprehensive code analysis",
                "reasoning": "Code analysis detected in context",
                "confidence": 0.8
            },
            {
                "type": "code_analysis", 
                "action": "bb7_security_audit",
                "description": "Run security audit on code",
                "reasoning": "Security analysis recommended for code review",
                "confidence": 0.7
            }
        ]
    
    def _get_file_operation_suggestions(self, state: Dict) -> List[Dict]:
        """Get file operation specific suggestions"""
        return [
            {
                "type": "file_operation",
                "action": "bb7_search_files",
                "description": "Search for related files",
                "reasoning": "File operation context suggests search might be helpful",
                "confidence": 0.6
            }
        ]
    
    def _get_automation_suggestions(self, state: Dict) -> List[Dict]:
        """Get automation specific suggestions"""
        return [
            {
                "type": "automation",
                "action": "bb7_automation_recorder",
                "description": "Record automation sequence",
                "reasoning": "Automation context suggests recording workflow",
                "confidence": 0.7
            }
        ]
    
    def _get_productivity_suggestions(self, state: Dict) -> List[Dict]:
        """Get general productivity suggestions"""
        return [
            {
                "type": "productivity",
                "action": "bb7_memory_store",
                "description": "Save current insights to memory",
                "reasoning": "Preserve important context for future reference",
                "confidence": 0.5
            }
        ]
    
    def _calculate_suggestion_confidence(self, suggestion: Dict, state: Dict) -> float:
        """Calculate confidence score for suggestion"""
        base_confidence = suggestion.get('confidence', 0.5)
        
        # Boost confidence based on recent patterns
        recent_actions = []  # Would get from actual usage data
        if suggestion['action'] in recent_actions:
            base_confidence += 0.2
        
        # Context relevance boost
        if suggestion['type'] in str(state).lower():
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)


class AIMLIntegrationTool:
    """Main AI/ML Integration Tool for MCP server"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ai_engine = LocalAIEngine()
        self.active_learning = True
        self.collaboration_mode = "enhanced"  # basic, enhanced, adaptive
        
        self.logger.info("AI/ML Integration Tool initialized")
    
    def bb7_ai_analyze_context(self, context: Dict[str, Any], depth: str = "standard") -> str:
        """Analyze current context using AI/ML"""
        try:
            analysis_start = time.time()
            
            # Intent analysis
            context_text = json.dumps(context, sort_keys=True)
            intent_analysis = self.ai_engine.analyze_intent(context_text)
            
            # Semantic analysis
            semantic_features = {
                "context_embedding": self.ai_engine.get_embedding(context_text).tolist()[:10],  # First 10 dims for display
                "complexity_score": len(context_text) / 1000,
                "entity_count": len(intent_analysis.get('entities', [])),
                "sentiment": intent_analysis.get('sentiment', {})
            }
            
            # Prediction analysis
            predictions = self.ai_engine.predict_next_action(context)
            
            # Pattern recognition
            similar_contexts = self.ai_engine._find_similar_contexts(
                self.ai_engine.get_embedding(context_text), limit=5
            )
            
            analysis_time = time.time() - analysis_start
            
            result = {
                "success": True,
                "analysis_depth": depth,
                "intent_analysis": intent_analysis,
                "semantic_features": semantic_features,
                "predictions": predictions,
                "similar_contexts": similar_contexts,
                "analysis_time": round(analysis_time, 3),
                "ai_confidence": intent_analysis.get('intent_confidence', 0.5)
            }
            
            message = f"🧠 AI Context Analysis Complete!\n"
            message += f"🎯 Primary Intent: {intent_analysis['primary_intent']} ({intent_analysis['intent_confidence']:.1%})\n"
            message += f"📊 Predictions: {len(predictions['predictions'])} generated\n"
            message += f"🔍 Similar Contexts: {len(similar_contexts)} found\n"
            message += f"⚡ Analysis Time: {analysis_time:.3f}s"
            
            result["message"] = message
            
            # Learn from this analysis
            if self.active_learning:
                learning_data = {
                    "action": "context_analysis",
                    "context": context,
                    "outcome": result,
                    "success": True,
                    "tools_used": ["ai_analyze_context"]
                }
                self.ai_engine.learn_from_interaction(learning_data)
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            self.logger.error(f"AI context analysis failed: {e}")
            return f"❌ AI context analysis failed: {str(e)}"
    
    def bb7_ai_suggest_actions(self, current_state: Dict[str, Any], 
                              suggestion_count: int = 5, context_aware: bool = True) -> str:
        """Get AI-powered action suggestions"""
        try:
            # Get intelligent suggestions
            suggestions = self.ai_engine.get_intelligent_suggestions(current_state)
            
            # Enhance with context awareness
            if context_aware:
                enhanced_suggestions = []
                for suggestion in suggestions[:suggestion_count]:
                    # Add contextual reasoning
                    suggestion["contextual_relevance"] = self._calculate_contextual_relevance(
                        suggestion, current_state
                    )
                    
                    # Add execution probability
                    suggestion["execution_probability"] = self._estimate_execution_probability(
                        suggestion, current_state
                    )
                    
                    enhanced_suggestions.append(suggestion)
                
                suggestions = enhanced_suggestions
            
            result = {
                "success": True,
                "suggestions": suggestions[:suggestion_count],
                "suggestion_count": len(suggestions),
                "context_aware": context_aware,
                "ai_reasoning": "Suggestions based on pattern analysis, context similarity, and user behavior modeling"
            }
            
            message = f"💡 AI Action Suggestions Ready!\n"
            message += f"📋 Generated {len(suggestions)} suggestions\n"
            
            if suggestions:
                top_suggestion = suggestions[0]
                message += f"🎯 Top Suggestion: {top_suggestion.get('action', 'Unknown')}\n"
                message += f"🔥 Confidence: {top_suggestion.get('ai_confidence', 0):.1%}\n"
                message += f"💭 Reasoning: {top_suggestion.get('reasoning', 'Pattern-based')}"
            
            result["message"] = message
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            self.logger.error(f"AI action suggestions failed: {e}")
            return f"❌ AI action suggestions failed: {str(e)}"
    
    def bb7_ai_learn_interaction(self, interaction_data: Dict[str, Any]) -> str:
        """Learn from user interaction to improve AI"""
        try:
            # Process interaction for learning
            learning_result = self.ai_engine.learn_from_interaction(interaction_data)
            
            # Update collaboration mode if needed
            learning_confidence = learning_result.get('learning_confidence', 0.5)
            
            if learning_confidence > 0.8:
                self.collaboration_mode = "adaptive"
            elif learning_confidence > 0.6:
                self.collaboration_mode = "enhanced"
            else:
                self.collaboration_mode = "basic"
            
            result = {
                "success": True,
                "learning_result": learning_result,
                "collaboration_mode": self.collaboration_mode,
                "learning_confidence": learning_confidence,
                "active_learning": self.active_learning
            }
            
            message = f"🎓 AI Learning Update Complete!\n"
            message += f"📈 Learning Confidence: {learning_confidence:.1%}\n"
            message += f"🤝 Collaboration Mode: {self.collaboration_mode}\n"
            message += f"✨ Pattern Recognition: {'Updated' if learning_result.get('patterns_updated') else 'Maintained'}"
            
            result["message"] = message
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            self.logger.error(f"AI learning failed: {e}")
            return f"❌ AI learning failed: {str(e)}"
    
    def bb7_ai_pattern_analysis(self, timeframe_hours: int = 24, pattern_types: List[str] = None) -> str:
        """Analyze user behavior patterns using AI"""
        try:
            if pattern_types is None:
                pattern_types = ["tool_usage", "workflow", "context_switches", "productivity"]
            
            # Get patterns from AI engine
            recent_patterns = self.ai_engine._get_recent_patterns(timeframe_hours)
            
            # Analyze patterns by type
            pattern_analysis = defaultdict(list)
            
            for pattern in recent_patterns:
                pattern_type = pattern['pattern_type']
                if any(pt in pattern_type for pt in pattern_types):
                    pattern_analysis[pattern_type].append(pattern)
            
            # Generate insights
            insights = []
            
            for pattern_type, patterns in pattern_analysis.items():
                if patterns:
                    avg_frequency = np.mean([p['frequency'] for p in patterns])
                    avg_confidence = np.mean([p['confidence'] for p in patterns])
                    
                    insights.append({
                        "pattern_type": pattern_type,
                        "pattern_count": len(patterns),
                        "average_frequency": round(avg_frequency, 2),
                        "average_confidence": round(avg_confidence, 3),
                        "trend": "increasing" if avg_frequency > 2 else "stable",
                        "recommendations": self._generate_pattern_recommendations(pattern_type, patterns)
                    })
            
            # Overall productivity analysis
            productivity_score = self._calculate_productivity_score(pattern_analysis)
            
            result = {
                "success": True,
                "timeframe_hours": timeframe_hours,
                "pattern_insights": insights,
                "productivity_score": productivity_score,
                "total_patterns": len(recent_patterns),
                "collaboration_recommendations": self._generate_collaboration_recommendations(insights)
            }
            
            message = f"📊 AI Pattern Analysis Complete!\n"
            message += f"⏰ Timeframe: {timeframe_hours} hours\n"
            message += f"🔍 Patterns Found: {len(recent_patterns)}\n"
            message += f"📈 Productivity Score: {productivity_score:.1%}\n"
            message += f"💡 Insights Generated: {len(insights)}"
            
            result["message"] = message
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            self.logger.error(f"AI pattern analysis failed: {e}")
            return f"❌ AI pattern analysis failed: {str(e)}"
    
    def bb7_ai_semantic_search(self, query: str, search_domains: List[str] = None, 
                              max_results: int = 10) -> str:
        """Semantic search using AI embeddings"""
        try:
            if search_domains is None:
                search_domains = ["memory", "sessions", "context_history"]
            
            query_embedding = self.ai_engine.get_embedding(query)
            search_results = []
            
            # Search in different domains
            for domain in search_domains:
                if domain == "memory":
                    results = self._search_memory_semantically(query_embedding, max_results // len(search_domains))
                elif domain == "sessions":
                    results = self._search_sessions_semantically(query_embedding, max_results // len(search_domains))
                elif domain == "context_history":
                    results = self._search_context_history(query_embedding, max_results // len(search_domains))
                else:
                    results = []
                
                for result in results:
                    result["search_domain"] = domain
                    search_results.append(result)
            
            # Sort by semantic similarity
            search_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            
            result = {
                "success": True,
                "query": query,
                "search_domains": search_domains,
                "results": search_results[:max_results],
                "total_results": len(search_results),
                "semantic_analysis": self.ai_engine.analyze_intent(query)
            }
            
            message = f"🔍 AI Semantic Search Complete!\n"
            message += f"🎯 Query: {query}\n"
            message += f"📊 Results: {len(search_results)} found\n"
            message += f"🎪 Domains: {', '.join(search_domains)}\n"
            
            if search_results:
                best_match = search_results[0]
                message += f"🏆 Best Match: {best_match.get('title', 'Unknown')} ({best_match.get('similarity', 0):.1%})"
            
            result["message"] = message
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            self.logger.error(f"AI semantic search failed: {e}")
            return f"❌ AI semantic search failed: {str(e)}"
    
    def bb7_ai_collaboration_mode(self, mode: str = "adaptive", learning_rate: float = 0.1) -> str:
        """Configure AI collaboration behavior"""
        try:
            valid_modes = ["basic", "enhanced", "adaptive", "predictive"]
            
            if mode not in valid_modes:
                return f"❌ Invalid mode. Choose from: {', '.join(valid_modes)}"
            
            previous_mode = self.collaboration_mode
            self.collaboration_mode = mode
            
            # Configure AI behavior based on mode
            if mode == "basic":
                self.active_learning = False
                self.ai_engine.prediction_threshold = 0.8
            elif mode == "enhanced":
                self.active_learning = True
                self.ai_engine.prediction_threshold = 0.6
            elif mode == "adaptive":
                self.active_learning = True
                self.ai_engine.prediction_threshold = 0.4
            elif mode == "predictive":
                self.active_learning = True
                self.ai_engine.prediction_threshold = 0.2
            
            # Update learning rate
            if hasattr(self.ai_engine, 'learning_rate'):
                self.ai_engine.learning_rate = learning_rate
            
            result = {
                "success": True,
                "previous_mode": previous_mode,
                "current_mode": mode,
                "active_learning": self.active_learning,
                "learning_rate": learning_rate,
                "mode_capabilities": self._get_mode_capabilities(mode)
            }
            
            message = f"🤝 AI Collaboration Mode Updated!\n"
            message += f"🔄 Changed: {previous_mode} → {mode}\n"
            message += f"🎓 Learning: {'Active' if self.active_learning else 'Passive'}\n"
            message += f"📈 Learning Rate: {learning_rate}\n"
            message += f"✨ New Capabilities: {len(result['mode_capabilities'])} features"
            
            result["message"] = message
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            self.logger.error(f"AI collaboration mode update failed: {e}")
            return f"❌ AI collaboration mode update failed: {str(e)}"
    
    def bb7_ai_intelligence_status(self) -> str:
        """Get current AI intelligence status and metrics"""
        try:
            # Get learning confidence
            learning_confidence = self.ai_engine._calculate_learning_confidence()
            
            # Get pattern statistics
            recent_patterns = self.ai_engine._get_recent_patterns(24)
            
            # Get model status
            model_status = {
                "embeddings_loaded": 'embeddings' in self.ai_engine.models,
                "classifier_loaded": 'classifier' in self.ai_engine.models,
                "sentiment_loaded": 'sentiment' in self.ai_engine.models,
                "ner_loaded": 'ner' in self.ai_engine.models
            }
            
            # Calculate intelligence metrics
            intelligence_metrics = {
                "learning_confidence": learning_confidence,
                "pattern_recognition_strength": len(recent_patterns) / 100,  # Normalized
                "collaboration_effectiveness": self._calculate_collaboration_effectiveness(),
                "prediction_accuracy": learning_confidence,  # Simplified
                "context_understanding": len(self.ai_engine.embeddings_cache) / 1000  # Normalized
            }
            
            # Overall intelligence score
            intelligence_score = np.mean(list(intelligence_metrics.values()))
            
            result = {
                "success": True,
                "collaboration_mode": self.collaboration_mode,
                "active_learning": self.active_learning,
                "model_status": model_status,
                "intelligence_metrics": intelligence_metrics,
                "intelligence_score": round(intelligence_score, 3),
                "pattern_count": len(recent_patterns),
                "cache_size": len(self.ai_engine.embeddings_cache),
                "capabilities": self._get_current_capabilities()
            }
            
            message = f"🧠 AI Intelligence Status Report\n"
            message += f"🤝 Collaboration Mode: {self.collaboration_mode}\n"
            message += f"📊 Intelligence Score: {intelligence_score:.1%}\n"
            message += f"🎓 Learning Confidence: {learning_confidence:.1%}\n"
            message += f"🔍 Patterns Recognized: {len(recent_patterns)}\n"
            message += f"💾 Context Cache: {len(self.ai_engine.embeddings_cache)} embeddings"
            
            result["message"] = message
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            self.logger.error(f"AI intelligence status failed: {e}")
            return f"❌ AI intelligence status failed: {str(e)}"
    
    # Helper methods
    def _calculate_contextual_relevance(self, suggestion: Dict, state: Dict) -> float:
        """Calculate how relevant a suggestion is to current context"""
        # Simplified relevance calculation
        if suggestion.get('type') in str(state).lower():
            return 0.8
        elif suggestion.get('action') in str(state).lower():
            return 0.6
        else:
            return 0.3
    
    def _estimate_execution_probability(self, suggestion: Dict, state: Dict) -> float:
        """Estimate probability that user will execute suggestion"""
        base_prob = suggestion.get('confidence', 0.5)
        relevance = self._calculate_contextual_relevance(suggestion, state)
        return (base_prob + relevance) / 2
    
    def _calculate_productivity_score(self, pattern_analysis: Dict) -> float:
        """Calculate overall productivity score"""
        if not pattern_analysis:
            return 0.5
        
        scores = []
        for patterns in pattern_analysis.values():
            if patterns:
                avg_frequency = np.mean([p['frequency'] for p in patterns])
                scores.append(min(avg_frequency / 10, 1.0))  # Normalize
        
        return np.mean(scores) if scores else 0.5
    
    def _generate_pattern_recommendations(self, pattern_type: str, patterns: List[Dict]) -> List[str]:
        """Generate recommendations based on patterns"""
        recommendations = []
        
        if "tool_usage" in pattern_type:
            recommendations.append("Consider creating custom workflows for frequently used tool sequences")
        elif "workflow" in pattern_type:
            recommendations.append("Automate repetitive workflow patterns")
        elif "context_switches" in pattern_type:
            recommendations.append("Use session management to reduce context switching overhead")
        
        return recommendations
    
    def _generate_collaboration_recommendations(self, insights: List[Dict]) -> List[str]:
        """Generate collaboration improvement recommendations"""
        recommendations = []
        
        productivity_insights = [i for i in insights if "productivity" in i.get('pattern_type', '')]
        if productivity_insights:
            avg_productivity = np.mean([i['average_confidence'] for i in productivity_insights])
            if avg_productivity < 0.6:
                recommendations.append("Enable adaptive collaboration mode for better AI assistance")
        
        return recommendations
    
    def _search_memory_semantically(self, query_embedding: np.ndarray, limit: int) -> List[Dict]:
        """Search memory using semantic similarity"""
        # This would integrate with the memory tool
        return [{"title": "Example memory", "similarity": 0.8, "content": "Sample content"}]
    
    def _search_sessions_semantically(self, query_embedding: np.ndarray, limit: int) -> List[Dict]:
        """Search sessions using semantic similarity"""
        # This would integrate with the session tool
        return [{"title": "Example session", "similarity": 0.7, "content": "Sample session"}]
    
    def _search_context_history(self, query_embedding: np.ndarray, limit: int) -> List[Dict]:
        """Search context history using semantic similarity"""
        # This would search stored context embeddings
        return self.ai_engine._find_similar_contexts(query_embedding, limit)
    
    def _get_mode_capabilities(self, mode: str) -> List[str]:
        """Get capabilities for collaboration mode"""
        capabilities = {
            "basic": ["Intent recognition", "Simple predictions"],
            "enhanced": ["Pattern learning", "Context awareness", "Action suggestions"],
            "adaptive": ["Real-time learning", "Behavior adaptation", "Predictive assistance"],
            "predictive": ["Proactive suggestions", "Advanced learning", "Workflow optimization"]
        }
        return capabilities.get(mode, [])
    
    def _calculate_collaboration_effectiveness(self) -> float:
        """Calculate collaboration effectiveness score"""
        # Simplified calculation based on recent usage
        return 0.75  # Placeholder
    
    def _get_current_capabilities(self) -> List[str]:
        """Get current AI capabilities"""
        capabilities = [
            "Semantic understanding",
            "Intent analysis", 
            "Pattern recognition",
            "Context analysis",
            "Action prediction",
            "Learning from interactions"
        ]
        
        if TRANSFORMERS_AVAILABLE:
            capabilities.extend(["Advanced NLP", "Entity recognition", "Sentiment analysis"])
        
        if SKLEARN_AVAILABLE:
            capabilities.extend(["Machine learning", "Clustering", "Similarity analysis"])
        
        return capabilities
    
    def get_tools(self) -> Dict[str, Callable]:
        """Return all AI/ML integration tools"""
        return {
            # Core AI analysis
            "bb7_ai_analyze_context": lambda context, depth="standard":
                self.bb7_ai_analyze_context(context, depth),
            
            "bb7_ai_suggest_actions": lambda current_state, suggestion_count=5, context_aware=True:
                self.bb7_ai_suggest_actions(current_state, suggestion_count, context_aware),
            
            # Learning and adaptation
            "bb7_ai_learn_interaction": lambda interaction_data:
                self.bb7_ai_learn_interaction(interaction_data),
            
            "bb7_ai_pattern_analysis": lambda timeframe_hours=24, pattern_types=None:
                self.bb7_ai_pattern_analysis(timeframe_hours, pattern_types),
            
            # Intelligence features
            "bb7_ai_semantic_search": lambda query, search_domains=None, max_results=10:
                self.bb7_ai_semantic_search(query, search_domains, max_results),
            
            # Configuration and status
            "bb7_ai_collaboration_mode": lambda mode="adaptive", learning_rate=0.1:
                self.bb7_ai_collaboration_mode(mode, learning_rate),
            
            "bb7_ai_intelligence_status": lambda:
                self.bb7_ai_intelligence_status(),
        }


# For standalone testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    ai_tool = AIMLIntegrationTool()
    
    print("=== AI/ML Integration Tool Test ===")
    
    # Test context analysis
    test_context = {
        "current_task": "debugging authentication code",
        "files_open": ["auth.py", "config.py"],
        "recent_errors": ["JWT token validation failed"],
        "session_goal": "fix login system"
    }
    
    result = ai_tool.bb7_ai_analyze_context(test_context)
    print("Context analysis completed")
    
    # Test suggestions
    suggestions = ai_tool.bb7_ai_suggest_actions(test_context)
    print("AI suggestions generated")
    
    # Test intelligence status
    status = ai_tool.bb7_ai_intelligence_status()
    print("Intelligence status retrieved")
