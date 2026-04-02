"""生成100封假邮件数据和对应附件文件。"""

import csv
import io
import json
import os
import random
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

from docx import Document
from openpyxl import Workbook
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation as PptxPresentation
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas

# 路径配置
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EMAILS_DIR = DATA_DIR / "emails"
ATTACHMENTS_DIR = DATA_DIR / "attachments"

# ============================================================
# 人员和公司数据
# ============================================================
PEOPLE = [
    {"name": "张三", "email": "zhangsan@techcorp.com", "dept": "技术部"},
    {"name": "李四", "email": "lisi@techcorp.com", "dept": "销售部"},
    {"name": "王五", "email": "wangwu@techcorp.com", "dept": "财务部"},
    {"name": "赵六", "email": "zhaoliu@techcorp.com", "dept": "人事部"},
    {"name": "孙七", "email": "sunqi@techcorp.com", "dept": "市场部"},
    {"name": "周八", "email": "zhouba@techcorp.com", "dept": "产品部"},
    {"name": "吴九", "email": "wujiu@techcorp.com", "dept": "运维部"},
    {"name": "郑十", "email": "zhengshi@techcorp.com", "dept": "法务部"},
    {"name": "钱磊", "email": "qianlei@techcorp.com", "dept": "技术部"},
    {"name": "陈静", "email": "chenjing@techcorp.com", "dept": "销售部"},
    {"name": "林涛", "email": "lintao@techcorp.com", "dept": "技术部"},
    {"name": "黄蕾", "email": "huanglei@techcorp.com", "dept": "财务部"},
    {"name": "刘洋", "email": "liuyang@clientcorp.com", "dept": "客户方"},
    {"name": "杨帆", "email": "yangfan@clientcorp.com", "dept": "客户方"},
    {"name": "马丽", "email": "mali@partnercorp.com", "dept": "合作方"},
]


def pick_sender():
    return random.choice(PEOPLE)


def pick_recipients(exclude_email, count=None):
    count = count or random.randint(1, 3)
    pool = [p for p in PEOPLE if p["email"] != exclude_email]
    return random.sample(pool, min(count, len(pool)))


def random_date(start_year=2024):
    start = datetime(start_year, 1, 1)
    delta = timedelta(days=random.randint(0, 450))
    return (start + delta).strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# 附件生成器
# ============================================================

def make_pdf(filepath: str, title: str, content: str):
    c = pdf_canvas.Canvas(filepath, pagesize=A4)
    c.setFont("Helvetica", 16)
    c.drawString(72, 750, title)
    c.setFont("Helvetica", 11)
    y = 720
    for line in content.split("\n"):
        if y < 72:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = 750
        c.drawString(72, y, line)
        y -= 16
    c.save()


def make_docx(filepath: str, title: str, content: str):
    doc = Document()
    doc.add_heading(title, level=1)
    for para in content.split("\n\n"):
        doc.add_paragraph(para)
    doc.save(filepath)


def make_xlsx(filepath: str, title: str, rows: list[list]):
    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]
    for row in rows:
        ws.append(row)
    wb.save(filepath)


def make_pptx(filepath: str, title: str, slides_content: list[tuple[str, str]]):
    prs = PptxPresentation()
    # Title slide
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = title
    slide.placeholders[1].text = "TechCorp Internal"
    # Content slides
    for slide_title, slide_body in slides_content:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = slide_title
        slide.placeholders[1].text = slide_body
    prs.save(filepath)


def make_csv_file(filepath: str, headers: list[str], rows: list[list]):
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def make_txt(filepath: str, content: str):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def make_png(filepath: str, text: str, size=(400, 300)):
    img = Image.new("RGB", size, color=(240, 240, 245))
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, size[0] - 10, size[1] - 10], outline=(100, 100, 200), width=2)
    draw.text((20, 20), text, fill=(50, 50, 50))
    img.save(filepath)


def make_jpg(filepath: str, text: str, size=(400, 300)):
    img = Image.new("RGB", size, color=(255, 250, 240))
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), text, fill=(80, 40, 40))
    img.save(filepath, "JPEG")


def make_zip(filepath: str, files_content: dict[str, str]):
    with zipfile.ZipFile(filepath, "w") as zf:
        for name, content in files_content.items():
            zf.writestr(name, content)


# ============================================================
# 邮件模板 — 8个业务场景
# ============================================================

