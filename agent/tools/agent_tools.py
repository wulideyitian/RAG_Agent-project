import os
from app.utils.logger_handler import logger
from langchain_core.tools import tool
from app.utils.config_handler import agent_conf
from app.utils.path_tool import get_abs_path
import json
import csv

# 延迟初始化 RAG 生成器
_rag_generator = None

def get_rag_generator():
    """获取 RAG 生成器实例（延迟加载）"""
    global _rag_generator
    if _rag_generator is None:
        try:
            from core.rag.generator import RAGGenerator
            _rag_generator = RAGGenerator()
        except Exception as e:
            logger.error(f"[get_rag_generator] 初始化失败：{e}")
            return None
    return _rag_generator

# 缓存配置文件路径，避免重复计算
_config_paths = {}

def _get_config_path(key: str) -> str:
    """
    获取配置路径并缓存
    :param key: 配置键名
    :return: 绝对路径
    """
    if key not in _config_paths:
        _config_paths[key] = get_abs_path(agent_conf[key])
    return _config_paths[key]




@tool(description="RAG 检索工具：从向量库精准检索笔记本相关资料。入参 query 为检索词，支持：'选购指南'、'故障排查'、'硬件知识'、'软件系统'、'维护保养'、'使用技巧'等维度。返回匹配的专业解答。")
async def rag_summarize(query: str) -> str:
    """
    RAG 核心检索工具，支持多维度检索
    :param query: 检索词，如 'RTX 4060 显卡性能'、'蓝屏故障处理'、'电池保养方法'
    :return: 向量检索后的专业资料字符串
    """
    rag = get_rag_generator()
    if rag is None:
        return "RAG 服务初始化失败，请稍后重试"
    return await rag.rag_summarize(query)


@tool(description="获取用户的笔记本设备详细信息，包括型号、CPU、内存、硬盘、显卡等配置。入参 user_id 为用户 ID（必需）。")
def get_user_device_info(user_id: str) -> str:
    """
    获取用户笔记本设备信息
    :param user_id: 用户 ID（必需参数，由前端/接口传入固定值）
    :return: 设备配置信息 JSON 字符串
    """
    # TODO: 实际项目中应从数据库查询用户设备信息
    # 这里返回示例数据
    logger.info(f"[get_user_device_info] 查询用户{user_id}的设备信息")
    return json.dumps({
        "user_id": user_id,
        "message": "请配置真实的用户设备数据库"
    }, ensure_ascii=False)



# ===== 工具函数实现（普通函数，可被其他工具内部调用）=====

