import os
import requests
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import json

from ..models import Paragraph, Risk, Statute
from ..database import SessionLocal

logger = logging.getLogger(__name__)

class AIService:
    """AI服务，处理OpenRouter API调用和向量检索"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "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")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.embedding_model = "text-embedding-ada-002"  # 保留用于向量化
        self.chat_model = "qwen/qwen3-235b-a22b:free"
    
    def _call_openrouter_api(self, messages: List[Dict], temperature: float = 0.1) -> str:
        """调用OpenRouter API"""
        try:
            response = requests.post(
                url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps({
                    "model": self.chat_model,
                    "messages": messages,
                    "temperature": temperature
                })
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                raise Exception(f"API call failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            raise
    
    async def get_embedding(self, text: str) -> List[float]:
        """获取文本的向量表示（简化版，使用文本hash作为向量）"""
        try:
            # 简化版向量化：使用文本的hash值生成固定长度向量
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            # 将hash转换为1536维向量（模拟OpenAI embedding维度）
            vector = []
            for i in range(0, len(text_hash), 2):
                vector.append(int(text_hash[i:i+2], 16) / 255.0)
            # 补齐到1536维
            while len(vector) < 1536:
                vector.extend(vector[:min(len(vector), 1536-len(vector))])
            return vector[:1536]
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            raise
    
    def get_embedding_sync(self, text: str) -> List[float]:
        """同步获取文本的向量表示"""
        try:
            # 简化版向量化：使用文本的hash值生成固定长度向量
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            # 将hash转换为1536维向量（模拟OpenAI embedding维度）
            vector = []
            for i in range(0, len(text_hash), 2):
                vector.append(int(text_hash[i:i+2], 16) / 255.0)
            # 补齐到1536维
            while len(vector) < 1536:
                vector.extend(vector[:min(len(vector), 1536-len(vector))])
            return vector[:1536]
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            raise
    
    def vectorize_paragraphs(self, task_id: int, paragraphs: List[str]):
        """对段落进行向量化并存储"""
        db = SessionLocal()
        try:
            for i, para_text in enumerate(paragraphs):
                # 获取向量
                embedding = self.get_embedding_sync(para_text)
                
                # 存储段落和向量
                paragraph = Paragraph(
                    task_id=task_id,
                    text=para_text,
                    embedding=embedding,
                    paragraph_index=i
                )
                db.add(paragraph)
            
            db.commit()
            logger.info(f"Vectorized {len(paragraphs)} paragraphs for task {task_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error vectorizing paragraphs: {e}")
            raise
        finally:
            db.close()
    
    def search_similar_paragraphs(self, query_text: str, task_id: int, limit: int = 5) -> List[Dict]:
        """基于向量相似度搜索相关段落"""
        db = SessionLocal()
        try:
            # 获取查询向量
            query_embedding = self.get_embedding_sync(query_text)
            
            # 使用PGVector进行相似度搜索
            sql = text("""
                SELECT id, text, paragraph_index,
                       embedding <-> :query_embedding as distance
                FROM paragraphs 
                WHERE task_id = :task_id
                ORDER BY embedding <-> :query_embedding
                LIMIT :limit
            """)
            
            result = db.execute(sql, {
                'query_embedding': str(query_embedding),
                'task_id': task_id,
                'limit': limit
            })
            
            similar_paragraphs = []
            for row in result:
                similar_paragraphs.append({
                    'id': row.id,
                    'text': row.text,
                    'paragraph_index': row.paragraph_index,
                    'similarity_score': 1 - row.distance  # 转换为相似度分数
                })
            
            return similar_paragraphs
            
        except Exception as e:
            logger.error(f"Error searching similar paragraphs: {e}")
            return []
        finally:
            db.close()
    
    def extract_entities_ner(self, text: str) -> Dict[str, List[str]]:
        """使用NER提取实体（简化版，实际可用spaCy等）"""
        logger.info(f"🔍 Starting entity extraction for text length: {len(text)}")
        
        try:
            # 预处理文本，确保有足够内容
            if len(text.strip()) < 10:
                logger.warning("⚠️ Text too short for entity extraction")
                return self._get_fallback_entities(text)
            
            prompt = f"""
            请仔细分析以下合同文本，提取所有可能的当事方名称。请特别注意：
            1. 公司名称（包含"有限公司"、"股份公司"、"集团"等）
            2. 个人姓名（通常在甲方、乙方、委托方、受托方等位置）
            3. 其他组织机构名称
            
            合同文本：
            {text[:3000]}
            
            请严格按照以下JSON格式返回，不要添加任何其他内容：
            {{
                "companies": ["公司名称1", "公司名称2"],
                "persons": ["姓名1", "姓名2"],
                "organizations": ["组织名称1", "组织名称2"]
            }}
            """
            
            messages = [
                {"role": "system", "content": "你是一个专业的合同实体提取专家。请仔细分析文本并准确提取所有当事方信息。"},
                {"role": "user", "content": prompt}
            ]
            
            result_text = self._call_openrouter_api(messages, temperature=0.1)
            logger.info(f"🤖 AI response: {result_text[:200]}...")
            
            # 尝试解析JSON
            entities = self._parse_entities_response(result_text)
            
            # 如果AI提取失败，使用正则表达式备用方案
            if not any(entities.values()):
                logger.warning("⚠️ AI extraction returned empty, trying regex fallback")
                entities = self._extract_entities_regex(text)
            
            logger.info(f"✅ Final entities extracted: {entities}")
            return entities
                
        except Exception as e:
            logger.error(f"❌ Error in NER extraction: {e}")
            return self._extract_entities_regex(text)
    
    def _parse_entities_response(self, result_text: str) -> Dict[str, List[str]]:
        """解析AI返回的实体提取结果"""
        try:
            # 直接解析JSON
            entities = json.loads(result_text)
            # 验证格式
            if isinstance(entities, dict) and all(key in entities for key in ["companies", "persons", "organizations"]):
                return entities
        except json.JSONDecodeError:
            pass
        
        # 尝试提取JSON部分
        import re
        json_match = re.search(r'\{[^{}]*"companies"[^{}]*\}', result_text, re.DOTALL)
        if json_match:
            try:
                entities = json.loads(json_match.group())
                return entities
            except json.JSONDecodeError:
                pass
        
        logger.warning("Failed to parse entities response as JSON")
        return {"companies": [], "persons": [], "organizations": []}
    
    def _extract_entities_regex(self, text: str) -> Dict[str, List[str]]:
        """使用正则表达式提取实体（备用方案）"""
        logger.info("🔧 Using regex fallback for entity extraction")
        
        import re
        companies = []
        persons = []
        organizations = []
        
        # 提取公司名称
        company_patterns = [
            r'([\u4e00-\u9fa5]+(?:有限公司|股份有限公司|集团|公司))',
            r'(\w+(?:有限公司|股份有限公司|集团|公司))',
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            companies.extend(matches)
        
        # 提取常见的合同角色标识后的名称
        role_patterns = [
            r'甲方[：:](\s*[\u4e00-\u9fa5]+(?:有限公司|公司|集团)?)',
            r'乙方[：:](\s*[\u4e00-\u9fa5]+(?:有限公司|公司|集团)?)',
            r'委托方[：:](\s*[\u4e00-\u9fa5]+(?:有限公司|公司|集团)?)',
            r'受托方[：:](\s*[\u4e00-\u9fa5]+(?:有限公司|公司|集团)?)',
        ]
        
        for pattern in role_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                name = match.strip()
                if '公司' in name or '集团' in name:
                    companies.append(name)
                else:
                    persons.append(name)
        
        # 去重
        companies = list(set(companies))
        persons = list(set(persons))
        organizations = list(set(organizations))
        
        result = {
            "companies": companies,
            "persons": persons,
            "organizations": organizations
        }
        
        logger.info(f"🎯 Regex extraction result: {result}")
        return result
    
    def _get_fallback_entities(self, text: str) -> Dict[str, List[str]]:
        """获取备用实体（当文本太短时）"""
        logger.info("📝 Using fallback entities for short text")
        return {
            "companies": ["合同当事方"],
            "persons": [],
            "organizations": []
        }
    
    def analyze_contract_risks(self, task_id: int, contract_type: str, role: str) -> List[Dict]:
        """分析合同风险"""
        db = SessionLocal()
        try:
            # 获取所有段落
            paragraphs = db.query(Paragraph).filter(Paragraph.task_id == task_id).all()
            
            if not paragraphs:
                logger.warning(f"No paragraphs found for task {task_id}")
                return []
            
            # 构建完整文本
            full_text = "\n\n".join([p.text for p in paragraphs])
            
            # 构建风险分析提示
            prompt = self._build_risk_analysis_prompt(full_text, contract_type, role)
            
            # 调用LLM分析
            messages = [
                {"role": "system", "content": "你是一个专业的合同风险分析专家，具有丰富的法律知识和实务经验。"},
                {"role": "user", "content": prompt}
            ]
            
            result_text = self._call_openrouter_api(messages, temperature=0.2)
            
            # 解析风险分析结果
            risks = self._parse_risk_analysis_result(result_text)
            
            # 保存风险到数据库
            self._save_risks_to_db(task_id, risks, db)
            
            return risks
            
        except Exception as e:
            logger.error(f"Error analyzing contract risks: {e}")
            return []
        finally:
            db.close()
    
    def _build_risk_analysis_prompt(self, text: str, contract_type: str, role: str) -> str:
        """构建风险分析提示"""
        return f"""
        请对以下{contract_type}合同进行全面的风险分析。我的角色是{role}。
        
        合同内容：
        {text[:4000]}  # 限制长度避免超出token限制
        
        请从以下角度进行分析并以JSON格式返回结果：
        
        {{
            "risks": [
                {{
                    "clause_id": "条款编号或标识",
                    "title": "风险标题",
                    "risk_level": "HIGH/MEDIUM/LOW",
                    "summary": "风险描述和分析",
                    "suggestion": "应对建议",
                    "related_laws": ["相关法律法规"]
                }}
            ]
        }}
        
        重点关注：
        1. 付款条款和违约责任
        2. 交付时间和质量标准
        3. 知识产权条款
        4. 免责和限责条款
        5. 争议解决机制
        6. 合同变更和终止条件
        """
    
    def _parse_risk_analysis_result(self, result_text: str) -> List[Dict]:
        """解析风险分析结果"""
        try:
            # 尝试直接解析JSON
            result = json.loads(result_text)
            return result.get('risks', [])
        except json.JSONDecodeError:
            # 如果不是标准JSON，尝试提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    return result.get('risks', [])
                except json.JSONDecodeError:
                    pass
            
            logger.warning("Failed to parse risk analysis result")
            return []
    
    def _save_risks_to_db(self, task_id: int, risks: List[Dict], db: Session):
        """保存风险到数据库"""
        try:
            for risk_data in risks:
                risk = Risk(
                    task_id=task_id,
                    clause_id=risk_data.get('clause_id', ''),
                    title=risk_data.get('title', ''),
                    risk_level=risk_data.get('risk_level', 'MEDIUM'),
                    summary=risk_data.get('summary', ''),
                    suggestion=risk_data.get('suggestion', '')
                )
                db.add(risk)
                db.flush()  # 获取risk.id
                
                # 保存相关法规
                related_laws = risk_data.get('related_laws', [])
                for law in related_laws:
                    statute = Statute(
                        risk_id=risk.id,
                        statute_ref=law,
                        statute_text=""  # 可以后续补充具体条文
                    )
                    db.add(statute)
            
            db.commit()
            logger.info(f"Saved {len(risks)} risks for task {task_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving risks to database: {e}")
            raise

# 全局AI服务实例 - 延迟初始化
ai_service = None

def get_ai_service():
    """获取AI服务实例（延迟初始化）"""
    global ai_service
    if ai_service is None:
        ai_service = AIService()
    return ai_service