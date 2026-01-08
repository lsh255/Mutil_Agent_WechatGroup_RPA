"""创建Excel模板文件"""
from openpyxl import Workbook
from openpyxl.styles import Font
from pathlib import Path


def create_template():
    """创建Excel台账模板"""
    wb = Workbook()
    ws = wb.active
    ws.title = "任务台账"
    
    # 设置表头
    headers = [
        "用户名",
        "任务ID",
        "任务阶段",
        "是否完成",
        "内容摘要",
        "提取信息1",
        "提取信息2",
        "提取信息3"
    ]
    
    # 写入表头
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True)
    
    # 保存模板
    template_path = Path("./templates/task_log.xlsx")
    template_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(template_path)
    
    print(f"Excel模板已创建: {template_path}")


if __name__ == "__main__":
    create_template()
