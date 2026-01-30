"""
初始化演示数据
"""
from app.core.storage import storage
from app.core.capsule import CapsuleCreate


def init_demo_data():
    """初始化演示胶囊"""
    
    demos = [
        CapsuleCreate(
            title="量子纠缠的瞬时关联",
            domain="physics",
            topics=["quantum", "entanglement", "bell-test"],
            insight="量子纠缠展示了一种超越经典物理的瞬时关联，测量一个粒子会瞬时影响另一个纠缠粒子的状态",
            evidence=[
                "Bell 不等式实验已多次验证量子纠缠的非定域性",
                "2022 年诺贝尔物理学奖授予了量子纠缠实验的开创者",
                "量子隐形传态已实现了超过 100 公里的量子态传输"
            ],
            action_items=[
                "探索量子纠缠在量子计算中的应用",
                "设计更精确的 Bell 测试实验",
                "研究量子纠缠在量子通信安全中的角色"
            ],
            applicability="量子计算、量子通信、量子密码学",
            source_type="discussion",
            authors=["爱因斯坦", "玻尔", "贝尔"],
            license="MIT"
        ),
        CapsuleCreate(
            title="Transformer 架构的自注意力机制",
            domain="AI",
            topics=["transformer", "attention", "NLP"],
            insight="Transformer 的自注意力机制让模型能够在处理序列时动态地关注不同位置的信息",
            evidence=[
                "Attention Is All You Need 论文提出了 Transformer 架构",
                "GPT、BERT 等大模型都基于 Transformer",
                "多头注意力可以捕捉不同类型的语义关系"
            ],
            action_items=[
                "在具体任务中尝试不同的注意力掩码策略",
                "探索稀疏注意力机制以提升长序列效率",
                "研究注意力权重的可解释性"
            ],
            applicability="自然语言处理、计算机视觉、多模态模型",
            source_type="discussion",
            authors=["Vaswani", "Shazeer", "Parikh"],
            license="MIT"
        ),
        CapsuleCreate(
            title="气候变化对农业的多维影响",
            domain="climate",
            topics=["climate-change", "agriculture", "food-security"],
            insight="气候变化通过温度升高、降水模式改变和极端天气，影响全球农业生产的稳定性和产量",
            evidence=[
                "IPCC 报告预测 2050 年全球粮食产量可能下降 10-25%",
                "极端干旱导致 2012 年美国玉米产量下降 27%",
                "海平面上升威胁沿海地区的农田和淡水资源的盐碱化"
            ],
            action_items=[
                "推广抗旱作物品种的研发和种植",
                "发展精准灌溉和智慧农业技术",
                "建立气候适应性农业政策支持体系"
            ],
            applicability="农业政策、粮食安全、可持续农业",
            source_type="discussion",
            authors=["IPCC专家组", "农业科学家"],
            license="CC-BY-4.0"
        )
    ]
    
    capsules = []
    for demo in demos:
        capsule = storage.create(demo)
        capsules.append(capsule)
        print(f"Created: {capsule.title} (Grade: {capsule.overall_grade}, Score: {capsule.overall_score:.1f})")
    
    return capsules


if __name__ == "__main__":
    print("Initializing demo data...")
    init_demo_data()
    print("\nDone!")
