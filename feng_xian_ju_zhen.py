# 定义概率等级
probability = {
    "极少发生": 1,
    "很少发生": 2,
    "偶尔发生": 3,
    "有时发生": 4,
    "经常发生": 5
}

# 定义后果等级
severity = {
    "轻微": 1,
    "轻度": 2,
    "严重": 3,
    "灾难": 4
}


def calculate_risk_value(prob, sev):
    # 计算风险值，这里采用乘积模型
    return prob * sev


def determine_risk_level(risk_value):
    # 划分风险等级
    if risk_value <= 4:
        return "低风险"
    elif 5 <= risk_value <= 9:
        return "中风险"
    elif 10 <= risk_value <= 15:
        return "高风险"
    else:
        return "极高风险"


def get_probability_level():
    print("概率等级：")
    for level in probability:
        print(f"- {level}")
    while True:
        level = input("请输入概率等级：")
        if level in probability:
            return probability[level]
        else:
            print("输入无效，请重新输入。")


def get_severity_level():
    print("后果等级：")
    for level in severity:
        print(f"- {level}")
    while True:
        level = input("请输入后果等级：")
        if level in severity:
            return severity[level]
        else:
            print("输入无效，请重新输入。")


def main():
    print("风险评估程序")
    prob = get_probability_level()
    sev = get_severity_level()
    risk_value = calculate_risk_value(prob, sev)
    risk_level = determine_risk_level(risk_value)
    print(f"\n风险值：{risk_value}")
    print(f"风险等级：{risk_level}")


if __name__ == "__main__":
    main()
