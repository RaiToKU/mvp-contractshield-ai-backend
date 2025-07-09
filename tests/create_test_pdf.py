#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试PDF文件
"""

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    def create_test_pdf():
        # 创建测试文件内容
        test_content = [
            "合同编号：CS-2024-001",
            "",
            "甲方：北京科技有限公司",
            "地址：北京市海淀区中关村大街1号",
            "法定代表人：张三",
            "",
            "乙方：上海贸易股份有限公司",
            "地址：上海市浦东新区陆家嘴金融中心",
            "法定代表人：李四",
            "",
            "本合同为采购合同，甲方向乙方采购办公设备。",
            "合同金额：人民币100万元整。",
            "",
            "签订日期：2024年1月1日",
            "有效期：2024年1月1日至2024年12月31日",
            "",
            "特别条款：",
            "1. 交货期限：合同签订后30个工作日内",
            "2. 付款方式：货到付款",
            "3. 质量保证：产品质量保证期为2年",
            "4. 违约责任：任何一方违约需承担合同总金额10%的违约金"
        ]
        
        pdf_path = "test_contract.pdf"
        
        # 创建PDF
        c = canvas.Canvas(pdf_path, pagesize=letter)
        
        # 添加文本内容
        y_position = 750
        for line in test_content:
            if line.strip():
                c.drawString(50, y_position, line)
            y_position -= 20
            if y_position < 50:  # 如果接近页面底部，创建新页面
                c.showPage()
                y_position = 750
        
        c.save()
        print(f"PDF文件已创建: {pdf_path}")
        return pdf_path
    
    if __name__ == "__main__":
        create_test_pdf()
        
except ImportError:
    print("reportlab未安装，无法创建PDF文件")
    print("请运行: pip install reportlab")