def _laptop_spec_impl(model_name: str) -> str:
    """
    查询笔记本详细规格参数（内部实现）
    :param model_name: 笔记本型号
    :return: JSON 格式的参数信息
    """
    try:
        specs_path = _get_config_path("laptop_specs_path")
        
        if not os.path.exists(specs_path):
            logger.warning(f"[laptop_spec] 规格库文件{specs_path}不存在")
            return "未找到笔记本规格数据库"
        
        with open(specs_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 确保字段存在
                if "型号" not in row or not row.get("型号"):
                    continue
                    
                # 模糊匹配型号
                if model_name.lower() in row["型号"].lower() or row["型号"].lower() in model_name.lower():
                    spec_info = {
                        "型号": row.get("型号", "未知"),
                        "CPU": row.get("CPU", "未知"),
                        "GPU": row.get("GPU", "未知"),
                        "屏幕尺寸": row.get("屏幕尺寸", "未知"),
                        "分辨率": row.get("屏幕分辨率", "未知"),
                        "刷新率": row.get("刷新率", "未知"),
                        "内存": row.get("内存", "未知"),
                        "硬盘": row.get("硬盘", "未知"),
                        "电池": row.get("电池", "未知"),
                        "重量": row.get("重量", "未知"),
                        "价格区间": row.get("价格区间", "未知"),
                        "用途分类": row.get("用途分类", "未知"),
                        "品牌": row.get("品牌", "未知")
                    }
                    return json.dumps(spec_info, ensure_ascii=False, indent=2)
        
        logger.warning(f"[laptop_spec] 未找到型号{model_name}的规格信息")
        return f"未找到'{model_name}'的规格信息，请确认型号是否正确"
    
    except Exception as e:
        logger.error(f"[laptop_spec] 查询失败：{str(e)}")
        return "查询失败，请稍后重试"


@tool(description="笔记本参数查询工具：根据型号查询 CPU、显卡、屏幕、电池、接口、重量等详细规格。入参 model_name 为笔记本型号（如'联想拯救者 R9000P'）。返回结构化 JSON 数据。")
def laptop_spec_tool(model_name: str) -> str:
    """查询笔记本详细规格参数（Agent 调用入口）"""
    return _laptop_spec_impl(model_name)


@tool(description="型号对比工具：对比 2 台笔记本的性能、价格、用途差异。入参 model_a 和 model_b 为两个型号。返回对比表格和差异分析。例：R9000P vs 拯救者 Y9000P")
def model_compare_tool(model_a: str, model_b: str) -> str:
    """
    对比两台笔记本的参数差异
    :param model_a: 第一个型号
    :param model_b: 第二个型号
    :return: 对比表格和分析
    """
    try:
        specs_path = _get_config_path("laptop_specs_path")
        
        if not os.path.exists(specs_path):
            return "未找到笔记本规格数据库"
        
        # 读取两个型号的信息
        models_data = {}
        with open(specs_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 确保字段存在
                if "型号" not in row or not row.get("型号"):
                    continue
                    
                for target_model in [model_a, model_b]:
                    if target_model.lower() in row["型号"].lower() or row["型号"].lower() in target_model.lower():
                        models_data[row["型号"]] = row
        
        if len(models_data) < 2:
            return f"未能找到两个型号的完整信息，当前找到：{list(models_data.keys())}"
        
        # 提取对比数据
        model_names = list(models_data.keys())[:2]  # 只取前两个匹配
        data_a = models_data[model_names[0]]
        data_b = models_data[model_names[1]]
        
        # 生成对比表格
        compare_items = [
            ("CPU", data_a["CPU"], data_b["CPU"]),
            ("GPU", data_a["GPU"], data_b["GPU"]),
            ("屏幕", f"{data_a['屏幕尺寸']} {data_a['屏幕分辨率']} {data_a['刷新率']}", 
                    f"{data_b['屏幕尺寸']} {data_b['屏幕分辨率']} {data_b['刷新率']}"),
            ("内存", data_a["内存"], data_b["内存"]),
            ("硬盘", data_a["硬盘"], data_b["硬盘"]),
            ("电池", data_a["电池"], data_b["电池"]),
            ("重量", data_a["重量"], data_b["重量"]),
            ("价格", data_a["价格区间"], data_b["价格区间"]),
            ("用途", data_a["用途分类"], data_b["用途分类"])
        ]
        
        result = f"【{model_names[0]} vs {model_names[1]}】对比分析\n\n"
        result += "【参数对比表】\n"
        result += "| 项目 | " + model_names[0] + " | " + model_names[1] + " | 差异 |\n"
        result += "|------|" + "---|" * 3 + "\n"
        
        for item, val_a, val_b in compare_items:
            diff_mark = "✅相同" if val_a == val_b else "🔴不同"
            result += f"| {item} | {val_a} | {val_b} | {diff_mark} |\n"
        
        # 分析总结
        result += "\n【核心差异】\n"
        if data_a["GPU"] != data_b["GPU"]:
            result += f"• 显卡差异：{data_a['GPU']} vs {data_b['GPU']}\n"
        if data_a["价格区间"] != data_b["价格区间"]:
            result += f"• 价格差异：{data_a['价格区间']} vs {data_b['价格区间']}\n"
        if data_a["用途分类"] != data_b["用途分类"]:
            result += f"• 定位差异：{data_a['用途分类']} vs {data_b['用途分类']}\n"
        
        result += "\n【选购建议】\n"
        result += f"• {model_names[0]}适合：{data_a['用途分类']}用户，预算{data_a['价格区间']}\n"
        result += f"• {model_names[1]}适合：{data_b['用途分类']}用户，预算{data_b['价格区间']}\n"
        
        return result
    
    except Exception as e:
        logger.error(f"[model_compare_tool] 对比失败：{str(e)}")
        return "对比失败，请稍后重试"


@tool(description="故障诊断工具：根据用户描述的症状定位故障原因，给出排查步骤。入参 symptoms 为故障描述（如'开机黑屏'、'风扇狂转掉帧'）。返回可能原因、解决步骤、送修建议。")
async def fault_diagnose_tool(symptoms: str) -> str:
    """
    故障诊断核心工具
    :param symptoms: 故障症状描述，如'开机黑屏，风扇不转'、'游戏掉帧发热'
    :return: 诊断报告（可能原因、排查步骤、送修建议）
    """
    try:
        # Step 1: RAG 检索故障案例库
        rag_query = f"笔记本故障：{symptoms}"
        rag_gen = get_rag_generator()
        rag_result = await rag_gen.rag_summarize(rag_query) if rag_gen else "RAG 检索服务暂时不可用"
        
        # Step 2: 关键词匹配（规则引擎）
        diagnosis_rules = {
            "黑屏": {
                "可能原因": ["电源问题", "内存接触不良", "主板故障", "屏幕损坏"],
                "排查步骤": [
                    "检查电源适配器和插座",
                    "释放静电（长按电源键 30 秒）",
                    "清洁内存条金手指",
                    "外接显示器测试"
                ],
                "送修建议": "若外接显示器无显示，建议送修检测主板"
            },
            "发热": {
                "可能原因": ["散热鳍片堵塞", "硅脂老化", "风扇故障", "高负载运行"],
                "排查步骤": [
                    "清理灰尘和散热鳍片",
                    "更换 CPU/GPU 硅脂",
                    "检查风扇转速",
                    "改善使用环境通风"
                ],
                "送修建议": "若清灰后仍高温，需检查热管是否失效"
            },
            "蓝屏": {
                "可能原因": ["驱动冲突", "内存故障", "系统文件损坏", "硬件不兼容"],
                "排查步骤": [
                    "记录蓝屏错误代码",
                    "运行 Windows 内存诊断",
                    "更新或回退驱动程序",
                    "检查最近安装的软件/硬件"
                ],
                "送修建议": "频繁蓝屏且内存检测报错，需更换内存条"
            },
            "掉帧": {
                "可能原因": ["温度墙降频", "功耗墙限制", "显存不足", "驱动问题"],
                "排查步骤": [
                    "监控 GPU 温度和频率",
                    "清理散热系统",
                    "更新显卡驱动",
                    "降低游戏画质设置"
                ],
                "送修建议": "若温度正常仍掉帧，需检查显卡核心"
            },
            "无法开机": {
                "可能原因": ["电池放电过度", "电源适配器损坏", "主板 EC 锁死", "开关故障"],
                "排查步骤": [
                    "连接电源适配器充电 30 分钟",
                    "更换同功率适配器测试",
                    "释放静电操作",
                    "检查电源指示灯"
                ],
                "送修建议": "若电源指示灯不亮，可能主板故障需送修"
            }
        }
        
        # 匹配症状关键词
        matched_diagnosis = None
        for keyword, diagnosis in diagnosis_rules.items():
            if keyword in symptoms:
                matched_diagnosis = diagnosis
                break
        
        # 生成诊断报告
        result = "【故障诊断报告】\n\n"
        
        if matched_diagnosis:
            result += "【可能原因】\n"
            for i, reason in enumerate(matched_diagnosis["可能原因"], 1):
                result += f"{i}. {reason}\n"
            
            result += "\n【排查步骤】\n"
            for i, step in enumerate(matched_diagnosis["排查步骤"], 1):
                result += f"{i}. {step}\n"
            
            result += f"\n【送修建议】\n{matched_diagnosis['送修建议']}\n"
        else:
            result += f"基于 RAG 检索结果：\n{rag_result}\n\n"
            result += "【建议】\n由于症状描述不够具体，建议补充：\n"
            result += "• 具体故障现象（何时开始、频率、有无规律）\n"
            result += "• 笔记本型号和使用年限\n"
            result += "• 最近是否有磕碰、进水、改装\n"
        
        return result
    
    except Exception as e:
        logger.error(f"[fault_diagnose_tool] 诊断失败：{str(e)}")
        return "诊断失败，请稍后重试"


@tool(description="购机推荐工具：根据预算和用途推荐笔记本。入参 budget 为预算（如'6000 元'），usage 为用途（游戏/办公/设计/编程）。返回推荐清单含型号、配置、理由、避坑点。")
async def purchase_recommend_tool(budget: str, usage: str) -> str:
    """
    购机推荐工具
    :param budget: 预算范围，如'6000 元'、'5000-7000 元'
    :param usage: 用途场景，如'游戏'、'办公'、'设计'、'编程'
    :return: 推荐清单（型号、配置、价格、理由、避坑点）
    """
    try:
        specs_path = _get_config_path("laptop_specs_path")
        
        if not os.path.exists(specs_path):
            return "未找到笔记本规格数据库"
        
        # 解析预算
        budget_num = 0
        budget_max = 99999
        if "元" in budget:
            budget_parts = budget.replace("元", "").split("-")
            if len(budget_parts) == 1:
                try:
                    budget_num = int(budget_parts[0])
                    budget_max = budget_num * 1.2
                except ValueError:
                    logger.warning(f"[purchase_recommend_tool] 预算解析失败：{budget}")
                    return "预算格式不正确，请使用如'6000 元'或'5000-7000 元'的格式"
            else:
                try:
                    budget_num = int(budget_parts[0])
                    budget_max = int(budget_parts[1])
                except ValueError:
                    logger.warning(f"[purchase_recommend_tool] 预算解析失败：{budget}")
                    return "预算格式不正确，请使用如'6000 元'或'5000-7000 元'的格式"
        
        # 读取并过滤数据
        recommendations = []
        with open(specs_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 确保字段存在
                if "价格区间" not in row or not row.get("价格区间"):
                    continue
                    
                price_range = row["价格区间"]
                # 简单价格匹配 - 修复价格解析 bug
                try:
                    # 处理"7000-8000 元"格式
                    price_str = price_range.split("-")[0].replace("元", "").strip()
                    price_min = int(price_str)
                except (ValueError, IndexError) as e:
                    logger.warning(f"[purchase_recommend_tool] 价格解析失败：{price_range}, 错误：{e}")
                    continue
                
                # 用途匹配
                usage_map = {
                    "游戏": ["游戏本"],
                    "办公": ["商务本", "办公本", "轻薄本"],
                    "设计": ["创作本", "全能本"],
                    "编程": ["商务本", "轻薄本", "全能本"]
                }
                
                target_categories = usage_map.get(usage, ["轻薄本", "商务本"])
                
                if (price_min <= budget_max and 
                    any(cat in row["用途分类"] for cat in target_categories)):
                    recommendations.append(row)
        
        # 排序（优先价格接近预算的）
        try:
            recommendations.sort(key=lambda x: abs(int(x["价格区间"].split("-")[0].replace("元", "")) - budget_num))
        except (ValueError, IndexError) as e:
            logger.warning(f"[purchase_recommend_tool] 排序失败：{e}")
        
        # 生成推荐
        if not recommendations:
            # RAG 检索备选
            rag_gen = get_rag_generator()
            rag_result = await rag_gen.rag_summarize(f"{usage}笔记本推荐 预算{budget}") if rag_gen else "RAG 检索服务暂时不可用"
            return f"未找到完全匹配的型号，基于 RAG 检索建议：\n{rag_result}"
        
        result = f"【{usage}笔记本推荐（预算{budget}）】\n\n"
        
        for i, rec in enumerate(recommendations[:5], 1):  # 最多推荐 5 款
            result += f"【推荐{i}】{rec['型号']}\n"
            result += f"• 核心配置：{rec['CPU']} + {rec['GPU']}\n"
            result += f"• 屏幕：{rec['屏幕尺寸']} {rec['屏幕分辨率']} {rec['刷新率']}\n"
            result += f"• 价格：{rec['价格区间']}\n"
            result += f"• 推荐理由：{rec['用途分类']}定位，性价比突出\n"
            
            # 避坑点
            if "游戏本" in rec["用途分类"]:
                result += "• 避坑点：注意散热表现，建议搭配散热底座\n"
            elif "轻薄本" in rec["用途分类"]:
                result += "• 避坑点：扩展性有限，购买时确认内存硬盘是否够用\n"
            else:
                result += "• 避坑点：根据实际需求选择配置，避免性能过剩\n"
            
            result += "\n"
        
        return result
    
    except Exception as e:
        logger.error(f"[purchase_recommend_tool] 推荐失败：{str(e)}")
        return "推荐失败，请稍后重试"



@tool(description="性能计算工具：估算显卡功耗、游戏帧率、续航时间等。入参 gpu_model 为显卡型号（如'RTX 4060'），可选 game 为游戏名称。返回功耗值、预估帧率等数据。")
async def performance_calc_tool(gpu_model: str, game: str = None) -> str:
    """
    性能估算工具
    :param gpu_model: 显卡型号，如'RTX 4060'、'RTX 4070'
    :param game: 游戏名称（可选），如'赛博朋克 2077'、'原神'
    :return: 性能估算数据
    """
    # 内置常见硬件参数
    gpu_specs = {
        "RTX 4050": {"TDP": "75-115W", "game_fps": {"原神": "120+", "赛博朋克": "45-60"}},
        "RTX 4060": {"TDP": "100-140W", "game_fps": {"原神": "144+", "赛博朋克": "60-80"}},
        "RTX 4070": {"TDP": "100-140W", "game_fps": {"原神": "144+", "赛博朋克": "80-100"}},
        "RTX 4080": {"TDP": "150-175W", "game_fps": {"原神": "144+", "赛博朋克": "100-120"}},
        "RTX 4090": {"TDP": "150-175W", "game_fps": {"原神": "144+", "赛博朋克": "120+"}},
        "RTX 3050": {"TDP": "60-95W", "game_fps": {"原神": "80-100", "赛博朋克": "30-45"}},
        "RTX 3050Ti": {"TDP": "60-95W", "game_fps": {"原神": "90-110", "赛博朋克": "35-50"}},
        "RTX 3060": {"TDP": "80-130W", "game_fps": {"原神": "120+", "赛博朋克": "50-70"}},
        "RTX 3070": {"TDP": "80-125W", "game_fps": {"原神": "144+", "赛博朋克": "60-80"}},
        "RTX 3070Ti": {"TDP": "80-125W", "game_fps": {"原神": "144+", "赛博朋克": "70-90"}},
        "RTX 3080": {"TDP": "80-165W", "game_fps": {"原神": "144+", "赛博朋克": "80-100"}},
    }
    
    # 查找匹配的 GPU
    matched_gpu = None
    for key in gpu_specs:
        if key.lower() in gpu_model.lower():
            matched_gpu = key
            break
    
    if not matched_gpu:
        # RAG 检索
        rag_gen = get_rag_generator()
        rag_result = await rag_gen.rag_summarize(f"{gpu_model} 显卡功耗和性能") if rag_gen else "RAG 检索服务暂时不可用"
        return f"未找到'{gpu_model}'的详细数据，基于 RAG 检索：\n{rag_result}"
    
    gpu_data = gpu_specs[matched_gpu]
    
    result = f"【{matched_gpu} 性能估算】\n\n"
    result += f"【功耗范围】{gpu_data['TDP']}\n"
    # 从 TDP 字符串中提取最大功耗值（去除单位 W），避免转换失败
    tdp_max = int(''.join(c for c in gpu_data['TDP'].split('-')[1] if c.isdigit()))
    result += f"【建议电源】至少{tdp_max + 50}W 适配器\n"
    
    if game:
        fps_estimate = gpu_data["game_fps"].get(game, "未知")
        result += f"\n【{game}帧率估算】\n"
        result += f"• 1080P 高画质：约{fps_estimate} FPS\n"
        result += f"• 实际帧率受 CPU、内存、散热影响\n"
    else:
        result += "\n【游戏性能参考】\n"
        for game_name, fps in gpu_data["game_fps"].items():
            result += f"• {game_name}: 约{fps} FPS\n"
    
    result += "\n【注意事项】\n"
    result += "• 以上数据为笔记本移动版显卡\n"
    result += "• 实际性能因厂商调校而异\n"
    result += "• 温度墙会影响持续性能释放\n"
    
    return result

