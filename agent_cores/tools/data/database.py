"""
数据库工具模块 - 提供数据库操作功能

包含一个数据库管理器类，用于操作模拟数据库。
"""
import logging
import time
import json
from typing import Dict, List, Any, Optional, Union

# 配置日志
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    数据库管理器 - 提供数据库操作功能
    
    该类模拟了一个简单的数据库接口，用于教学和示例目的。
    """
    
    def __init__(self):
        """初始化数据库管理器"""
        self.data_store = {
            "users": [
                {"id": 1, "name": "张三", "age": 30, "email": "zhangsan@example.com"},
                {"id": 2, "name": "李四", "age": 25, "email": "lisi@example.com"},
                {"id": 3, "name": "王五", "age": 40, "email": "wangwu@example.com"}
            ],
            "products": [
                {"id": 1, "name": "笔记本电脑", "price": 5999, "stock": 10},
                {"id": 2, "name": "手机", "price": 2999, "stock": 20},
                {"id": 3, "name": "平板电脑", "price": 3999, "stock": 15}
            ],
            "orders": [
                {"id": 1, "user_id": 1, "product_id": 2, "quantity": 1, "total": 2999, "date": "2023-05-10"},
                {"id": 2, "user_id": 2, "product_id": 1, "quantity": 1, "total": 5999, "date": "2023-05-11"},
                {"id": 3, "user_id": 3, "product_id": 3, "quantity": 2, "total": 7998, "date": "2023-05-12"}
            ]
        }
        logger.info("数据库管理器初始化完成")
    
    def search_database(self, table: str, query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        搜索数据库表
        
        Args:
            table: 表名
            query: 查询条件，为空则返回所有记录
            
        Returns:
            查询结果
        """
        logger.info(f"搜索数据库: 表={table}, 查询条件={query}")
        
        try:
            # 检查表是否存在
            if table not in self.data_store:
                return {
                    "error": True,
                    "message": f"表 {table} 不存在",
                    "results": []
                }
            
            # 获取表数据
            table_data = self.data_store[table]
            
            # 如果没有查询条件，返回所有数据
            if not query:
                return {
                    "error": False,
                    "count": len(table_data),
                    "results": table_data
                }
            
            # 根据查询条件过滤数据
            filtered_data = []
            for record in table_data:
                match = True
                for key, value in query.items():
                    if key not in record or record[key] != value:
                        match = False
                        break
                
                if match:
                    filtered_data.append(record)
            
            return {
                "error": False,
                "count": len(filtered_data),
                "results": filtered_data
            }
            
        except Exception as e:
            logger.error(f"搜索数据库失败: {str(e)}")
            return {
                "error": True,
                "message": f"搜索失败: {str(e)}",
                "results": []
            }
    
    def insert_record(self, table: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        插入记录到数据库
        
        Args:
            table: 表名
            record: 要插入的记录
            
        Returns:
            插入结果
        """
        logger.info(f"插入记录: 表={table}, 记录={record}")
        
        try:
            # 检查表是否存在
            if table not in self.data_store:
                return {
                    "error": True,
                    "message": f"表 {table} 不存在"
                }
            
            # 生成新ID
            max_id = 0
            for existing_record in self.data_store[table]:
                if existing_record["id"] > max_id:
                    max_id = existing_record["id"]
            
            # 设置新记录的ID
            new_record = record.copy()
            new_record["id"] = max_id + 1
            
            # 添加记录
            self.data_store[table].append(new_record)
            
            return {
                "error": False,
                "message": "记录插入成功",
                "record": new_record
            }
            
        except Exception as e:
            logger.error(f"插入记录失败: {str(e)}")
            return {
                "error": True,
                "message": f"插入失败: {str(e)}"
            }
    
    def update_record(self, table: str, record_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新数据库记录
        
        Args:
            table: 表名
            record_id: 记录ID
            updates: 要更新的字段
            
        Returns:
            更新结果
        """
        logger.info(f"更新记录: 表={table}, ID={record_id}, 更新={updates}")
        
        try:
            # 检查表是否存在
            if table not in self.data_store:
                return {
                    "error": True,
                    "message": f"表 {table} 不存在"
                }
            
            # 查找记录
            for i, record in enumerate(self.data_store[table]):
                if record["id"] == record_id:
                    # 更新记录
                    for key, value in updates.items():
                        if key != "id":  # 不允许更新ID
                            self.data_store[table][i][key] = value
                    
                    return {
                        "error": False,
                        "message": "记录更新成功",
                        "record": self.data_store[table][i]
                    }
            
            return {
                "error": True,
                "message": f"未找到ID为 {record_id} 的记录"
            }
            
        except Exception as e:
            logger.error(f"更新记录失败: {str(e)}")
            return {
                "error": True,
                "message": f"更新失败: {str(e)}"
            }
    
    def delete_record(self, table: str, record_id: int) -> Dict[str, Any]:
        """
        删除数据库记录
        
        Args:
            table: 表名
            record_id: 记录ID
            
        Returns:
            删除结果
        """
        logger.info(f"删除记录: 表={table}, ID={record_id}")
        
        try:
            # 检查表是否存在
            if table not in self.data_store:
                return {
                    "error": True,
                    "message": f"表 {table} 不存在"
                }
            
            # 查找记录
            for i, record in enumerate(self.data_store[table]):
                if record["id"] == record_id:
                    # 删除记录
                    deleted_record = self.data_store[table].pop(i)
                    
                    return {
                        "error": False,
                        "message": "记录删除成功",
                        "record": deleted_record
                    }
            
            return {
                "error": True,
                "message": f"未找到ID为 {record_id} 的记录"
            }
            
        except Exception as e:
            logger.error(f"删除记录失败: {str(e)}")
            return {
                "error": True,
                "message": f"删除失败: {str(e)}"
            }
    
    def execute_query(self, query: str) -> Dict[str, Any]:
        """
        执行SQL查询（模拟）
        
        Args:
            query: SQL查询字符串
            
        Returns:
            查询结果
        """
        logger.info(f"执行查询: {query}")
        
        try:
            # 这里只是模拟，不是真正的SQL解析
            # 仅支持一些简单的查询模式
            
            # 模拟SELECT查询
            if query.lower().startswith("select"):
                # 提取表名
                from_part = query.lower().split("from")[1].strip()
                table_name = from_part.split()[0].strip()
                
                # 检查表是否存在
                if table_name not in self.data_store:
                    return {
                        "error": True,
                        "message": f"表 {table_name} 不存在",
                        "results": []
                    }
                
                # 简单处理WHERE子句
                where_condition = {}
                if "where" in query.lower():
                    where_part = query.lower().split("where")[1].strip()
                    # 简单解析条件（仅支持简单的等于条件）
                    for condition in where_part.split("and"):
                        if "=" in condition:
                            parts = condition.split("=")
                            key = parts[0].strip()
                            value = parts[1].strip()
                            # 尝试解析值（数字或字符串）
                            try:
                                if value.isdigit():
                                    value = int(value)
                                elif value.startswith("'") and value.endswith("'"):
                                    value = value[1:-1]
                                where_condition[key] = value
                            except:
                                pass
                
                # 使用search_database方法执行查询
                return self.search_database(table_name, where_condition)
            
            return {
                "error": True,
                "message": "不支持的查询类型，仅支持简单的SELECT查询",
                "results": []
            }
            
        except Exception as e:
            logger.error(f"执行查询失败: {str(e)}")
            return {
                "error": True,
                "message": f"查询失败: {str(e)}",
                "results": []
            } 