def gen_project_emails(start_id: int) -> list[dict]:
    """项目进度汇报 — 15封"""
    emails = []
    projects = ["Phoenix", "Aurora", "Titan", "Neptune", "Atlas"]
    report_types = ["周报", "月度汇报", "里程碑报告"]

    for i in range(15):
        eid = f"email_{start_id + i:03d}"
        proj = projects[i % len(projects)]
        rtype = report_types[i % len(report_types)]
        sender = pick_sender()
        recipients = pick_recipients(sender["email"])
        date = random_date()
        subject = f"{proj}项目{rtype} - {date[:7]}"

        body_text = (
            f"各位好，\n\n以下是{proj}项目的{rtype}：\n\n"
            f"1. 本周完成了核心模块的开发和测试\n"
            f"2. 解决了3个关键bug，系统稳定性提升20%\n"
            f"3. 与客户完成了第{i+1}轮需求确认\n"
            f"4. 下周计划进入集成测试阶段\n\n"
            f"详情见附件。\n\n{sender['name']}"
        )

        attachments = []
        if i % 3 == 0:
            fname = f"{proj}_progress_{i+1}.docx"
            att_path = str(ATTACHMENTS_DIR / fname)
            make_docx(att_path, f"{proj}项目{rtype}", (
                f"{proj}项目进度报告\n\n"
                f"报告周期: {date[:7]}\n\n"
                f"一、工作完成情况\n\n"
                f"本周期内，{proj}项目团队完成了以下工作：\n"
                f"- 完成了用户认证模块的开发，支持OAuth2.0和SAML\n"
                f"- 数据库性能优化，查询速度提升35%\n"
                f"- 前端页面重构，用户体验评分从7.2提升到8.5\n"
                f"- 修复了{random.randint(5, 15)}个已知缺陷\n\n"
                f"二、风险与问题\n\n"
                f"- 第三方API接口响应时间不稳定，需要增加缓存层\n"
                f"- 新需求可能影响原有排期\n\n"
                f"三、下阶段计划\n\n"
                f"- 集成测试\n- 性能压测\n- 用户验收测试"
            ))
            attachments.append({"filename": fname, "type": "docx"})
        elif i % 3 == 1:
            fname = f"{proj}_presentation_{i+1}.pptx"
            att_path = str(ATTACHMENTS_DIR / fname)
            make_pptx(att_path, f"{proj} Project Update", [
                ("Progress Overview", f"Sprint {i+1} completed\nVelocity: {random.randint(20,40)} story points\nBurn-down on track"),
                ("Key Achievements", f"- Module A delivered\n- Performance improved {random.randint(10,50)}%\n- Zero critical bugs in production"),
                ("Next Steps", "- Integration testing\n- Security audit\n- UAT preparation"),
            ])
            attachments.append({"filename": fname, "type": "pptx"})
        else:
            fname = f"{proj}_tasks_{i+1}.xlsx"
            att_path = str(ATTACHMENTS_DIR / fname)
            make_xlsx(att_path, "Tasks", [
                ["Task ID", "Task Name", "Status", "Assignee", "Due Date"],
                [f"T-{i*10+1}", "Backend API development", "Completed", sender["name"], date[:10]],
                [f"T-{i*10+2}", "Frontend integration", "In Progress", recipients[0]["name"], date[:10]],
                [f"T-{i*10+3}", "Database optimization", "Completed", sender["name"], date[:10]],
                [f"T-{i*10+4}", "Unit testing", "In Progress", recipients[0]["name"], date[:10]],
                [f"T-{i*10+5}", "Documentation", "Pending", sender["name"], date[:10]],
            ])
            attachments.append({"filename": fname, "type": "xlsx"})

        emails.append({
            "id": eid,
            "from": {"name": sender["name"], "email": sender["email"]},
            "to": [{"name": r["name"], "email": r["email"]} for r in recipients],
            "cc": [],
            "subject": subject,
            "body": body_text,
            "date": date,
            "tags": ["项目", proj],
            "attachments": attachments,
        })
    return emails


