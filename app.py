import streamlit as st
import google.generativeai as genai
import json
import re
from streamlit_js_eval import streamlit_js_eval
from streamlit.components.v1 import html as components_html

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

MODEL_NAME = "gemini-2.5-flash"

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
        model = genai.GenerativeModel(MODEL_NAME)
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
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        else:
            return json.loads(response_text)
    except json.JSONDecodeError as e:
        return None

def translate_fields(data):
    """
    Translate generated English fields back to Chinese using the Gemini model.
    Returns a dict with keys: name_cn, short_desc_cn, long_desc_cn (list), keywords_cn (list)
    If translation fails, returns None.
    """
    try:
        # Prepare payload safely using json.dumps so special chars are preserved
        payload = {
            "name": data.get("name", ""),
            "short_desc": data.get("short_desc", ""),
            "long_desc": data.get("long_desc", []),
            "keywords": data.get("keywords", [])
        }

        prompt = (
            "请将下面 JSON 中的英文营销文案翻译成通顺、自然的中文，并以有效的 JSON 返回。"
            " 只返回 JSON，不要额外文字。输出的键名应为 name_cn, short_desc_cn, long_desc_cn, keywords_cn。\n\n"
            + json.dumps(payload, ensure_ascii=False)
        )

        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)

        if not response.text:
            return None

        translated = parse_json_response(response.text.strip())
        return translated

    except Exception:
        return None

def copy_to_clipboard(text, success_message="✅ 已复制到剪贴板！"):
    """
    Copy text to clipboard using JavaScript and show success message
    """
    # Escape special characters for JavaScript
    escaped_text = text.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
    
    js_code = f"""
    navigator.clipboard.writeText(`{escaped_text}`).then(function() {{
        console.log('Copied to clipboard successfully');
    }}).catch(function(err) {{
        console.error('Failed to copy: ', err);
        // Fallback for older browsers
        var textArea = document.createElement("textarea");
        textArea.value = `{escaped_text}`;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {{
            document.execCommand('copy');
            console.log('Fallback copy successful');
        }} catch (err) {{
            console.error('Fallback copy failed: ', err);
        }}
        document.body.removeChild(textArea);
    }});
    """
    
    streamlit_js_eval(js=js_code, key=f"copy_{hash(text)}")
    st.success(success_message)


def render_copy_button(text, label="📋 复制", key="copy_btn", height=40):
        """
        Render a client-side HTML copy button using Streamlit components so clicking doesn't
        cause a Streamlit rerun. This copies `text` to the clipboard and temporarily
        updates the button label to show success.
        """
        # Use json.dumps to safely escape the text for JS string literal
        js_text = json.dumps(text)
        safe_label = label.replace("'", "\\'")
        component_html = f"""
        <button id="{key}" style="padding:6px 10px;border-radius:6px;border:1px solid #ddd;background:#f8f9fa;cursor:pointer">{safe_label}</button>
        <script>
        (function(){{
            const btn = document.getElementById('{key}');
            if(!btn) return;
            btn.addEventListener('click', async function(e){{
                try{{
                    await navigator.clipboard.writeText({js_text});
                    const old = btn.innerText;
                    btn.innerText = '✅ 已复制';
                    setTimeout(()=> btn.innerText = old, 1500);
                }}catch(err){{
                    console.error('Copy failed', err);
                    const old = btn.innerText;
                    btn.innerText = '❌ 复制失败';
                    setTimeout(()=> btn.innerText = old, 1500);
                }}
            }});
        }})();
        </script>
        """
        try:
                components_html(component_html, height=height)
        except Exception as e:
                # Fallback to server-side copy if components fail
                st.button(label, key=key)

