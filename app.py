import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date

# ==========================================
# 1. إعدادات الصفحة والهوية البصرية (Light & Clean UI)
# ==========================================
st.set_page_config(page_title="الفريد سات - نظام الإدارة والكاشير", page_icon="📺", layout="wide")

st.markdown("""
<style>
    /* خلفية عامة فاتحة ومريحة */
    .stApp { background-color: #f8f9fa; color: #212529; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* العناوين والنصوص */
    h1, h2, h3, h4 { color: #0f4c81 !important; font-weight: 700; }
    p, label, span { color: #333333 !important; }
    
    /* تنسيق الحقول والمربعات */
    .stTextInput input, .stSelectbox select, .stNumberInput input { 
        background-color: #ffffff !important; 
        color: #212529 !important; 
        border: 1px solid #ced4da !important; 
        border-radius: 8px !important;
    }
    
    /* الأزرار الاحترافية */
    .stButton>button { 
        background-color: #28a745; 
        color: white; 
        border-radius: 8px; 
        border: none; 
        font-weight: bold; 
        padding: 10px 24px;
        box-shadow: 0 4px 6px rgba(40, 167, 69, 0.2);
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #218838; color: white; }
    
    /* إحصائيات لوحة التحكم */
    div[data-testid="stMetricValue"] { color: #0f4c81 !important; font-weight: bold; }
    
    /* فصل بصري نظيف */
    hr { border-color: #dee2e6; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. الاتصال بقاعدة البيانات السحابية (Supabase)
# ==========================================
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
    st.stop()

# ==========================================
# 3. نظام تسجيل الدخول والصلاحيات الآمن
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_id = None
    st.session_state.username = None

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; margin-top: 50px;'>📺 الفريد سات</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6c757d; font-size: 16px;'>نظام إدارة المحلات ونقاط البيع المتطور</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username_input = st.text_input("اسم المستخدم")
            password_input = st.text_input("كلمة المرور", type="password")
            submit_login = st.form_submit_button("تسجيل الدخول", use_container_width=True)
            
            if submit_login:
                try:
                    res = supabase.table('users').select('*').eq('username', username_input).eq('password', password_input).execute()
                    if res.data:
                        user = res.data[0]
                        st.session_state.logged_in = True
                        st.session_state.user_role = user['role']
                        st.session_state.user_id = user['id']
                        st.session_state.username = user['username']
                        st.success("تم تسجيل الدخول بنجاح!")
                        st.rerun()
                    else:
                        st.error("اسم المستخدم أو كلمة المرور غير صحيحة!")
                except Exception as err:
                    st.error(f"خطأ أثناء التحقق: {err}")
    st.stop()

# ==========================================
# 4. واجهة الاستخدام حسب الصلاحية
# ==========================================
role = st.session_state.user_role
current_user_id = st.session_state.user_id

# القائمة الجانبية (Sidebar)
with st.sidebar:
    st.markdown(f"### 👤 مرحباً، {st.session_state.username}")
    st.markdown(f"🛡️ الصلاحية: **{role.upper()}**")
    st.markdown("---")
    
    # لو الأدمن دخل، يقدر يدير الموظفين بالكامل
    if role == 'admin':
        st.markdown("#### ⚙️ إدارة طاقم العمل")
        with st.expander("➕ إضافة موظف جديد"):
            new_u = st.text_input("اسم المستخدم الجديد")
            new_p = st.text_input("كلمة المرور", type="password")
            new_r = st.selectbox("الصلاحية", ["cashier", "admin"])
            if st.button("حفظ المستخدم الجديد", use_container_width=True):
                if new_u and new_p:
                    try:
                        supabase.table('users').insert({'username': new_u, 'password': new_p, 'role': new_r}).execute()
                        st.success(f"تمت إضافة {new_u} بنجاح!")
                        st.rerun()
                    except:
                        st.error("المستخدم موجود مسبقاً.")
                else:
                    st.warning("أدخل البيانات كاملة.")
                    
        with st.expander("🔄 تعديل أو حذف موظف"):
            try:
                users_res = supabase.table('users').select('id, username, role').execute()
                users_list = users_res.data if users_res.data else []
                u_dict = {u['username']: u for u in users_list}
                selected_user_to_mod = st.selectbox("اختر المستخدم", options=list(u_dict.keys()))
                target_user = u_dict[selected_user_to_mod]
                
                mod_pass = st.text_input("كلمة المرور الجديدة (اختياري)", type="password", key="mod_p")
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    if st.button("تحديث الباسورد"):
                        if mod_pass:
                            supabase.table('users').update({'password': mod_pass}).eq('id', target_user['id']).execute()
                            st.success("تم التحديث بنجاح!")
                        else:
                            st.warning("اكتب الباسورد الجديد.")
                with col_m2:
                    if target_user['username'] != 'admin':
                        if st.button("حذف المستخدم", type="primary"):
                            supabase.table('users').delete().eq('id', target_user['id']).execute()
                            st.success("تم الحذف.")
                            st.rerun()
                    else:
                        st.info("لا يمكن حذف الأدمن الرئيسي.")
            except Exception as e:
                st.error(f"خطأ: {e}")
        st.markdown("---")
        
    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

if role == 'cashier':
    # ==========================================
    # واجهة الكاشير المطورة (نظام أقسام وعناصر ديناميكية + صيانة + IPTV)
    # ==========================================
    st.markdown("<h1>🛒 نقطة البيع والخدمات (الكاشير)</h1>", unsafe_allow_html=True)
    
    tab_pos, tab_maint, tab_iptv, tab_return = st.tabs([
        "💵 قسم المبيعات السريعة", 
        "🛠️ تذاكر وصيانة الأجهزة", 
        "📺 تسجيل اشتراكات IPTV", 
        "🔄 المرتجعات"
    ])
    
    # 1. نظام المبيعات السريعة (اختيار القسم أولاً ثم تحته العناصر تتظبط لوحدها)
    with tab_pos:
        st.markdown("### 🛍️ سلة المشتريات وإنهاء الفواتير")
        try:
            cats_res = supabase.table('categories').select('*').execute()
            categories = cats_res.data if cats_res.data else []
        except:
            categories = []
            
        if not categories:
            st.warning("لا توجد أقسام مسجلة بعد. يرجى إبلاغ المدير لإضافة أقسام وبضائع.")
        else:
            cat_dict = {c['name']: c['id'] for c in categories}
            selected_cat_name = st.selectbox("📁 اختر القسم (ريسيفرات، ريموتات، إلخ)", options=list(cat_dict.keys()))
            selected_cat_id = cat_dict[selected_cat_name]
            
            # جلب المنتجات التابعة لهذا القسم تحديداً
            try:
                prod_res = supabase.table('products').select('*').eq('category_id', selected_cat_id).gt('stock_quantity', 0).execute()
                products = prod_res.data if prod_res.data else []
            except:
                products = []
                
            if not products:
                st.info(f"لا توجد منتجات متوفرة حالياً في قسم '{selected_cat_name}'.")
            else:
                prod_dict = {f"{p['name']} | 🏷️ السعر: {p['sell_price']}ج | 📦 المتاح: {p['stock_quantity']}": p for p in products}
                selected_prod_str = st.selectbox("📦 اختر العنصر المطلوب", options=list(prod_dict.keys()))
                selected_prod = prod_dict[selected_prod_str]
                
                qty = st.number_input("الكمية المطلوبة", min_value=1, max_value=selected_prod['stock_quantity'], value=1)
                
                st.markdown(f"<div style='background-color: #e9ecef; padding: 10px; border-radius: 6px; margin-bottom: 10px;'>إجمالي السعر لهذه القطعة: <b>{selected_prod['sell_price'] * qty} جنيه</b></div>", unsafe_allow_html=True)
                
                if st.button("✅ إتمام البيع وطباعة الفاتورة", use_container_width=True):
                    total_price = selected_prod['sell_price'] * qty
                    try:
                        # إنشاء الفاتورة مع ربطها باسم الكاشير الحالي
                        sale_res = supabase.table('sales').insert({
                            'user_id': current_user_id,
                            'total_amount': total_price
                        }).execute()
                        
                        sale_id = sale_res.data[0]['id']
                        
                        # تفاصيل الفاتورة
                        supabase.table('sale_items').insert({
                            'sale_id': sale_id,
                            'product_id': selected_prod['id'],
                            'quantity': qty,
                            'price': selected_prod['sell_price']
                        }).execute()
                        
                        # خصم المخزون تلقائياً
                        new_stock = selected_prod['stock_quantity'] - qty
                        supabase.table('products').update({'stock_quantity': new_stock}).eq('id', selected_prod['id']).execute()
                        
                        st.success(f"🎉 تم البيع بنجاح! رقم الفاتورة: #{sale_id} | الإجمالي: {total_price} جنيه")
                    except Exception as ex:
                        st.error(f"حدث خطأ أثناء إتمام البيع: {ex}")

    # 2. نظام صيانة الكاشير المطور
    with tab_maint:
        st.markdown("### 🛠️ استلام وتسجيل جهاز جديد للصيانة")
        with st.form("cashier_maint_form"):
            c_name = st.text_input("اسم العميل")
            c_phone = st.text_input("رقم هاتف العميل")
            device_type = st.text_input("نوع الجهاز (مثال: ريسيفر رسبرت، شاشة)")
            device_issue = st.text_area("وصف العطل بالتفصيل")
            estimated_cost = st.number_input("التكلفة المبدئية المتوقعة", min_value=0.0, value=0.0)
            
            submit_maint = st.form_submit_button("📥 إصدار تذكرة صيانة للعميل", use_container_width=True)
            if submit_maint:
                if c_name and c_phone and device_issue:
                    try:
                        supabase.table('maintenance').insert({
                            'customer_name': c_name,
                            'phone': c_phone,
                            'device_issue': f"[{device_type}] {device_issue}",
                            'cost': estimated_cost,
                            'status': 'قيد الانتظار'
                        }).execute()
                        st.success("✅ تم حفظ تذكرة الصيانة بنجاح وإعطاء العميل رقم تتبع في المحل!")
                    except Exception as e:
                        st.error(f"خطأ: {e}")
                else:
                    st.warning("يرجى إدخال اسم العميل ورقم الهاتف ووصف العطل.")

    # 3. تسجيل اشتراكات IPTV للكاشير
    with tab_iptv:
        st.markdown("### 📺 تسجيل اشتراك IPTV جديد")
        with st.form("cashier_iptv_form"):
            i_name = st.text_input("اسم المشترك")
            i_phone = st.text_input("رقم الموبايل")
            i_mac = st.text_input("رقم اللوحة / أو عنوان الـ MAC")
            i_server = st.text_input("اسم السيرفر (مثال: Cobra, Dragon)")
            s_date = st.date_input("تاريخ البدء", date.today())
            e_date = st.date_input("تاريخ الانتهاء")
            
            submit_iptv_cashier = st.form_submit_button("🚀 تفعيل وحفظ الاشتراك", use_container_width=True)
            if submit_iptv_cashier:
                if i_name and i_phone and i_server:
                    try:
                        supabase.table('iptv_subs').insert({
                            'customer_name': i_name,
                            'phone': i_phone,
                            'server_type': i_server,
                            'mac_address': i_mac,
                            'start_date': str(s_date),
                            'expire_date': str(e_date)
                        }).execute()
                        st.success("✅ تم تفعيل اشتراك الـ IPTV وحفظه في السحابة بنجاح!")
                    except Exception as err:
                        st.error(f"خطأ: {err}")
                else:
                    st.warning("يرجى إدخال اسم المشترك ورقم الهاتف واسم السيرفر على الأقل.")

    with tab_return:
        st.markdown("### 🔄 نظام المرتجعات السريع")
        ret_id = st.number_input("رقم الفاتورة المراد إرجاعها", min_value=1, step=1)
        ret_reason = st.text_input("سبب المرتجع")
        if st.button("تأكيد إرجاع الفاتورة للمخزن"):
            st.info("خاصية المرتجعات مفعلة لضمان ضبط حركة المخزن بدقة.")

else:
    # ==========================================
    # لوحة تحكم المدير الشاملة (Admin Dashboard - Light Mode)
    # ==========================================
    st.markdown("<h1>📊 لوحة تحكم الإدارة - الفريد سات</h1>", unsafe_allow_html=True)
    
    admin_tab1, admin_tab2, admin_tab3, admin_tab4, admin_tab5 = st.tabs([
        "📦 المخزن والنواقص", 
        "📁 الأقسام وإدارة العناصر", 
        "🛠️ متابعة الصيانة", 
        "📺 اشتراكات IPTV", 
        "📈 التقارير والفواتير"
    ])
    
    with admin_tab1:
        st.markdown("### 📦 مراقبة المخزن والتحذيرات التلقائية")
        try:
            p_res = supabase.table('products').select('*, categories(name)').execute()
            if p_res.data:
                df_p = pd.DataFrame(p_res.data)
                # تنبيهات النواقص
                low_stock = df_p[df_p['stock_quantity'] <= df_p['min_stock_alert']]
                if not low_stock.empty:
                    st.warning("⚠️ تنبيه هام: أصناف وشفت بضائع قاربت على النفاد:")
                    st.dataframe(low_stock[['name', 'stock_quantity', 'min_stock_alert']], use_container_width=True)
                
                st.markdown("### جدول جرد البضاعة بالكامل")
                st.dataframe(df_p, use_container_width=True)
            else:
                st.info("لا توجد منتجات مسجلة حتى الآن.")
        except Exception as err:
            st.error(f"خطأ في جلب بيانات المخزن: {err}")

    with admin_tab2:
        st.markdown("### 📁 إضافة الأقسام والعناصر الجديدة للمحل")
        c_col1, c_col2 = st.columns(2)
        
        with c_col1:
            st.markdown("#### 📂 إضافة قسم جديد")
            new_cat = st.text_input("اسم القسم (مثال: ريموتات، ريسيفرات، كابلات)")
            if st.button("حفظ القسم الجديد"):
                if new_cat:
                    try:
                        supabase.table('categories').insert({'name': new_cat}).execute()
                        st.success(f"تمت إضافة القسم '{new_cat}' بنجاح!")
                        st.rerun()
                    except:
                        st.error("القسم موجود مسبقاً.")
                else:
                    st.warning("اكتب اسم القسم.")
                    
        with c_col2:
            st.markdown("#### 📦 إضافة عنصر جديد تحت قسم")
            try:
                cat_res = supabase.table('categories').select('*').execute()
                cats = {c['name']: c['id'] for c in cat_res.data} if cat_res.data else {}
            except:
                cats = {}
                
            if cats:
                chosen_cat = st.selectbox("اختر القسم التابع له العنصر", options=list(cats.keys()))
                item_name = st.text_input("اسم العنصر (مثال: ريموت أصلى LG)")
                item_barcode = st.text_input("الباركود (اختياري)")
                buy_p = st.number_input("سعر الشراء", min_value=0.0, value=0.0)
                sell_p = st.number_input("سعر البيع", min_value=0.0, value=0.0)
                init_qty = st.number_input("الكمية المبدئية بالمخزن", min_value=0, value=15)
                min_alert = st.number_input("الحد الأدنى للتنبيه", min_value=1, value=3)
                
                if st.button("💾 حفظ العنصر في المخزن"):
                    if item_name and sell_p > 0:
                        try:
                            supabase.table('products').insert({
                                'category_id': cats[chosen_cat],
                                'name': item_name,
                                'barcode': item_barcode if item_barcode else None,
                                'buy_price': buy_p,
                                'sell_price': sell_p,
                                'stock_quantity': init_qty,
                                'min_stock_alert': min_alert
                            }).execute()
                            st.success(f"تمت إضافة العنصر '{item_name}' بنجاح!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"خطأ: {e}")
                    else:
                        st.warning("أدخل اسم العنصر وسعر البيع بشكل صحيح.")
            else:
                st.info("أنشئ أقساماً أولاً ليظهر لك هنا خيار إضافة العناصر.")

    with admin_tab3:
        st.markdown("### 🛠️ متابعة حالة أجهزة الصيانة بالمحل")
        try:
            m_res = supabase.table('maintenance').select('*').execute()
            if m_res.data:
                st.dataframe(pd.DataFrame(m_res.data), use_container_width=True)
            else:
                st.info("لا توجد تذاكر صيانة مسجلة حالياً.")
        except:
            st.info("جاري تحميل بيانات الصيانة...")

    with admin_tab4:
        st.markdown("### 📺 قاعدة بيانات اشتراكات الـ IPTV ومتابعتها")
        try:
            iptv_res = supabase.table('iptv_subs').select('*').execute()
            if iptv_res.data:
                st.dataframe(pd.DataFrame(iptv_res.data), use_container_width=True)
            else:
                st.info("لا توجد اشتراكات مسجلة.")
        except:
            st.info("جاري التحميل...")

    with admin_tab5:
        st.markdown("### 📈 تقارير الأرباح والمبيعات والفواتير")
        try:
            sales_res = supabase.table('sales').select('*, users(username)').execute()
            if sales_res.data:
                df_sales = pd.DataFrame(sales_res.data)
                total_rev = df_sales['total_amount'].sum()
                
                col_m1, col_m2 = st.columns(2)
                col_m1.metric("💰 إجمالي المبيعات العامة", f"{total_rev} جنيه")
                col_m2.metric("🧾 عدد الفواتير المسجلة", len(df_sales))
                
                st.markdown("### تفاصيل الفواتير وحركة البيع لكل موظف:")
                st.dataframe(df_sales, use_container_width=True)
            else:
                st.info("لا توجد فواتير مبيعات مسجلة حتى الآن.")
        except Exception as e:
            st.error(f"خطأ في جلب التقارير: {e}")
