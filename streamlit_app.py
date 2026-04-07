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
