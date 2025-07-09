import asyncio
from typing import Dict, List
from sqlalchemy.orm import Session
import logging

from ..models import Task, File, Role
from ..database import SessionLocal
from ..websocket_manager import manager
from .file_service import get_file_service
from .ai_service import get_ai_service

logger = logging.getLogger(__name__)

class ReviewService:
    """审查服务，协调整个审查流程"""
    
    def __init__(self):
        pass
    
    def get_draft_roles(self, task_id: int) -> Dict:
        """获取草稿角色识别结果"""
        db = SessionLocal()
        try:
            # 获取任务信息
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            # 检查实体数据是否已提取
            entities = task.entities_data
            if not entities:
                # 如果没有实体数据，尝试重新提取
                file_record = db.query(File).filter(File.task_id == task_id).first()
                if not file_record or not file_record.ocr_text:
                    raise ValueError(f"No OCR text found for task {task_id}")
                
                # 重新提取实体
                entities = get_ai_service().extract_entities_ner(file_record.ocr_text)
                
                # 保存到数据库
                from sqlalchemy import func
                task.entities_data = entities
                task.entities_extracted_at = func.now()
                task.status = "ENTITY_READY"
                db.commit()
                logger.info(f"Re-extracted entities for task {task_id}: {entities}")
            
            # 构建候选角色
            candidates = self._build_role_candidates(entities, task.contract_type)
            
            return {
                "task_id": task_id,
                "contract_type": task.contract_type,
                "candidates": candidates,
                "entities_extracted_at": task.entities_extracted_at.isoformat() if task.entities_extracted_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting draft roles: {e}")
            raise
        finally:
            db.close()
    
    def confirm_roles(self, task_id: int, role: str, party_names: List[str] = None, selected_entity_index: int = 0) -> Dict:
        """确认角色信息"""
        logger.info(f"🔧 ReviewService.confirm_roles called - task_id: {task_id}, role: {role}, party_names: {party_names}, selected_entity_index: {selected_entity_index}")
        
        db = SessionLocal()
        try:
            # 获取任务信息
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                error_msg = f"Task {task_id} not found"
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)
            
            logger.info(f"📋 Task found - status: {task.status}, entities_data: {task.entities_data}")
            
            # 如果没有提供party_names，从实体数据中自动选择
            if not party_names:
                if selected_entity_index is not None:
                    entities = task.entities_data
                    
                    if entities:
                        all_entities = []
                        all_entities.extend(entities.get("companies", []))
                        all_entities.extend(entities.get("persons", []))
                        all_entities.extend(entities.get("organizations", []))
                        
                        if all_entities and 0 <= selected_entity_index < len(all_entities):
                            party_names = [all_entities[selected_entity_index]]
                            logger.info(f"🎯 Auto-selected party_names from index {selected_entity_index}: {party_names}")
                        else:
                            logger.warning(f"⚠️ Invalid entity index {selected_entity_index} for entities: {all_entities}")
                    else:
                        logger.warning(f"⚠️ No entities data for task {task_id}")
            else:
                logger.info(f"✅ Using provided party_names: {party_names}")
            
            # 检查最终的party_names，如果为空则提供默认选项
            used_default_names = False
            if not party_names:
                used_default_names = True
                logger.warning(f"⚠️ No entities found, providing default party names for role: {role}")
                # 基于角色提供默认主体名称
                if role in ["buyer", "client"]:
                    party_names = ["委托方"]
                elif role in ["seller", "provider"]:
                    party_names = ["服务方"]
                elif role == "party_a":
                    party_names = ["甲方"]
                elif role == "party_b":
                    party_names = ["乙方"]
                elif role == "landlord":
                    party_names = ["出租方"]
                elif role == "tenant":
                    party_names = ["承租方"]
                else:
                    party_names = ["当事方"]
                
                logger.info(f"🎯 Using default party_names for role {role}: {party_names}")
            
            # 更新任务状态
            task.role = role
            task.status = "READY"
            logger.info(f"📝 Updated task - role: {role}, status: READY")
            
            # 保存角色信息
            role_record = Role(
                task_id=task_id,
                role_key=role,
                party_names=party_names
            )
            db.add(role_record)
            db.commit()
            logger.info(f"💾 Role record saved to database")
            
            # 判断是否为自动选择
            auto_selected = selected_entity_index is not None or used_default_names
            
            result = {
                "status": "READY", 
                "role": role, 
                "party_names": party_names,
                "auto_selected": auto_selected,
                "used_default_names": used_default_names,
                "message": "角色确认成功" if not used_default_names else "角色确认成功（使用默认主体名称）"
            }
            
            logger.info(f"✅ Roles confirmed for task {task_id}: {role}, party_names: {party_names}")
            logger.info(f"📤 Returning result: {result}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error confirming roles for task {task_id}: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            raise
        finally:
            db.close()
    
    async def start_review(self, task_id: int):
        """开始异步审查流程"""
        db = SessionLocal()
        try:
            # 更新任务状态
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            task.status = "IN_PROGRESS"
            db.commit()
            
            # 发送开始消息
            await manager.send_progress(task_id, {
                "stage": "start",
                "progress": 0,
                "message": "开始审查流程"
            })
            
            # 执行审查流程
            await self._run_review_pipeline(task_id)
            
        except Exception as e:
            logger.error(f"Error starting review: {e}")
            # 更新任务状态为失败
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = "FAILED"
                db.commit()
            
            await manager.send_error(task_id, str(e))
        finally:
            db.close()
    
    async def _run_review_pipeline(self, task_id: int):
        """执行完整的审查管道"""
        try:
            # 阶段1: OCR和文本提取
            await manager.send_progress(task_id, {
                "stage": "ocr",
                "progress": 20,
                "message": "正在提取文本内容"
            })
            
            ocr_text = await self._ensure_ocr_text(task_id)
            
            # 阶段2: 段落分割
            await manager.send_progress(task_id, {
                "stage": "segmentation",
                "progress": 40,
                "message": "正在分割段落"
            })
            
            paragraphs = get_file_service().split_text_into_paragraphs(ocr_text)
            
            # 阶段3: 向量化
            await manager.send_progress(task_id, {
                "stage": "vectorize",
                "progress": 60,
                "message": "正在进行向量化处理"
            })
            
            get_ai_service().vectorize_paragraphs(task_id, paragraphs)
            
            # 阶段4: 风险分析
            await manager.send_progress(task_id, {
                "stage": "analysis",
                "progress": 80,
                "message": "正在进行风险分析"
            })
            
            db = SessionLocal()
            task = db.query(Task).filter(Task.id == task_id).first()
            risks = get_ai_service().analyze_contract_risks(
                task_id, 
                task.contract_type, 
                task.role
            )
            db.close()
            
            # 阶段5: 完成
            await manager.send_progress(task_id, {
                "stage": "complete",
                "progress": 100,
                "message": "审查完成"
            })
            
            # 更新任务状态
            db = SessionLocal()
            task = db.query(Task).filter(Task.id == task_id).first()
            task.status = "COMPLETED"
            db.commit()
            db.close()
            
            # 发送完成消息
            await manager.send_completion(task_id, {
                "risks_count": len(risks),
                "message": "合同审查已完成"
            })
            
        except Exception as e:
            logger.error(f"Error in review pipeline: {e}")
            raise
    
    async def _ensure_ocr_text(self, task_id: int) -> str:
        """确保OCR文本已提取"""
        db = SessionLocal()
        try:
            file_record = db.query(File).filter(File.task_id == task_id).first()
            if not file_record:
                raise ValueError(f"No file found for task {task_id}")
            
            if not file_record.ocr_text:
                # 提取文本
                ocr_text = get_file_service().extract_text_from_file(file_record.path)
                file_record.ocr_text = ocr_text
                db.commit()
                return ocr_text
            else:
                return file_record.ocr_text
                
        finally:
            db.close()
    
    def _build_role_candidates(self, entities: Dict, contract_type: str) -> List[Dict]:
        """构建角色候选列表"""
        candidates = []
        
        # 基于合同类型提供默认角色选项
        if contract_type in ["采购合同", "供应合同"]:
            candidates.extend([
                {"role": "buyer", "label": "采购方", "description": "合同中的采购方，负责购买商品或服务", "entities": entities.get("companies", [])},
                {"role": "seller", "label": "供应方", "description": "合同中的供应方，负责提供商品或服务", "entities": entities.get("companies", [])}
            ])
        elif contract_type in ["服务合同", "咨询合同"]:
            candidates.extend([
                {"role": "client", "label": "委托方", "description": "合同中的委托方，接受服务的一方", "entities": entities.get("companies", [])},
                {"role": "provider", "label": "服务方", "description": "合同中的服务提供方，提供专业服务", "entities": entities.get("companies", [])}
            ])
        else:
            # 通用角色
            candidates.extend([
                {"role": "party_a", "label": "甲方", "description": "合同中的甲方当事人", "entities": entities.get("companies", [])},
                {"role": "party_b", "label": "乙方", "description": "合同中的乙方当事人", "entities": entities.get("companies", [])}
            ])
        
        return candidates
    
    def get_review_result(self, task_id: int) -> Dict:
        """获取审查结果"""
        db = SessionLocal()
        try:
            from ..models import Risk, Statute
            
            # 获取任务信息
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            # 获取风险列表
            risks = db.query(Risk).filter(Risk.task_id == task_id).all()
            
            risk_list = []
            for risk in risks:
                # 获取相关法规
                statutes = db.query(Statute).filter(Statute.risk_id == risk.id).all()
                
                risk_data = {
                    "id": risk.id,
                    "clause_id": risk.clause_id,
                    "title": risk.title,
                    "risk_level": risk.risk_level,
                    "summary": risk.summary,
                    "suggestion": risk.suggestion,
                    "statutes": [{
                        "ref": statute.statute_ref,
                        "text": statute.statute_text
                    } for statute in statutes]
                }
                risk_list.append(risk_data)
            
            # 生成摘要
            summary = self._generate_summary(risk_list)
            
            return {
                "task_id": task_id,
                "status": task.status,
                "contract_type": task.contract_type,
                "role": task.role,
                "risks": risk_list,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error getting review result: {e}")
            raise
        finally:
            db.close()
    
    def _generate_summary(self, risks: List[Dict]) -> Dict:
        """生成风险摘要"""
        total_risks = len(risks)
        high_risks = len([r for r in risks if r['risk_level'] == 'HIGH'])
        medium_risks = len([r for r in risks if r['risk_level'] == 'MEDIUM'])
        low_risks = len([r for r in risks if r['risk_level'] == 'LOW'])
        
        return {
            "total_risks": total_risks,
            "high_risks": high_risks,
            "medium_risks": medium_risks,
            "low_risks": low_risks,
            "risk_distribution": {
                "HIGH": high_risks,
                "MEDIUM": medium_risks,
                "LOW": low_risks
            }
        }

# 全局审查服务实例
review_service = ReviewService()