def display_marketing_content(data):
    """
    Display the marketing content in an attractive format with working copy buttons
    """
    # Display category
    if 'category' in data:
        st.info(f"🏷️ **识别的产品类别:** {data['category']}")

    # Attempt to get Chinese translations for each field
    translations = translate_fields(data)
    name_cn = None
    short_cn = None
    long_cn = None
    keywords_cn = None
    if translations and isinstance(translations, dict):
        name_cn = translations.get('name_cn')
        short_cn = translations.get('short_desc_cn')
        long_cn = translations.get('long_desc_cn')
        keywords_cn = translations.get('keywords_cn')
    
    # Product Name Section
    st.markdown("### 📦 产品名称")
    name_col, copy_col = st.columns([4, 1])
    with name_col:
        name = data.get('name', '无')
        st.markdown(f"**{name}**")
        if name_cn:
            # show Chinese translation under the English name
            st.caption(f"中文翻译：{name_cn}")
    with copy_col:
        # client-side copy buttons (won't trigger Streamlit rerun)
        render_copy_button(name, label="📋 复制", key=f"copy_name_{abs(hash(name))}")
        if name_cn:
            render_copy_button(name_cn, label="📋 复制中文", key=f"copy_name_cn_{abs(hash(name_cn))}")
    
    st.divider()
    
    # Short Description Section
    st.markdown("### 💫 营销标语")
    short_col, copy_col2 = st.columns([4, 1])
    with short_col:
        short_desc = data.get('short_desc', '无')
        st.markdown(f"*{short_desc}*")
        if short_cn:
            st.caption(f"中文翻译：{short_cn}")
    with copy_col2:
        render_copy_button(short_desc, label="📋 复制", key=f"copy_short_{abs(hash(short_desc))}")
        if short_cn:
            render_copy_button(short_cn, label="📋 复制中文", key=f"copy_short_cn_{abs(hash(short_cn))}")
    
    st.divider()
    
    # Long Description Section
    st.markdown("### ✨ 产品亮点")
    long_col, copy_col3 = st.columns([4, 1])
    with long_col:
        long_desc = data.get('long_desc', [])
        if isinstance(long_desc, list):
            for i, point in enumerate(long_desc, 1):
                st.markdown(f"**{i}.** {point}")
            formatted_desc = "\n".join([f"{i}. {point}" for i, point in enumerate(long_desc, 1)])
        else:
            st.markdown(long_desc)
            formatted_desc = str(long_desc)
        # show Chinese translations for long description if available
        if long_cn:
            if isinstance(long_cn, list):
                for i, point in enumerate(long_cn, 1):
                    st.caption(f"{i}. {point}")
                long_cn_text = "\n".join([f"{i}. {p}" for i, p in enumerate(long_cn, 1)])
            else:
                st.caption(str(long_cn))
                long_cn_text = str(long_cn)
        else:
            long_cn_text = None
    
    with copy_col3:
        render_copy_button(formatted_desc, label="📋 复制", key=f"copy_long_{abs(hash(formatted_desc))}")
        if long_cn:
            render_copy_button(long_cn_text or ("\n".join(long_cn) if isinstance(long_cn, list) else str(long_cn)), label="📋 复制中文", key=f"copy_long_cn_{abs(hash(str(long_cn)))}")
    
    st.divider()
    
    # Keywords Section
    st.markdown("### 🔍 SEO 关键词")
    keywords_col, copy_col4 = st.columns([4, 1])
    with keywords_col:
        keywords = data.get('keywords', [])
        if isinstance(keywords, list):
            keyword_tags = " ".join([f"`{kw}`" for kw in keywords])
            st.markdown(keyword_tags)
            keywords_text = ", ".join(keywords)
        else:
            st.markdown(f"`{keywords}`")
            keywords_text = str(keywords)
        # Chinese keywords display
        if keywords_cn:
            if isinstance(keywords_cn, list):
                kw_cn_tags = " ".join([f"`{kw}`" for kw in keywords_cn])
                st.markdown(kw_cn_tags)
                keywords_cn_text = ", ".join(keywords_cn)
            else:
                st.markdown(f"`{keywords_cn}`")
                keywords_cn_text = str(keywords_cn)
        else:
            keywords_cn_text = None
    
    with copy_col4:
        render_copy_button(keywords_text, label="📋 复制", key=f"copy_keywords_{abs(hash(keywords_text))}")
        if keywords_cn:
            render_copy_button(keywords_cn_text or (", ".join(keywords_cn) if isinstance(keywords_cn, list) else str(keywords_cn)), label="📋 复制中文", key=f"copy_keywords_cn_{abs(hash(str(keywords_cn)))}")
    
    st.divider()
    
    # Complete copy section
    st.markdown("### 📄 完整文案")
    
    complete_text = f"""Product Name: {name}

Marketing Tagline: {short_desc}

Key Features:
{formatted_desc}

SEO Keywords: {keywords_text}"""
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**完整的英文营销文案，包含所有元素**")
    with col2:
        render_copy_button(complete_text, label="📋 复制完整文案", key=f"copy_complete_{abs(hash(complete_text))}")
    
    # Show preview in expander
    with st.expander("📖 预览完整文案", expanded=False):
        st.text(complete_text)

# Initialize session state for generated content
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = None

# ---- Main Streamlit UI ----
st.title("🌏 产品营销文案生成器")
st.markdown("*将中文产品信息转换为吸引人的英文营销文案*")

# Main form
with st.form("input_form"):
    chinese_input = st.text_area(
        "输入产品规格/信息（中文）：",
        height=100,
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
            st.session_state.generated_content = None
        else:
            # Try to parse JSON
            parsed_data = parse_json_response(result)
            
            if parsed_data:
                st.session_state.generated_content = parsed_data
                st.success("🎉 营销文案生成成功！")
            else:
                st.warning("⚠️ 无法解析响应。显示原始输出：")
                st.code(result, language="text")
                st.session_state.generated_content = None

# Display generated content if it exists
if st.session_state.generated_content:
    st.markdown("---")
    display_marketing_content(st.session_state.generated_content)

# Footer
st.markdown("---")
st.markdown("*由 Google Gemini AI 驱动")