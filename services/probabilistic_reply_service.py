"""
概率性回复服务模块
负责根据配置的概率决定是否触发回复
"""
import random
import time
from typing import Optional
from astrbot.api import logger


class ProbabilisticReplyService:
    """概率性回复服务
    
    提供概率性回复功能，根据配置的概率值决定是否触发LLM回复
    """
    
    def __init__(self, config: dict):
        """初始化概率性回复服务
        
        Args:
            config: 插件配置字典
        """
        self.config = config
        self._last_decision_time = {}  # 记录每个会话最后决策时间
        self._load_config()
        
        logger.info(f"概率性回复服务初始化完成 - 启用状态: {self.enabled}, 回复概率: {self.reply_probability}")
    
    def _load_config(self):
        """加载配置项"""
        chat_reply_config = self.config.get("Chat_Reply", {})
        
        # 概率性回复启用状态
        self.enabled = chat_reply_config.get("Enable_Probabilistic_Reply", False)
        
        # 回复概率 (0.0-1.0)
        self.reply_probability = float(chat_reply_config.get("Reply_Probability", 0.3))
        
        # 确保概率值在有效范围内
        self.reply_probability = max(0.0, min(1.0, self.reply_probability))
        
        logger.debug(f"概率性回复配置加载完成 - 启用: {self.enabled}, 概率: {self.reply_probability}")
    
    def should_generate_reply(self, session_id: str = None) -> bool:
        """判断是否应该生成回复
        
        Args:
            session_id: 会话标识符，用于记录决策时间和调试
            
        Returns:
            bool: True表示应该生成回复，False表示不应该生成回复
        """
        # 如果未启用概率性回复，则按原逻辑总是回复
        if not self.enabled:
            logger.debug("概率性回复未启用，将总是生成回复")
            return True
            
        # 生成随机数进行概率判断
        random_value = random.random()
        should_reply = random_value <= self.reply_probability
        
        # 记录决策时间
        if session_id:
            self._last_decision_time[session_id] = time.time()
        
        logger.info(f"概率性回复决策 - 随机值: {random_value:.3f}, 阈值: {self.reply_probability:.3f}, "
                   f"结果: {'回复' if should_reply else '不回复'}, 会话: {session_id or 'Unknown'}")
        
        return should_reply
    
    def get_reply_strategy_info(self) -> dict:
        """获取当前回复策略信息
        
        Returns:
            dict: 包含回复策略配置的信息
        """
        return {
            "enabled": self.enabled,
            "reply_probability": self.reply_probability,
            "strategy_type": "probabilistic" if self.enabled else "always_reply",
            "description": f"概率性回复 ({self.reply_probability*100:.1f}%)" if self.enabled else "总是回复"
        }
    
    def update_config(self, new_config: dict):
        """动态更新配置
        
        Args:
            new_config: 新的配置字典
        """
        self.config = new_config
        old_enabled = self.enabled
        old_probability = self.reply_probability
        
        self._load_config()
        
        if old_enabled != self.enabled or old_probability != self.reply_probability:
            logger.info(f"概率性回复配置已更新 - "
                       f"启用状态: {old_enabled} -> {self.enabled}, "
                       f"回复概率: {old_probability} -> {self.reply_probability}")
    
    def get_session_statistics(self, session_id: str) -> Optional[dict]:
        """获取特定会话的统计信息
        
        Args:
            session_id: 会话标识符
            
        Returns:
            dict: 包含会话统计信息的字典，如果会话不存在则返回None
        """
        if session_id not in self._last_decision_time:
            return None
            
        return {
            "session_id": session_id,
            "last_decision_time": self._last_decision_time[session_id],
            "time_since_last_decision": time.time() - self._last_decision_time[session_id]
        }
    
    def cleanup_old_sessions(self, max_age_seconds: int = 3600):
        """清理旧的会话记录
        
        Args:
            max_age_seconds: 最大保留时间，超过此时间的会话记录将被删除
        """
        current_time = time.time()
        sessions_to_remove = []
        
        for session_id, last_time in self._last_decision_time.items():
            if current_time - last_time > max_age_seconds:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self._last_decision_time[session_id]
            
        if sessions_to_remove:
            logger.debug(f"清理了 {len(sessions_to_remove)} 个过期会话记录")
    
    def get_service_status(self) -> dict:
        """获取服务状态信息
        
        Returns:
            dict: 服务状态信息
        """
        return {
            "service_name": "ProbabilisticReplyService",
            "enabled": self.enabled,
            "reply_probability": self.reply_probability,
            "active_sessions": len(self._last_decision_time),
            "strategy_description": self.get_reply_strategy_info()["description"]
        }