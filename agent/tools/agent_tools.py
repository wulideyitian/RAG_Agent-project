import os
from utils.logger_handler import logger
from langchain_core.tools import tool
from rag.rag_service import RagSummarizeService
import random
from utils.config_handler import agent_conf
from utils.path_tool import get_abs_path
import json

rag = RagSummarizeService()

# 模拟用户笔记本设备信息库
user_devices = {
    "1001": {"model": "联想 ThinkPad X1 Carbon", "cpu": "i7-1355U", "ram": "16GB", "storage": "512GB SSD", "purchase_date": "2024-03"},
    "1002": {"model": "戴尔 XPS 15 9530", "cpu": "i9-13900H", "ram": "32GB", "storage": "1TB SSD", "gpu": "RTX 4060", "purchase_date": "2024-05"},
    "1003": {"model": "MacBook Pro 14 M3", "cpu": "M3 Pro", "ram": "18GB", "storage": "512GB SSD", "purchase_date": "2024-06"},
}

user_ids = ["1001", "1002", "1003", "1004", "1005"]
month_arr = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06",
             "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12"]

external_data = {}


@tool(description="RAG 检索工具：从向量库精准检索笔记本相关资料。入参 query 为检索词，支持：'选购指南'、'故障排查'、'硬件知识'、'软件系统'、'维护保养'、'使用技巧'等维度。返回匹配的专业解答。")
def rag_summarize(query: str) -> str:
    """
    RAG 核心检索工具，支持多维度检索
    :param query: 检索词，如 'RTX 4060 显卡性能'、'蓝屏故障处理'、'电池保养方法'
    :return: 向量检索后的专业资料字符串
    """
    return rag.rag_summarize(query)


@tool(description="获取指定城市的天气环境信息，用于判断该环境对笔记本使用的影响（如潮湿需防潮、高温注意散热）。入参 city 为城市名。")
def get_weather(city: str) -> str:
    """
    获取城市天气信息，用于环境适配建议
    :param city: 城市名称，如 '深圳'、'北京'
    :return: 天气信息字符串，包含气温、湿度、降雨概率
    """
    # TODO: 实际项目中应接入真实天气 API
    weather_data = {
        "深圳": "气温 28℃，湿度 85%，多云，近期潮湿",
        "合肥": "气温 26℃，湿度 70%，晴，空气干燥",
        "杭州": "气温 27℃，湿度 80%，小雨，潮湿闷热",
        "北京": "气温 22℃，湿度 45%，晴，空气干燥",
    }
    return weather_data.get(city, f"城市{city}天气为晴天，气温 26 摄氏度，空气湿度 50%")


@tool(description="获取当前发起请求的用户所处的城市名称，用于提供地域适配的笔记本使用建议（如南方防潮、北方防尘）。无入参。")
def get_user_location() -> str:
    """
    获取用户所在城市
    :return: 城市名称字符串
    """
    return random.choice(["深圳", "合肥", "杭州", "北京"])


@tool(description="获取用户的唯一标识 ID（数字字符串），用于检索该用户的笔记本设备信息和使用记录。无入参。")
def get_user_id() -> str:
    """
    获取当前用户 ID
    :return: 用户 ID 字符串，如 '1001'
    """
    return random.choice(user_ids)


@tool(description="获取系统当前月份，格式固定为 YYYY-MM（如'2025-06'），用于生成当月的笔记本使用报告。无入参。")
def get_current_month() -> str:
    """
    获取当前月份
    :return: 月份字符串，格式 YYYY-MM
    """
    return random.choice(month_arr)


@tool(description="获取用户的笔记本设备详细信息，包括型号、CPU、内存、硬盘、显卡等配置。入参 user_id 为用户 ID，可选。若未指定自动获取当前用户。")
def get_user_device_info(user_id: str = None) -> str:
    """
    获取用户笔记本设备信息
    :param user_id: 用户 ID，可选参数，若不传则使用当前用户
    :return: 设备配置信息 JSON 字符串
    """
    if not user_id:
        user_id = get_user_id()
    
    device = user_devices.get(user_id)
    if not device:
        logger.warning(f"[get_user_device_info] 未找到用户{user_id}的设备信息")
        return "未找到该用户的设备信息"
    
    return json.dumps(device, ensure_ascii=False)


def generate_external_data():
    """
    生成笔记本电脑用户使用记录数据
    数据结构：{
        "user_id": {
            "month": {
                "usage_hours": 使用时长,
                "battery_health": 电池健康度,
                "temperature": 温度表现,
                "maintenance": 维护记录
            }
        }
    }
    """
    if not external_data:
        external_data_path = get_abs_path(agent_conf["external_data_path"])
        
        if not os.path.exists(external_data_path):
            raise FileNotFoundError(f"外部数据文件{external_data_path}不存在")
        
        with open(external_data_path, "r", encoding="utf-8") as f:
            for line in f.readlines()[1:]:
                arr: list[str] = line.strip().split(",")
                
                if len(arr) < 6:
                    continue
                
                user_id: str = arr[0].replace('"', "")
                model: str = arr[1].replace('"', "")
                usage_desc: str = arr[2].replace('"', "")
                hardware_status: str = arr[3].replace('"', "")
                comparison: str = arr[4].replace('"', "")
                month: str = arr[5].replace('"', "")
                
                if user_id not in external_data:
                    external_data[user_id] = {}
                
                # 解析电池健康度（从文本中提取）
                battery_health = "95%"
                if "电池健康度" in hardware_status:
                    import re
                    match = re.search(r'电池健康度 (\d+)%', hardware_status)
                    if match:
                        battery_health = f"{match.group(1)}%"
                
                external_data[user_id][month] = {
                    "型号": model,
                    "使用时长": usage_desc,
                    "硬件状态": hardware_status,
                    "对比分析": comparison,
                    "电池健康度": battery_health,
                }


@tool(description="检索指定用户在指定月份的笔记本使用记录，包含使用时长、电池健康、散热表现、维护记录等。入参：user_id（用户 ID）、month（月份 YYYY-MM）。")
def fetch_external_data(user_id: str, month: str) -> str:
    """
    获取用户笔记本使用记录
    :param user_id: 用户 ID
    :param month: 月份，格式 YYYY-MM
    :return: 使用记录结构化字符串
    """
    generate_external_data()
    
    try:
        data = external_data[user_id][month]
        return (
            f"【{data['型号']}】使用记录\n"
            f"• 使用时长：{data['使用时长']}\n"
            f"• 硬件状态：{data['硬件状态']}\n"
            f"• 电池健康：{data['电池健康度']}\n"
            f"• 对比分析：{data['对比分析']}"
        )
    except KeyError:
        logger.warning(f"[fetch_external_data] 未能检索到用户{user_id}在{month}的使用记录")
        return f"未找到用户{user_id}在{month}的使用记录"


@tool(description="生成笔记本专属使用报告的工具。调用后会自动注入上下文，为后续报告生成提供结构化数据支撑。仅在用户明确要求生成/查询使用报告时调用。无入参，无返回值。")
def fill_context_for_report():
    """
    为笔记本报告生成场景注入上下文信息
    仅在用户要求生成报告时调用，非报告场景禁止调用
    """
    return "fill_context_for_report 已调用，报告上下文已注入"
