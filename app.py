import streamlit as st
import google.generativeai as genai
import json
import re

# Configure page
st.set_page_config(page_title="CN → EN Product Marketing Generator", layout="wide")

# Get API key from secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    if not api_key:
        st.error("GEMINI_API_KEY not set. Please check your Streamlit secrets.")
        st.stop()
except KeyError:
    st.error("GEMINI_API_KEY not found in secrets. Please add it to your Streamlit secrets.")
    st.stop()

# Configure Gemini
genai.configure(api_key=api_key)

MODEL_NAME = "gemini-2.5-flash"  # Updated model name

def generate_marketing_text(chinese_input):
    """
    Calls the Gemini API to generate English product name & description based on Chinese input.
    """
    
    prompt = f"""
你是专业的电商文案撰写和翻译专家，擅长创作吸引人的营销文案。
根据以下中文产品信息，生成高质量、有吸引力的英文营销文案：

产品信息（中文）：
{chinese_input}

要求：
- 自动识别产品类别（英文）
- 产品名称：吸引眼球，≤ 60个字符，突出卖点
- 简短描述：引人注目的营销语句，≤ 120个字符，强调价值主张
- 详细描述：以吸引人的要点形式列出，3-5个要点，每个要点都要突出产品优势和益处
- 使用富有感染力的营销语言，强调产品的独特性和价值
- 输出语言：英文
- 不要编造技术规格；如果缺少规格信息，请省略
- 自动提取并翻译相关关键词

营销文案风格：
- 使用动感、积极的形容词
- 强调用户体验和益处
- 突出产品的独特卖点
- 创造购买欲望和紧迫感

如果产品有不同规格（如1L、1.5L等），请在产品名称中体现规格差异，但共享相同的基础产品信息。

格式为有效的JSON：
{{
  "category": "Product Category",
  "name": "Attractive Product Name",
  "short_desc": "Compelling marketing tagline",
  "long_desc": [
    "Compelling benefit point 1",
    "Compelling benefit point 2", 
    "Compelling benefit point 3",
    "Compelling benefit point 4"
  ],
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4"]
}}

只返回JSON，不要其他文字。
"""
    
    try:
        # Initialize the model
        model = genai.GenerativeModel(MODEL_NAME)
        
        # Generate content
        response = model.generate_content(prompt)
        
        if response.text:
            return response.text.strip()
        else:
            return "Error: No response generated"
            
    except Exception as e:
        return f"Error: {str(e)}"

def parse_json_response(response_text):
    """
    Attempts to parse the JSON response from Gemini
    """
    try:
        # Try to extract JSON from the response if it contains other text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        else:
            # Try parsing the entire response
            return json.loads(response_text)
    except json.JSONDecodeError as e:
        return None

def display_marketing_content(data):
    """
    Display the marketing content in an attractive format with individual copy buttons
    """
    # Display category
    if 'category' in data:
        st.info(f"🏷️ **识别的产品类别:** {data['category']}")
    
    # Product Name Section
    st.markdown("### 📦 产品名称")
    name_col, copy_col = st.columns([4, 1])
    with name_col:
        name = data.get('name', '无')
        st.markdown(f"**{name}**")
    with copy_col:
        if st.button("📋", key="copy_name", help="复制产品名称"):
            st.code(name, language="text")
    
    st.divider()
    
    # Short Description Section
    st.markdown("### 💫 营销标语")
    short_col, copy_col2 = st.columns([4, 1])
    with short_col:
        short_desc = data.get('short_desc', '无')
        st.markdown(f"*{short_desc}*")
    with copy_col2:
        if st.button("📋", key="copy_short", help="复制营销标语"):
            st.code(short_desc, language="text")
    
    st.divider()
    
    # Long Description Section
    st.markdown("### ✨ 产品亮点")
    long_col, copy_col3 = st.columns([4, 1])
    with long_col:
        long_desc = data.get('long_desc', [])
        if isinstance(long_desc, list):
            for i, point in enumerate(long_desc, 1):
                st.markdown(f"**{i}.** {point}")
        else:
            st.markdown(long_desc)
    
    with copy_col3:
        if st.button("📋", key="copy_long", help="复制产品亮点"):
            if isinstance(long_desc, list):
                formatted_desc = "\n".join([f"{i}. {point}" for i, point in enumerate(long_desc, 1)])
            else:
                formatted_desc = str(long_desc)
            st.code(formatted_desc, language="text")
    
    st.divider()
    
    # Keywords Section
    st.markdown("### 🔍 SEO 关键词")
    keywords = data.get('keywords', [])
    if isinstance(keywords, list):
        keyword_tags = " ".join([f"`{kw}`" for kw in keywords])
        st.markdown(keyword_tags)
    else:
        st.markdown(f"`{keywords}`")
    
    # Complete copy section
    st.divider()
    st.markdown("### 📄 完整文案")
    
    complete_text = f"""Product Name: {name}

Marketing Tagline: {short_desc}

Key Features:
{chr(10).join([f"{i}. {point}" for i, point in enumerate(long_desc, 1)]) if isinstance(long_desc, list) else long_desc}

SEO Keywords: {", ".join(keywords) if isinstance(keywords, list) else str(keywords)}"""
    
    if st.button("📋 复制完整文案", key="copy_complete", use_container_width=True):
        st.code(complete_text, language="text")
        st.success("✅ 完整文案已显示，请手动复制！")

# ---- Main Streamlit UI ----
st.title("🌏 产品营销文案生成器")

# Main form
with st.form("input_form"):
    chinese_input = st.text_area(
        "输入产品规格/信息（中文）：",
        height=50,
        placeholder="例如：这款保温水杯有1L和1.5L两种规格，采用304不锈钢内胆，双层真空保温设计，可保温12小时，杯盖密封性好不漏水，适合办公室和户外使用..."
    )
    
    submitted = st.form_submit_button("🚀 生成英文营销文案", use_container_width=True)

# Handle form submission
if submitted:
    if not chinese_input.strip():
        st.warning("⚠️ 请输入产品的中文信息。")
    else:
        with st.spinner("🤖 正在生成吸引人的营销文案..."):
            result = generate_marketing_text(chinese_input)
        
        if result.startswith("Error:"):
            st.error(result)
        else:
            # Try to parse JSON
            parsed_data = parse_json_response(result)
            
            if parsed_data:
                display_marketing_content(parsed_data)
            else:
                st.warning("⚠️ 无法解析响应。显示原始输出：")
                st.code(result, language="text")

# Footer
st.markdown("---")
st.markdown("*由 Google Gemini AI 驱动*")