def gen_finance_emails(start_id: int) -> list[dict]:
    """财务/销售报表 — 15封"""
    emails = []
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    report_names = ["销售报告", "预算执行表", "成本分析", "收入统计", "利润报表"]

    for i in range(15):
        eid = f"email_{start_id + i:03d}"
        q = quarters[i % 4]
        rname = report_names[i % 5]
        sender = pick_sender()
        recipients = pick_recipients(sender["email"])
        date = random_date()
        year = date[:4]
        subject = f"{year}年{q}{rname}"

        revenue = random.randint(500, 2000)
        cost = random.randint(200, 800)
        profit = revenue - cost

        body_text = (
            f"各位领导好，\n\n"
            f"附件为{year}年{q}的{rname}，请查阅。\n\n"
            f"本季度概要：\n"
            f"- 营收：{revenue}万元，同比增长{random.randint(5,30)}%\n"
            f"- 成本：{cost}万元\n"
            f"- 净利润：{profit}万元\n"
            f"- 新签客户：{random.randint(10,50)}家\n\n"
            f"如有疑问请随时沟通。\n\n{sender['name']}"
        )

        attachments = []
        if i % 3 == 0:
            fname = f"finance_{q}_{year}_{i+1}.xlsx"
            att_path = str(ATTACHMENTS_DIR / fname)
            months = [f"{q[1]}月{j}" for j in ["上旬", "中旬", "下旬"]]
            make_xlsx(att_path, f"{q} Finance", [
                ["Period", "Revenue (万)", "Cost (万)", "Profit (万)", "Growth %"],
                [months[0], revenue // 3, cost // 3, profit // 3, f"{random.randint(5,25)}%"],
                [months[1], revenue // 3 + 10, cost // 3, profit // 3 + 10, f"{random.randint(5,25)}%"],
                [months[2], revenue // 3 + 20, cost // 3 - 5, profit // 3 + 25, f"{random.randint(5,25)}%"],
                ["Total", revenue, cost, profit, f"{random.randint(10,30)}%"],
            ])
            attachments.append({"filename": fname, "type": "xlsx"})
        elif i % 3 == 1:
            fname = f"finance_{q}_{year}_{i+1}.pdf"
            att_path = str(ATTACHMENTS_DIR / fname)
            make_pdf(att_path, f"{year} {q} Financial Report", (
                f"Financial Summary for {q} {year}\n\n"
                f"Total Revenue: {revenue}0,000 RMB\n"
                f"Total Cost: {cost}0,000 RMB\n"
                f"Net Profit: {profit}0,000 RMB\n"
                f"YoY Growth: {random.randint(5,30)}%\n\n"
                f"Key Highlights:\n"
                f"- New client acquisition exceeded targets by {random.randint(10,40)}%\n"
                f"- Operating costs reduced through process optimization\n"
                f"- Subscription revenue grew {random.randint(15,45)}% quarter-over-quarter"
            ))
            attachments.append({"filename": fname, "type": "pdf"})
        else:
            fname = f"sales_data_{q}_{year}_{i+1}.csv"
            att_path = str(ATTACHMENTS_DIR / fname)
            make_csv_file(att_path,
                ["Client", "Product", "Amount (万)", "Region", "Sales Rep"],
                [
                    [f"Client_{j}", random.choice(["Enterprise", "Standard", "Premium"]),
                     str(random.randint(10, 200)), random.choice(["华东", "华北", "华南", "西南"]),
                     random.choice([p["name"] for p in PEOPLE[:5]])]
                    for j in range(random.randint(8, 15))
                ]
            )
            attachments.append({"filename": fname, "type": "csv"})

        emails.append({
            "id": eid,
            "from": {"name": sender["name"], "email": sender["email"]},
            "to": [{"name": r["name"], "email": r["email"]} for r in recipients],
            "cc": [{"name": PEOPLE[4]["name"], "email": PEOPLE[4]["email"]}],
            "subject": subject,
            "body": body_text,
            "date": date,
            "tags": ["财务", rname],
            "attachments": attachments,
        })
    return emails


def gen_meeting_emails(start_id: int) -> list[dict]:
    """会议纪要 — 12封"""
    emails = []
    meeting_types = ["周会", "技术评审会", "产品规划会", "部门例会", "战略研讨会", "复盘会"]

    for i in range(12):
        eid = f"email_{start_id + i:03d}"
        mtype = meeting_types[i % len(meeting_types)]
        sender = pick_sender()
        recipients = pick_recipients(sender["email"], count=random.randint(3, 6))
        date = random_date()
        week_num = random.randint(1, 52)
        subject = f"第{week_num}周{mtype}纪要"

        body_text = (
            f"各位同事，\n\n"
            f"以下是本次{mtype}的会议纪要，详细内容见附件。\n\n"
            f"会议时间：{date}\n"
            f"参会人员：{', '.join(r['name'] for r in recipients)}\n\n"
            f"主要议题：\n"
            f"1. {random.choice(['系统性能优化方案讨论', 'Q3目标回顾与Q4规划', '新产品线规划', '客户反馈处理流程优化'])}\n"
            f"2. {random.choice(['人员招聘进度', '技术债务清理', '用户增长策略', '预算调整'])}\n"
            f"3. {random.choice(['跨部门协作流程', '代码审查规范', '客户满意度提升', '成本控制措施'])}\n\n"
            f"Action Items 见附件。\n\n{sender['name']}"
        )

        attachments = []
        if i % 2 == 0:
            fname = f"meeting_minutes_w{week_num}_{i+1}.docx"
            att_path = str(ATTACHMENTS_DIR / fname)
            make_docx(att_path, f"第{week_num}周{mtype}纪要", (
                f"会议纪要\n\n"
                f"会议类型：{mtype}\n"
                f"会议时间：{date}\n"
                f"主持人：{sender['name']}\n"
                f"参会人：{', '.join(r['name'] for r in recipients)}\n\n"
                f"一、议题讨论\n\n"
                f"1. 系统优化方案\n"
                f"经讨论，决定采用微服务架构重构现有系统。预计分三个阶段完成，第一阶段重点优化数据库查询性能。\n\n"
                f"2. 人员安排\n"
                f"新招聘的两名高级工程师将于下月入职，分配至{random.choice(['前端', '后端', '数据'])}团队。\n\n"
                f"二、Action Items\n\n"
                f"- {recipients[0]['name']}：完成技术方案文档，截止{date[:8]}28\n"
                f"- {sender['name']}：协调资源分配\n"
                f"- {recipients[-1]['name']}：更新项目排期"
            ))
            attachments.append({"filename": fname, "type": "docx"})
        else:
            fname = f"meeting_notes_w{week_num}_{i+1}.txt"
            att_path = str(ATTACHMENTS_DIR / fname)
            make_txt(att_path, (
                f"== {mtype} 第{week_num}周 ==\n"
                f"日期: {date}\n"
                f"主持: {sender['name']}\n\n"
                f"讨论要点:\n"
                f"- 上周任务完成率: {random.randint(70,100)}%\n"
                f"- 未完成事项: 接口联调、自动化测试用例补充\n"
                f"- 本周重点: 性能压测、上线前checklist确认\n\n"
                f"决议:\n"
                f"1. 增加代码review频率，每个PR至少2人审核\n"
                f"2. 启动自动化测试覆盖率提升计划，目标80%\n"
                f"3. 下周三进行全链路压测\n\n"
                f"下次会议: 下周{random.choice(['一', '三', '五'])} 10:00"
            ))
            attachments.append({"filename": fname, "type": "txt"})

        emails.append({
            "id": eid,
            "from": {"name": sender["name"], "email": sender["email"]},
            "to": [{"name": r["name"], "email": r["email"]} for r in recipients],
            "cc": [],
            "subject": subject,
            "body": body_text,
            "date": date,
            "tags": ["会议", mtype],
            "attachments": attachments,
        })
    return emails


def gen_legal_emails(start_id: int) -> list[dict]:
    """合同/法务 — 10封"""
    emails = []
    contract_types = ["服务协议", "采购合同", "保密协议(NDA)", "合作框架协议", "软件许可协议",
                      "数据处理协议", "竞业禁止协议", "劳动合同补充", "知识产权协议", "外包服务合同"]

    for i in range(10):
        eid = f"email_{start_id + i:03d}"
        ctype = contract_types[i]
        sender = pick_sender()
        recipients = pick_recipients(sender["email"])
        date = random_date()
        contract_no = f"CT-{date[:4]}-{random.randint(1000,9999)}"
        subject = f"[法务] {ctype} - {contract_no}"

        body_text = (
            f"您好，\n\n"
            f"附件为{ctype}（合同编号：{contract_no}），请审阅。\n\n"
            f"合同要点：\n"
            f"- 合同期限：{random.choice(['1年', '2年', '3年'])}\n"
            f"- 合同金额：{random.randint(10, 500)}万元\n"
            f"- 生效日期：{date[:10]}\n"
            f"- 付款方式：{random.choice(['月付', '季付', '年付', '里程碑付款'])}\n\n"
            f"请在{random.randint(3,7)}个工作日内完成审阅并反馈意见。\n\n{sender['name']}\n法务部"
        )

        attachments = []
        if i % 2 == 0:
            fname = f"contract_{contract_no}.pdf"
            att_path = str(ATTACHMENTS_DIR / fname)
            make_pdf(att_path, f"Contract {contract_no}", (
                f"{ctype}\n\n"
                f"Contract No: {contract_no}\n"
                f"Date: {date[:10]}\n\n"
                f"ARTICLE 1 - DEFINITIONS\n"
                f"This agreement defines the terms and conditions between TechCorp and the counterparty.\n\n"
                f"ARTICLE 2 - SCOPE OF SERVICES\n"
                f"The service provider shall deliver software development and maintenance services.\n\n"
                f"ARTICLE 3 - PAYMENT TERMS\n"
                f"Payment shall be made within 30 days of invoice receipt.\n\n"
                f"ARTICLE 4 - CONFIDENTIALITY\n"
                f"Both parties agree to maintain strict confidentiality of all shared information.\n\n"
                f"ARTICLE 5 - TERM AND TERMINATION\n"
                f"This agreement shall remain in effect for the specified contract period."
            ))
            attachments.append({"filename": fname, "type": "pdf"})
        else:
            fname = f"contract_{contract_no}.docx"
            att_path = str(ATTACHMENTS_DIR / fname)
            make_docx(att_path, f"{ctype} - {contract_no}", (
                f"合同编号：{contract_no}\n签订日期：{date[:10]}\n\n"
                f"甲方：TechCorp 科技有限公司\n"
                f"乙方：[对方公司名称]\n\n"
                f"第一条 合同目的\n\n"
                f"本合同旨在明确双方在{ctype}相关事务中的权利和义务。\n\n"
                f"第二条 服务内容\n\n"
                f"乙方应按照甲方要求提供相关服务，确保服务质量符合行业标准。\n\n"
                f"第三条 费用与支付\n\n"
                f"合同总金额为人民币{random.randint(10,500)}万元整，按约定方式支付。\n\n"
                f"第四条 保密条款\n\n"
                f"双方应对在合同执行过程中知悉的对方商业秘密严格保密。"
            ))
            attachments.append({"filename": fname, "type": "docx"})

        emails.append({
            "id": eid,
            "from": {"name": sender["name"], "email": sender["email"]},
            "to": [{"name": r["name"], "email": r["email"]} for r in recipients],
            "cc": [{"name": PEOPLE[7]["name"], "email": PEOPLE[7]["email"]}],
            "subject": subject,
            "body": body_text,
            "date": date,
            "tags": ["法务", "合同"],
            "attachments": attachments,
        })
    return emails


def gen_tech_emails(start_id: int) -> list[dict]:
    """技术文档 — 12封"""
    emails = []
    topics = [
        ("微服务架构设计文档", "architecture"),
        ("API接口规范 v2.0", "api_spec"),
        ("数据库设计说明书", "db_design"),
        ("部署运维手册", "deployment"),
        ("安全审计报告", "security"),
        ("性能测试报告", "perf_test"),
        ("技术选型评估", "tech_eval"),
        ("代码规范指南", "code_style"),
        ("灾备方案", "disaster_recovery"),
        ("监控告警方案", "monitoring"),
        ("CI/CD流水线配置", "cicd"),
        ("容器化迁移方案", "containerization"),
    ]

    for i in range(12):
        eid = f"email_{start_id + i:03d}"
        topic_name, topic_key = topics[i]
        sender = pick_sender()
        recipients = pick_recipients(sender["email"])
        date = random_date()
        version = f"v{random.randint(1,3)}.{random.randint(0,9)}"
        subject = f"[技术] {topic_name} {version}"

        body_text = (
            f"Hi all,\n\n"
            f"附件是最新版本的{topic_name}（{version}），主要更新：\n\n"
            f"1. 根据上次评审意见修改了架构方案\n"
            f"2. 补充了异常处理和降级策略\n"
            f"3. 更新了技术栈版本号\n\n"
            f"请大家review后提出意见，计划在本周五前定稿。\n\n{sender['name']}"
        )

        attachments = []
        if i % 4 == 0:
            fname = f"tech_{topic_key}_{version}.pdf"
            att_path = str(ATTACHMENTS_DIR / fname)
            make_pdf(att_path, f"{topic_name} {version}", (
                f"Technical Document: {topic_name}\n"
                f"Version: {version}\n"
                f"Author: {sender['name']}\n"
                f"Date: {date[:10]}\n\n"
                f"1. Overview\n"
                f"This document describes the technical architecture and implementation details.\n\n"
                f"2. System Architecture\n"
                f"The system adopts a microservices architecture with the following components:\n"
                f"- API Gateway (Kong/Nginx)\n"
                f"- Service Discovery (Consul)\n"
                f"- Message Queue (RabbitMQ)\n"
                f"- Cache Layer (Redis)\n"
                f"- Database (PostgreSQL + MongoDB)\n\n"
                f"3. Performance Requirements\n"
                f"- API Response Time: < 200ms (P99)\n"
                f"- Throughput: > 10000 QPS\n"
                f"- Availability: 99.99%"
            ))
            attachments.append({"filename": fname, "type": "pdf"})
        elif i % 4 == 1:
            fname = f"tech_{topic_key}_{version}.txt"
            att_path = str(ATTACHMENTS_DIR / fname)
            make_txt(att_path, (
                f"# {topic_name} {version}\n\n"
                f"## 概述\n"
                f"本文档详细描述了系统的技术方案和实施细节。\n\n"
                f"## 技术栈\n"
                f"- 后端: Python 3.12 + FastAPI\n"
                f"- 前端: React 18 + TypeScript\n"
                f"- 数据库: PostgreSQL 16\n"
                f"- 缓存: Redis 7\n"
                f"- 消息队列: RabbitMQ 3.12\n\n"
                f"## 接口设计\n"
                f"RESTful API 风格，JSON 数据格式\n"
                f"认证方式: JWT Token\n"
                f"限流策略: 令牌桶算法，100次/分钟\n\n"
                f"## 部署方案\n"
                f"Kubernetes 集群部署，Docker 容器化\n"
                f"CI/CD: GitHub Actions\n"
                f"监控: Prometheus + Grafana"
            ))
            attachments.append({"filename": fname, "type": "txt"})
        elif i % 4 == 2:
            fname = f"tech_{topic_key}_{version}.zip"
            att_path = str(ATTACHMENTS_DIR / fname)
            make_zip(att_path, {
                "README.md": f"# {topic_name}\n\nVersion: {version}\n\nSee docs/ folder for details.",
                "docs/overview.md": f"# Overview\n\nThis project implements {topic_name}.",
                "docs/api.md": "# API Reference\n\n## GET /api/health\nReturns service health status.\n\n## POST /api/data\nSubmit data for processing.",
                "config/settings.yaml": f"app:\n  name: {topic_key}\n  version: {version}\n  debug: false\n  port: 8080",
            })
            attachments.append({"filename": fname, "type": "zip"})
        else:
            fname = f"tech_{topic_key}_{version}.pdf"
            att_path = str(ATTACHMENTS_DIR / fname)
            make_pdf(att_path, f"{topic_name}", (
                f"Document: {topic_name} {version}\n\n"
                f"1. Background\n"
                f"Current system faces scalability challenges.\n\n"
                f"2. Proposed Solution\n"
                f"Migrate to cloud-native architecture with auto-scaling.\n\n"
                f"3. Implementation Plan\n"
                f"Phase 1: Containerization (2 weeks)\n"
                f"Phase 2: Orchestration (3 weeks)\n"
                f"Phase 3: Monitoring setup (1 week)\n\n"
                f"4. Risk Assessment\n"
                f"- Data migration risks: Medium\n"
                f"- Service disruption: Low (blue-green deployment)\n"
                f"- Cost increase: Temporary, offset by efficiency gains"
            ))
            attachments.append({"filename": fname, "type": "pdf"})

        emails.append({
            "id": eid,
            "from": {"name": sender["name"], "email": sender["email"]},
            "to": [{"name": r["name"], "email": r["email"]} for r in recipients],
            "cc": [],
            "subject": subject,
            "body": body_text,
            "date": date,
            "tags": ["技术", topic_key],
            "attachments": attachments,
        })
    return emails


def gen_hr_emails(start_id: int) -> list[dict]:
    """人事行政 — 10封"""
    emails = []
    hr_topics = [
        "月度考勤统计", "培训计划通知", "年度体检安排", "绩效考核通知",
        "员工活动通知", "办公用品采购", "新员工入职指南", "假期安排通知",
        "薪酬调整通知", "部门组织架构调整",
    ]

    for i in range(10):
        eid = f"email_{start_id + i:03d}"
        topic = hr_topics[i]
        sender = PEOPLE[3]  # 赵六 from HR
        recipients = pick_recipients(sender["email"], count=random.randint(3, 8))
        date = random_date()
        month = random.randint(1, 12)
        subject = f"[人事] {topic} - {date[:4]}年{month}月"

        body_text = (
            f"全体同事好，\n\n"
            f"现发送{date[:4]}年{month}月{topic}，详情见附件。\n\n"
        )

        if "考勤" in topic:
            body_text += "请各位核对个人考勤数据，如有异议请于3个工作日内反馈。\n"
        elif "培训" in topic:
            body_text += f"本次培训主题为「{random.choice(['项目管理', 'AI应用', '沟通技巧', '领导力'])}」，请相关同事准时参加。\n"
        elif "绩效" in topic:
            body_text += "请各部门经理于月底前完成绩效评估并提交。\n"

        body_text += f"\n谢谢！\n{sender['name']}\n人事行政部"

        attachments = []
        if i % 2 == 0:
            fname = f"hr_{topic.replace('/', '_')}_{month}_{i+1}.xlsx"
            att_path = str(ATTACHMENTS_DIR / fname)
            make_xlsx(att_path, topic[:31], [
                ["Employee", "Department", "Working Days", "Leave Days", "Overtime (hrs)", "Status"],
                *[
                    [p["name"], p["dept"], random.randint(18, 23), random.randint(0, 3),
                     random.randint(0, 20), random.choice(["Normal", "Late 1x", "Normal"])]
                    for p in PEOPLE[:10]
                ],
            ])
            attachments.append({"filename": fname, "type": "xlsx"})
        else:
            fname = f"hr_{topic.replace('/', '_')}_{month}_{i+1}.pdf"
            att_path = str(ATTACHMENTS_DIR / fname)
            make_pdf(att_path, f"{topic} - {date[:4]}年{month}月", (
                f"TechCorp Human Resources\n"
                f"{topic}\n\n"
                f"Date: {date[:4]}-{month:02d}\n\n"
                f"Details:\n"
                f"- Applicable to all employees\n"
                f"- Effective from {date[:10]}\n"
                f"- Please review and acknowledge\n\n"
                f"Contact HR department for questions."
            ))
            attachments.append({"filename": fname, "type": "pdf"})

        emails.append({
            "id": eid,
            "from": {"name": sender["name"], "email": sender["email"]},
            "to": [{"name": r["name"], "email": r["email"]} for r in recipients],
            "cc": [],
            "subject": subject,
            "body": body_text,
            "date": date,
            "tags": ["人事", topic],
            "attachments": attachments,
        })
    return emails


def gen_daily_emails(start_id: int) -> list[dict]:
    """日常沟通 — 12封"""
    emails = []
    topics = [
        ("线上问题反馈：用户登录异常", "login_issue"),
        ("产品截图确认", "screenshot_review"),
        ("环境配置问题求助", "env_config"),
        ("代码Review意见", "code_review"),
        ("接口联调问题", "api_debug"),
        ("测试环境故障通知", "test_env"),
        ("功能验收反馈", "acceptance"),
        ("UI设计稿确认", "ui_design"),
        ("数据库慢查询告警", "slow_query"),
        ("上线checklist确认", "deploy_check"),
        ("Bug修复进度同步", "bug_fix"),
        ("需求变更沟通", "req_change"),
    ]

    for i in range(12):
        eid = f"email_{start_id + i:03d}"
        topic_name, topic_key = topics[i]
        sender = pick_sender()
        recipients = pick_recipients(sender["email"], count=random.randint(1, 3))
        date = random_date()
        subject = topic_name

        body_text = (
            f"Hi {recipients[0]['name']}，\n\n"
        )

        attachments = []
        if "截图" in topic_name or "UI" in topic_name:
            body_text += (
                f"附件是相关截图，请确认是否符合预期。\n\n"
                f"具体问题：\n"
                f"1. 页面{random.choice(['顶部导航栏', '侧边栏', '弹窗', '列表页'])}样式需要调整\n"
                f"2. {random.choice(['字体大小', '间距', '颜色', '对齐方式'])}与设计稿不一致\n"
            )
            if "截图" in topic_name:
                fname = f"screenshot_{topic_key}_{i+1}.png"
                att_path = str(ATTACHMENTS_DIR / fname)
                make_png(att_path, f"Screenshot: {topic_name}\n\nUI Element Preview\nVersion: {date[:10]}")
                attachments.append({"filename": fname, "type": "png"})
            else:
                fname = f"screenshot_{topic_key}_{i+1}.jpg"
                att_path = str(ATTACHMENTS_DIR / fname)
                make_jpg(att_path, f"Screenshot: {topic_name}\n\nDesign Review\n{date[:10]}")
                attachments.append({"filename": fname, "type": "jpg"})
        else:
            body_text += (
                f"关于{topic_name}的情况说明：\n\n"
                f"现象：{random.choice(['接口超时', '页面白屏', '数据不一致', '功能异常'])}，"
                f"影响范围：{random.choice(['部分用户', '全量用户', '测试环境', '内部系统'])}。\n\n"
                f"初步分析原因是{random.choice(['配置错误', '代码逻辑问题', '第三方服务异常', '数据库连接池满'])}，"
                f"目前正在排查中。\n\n"
                f"预计{random.choice(['1小时', '2小时', '半天', '今天'])}内修复。\n"
            )

        body_text += f"\n{sender['name']}"

        emails.append({
            "id": eid,
            "from": {"name": sender["name"], "email": sender["email"]},
            "to": [{"name": r["name"], "email": r["email"]} for r in recipients],
            "cc": [],
            "subject": subject,
            "body": body_text,
            "date": date,
            "tags": ["日常沟通"],
            "attachments": attachments,
        })
    return emails


def gen_client_emails(start_id: int) -> list[dict]:
    """客户往来 — 14封"""
    emails = []
    clients = ["CloudMax", "DataPeak", "SmartFlow", "NetWave", "InfoLink", "DigiCore", "ByteRun"]
    doc_types = [
        ("报价单", "quotation"), ("需求确认书", "requirements"),
        ("验收报告", "acceptance"), ("技术方案", "proposal"),
        ("项目计划", "plan"), ("变更申请", "change_request"),
        ("服务协议", "service_agreement"),
    ]

    for i in range(14):
        eid = f"email_{start_id + i:03d}"
        client = clients[i % len(clients)]
        doc_name, doc_key = doc_types[i % len(doc_types)]
        sender = pick_sender()
        recipients = pick_recipients(sender["email"])
        date = random_date()
        project_code = f"PRJ-{random.randint(100,999)}"
        subject = f"[{client}] {doc_name} - {project_code}"

        body_text = (
            f"Dear {recipients[0]['name']}，\n\n"
            f"附件为{client}项目（{project_code}）的{doc_name}，请查阅。\n\n"
        )

        if "报价" in doc_name:
            total = random.randint(50, 800)
            body_text += (
                f"本次报价总金额：{total}万元\n"
                f"有效期：30天\n"
                f"包含：软件开发、测试、部署及3个月免费维护期\n"
            )
        elif "验收" in doc_name:
            body_text += (
                f"项目已完成全部交付物，主要成果：\n"
                f"- 系统功能{random.randint(95,100)}%完成\n"
                f"- 测试用例通过率{random.randint(97,100)}%\n"
                f"- 性能指标全部达标\n"
            )
        elif "需求" in doc_name:
            body_text += (
                f"经与{client}确认，需求要点如下：\n"
                f"- 用户管理模块：支持RBAC权限体系\n"
                f"- 数据分析模块：实时报表和数据可视化\n"
                f"- 系统对接：与现有ERP系统API对接\n"
            )
        else:
            body_text += f"请在收到后3个工作日内反馈意见。\n"

        body_text += f"\n祝好！\n{sender['name']}"

        attachments = []
        if i % 3 == 0:
            fname = f"client_{client}_{doc_key}_{project_code}.pdf"
            att_path = str(ATTACHMENTS_DIR / fname)
            make_pdf(att_path, f"{client} - {doc_name}", (
                f"Client: {client}\n"
                f"Project: {project_code}\n"
                f"Document: {doc_name}\n"
                f"Date: {date[:10]}\n\n"
                f"1. Project Scope\n"
                f"Development of enterprise management system including:\n"
                f"- User authentication and authorization\n"
                f"- Business process management\n"
                f"- Data analytics and reporting\n"
                f"- System integration via REST APIs\n\n"
                f"2. Deliverables\n"
                f"- Source code and documentation\n"
                f"- Test reports\n"
                f"- Deployment guide\n"
                f"- Training materials"
            ))
            attachments.append({"filename": fname, "type": "pdf"})
        elif i % 3 == 1:
            fname = f"client_{client}_{doc_key}_{project_code}.docx"
            att_path = str(ATTACHMENTS_DIR / fname)
            make_docx(att_path, f"{client} - {doc_name}", (
                f"项目编号：{project_code}\n客户：{client}\n日期：{date[:10]}\n\n"
                f"一、项目概述\n\n"
                f"为{client}开发企业级管理系统，涵盖用户管理、业务流程、数据分析等模块。\n\n"
                f"二、具体内容\n\n"
                f"1. 功能需求：{random.randint(15,30)}个功能模块\n"
                f"2. 非功能需求：支持{random.randint(500,5000)}并发用户\n"
                f"3. 交付周期：{random.randint(2,6)}个月\n\n"
                f"三、费用明细\n\n"
                f"开发费用：{random.randint(30,300)}万元\n"
                f"维护费用：{random.randint(5,30)}万元/年"
            ))
            attachments.append({"filename": fname, "type": "docx"})
        else:
            fname = f"client_{client}_{doc_key}_{project_code}.xlsx"
            att_path = str(ATTACHMENTS_DIR / fname)
            make_xlsx(att_path, doc_name[:31], [
                ["Item", "Description", "Quantity", "Unit Price (万)", "Total (万)"],
                ["Software Development", "Custom development", 1, random.randint(50, 200), random.randint(50, 200)],
                ["Testing", "QA and testing", 1, random.randint(10, 30), random.randint(10, 30)],
                ["Deployment", "Production deployment", 1, random.randint(5, 15), random.randint(5, 15)],
                ["Training", "User training", random.randint(2, 5), 2, random.randint(4, 10)],
                ["Maintenance", "Annual maintenance", 1, random.randint(10, 50), random.randint(10, 50)],
            ])
            attachments.append({"filename": fname, "type": "xlsx"})

        emails.append({
            "id": eid,
            "from": {"name": sender["name"], "email": sender["email"]},
            "to": [{"name": r["name"], "email": r["email"]} for r in recipients],
            "cc": [],
            "subject": subject,
            "body": body_text,
            "date": date,
            "tags": ["客户", client],
            "attachments": attachments,
        })
    return emails


# ============================================================
# 主函数
# ============================================================

def main():
    random.seed(42)

    # 创建目录
    EMAILS_DIR.mkdir(parents=True, exist_ok=True)
    ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating email data...")

    all_emails = []
    offset = 1

    generators = [
        ("项目进度汇报", gen_project_emails, 15),
        ("财务/销售报表", gen_finance_emails, 15),
        ("会议纪要", gen_meeting_emails, 12),
        ("合同/法务", gen_legal_emails, 10),
        ("技术文档", gen_tech_emails, 12),
        ("人事行政", gen_hr_emails, 10),
        ("日常沟通", gen_daily_emails, 12),
        ("客户往来", gen_client_emails, 14),
    ]

    for name, gen_func, count in generators:
        print(f"  Generating {name} ({count} emails)...")
        emails = gen_func(offset)
        all_emails.extend(emails)
        offset += count

    # 保存邮件 JSON
    emails_file = EMAILS_DIR / "emails.json"
    with open(emails_file, "w", encoding="utf-8") as f:
        json.dump(all_emails, f, ensure_ascii=False, indent=2)

    print(f"\nDone! Generated {len(all_emails)} emails.")
    print(f"  Emails JSON: {emails_file}")
    print(f"  Attachments: {ATTACHMENTS_DIR}")

    # 统计附件
    att_types: dict[str, int] = {}
    for email in all_emails:
        for att in email["attachments"]:
            ext = att["type"]
            att_types[ext] = att_types.get(ext, 0) + 1
    print(f"\nAttachment stats:")
    for ext, count in sorted(att_types.items()):
        print(f"  .{ext}: {count} files")


if __name__ == "__main__":
    main()
