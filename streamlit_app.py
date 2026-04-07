import streamlit as st
import httpx
import pandas as pd

# 设置页面配置
st.set_page_config(page_title="仿制药研发助手", layout="wide")

st.title("💊 仿制药制剂开发：参比制剂(RLD)信息查询")
st.markdown("输入药品商品名，一键获取 FDA 注册信息、RLD 状态及说明书链接。")

# 侧边栏配置
drug_name = st.text_input("请输入药品商品名 (例如: Eliquis, Januvia):", "")

if drug_name:
    with st.spinner('正在从 FDA 调取资料...'):
        try:
            # 1. 调用 openFDA API
            base_url = "https://api.fda.gov/drug/drugsfda.json"
            params = {"search": f'openfda.brand_name:"{drug_name}"', "limit": 1}
            
            response = httpx.get(base_url, params=params)
            
            if response.status_code == 200:
                data = response.json()["results"][0]
                
                # 2. 提取关键信息
                brand_name = data.get("openfda", {}).get("brand_name", [""])[0]
                generic_name = data.get("openfda", {}).get("generic_name", [""])[0]
                sponsor = data.get("sponsor_name", "")
                app_no = data.get("application_number", "")
                
                # 判断 RLD
                products = data.get("products", [])
                is_rld = any(p.get("reference_drug") == "Yes" for p in products)
                
                # 3. UI 展示
                col1, col2 = st.columns(2)
                with col1:
                    st.success(f"### {brand_name}")
                    st.write(f"**通用名:** {generic_name}")
                    st.write(f"**持证商:** {sponsor}")
                    st.write(f"**申请号:** {app_no}")
                
                with col2:
                    st.metric("参比制剂 (RLD)", "是" if is_rld else "否")
                    st.info(f"[点击跳转 FDA 官网详情](https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo={app_no[3:]})")

                # 4. 剂型与规格列表
                st.subheader("剂型与规格信息")
                prod_df = pd.DataFrame([
                    {
                        "剂型": p.get("dosage_form"),
                        "规格": p.get("active_ingredients", [{}])[0].get("strength"),
                        "给药途径": p.get("route"),
                        "RLD": p.get("reference_drug")
                    } for p in products
                ])
                st.table(prod_df)
                
            else:
                st.error("未找到相关药品，请检查拼写是否正确。")
        except Exception as e:
            st.error(f"连接失败: {e}")
import pdfplumber
import re
import io

# ... (保留你之前 V1.0 的全部代码) ...

st.divider() # 添加一条分割线

st.header("📄 第二阶段：审评报告 (Review Docs) 智能解析")
st.markdown("由于 FDA 反爬虫限制，请点击上方详情链接下载 **Clinical Pharmacology Review** 等 PDF 文件，并在此处上传进行智能信息提取。")

uploaded_file = st.file_uploader("请上传 FDA PDF 审评报告", type="pdf")

if uploaded_file is not None:
    with st.spinner('正在解析 PDF 文件，这可能需要几十秒钟...'):
        try:
            # 1. 读取 PDF 文本
            all_text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                # 为了演示速度，这里可以限制只读取前 50 页，实际应用中可读取全部
                total_pages = len(pdf.pages)
                st.info(f"成功加载 PDF，共 {total_pages} 页。正在提取文本...")
                for i in range(total_pages):
                    page = pdf.pages[i]
                    text = page.extract_text()
                    if text:
                        # 记录页码，方便溯源
                        all_text += f"\n\n--- [Page {i+1}] ---\n\n" + text

            st.success("PDF 文本提取完成！")

            # 2. 交互式查询模块
            st.subheader("🔍 关键信息秒查")
            
            # 提供一些制剂开发常用的预设关键词
            suggested_keywords = ["fasting", "fed", "dissolution", "Cmax", "AUC", "half-life", "IVIVC"]
            selected_kw = st.selectbox("选择常用搜索词，或在下方自定义输入：", ["自定义..."] + suggested_keywords)
            
            search_query = st.text_input("输入你要在 PDF 中寻找的关键词 (支持英文):", 
                                         value=selected_kw if selected_kw != "自定义..." else "")

            if search_query:
                # 3. 提取包含关键词的上下文段落
                st.markdown(f"**关于 `{search_query}` 的搜索结果：**")
                
                # 按换行符分割文本，寻找包含关键词的行或段落
                paragraphs = all_text.split('\n\n')
                results_found = 0
                
                for p in paragraphs:
                    # 不区分大小写搜索
                    if search_query.lower() in p.lower():
                        results_found += 1
                        # 使用高亮显示关键词
                        highlighted_text = re.sub(f"({search_query})", r"**\1**", p, flags=re.IGNORECASE)
                        st.info(highlighted_text)
                        
                        # 为了避免结果过多撑爆页面，限制展示前 5 个匹配项
                        if results_found >= 5:
                            st.warning("结果超过 5 条，仅展示前 5 个最相关的段落。")
                            break
                            
                if results_found == 0:
                    st.write("未在文档中找到该关键词。")

        except Exception as e:
            st.error(f"解析 PDF 时发生错误: {e}")
