"""
AI服务客户端 - 集成OpenAI和Anthropic API
"""

import os
import asyncio
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import openai
import anthropic
import tiktoken
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

@dataclass
class AIResponse:
    """AI响应数据结构"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time: float

class AIClientError(Exception):
    """AI客户端异常"""
    pass

class AIClient:
    """统一的AI服务客户端"""
    
    def __init__(self):
        # OpenAI配置
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = None
        if self.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
        
        # Anthropic配置
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_client = None
        if self.anthropic_api_key:
            self.anthropic_client = AsyncAnthropic(api_key=self.anthropic_api_key)
        
        # 支持的模型配置
        self.supported_models = {
            "openai": {
                "gpt-3.5-turbo": {"max_tokens": 4096, "cost_per_1k": 0.002},
                "gpt-4": {"max_tokens": 8192, "cost_per_1k": 0.03},
                "gpt-4-turbo": {"max_tokens": 128000, "cost_per_1k": 0.01},
            },
            "anthropic": {
                "claude-3-haiku": {"max_tokens": 200000, "cost_per_1k": 0.00025},
                "claude-3-sonnet": {"max_tokens": 200000, "cost_per_1k": 0.003},
                "claude-3-opus": {"max_tokens": 200000, "cost_per_1k": 0.015},
            }
        }
    
    def get_available_models(self) -> List[str]:
        """获取可用的AI模型列表"""
        available = []
        
        if self.openai_client:
            available.extend(self.supported_models["openai"].keys())
        
        if self.anthropic_client:
            available.extend(self.supported_models["anthropic"].keys())
        
        return available
    
    def count_tokens(self, text: str, model: str = "gpt-3.5-turbo") -> int:
        """计算文本的token数量"""
        try:
            if model.startswith("gpt"):
                encoding = tiktoken.encoding_for_model(model)
                return len(encoding.encode(text))
            elif model.startswith("claude"):
                # Anthropic的token计算（近似）
                return len(text) // 4  # 粗略估算：4个字符约等于1个token
            else:
                return len(text.split())  # 简单的单词计数
        except Exception:
            return len(text.split())
    
    async def call_openai(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AIResponse:
        """调用OpenAI API"""
        if not self.openai_client:
            raise AIClientError("OpenAI API key not configured")
        
        if model not in self.supported_models["openai"]:
            raise AIClientError(f"Unsupported OpenAI model: {model}")
        
        import time
        start_time = time.time()
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or self.supported_models["openai"][model]["max_tokens"] // 2
            )
            
            response_time = time.time() - start_time
            
            return AIResponse(
                content=response.choices[0].message.content,
                model=model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                finish_reason=response.choices[0].finish_reason,
                response_time=response_time
            )
        
        except Exception as e:
            raise AIClientError(f"OpenAI API call failed: {str(e)}")
    
    async def call_anthropic(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-3-haiku",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AIResponse:
        """调用Anthropic API"""
        if not self.anthropic_client:
            raise AIClientError("Anthropic API key not configured")
        
        if model not in self.supported_models["anthropic"]:
            raise AIClientError(f"Unsupported Anthropic model: {model}")
        
        import time
        start_time = time.time()
        
        try:
            # 转换消息格式（Anthropic格式稍有不同）
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    user_messages.append(msg)
            
            response = await self.anthropic_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message if system_message else None,
                messages=user_messages
            )
            
            response_time = time.time() - start_time
            
            return AIResponse(
                content=response.content[0].text,
                model=model,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                finish_reason=response.stop_reason,
                response_time=response_time
            )
        
        except Exception as e:
            raise AIClientError(f"Anthropic API call failed: {str(e)}")
    
    async def generate_completion(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AIResponse:
        """统一的文本生成接口"""
        
        # 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # 根据模型选择对应的API
        if model.startswith("gpt"):
            return await self.call_openai(messages, model, temperature, max_tokens)
        elif model.startswith("claude"):
            return await self.call_anthropic(messages, model, temperature, max_tokens or 1000)
        else:
            raise AIClientError(f"Unsupported model: {model}")
    
    async def batch_generate(
        self,
        prompts: List[str],
        model: str = "gpt-3.5-turbo",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_concurrent: int = 5
    ) -> List[AIResponse]:
        """批量生成（并发控制）"""
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_single(prompt: str) -> AIResponse:
            async with semaphore:
                return await self.generate_completion(
                    prompt, model, system_prompt, temperature
                )
        
        tasks = [generate_single(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)

# 全局AI客户端实例
ai_client = AIClient()

def get_ai_client() -> AIClient:
    """获取AI客户端实例"""
    return ai_client
