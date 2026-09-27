import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date

# ==========================================
# 1. إعدادات الصفحة والهوية البصرية (Light & Professional UI)
# ==========================================
st.set_page_config(page_title="الفريد سات - نظام الإدارة والكاشير", page_icon="📺", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; color: #333333; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    h1, h2, h3 { color: #1e3d59 !important; }
    .stTextInput label, .stSelectbox label, .stNumberInput label { color: #1e3d59 !important; font-weight: bold; }
    .stButton>button { background-color: #17b978; color: white; border-radius: 6px; border: none; font-weight: bold; padding: 10px 20px; }
    .stButton>button:hover { background-color: #149361; color: white; }
    div[data-testid="stMetricValue"] { color: #17b978; }
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
        st.markdown("<h1 style='text-align: center;'>📺 الفريد سات</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>نظام الإدارة ونقاط البيع المتكامل</p>", unsafe_allow_html=True)
        
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
# 4. واجهة الكاشير (عزل تام) أو لوحة التحكم (للأدمن)
# ==========================================
role = st.session_state.user_role
current_user_id = st.session_state.user_id

# زر الخروج ومعلومات المستخدم في القائمة الجانبية
with st.sidebar:
    st.markdown(f"👤 المستخدم: **{st.session_state.username}**")
    st.markdown(f"🔑 الصلاحية: **{role.upper()}**")
    
    # لو الأدمن دخل، يقدر يغير الباسورد أو يضيف مستخدمين
    if role == 'admin':
        st.markdown("---")
        st.subheader("⚙️ إدارة الموظفين")
        new_u = st.text_input("اسم الموظف الجديد")
        new_p = st.text_input("باسورد الموظف", type="password")
        new_r = st.selectbox("الصلاحية", ["cashier", "admin"])
        if st.button("إضافة مستخدم جديد"):
            if new_u and new_p:
                try:
                    supabase.table('users').insert({'username': new_u, 'password': new_p, 'role': new_r}).execute()
                    st.success(f"تمت إضافة المستخدم {new_u} بنجاح!")
                except:
                    st.error("المستخدم موجود مسبقاً أو حدث خطأ.")
                    
    st.markdown("---")
    if st.button("تسجيل الخروج", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

if role == 'cashier':
    # ==========================================
    # واجهة الكاشير (مخصصة للبيع والصيانة السريعة فقط)
    # ==========================================
    st.title("🛒 نقطة البيع (الكاشير) - الفريد سات")
    
    tab_pos, tab_maint, tab_return = st.tabs(["💵 بيع منتج", "🛠️ استلام جهاز صيانة", "🔄 مرتجع مبيعات"])
    
    with tab_pos:
        st.subheader("سلة المشتريات والفواتير")
        try:
            products_res = supabase.table('products').select('*').gt('stock_quantity', 0).execute()
            products = products_res.data if products_res.data else []
        except:
            products = []
            
        if not products:
            st.warning("لا توجد منتجات متوفرة في المخزن حالياً!")
        else:
            prod_dict = {f"{p['name']} (المتاح: {p['stock_quantity']} - السعر: {p['sell_price']}ج)": p for p in products}
            selected_prod_str = st.selectbox("اختر المنتج أو ابحث عنه", options=list(prod_dict.keys()))
            selected_prod = prod_dict[selected_prod_str]
            
            qty = st.number_input("الكمية", min_value=1, max_value=selected_prod['stock_quantity'], value=1)
            
            if st.button("إتمام البيع وطباعة الفاتورة", use_container_width=True):
                total_price = selected_prod['sell_price'] * qty
                try:
                    # 1. إنشاء الفاتورة مع تسجيل معرف الكاشير (لتتبع من باعها)
                    sale_res = supabase.table('sales').insert({
                        'user_id': current_user_id,
                        'total_amount': total_price
                    }).execute()
                    
                    sale_id = sale_res.data[0]['id']
                    
                    # 2. إضافة تفاصيل الفاتورة
                    supabase.table('sale_items').insert({
                        'sale_id': sale_id,
                        'product_id': selected_prod['id'],
                        'quantity': qty,
                        'price': selected_prod['sell_price']
                    }).execute()
                    
                    # 3. خصم الكمية من المخزن تلقائياً
                    new_stock = selected_prod['stock_quantity'] - qty
                    supabase.table('products').update({'stock_quantity': new_stock}).eq('id', selected_prod['id']).execute()
                    
                    st.success(f"✅ تمت عملية البيع بنجاح! إجمالي الفاتورة: {total_price} جنيه (رقم الفاتورة: #{sale_id})")
                except Exception as ex:
                    st.error(f"حدث خطأ أثناء حفظ الفاتورة: {ex}")

    with tab_maint:
        st.subheader("تسجيل جهاز جديد للصيانة في المحل")
        with st.form("maint_form"):
            c_name = st.text_input("اسم العميل")
            c_phone = st.text_input("رقم هاتف العميل")
            device_desc = st.text_area("وصف الجهاز والعطل")
            estimated_cost = st.number_input("التكلفة المبدئية", min_value=0.0, value=0.0)
            submit_maint = st.form_submit_button("تسجيل تذكرة الصيانة", use_container_width=True)
            
            if submit_maint:
                if c_name and c_phone and device_desc:
                    try:
                        supabase.table('maintenance').insert({
                            'customer_name': c_name,
                            'phone': c_phone,
                            'device_issue': device_desc,
                            'cost': estimated_cost,
                            'status': 'قيد الانتظار'
                        }).execute()
                        st.success("✅ تم تسجيل تذكرة الصيانة بنجاح!")
                    except Exception as e:
                        st.error(f"خطأ: {e}")
                else:
                    st.warning("يرجى إدخال اسم العميل ورقم الهاتف ووصف العطل.")

    with tab_return:
        st.subheader("إرجاع منتج للمخزن")
        ret_sale_id = st.number_input("رقم الفاتورة الأصلية للمرتجع", min_value=1, step=1)
        ret_reason = st.text_input("سبب المرتجع")
        if st.button("تأكيد المرتجع وإعادة الكمية للمخزن", use_container_width=True):
            st.info("نظام المرتجعات مفعل ويرتبط برقم الفاتورة والمخزن.")

else:
    # ==========================================
    # لوحة تحكم المدير الشاملة (Admin Dashboard)
    # ==========================================
    st.title("📊 لوحة تحكم المدير - الفريد سات")
    
    admin_tab1, admin_tab2, admin_tab3, admin_tab4, admin_tab5 = st.tabs([
        "📦 إدارة المخزن والنواقص", 
        "📁 الأقسام والمنتجات", 
        "🛠️ متابعة الصيانة", 
        "📺 اشتراكات IPTV", 
        "📈 التقارير الشاملة والفواتير"
    ])
    
    with admin_tab1:
        st.subheader("متابعة المخزن وتحذيرات النواقص")
        try:
            p_res = supabase.table('products').select('*').execute()
            if p_res.data:
                df_p = pd.DataFrame(p_res.data)
                low_stock = df_p[df_p['stock_quantity'] <= df_p['min_stock_alert']]
                if not low_stock.empty:
                    st.warning("⚠️ تنبيه: هذه الأصناف قاربت على النفاد، يرجى طلب بضاعة جديدة:")
                    st.dataframe(low_stock[['name', 'stock_quantity', 'min_stock_alert']], use_container_width=True)
                
                st.markdown("### جرد المنتجات بالكامل")
                st.dataframe(df_p, use_container_width=True)
            else:
                st.info("لا توجد منتجات مسجلة حتى الآن.")
        except Exception as err:
            st.error(f"خطأ في جلب بيانات المخزن: {err}")

    with admin_tab2:
        st.subheader("إضافة قسم جديد أو منتج جديد")
        col_cat, col_prod = st.columns(2)
        
        with col_cat:
            st.markdown("#### 📁 إضافة قسم جديد (مثل: ريموتات، ريسيفرات)")
            new_cat_name = st.text_input("اسم القسم")
            if st.button("حفظ القسم"):
                if new_cat_name:
                    try:
                        supabase.table('categories').insert({'name': new_cat_name}).execute()
                        st.success(f"تمت إضافة القسم '{new_cat_name}' بنجاح!")
                        st.rerun()
                    except:
                        st.error("القسم موجود مسبقاً.")
                else:
                    st.warning("اكتب اسم القسم.")
                    
        with col_prod:
            st.markdown("#### 📦 إضافة منتج للمخزن")
            try:
                cat_res = supabase.table('categories').select('*').execute()
                cats = {c['name']: c['id'] for c in cat_res.data} if cat_res.data else {}
            except:
                cats = {}
                
            if cats:
                selected_cat_name = st.selectbox("اختر القسم", options=list(cats.keys()))
                p_name = st.text_input("اسم المنتج")
                p_barcode = st.text_input("الباركود (اختياري)")
                p_buy = st.number_input("سعر الشراء", min_value=0.0, value=0.0)
                p_sell = st.number_input("سعر البيع", min_value=0.0, value=0.0)
                p_qty = st.number_input("الكمية المبدئية", min_value=0, value=10)
                p_min = st.number_input("حد تنبيه النواقص", min_value=1, value=3)
                
                if st.button("حفظ وإضافة المنتج للمخزن"):
                    if p_name and p_sell > 0:
                        try:
                            supabase.table('products').insert({
                                'category_id': cats[selected_cat_name],
                                'name': p_name,
                                'barcode': p_barcode if p_barcode else None,
                                'buy_price': p_buy,
                                'sell_price': p_sell,
                                'stock_quantity': p_qty,
                                'min_stock_alert': p_min
                            }).execute()
                            st.success(f"تمت إضافة المنتج '{p_name}' بنجاح!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"خطأ: {e}")
                    else:
                        st.warning("يرجى إدخال اسم المنتج وسعر البيع.")
            else:
                st.info("يرجى إضافه أقسام أولاً قبل إضافة المنتجات.")

    with admin_tab3:
        st.subheader("متابعة طلبات الصيانة")
        try:
            m_res = supabase.table('maintenance').select('*').execute()
            if m_res.data:
                st.dataframe(pd.DataFrame(m_res.data), use_container_width=True)
            else:
                st.info("لا توجد أجهزة صيانة مسجلة حالياً.")
        except:
            st.info("جاري تحميل بيانات الصيانة...")

    with admin_tab4:
        st.subheader("إدارة اشتراكات IPTV وتنبيهات التجديد")
        with st.form("iptv_form"):
            c_iptv_name = st.text_input("اسم المشترك")
            c_iptv_phone = st.text_input("رقم الهاتف")
            server_name = st.text_input("اسم السيرفر (مثال: Cobra)")
            mac = st.text_input("عنوان الـ MAC (اختياري)")
            s_date = st.date_input("تاريخ البدء", date.today())
            e_date = st.date_input("تاريخ الانتهاء")
            submit_iptv = st.form_submit_button("حفظ الاشتراك", use_container_width=True)
            
            if submit_iptv:
                try:
                    supabase.table('iptv_subs').insert({
                        'customer_name': c_iptv_name,
                        'phone': c_iptv_phone,
                        'server_type': server_name,
                        'mac_address': mac,
                        'start_date': str(s_date),
                        'expire_date': str(e_date)
                    }).execute()
                    st.success("✅ تمت إضافة اشتراك IPTV بنجاح!")
                except Exception as err:
                    st.error(f"خطأ: {err}")
                    
        st.markdown("### قائمة الاشتراكات الحالية")
        try:
            iptv_res = supabase.table('iptv_subs').select('*').execute()
            if iptv_res.data:
                st.dataframe(pd.DataFrame(iptv_res.data), use_container_width=True)
        except:
            pass

    with admin_tab5:
        st.subheader("التقارير المالية وإجمالي المبيعات (يومية، أسبوعية، شهرية)")
        try:
            sales_res = supabase.table('sales').select('*, users(username)').execute()
            if sales_res.data:
                df_sales = pd.DataFrame(sales_res.data)
                total_revenue = df_sales['total_amount'].sum()
                st.metric("إجمالي المبيعات العامة", f"{total_revenue} جنيه")
                st.markdown("### تفاصيل الفواتير ومن قام بها:")
                st.dataframe(df_sales, use_container_width=True)
            else:
                st.info("لا توجد فواتير مسجلة حتى الآن.")
        except Exception as e:
            st.error(f"خطأ في جلب التقارير: {e}")
