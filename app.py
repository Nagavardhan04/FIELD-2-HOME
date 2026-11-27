# =========================================================
# FIELD 2 HOME
# BHOOMI TO BHAVAN
# Direct Farmer to Customer Marketplace
# =========================================================

import streamlit as st
import streamlit.components.v1 as components
from streamlit_oauth import OAuth2Component
from pathlib import Path
from urllib.parse import quote_plus

# Firebase database functions
from services.firebase_service import (
    add_product_to_database,
    get_products_from_database,
    update_product_in_database,
    delete_product_from_database,
    register_account,
    sign_in_account,
    sign_in_with_google_id_token,
    get_farmer_products,
    submit_farmer_verification,
    get_pending_farmer_applications,
    review_farmer_application,
    create_order,
    get_customer_orders,
    get_farmer_orders,
    update_farmer_order_item_status,
    get_all_orders,
    get_pending_delivery_partners,
    review_delivery_partner,
    get_approved_delivery_partners,
    assign_order_to_delivery_partner,
    get_delivery_partner_orders,
    update_delivery_status,
    set_auth_context,
    clear_auth_context
)


_phone_otp_component = components.declare_component(
    "field2home_phone_otp", path=str(Path(__file__).resolve().parent / "components" / "phone_otp")
)


# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="FIELD 2 HOME",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# 2. WEBSITE DESIGN
# =========================================================

# Use st.html() instead of st.markdown() for HTML.
# This prevents HTML tags from appearing as plain text.

st.html("""
<style>

.stApp {
    background-color: #f5f8f5;
}

.block-container {
    max-width: 1250px;
    padding-top: 25px;
    padding-bottom: 50px;
}

/* Header */

.location-card {
    background-color: #e4f4e7;
    padding: 25px;
    border-radius: 16px;
    color: #176b3c;
    font-family: Arial, sans-serif;
}

/* Promotional banner */

.promo-banner {
    background: linear-gradient(
        120deg,
        #105c34,
        #40ad65
    );

    padding: 40px;
    border-radius: 20px;
    margin-top: 25px;
    margin-bottom: 30px;
    color: white;
    font-family: Arial, sans-serif;
}

.promo-banner h2 {
    color: white;
    font-size: 30px;
}

.promo-banner h3 {
    color: white;
}

.promo-banner p {
    color: white;
    font-size: 17px;
    line-height: 1.7;
}

/* Product price */

.product-price {
    color: #188346;
    font-size: 24px;
    font-weight: bold;
}

/* Brand */

.brand-name {
    color: #176b3c;
    font-size: 27px;
    font-weight: bold;
}

</style>
""")


# =========================================================
# 3. SESSION STORAGE
# =========================================================

# Shopping cart is stored temporarily in Streamlit session.

if "cart" not in st.session_state:

    st.session_state.cart = {}


# =========================================================
# 4. LOAD PRODUCTS FROM FIREBASE
# =========================================================

def load_products():

    try:

        products = get_products_from_database()

        return products

    except Exception as error:

        st.error("Unable to load products from Firebase.")

        st.error(str(error))

        return []


# =========================================================
# 5. SEARCH PRODUCTS
# =========================================================

def search_products(products, keyword):

    result = []

    keyword = keyword.lower().strip()

    for product in products:

        name = product.get("name", "").lower()

        farmer = product.get("farmer", "").lower()

        if keyword in name or keyword in farmer:

            result.append(product)

    return result


# =========================================================
# 6. FILTER PRODUCTS BY CATEGORY
# =========================================================

def filter_products(products, category):

    if category == "All":

        return products

    result = []

    for product in products:

        if product.get("category") == category:

            result.append(product)

    return result


# =========================================================
# 7. SORT PRODUCTS BY PRICE
# =========================================================

def sort_products(products, sorting):

    if sorting == "Low to High":

        return sorted(
            products,
            key=lambda item: float(item.get("price", 0))
        )

    elif sorting == "High to Low":

        return sorted(
            products,
            key=lambda item: float(item.get("price", 0)),
            reverse=True
        )

    return products


# =========================================================
# 8. CALCULATE DISCOUNT
# =========================================================

def calculate_discount(original_price, selling_price):

    if original_price <= 0:

        return 0

    if selling_price >= original_price:

        return 0

    discount = (
        (original_price - selling_price)
        / original_price
    ) * 100

    return round(discount)


# =========================================================
# 9. HEADER AND LOGO
# =========================================================

left, right = st.columns([1, 3])

with left:

    # Find the logo inside the project folder.

    project_folder = Path(__file__).resolve().parent

    logo_path = (
        project_folder
        / "assets"
        / "images"
        / "logo.png"
    )

    if logo_path.exists():

        st.image(
            str(logo_path),
            width=190
        )

    else:

        st.markdown(
            '<div class="brand-name">🌱 FIELD 2 HOME</div>',
            unsafe_allow_html=True
        )


with right:

    # st.html renders the HTML directly.

    st.html("""
    <div class="location-card">

        <h3>📍 FIELD 2 HOME</h3>

        <p>Fresh from Farmers to Your Home</p>

        <h4>BHOOMI TO BHAVAN</h4>

        <p>🌱 Supporting Indian Farmers</p>

    </div>
    """)


st.write("")


# =========================================================
# 10. ACCOUNT REGISTRATION AND LOGIN
# =========================================================

if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

api_key = st.secrets.get("FIREBASE_WEB_API_KEY", "")
admin_emails = [
    email.strip().lower()
    for email in st.secrets.get("ADMIN_EMAILS", [])
    if str(email).strip()
]

# Backend verifies this Firebase ID token independently on every protected call.
_current_session = st.session_state.get("auth_user") or {}
set_auth_context(_current_session.get("id_token", ""), admin_emails)

st.subheader("Account Access")

if st.session_state.auth_user is None:
    login_tab, register_tab = st.tabs(["Login", "Create Account"])

    with login_tab:
        with st.form("login_form"):
            login_email = st.text_input("Email address", key="login_email")
            login_password = st.text_input(
                "Password", type="password", key="login_password"
            )
            login_clicked = st.form_submit_button("LOGIN", use_container_width=True)

        if login_clicked:
            try:
                signed_in_user = sign_in_account(
                    login_email, login_password, api_key
                )
                if signed_in_user.get("email", "").lower() in admin_emails:
                    signed_in_user["role"] = "admin"
                st.session_state.auth_user = signed_in_user
                st.success("Login successful!")
                st.rerun()
            except Exception as error:
                st.error(str(error))

        # Google OAuth login. Configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
        # in .streamlit/secrets.toml before using this button.
        google_client_id = st.secrets.get("GOOGLE_CLIENT_ID", "")
        google_client_secret = st.secrets.get("GOOGLE_CLIENT_SECRET", "")
        if google_client_id and google_client_secret:
            oauth = OAuth2Component(
                google_client_id,
                google_client_secret,
                "https://accounts.google.com/o/oauth2/v2/auth",
                "https://oauth2.googleapis.com/token",
                "https://oauth2.googleapis.com/token",  # refresh token endpoint
                "https://oauth2.googleapis.com/revoke",  # revoke token endpoint
            )
            google_result = oauth.authorize_button(
                name="CONTINUE WITH GOOGLE",
                icon="https://www.google.com/favicon.ico",
                redirect_uri=st.secrets.get("GOOGLE_REDIRECT_URI", "http://localhost:8501"),
                scope="openid email profile",
                key="google_login",
                extras_params={"prompt": "select_account"},
            )

            if google_result and isinstance(google_result, dict):
                google_token = google_result.get("token", google_result)
                google_id_token = google_token.get("id_token") if isinstance(google_token, dict) else None
                if google_id_token:
                    try:
                        google_user = sign_in_with_google_id_token(google_id_token, api_key)
                        if google_user.get("email", "").lower() in admin_emails:
                            google_user["role"] = "admin"
                        st.session_state.auth_user = google_user
                        st.success("Google login successful!")
                        st.rerun()
                    except Exception as error:
                        st.error("Google login failed: " + str(error))
                elif google_token:
                    st.error("Google did not return an ID token. Check that the OAuth scope includes openid.")

        else:
            st.info(
                "To enable Google login, add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET "
                "to .streamlit/secrets.toml after creating a Google OAuth web client."
            )

    with register_tab:
        st.markdown("#### Verify your mobile number before registration")
        firebase_phone_config = {
            "apiKey": api_key,
            "authDomain": st.secrets.get("FIREBASE_AUTH_DOMAIN", "field-2-home.firebaseapp.com"),
            "projectId": st.secrets.get("FIREBASE_PROJECT_ID", "field-2-home"),
            "appId": st.secrets.get("FIREBASE_APP_ID", "1:1082295694846:web:eb99fd58e71261dd1a3caf"),
        }
        otp_result = _phone_otp_component(
            firebase_config=firebase_phone_config, default=None, key="field2home_phone_otp"
        )
        if isinstance(otp_result, dict) and otp_result.get("verified") and otp_result.get("phone"):
            st.session_state["verified_registration_phone"] = otp_result["phone"]
        verified_phone = st.session_state.get("verified_registration_phone", "")
        if verified_phone:
            st.success(f"Verified phone number: {verified_phone}")
        else:
            st.warning("Complete phone OTP verification before creating your account.")

        with st.form("register_form"):
            full_name = st.text_input("Full name", key="register_name")
            register_email = st.text_input("Email address", key="register_email")
            register_password = st.text_input(
                "Create password (minimum 6 characters)",
                type="password", key="register_password"
            )
            account_role = st.selectbox(
                "Create account as", ["Customer", "Farmer", "Delivery Partner"]
            )
            register_clicked = st.form_submit_button(
                "CREATE ACCOUNT", use_container_width=True
            )

        if register_clicked:
            try:
                if not st.session_state.get("verified_registration_phone"):
                    raise ValueError("Please complete phone OTP verification first.")
                st.session_state.auth_user = register_account(
                    register_email,
                    register_password,
                    account_role.lower(),
                    full_name,
                    api_key,
                    st.session_state.get("verified_registration_phone"),
                )
                st.session_state.pop("verified_registration_phone", None)
                st.success("Account created successfully!")
                st.rerun()
            except Exception as error:
                st.error(str(error))

    st.info(
        "Create a Customer, Farmer, or Delivery Partner account, or log in with your authorised administrator email."
    )
    navigation_options = ["Home"]

else:
    current_user = st.session_state.auth_user

    # Re-check the configured administrator email on every rerun.
    # This also fixes an old session that was created before ADMIN_EMAILS was set.
    current_email = str(current_user.get("email", "")).strip().lower()
    if current_email and current_email in admin_emails:
        current_user["role"] = "admin"
        st.session_state.auth_user = current_user

    user_col, logout_col = st.columns([4, 1])
    with user_col:
        st.success(
            f"Signed in as {current_user['full_name']} "
            f"({current_user['role'].title()})"
        )
    with logout_col:
        if st.button("LOG OUT", use_container_width=True):
            st.session_state.auth_user = None
            st.session_state.cart = {}
            st.rerun()

    # Each account type receives only its own navigation options.
    role = current_user.get("role", "").strip().lower()

    if role == "admin":
        navigation_options = ["Home", "Admin Portal"]

    elif role == "farmer":
        navigation_options = ["Home", "Farmer Verification"]
        if current_user.get("verification_status") == "approved":
            navigation_options.extend(["Farmer", "Farmer Orders"])

    elif role == "customer":
        navigation_options = ["Home", "Customer", "Cart", "My Orders"]

    elif role == "delivery_partner":
        navigation_options = ["Home"]
        if current_user.get("verification_status") == "approved":
            navigation_options.append("Delivery Partner")

    else:
        navigation_options = ["Home"]

navigation = st.radio(
    "Select Portal", navigation_options, horizontal=True
)


# =========================================================
# 11. HOME PAGE
# =========================================================

if navigation == "Home":

    st.title("Welcome to FIELD 2 HOME 🌱")

    # Promotional banner

    st.html("""
    <div class="promo-banner">

        <h2>🌱 DAILY FRESH DEALS</h2>

        <h3>Freshness from Farm to Home!</h3>

        <p>
            Buy groceries directly from farmers.
            Discover fresh products at better prices.
        </p>

        <h4>BHOOMI TO BHAVAN</h4>

    </div>
    """)

    st.subheader("Shop with FIELD 2 HOME")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.subheader("🛒 Customer")

        st.write(
            "Discover fresh products and shop directly from farmers."
        )

    with col2:

        st.subheader("👨‍🌾 Farmer")

        st.write(
            "Add agricultural products and manage your listings."
        )

    with col3:

        st.subheader("🚚 Delivery")

        st.write(
            "Receive fresh products at your doorstep."
        )

    st.divider()

    st.subheader("Why FIELD 2 HOME?")

    st.write("🌱 Direct farmer-to-customer connection.")

    st.write("🥬 Fresh agricultural products.")

    st.write("💰 Better prices by reducing intermediaries.")

    st.write("🇮🇳 Supporting local farmers.")


# =========================================================
# 12. FARMER VERIFICATION APPLICATION
# =========================================================

elif navigation == "Farmer Verification":

    user = st.session_state.get("auth_user")
    if not user or user.get("role") != "farmer":
        st.error("Please log in with a Farmer account.")
        st.stop()

    st.title("🛡️ Farmer Verification")
    st.write("Farmer accounts must be reviewed before they can list products.")
    status = user.get("verification_status", "pending")

    if status == "approved":
        st.success("Your farmer account is approved. You can open the Farmer Dashboard.")
    elif status == "rejected":
        st.error("Your application was not approved. Review the admin note below and submit again.")
    else:
        st.info("Your farmer account is not yet approved. Submit your verification details below.")

    if status != "approved":
        st.warning(
            "Privacy: Do not enter your full Aadhaar number, OTP, bank details, or upload public document links. "
            "This prototype stores only the last four characters of your farmer/reference ID. "
            "An authorized admin must inspect original supporting proof separately."
        )
        with st.form("farmer_verification_form"):
            method = st.selectbox(
                "Verification method",
                ["AgriStack Farmer ID", "RTC / Pahani / Land Record", "Tenant / Cultivator Proof", "FPO Membership"]
            )
            reference = st.text_input(
                "Farmer ID / application reference (last 4 characters only)",
                max_chars=4,
                help="Enter only the final four characters. Do not enter the complete government ID."
            )
            state_name = st.text_input("State")
            district_name = st.text_input("District")
            confirm_original = st.checkbox(
                "I can present the original supporting proof to an authorized FIELD 2 HOME administrator for manual review."
            )
            submit_application = st.form_submit_button("SUBMIT FOR VERIFICATION", use_container_width=True)

        if submit_application:
            if len(reference.strip()) != 4:
                st.error("Enter exactly the last four characters of the reference.")
            elif not state_name.strip() or not district_name.strip():
                st.error("Please enter your state and district.")
            elif not confirm_original:
                st.error("Please confirm that you can present the original supporting proof for review.")
            else:
                try:
                    submit_farmer_verification(
                        user["uid"],
                        {
                            "verification_method": method,
                            "reference_last4": reference.strip(),
                            "farm_state": state_name.strip(),
                            "farm_district": district_name.strip(),
                        },
                    )
                    st.session_state.auth_user["verification_status"] = "pending"
                    st.success("Application submitted. Your status is PENDING ADMIN REVIEW.")
                    st.rerun()
                except Exception as error:
                    st.error("Could not submit the application: " + str(error))

    if user.get("admin_note"):
        st.caption("Admin note: " + str(user.get("admin_note")))


# =========================================================
# 13. ADMIN FARMER VERIFICATION
# =========================================================

elif navigation == "Admin Portal":

    user = st.session_state.get("auth_user")
    if not user or user.get("role") != "admin":
        st.error("Admin access is required.")
        st.stop()

    st.title("🛡️ FIELD 2 HOME – ADMIN PORTAL")
    st.caption("Administrator workspace: review farmer verification applications.")
    st.subheader("Farmer Verification Management")
    try:
        applications = get_pending_farmer_applications()
    except Exception as error:
        st.error("Could not load applications: " + str(error))
        applications = []

    if not applications:
        st.info("There are no pending farmer applications.")
    else:
        for application in applications:
            uid = application.get("uid", "")
            with st.container(border=True):
                st.subheader(application.get("full_name", "Farmer"))
                st.write("Email:", application.get("email", ""))
                st.write("Verification method:", application.get("verification_method", "Not provided"))
                st.write("Reference ending:", "••••" + str(application.get("verification_reference_last4", "")))
                st.write("Farm area:", application.get("farm_district", ""), ",", application.get("farm_state", ""))
                st.warning("Do not approve based only on the entered reference. Inspect original government/FPO/land proof separately.")
                with st.form("review_farmer_" + uid):
                    admin_note = st.text_input("Review note (do not include sensitive ID numbers)", key="note_" + uid)
                    approve_col, reject_col = st.columns(2)
                    with approve_col:
                        approve = st.form_submit_button("APPROVE FARMER", use_container_width=True)
                    with reject_col:
                        reject = st.form_submit_button("REJECT APPLICATION", use_container_width=True)
                if approve or reject:
                    decision = "approved" if approve else "rejected"
                    try:
                        review_farmer_application(uid, decision, admin_note)
                        st.success("Application " + decision + ".")
                        st.rerun()
                    except Exception as error:
                        st.error("Could not update application: " + str(error))

    st.divider()
    st.subheader("🚚 Delivery Partner Applications")
    try:
        pending_partners = get_pending_delivery_partners()
        if not pending_partners:
            st.info("There are no pending delivery partner applications.")
        for partner_app in pending_partners:
            partner_uid = partner_app.get("uid", "")
            with st.container(border=True):
                st.write("Name:", partner_app.get("full_name", ""))
                st.write("Email:", partner_app.get("email", ""))
                with st.form("delivery_partner_review_" + partner_uid):
                    partner_note = st.text_input("Review note", key="delivery_note_" + partner_uid)
                    yes_col, no_col = st.columns(2)
                    with yes_col:
                        partner_approve = st.form_submit_button("APPROVE PARTNER", use_container_width=True)
                    with no_col:
                        partner_reject = st.form_submit_button("REJECT", use_container_width=True)
                if partner_approve or partner_reject:
                    review_delivery_partner(
                        partner_uid,
                        "approved" if partner_approve else "rejected",
                        partner_note
                    )
                    st.success("Delivery partner application reviewed.")
                    st.rerun()
    except Exception as error:
        st.error("Could not load delivery partner applications: " + str(error))

    st.divider()
    st.subheader("🚚 Assign Orders to Delivery Partners")
    try:
        assignable_orders = [
            order for order in get_all_orders()
            if order.get("status") != "delivered"
            and not order.get("delivery_partner_uid")
            and any(item.get("item_status") == "ready_for_pickup" for item in order.get("items", []))
        ]
        approved_partners = get_approved_delivery_partners()
        if not assignable_orders:
            st.info("No orders are ready for delivery assignment yet. A farmer must mark items Ready for Pickup.")
        elif not approved_partners:
            st.warning("No approved delivery partners are available yet.")
        else:
            partner_labels = {
                f"{p.get('full_name', 'Partner')} ({p.get('email', '')})": p["uid"]
                for p in approved_partners
            }
            for assign_order in assignable_orders:
                with st.container(border=True):
                    st.write("Order:", assign_order.get("order_id", ""))
                    st.write("Customer:", assign_order.get("customer_name", ""))
                    st.write("Total: ₹", assign_order.get("total", 0))
                    chosen_partner_label = st.selectbox(
                        "Choose delivery partner",
                        list(partner_labels.keys()),
                        key="assign_partner_" + assign_order.get("order_id", "")
                    )
                    if st.button("ASSIGN DELIVERY", key="assign_order_" + assign_order.get("order_id", "")):
                        assign_order_to_delivery_partner(
                            assign_order["order_id"],
                            partner_labels[chosen_partner_label],
                            st.session_state.auth_user["uid"]
                        )
                        st.success("Order assigned to delivery partner.")
                        st.rerun()
    except Exception as error:
        st.error("Could not assign delivery orders: " + str(error))

    st.divider()
    st.subheader("📦 Marketplace Orders")
    try:
        all_orders = get_all_orders()
        if not all_orders:
            st.info("No customer orders have been placed yet.")
        else:
            for admin_order in all_orders:
                with st.expander("Order " + admin_order.get("order_id", "")):
                    st.write("Customer:", admin_order.get("customer_name", ""))
                    st.write("Status:", admin_order.get("status", ""))
                    st.write("Total: ₹", admin_order.get("total", 0))
                    st.write("Payment:", admin_order.get("payment_method", ""))
                    for admin_item in admin_order.get("items", []):
                        st.write(
                            f"• {admin_item.get('name', 'Product')} × "
                            f"{admin_item.get('quantity', 0)}"
                        )
    except Exception as error:
        st.error("Could not load marketplace orders: " + str(error))


# =========================================================
# 14. FARMER DASHBOARD AND PRODUCT MANAGEMENT
# =========================================================

elif navigation == "Farmer":

    if not st.session_state.get("auth_user") or st.session_state.auth_user.get("role") != "farmer":
        st.error("Please log in with a Farmer account to access this dashboard.")
        st.stop()

    if st.session_state.auth_user.get("verification_status") != "approved":
        st.warning("Your farmer account must be approved before you can list or manage products. Open Farmer Verification to check your status.")
        st.stop()

    farmer_uid = st.session_state.auth_user["uid"]
    st.title("👨‍🌾 Farmer Dashboard")
    st.write("Add new agricultural products and manage existing listings.")

    st.subheader("Add Your Product")

    with st.form("farmer_product_form"):

        farmer_name = st.text_input("Farmer Name")
        farm_location = st.text_input("Farm Location / Village / District")
        product_name = st.text_input("Product Name")

        category = st.selectbox(
            "Product Category",
            ["Vegetables", "Fruits", "Dairy", "Grains", "Other"]
        )

        variety = st.text_input("Product Variety")
        selling_price = st.number_input(
            "Selling Price (₹)", min_value=0.01, value=10.0, step=1.0
        )
        original_price = st.number_input(
            "Original Price (₹)", min_value=0.01, value=10.0, step=1.0
        )
        quantity = st.text_input(
            "Product Quantity", placeholder="Example: 1 kg"
        )
        stock = st.number_input(
            "Available Stock", min_value=0, value=1, step=1
        )
        image_url = st.text_input("Product Image URL (optional)")

        submit = st.form_submit_button(
            "ADD PRODUCT", use_container_width=True
        )

    if submit:
        if not farmer_name.strip():
            st.error("Please enter farmer name.")
        elif not farm_location.strip():
            st.error("Please enter farm location.")
        elif not product_name.strip():
            st.error("Please enter product name.")
        elif not quantity.strip():
            st.error("Please enter product quantity.")
        elif selling_price > original_price:
            st.error("Selling price cannot be greater than original price.")
        else:
            product = {
                "farmer": farmer_name.strip(),
                "location": farm_location.strip(),
                "name": product_name.strip(),
                "category": category,
                "variety": variety.strip(),
                "price": selling_price,
                "original_price": original_price,
                "quantity": quantity.strip(),
                "stock": int(stock),
                "image": image_url.strip(),
                "owner_uid": farmer_uid
            }

            try:
                product_id = add_product_to_database(product)
                st.success("Product added successfully!")
                st.caption("Product ID: " + product_id)
                st.rerun()
            except Exception as error:
                st.error("Product could not be saved.")
                st.error(str(error))

    # Product management section.
    st.divider()
    st.subheader("Manage Marketplace Products")
    st.caption("Only products created by your signed-in farmer account are shown here.")

    try:
        products = get_farmer_products(farmer_uid)
    except Exception as error:
        st.error("Could not load your products: " + str(error))
        products = []

    if not products:
        st.info("No products have been added yet.")
    else:
        for product in products:
            product_id = product.get("id", "")
            if not product_id:
                continue

            with st.container(border=True):
                left, right = st.columns([3, 1])

                with left:
                    st.subheader(product.get("name", "Product"))
                    st.write("Farmer:", product.get("farmer", ""))
                    st.write("Location:", product.get("location", ""))
                    st.write("Category:", product.get("category", ""))
                    st.write("Price: ₹", product.get("price", 0))
                    st.write("Available Stock:", product.get("stock", 0))

                with right:
                    image_url_existing = product.get("image", "").strip()
                    if image_url_existing:
                        try:
                            st.image(image_url_existing, use_container_width=True)
                        except Exception:
                            st.caption("Image unavailable")

                # Edit form for this product.
                with st.expander("✏️ Edit Product"):
                    with st.form("edit_product_" + product_id):
                        edit_name = st.text_input(
                            "Product Name",
                            value=str(product.get("name", "")),
                            key="edit_name_" + product_id
                        )
                        edit_farmer = st.text_input(
                            "Farmer Name",
                            value=str(product.get("farmer", "")),
                            key="edit_farmer_" + product_id
                        )
                        edit_location = st.text_input(
                            "Farm Location",
                            value=str(product.get("location", "")),
                            key="edit_location_" + product_id
                        )

                        categories = ["Vegetables", "Fruits", "Dairy", "Grains", "Other"]
                        current_category = product.get("category", "Other")
                        category_index = categories.index(current_category) if current_category in categories else 4
                        edit_category = st.selectbox(
                            "Category",
                            categories,
                            index=category_index,
                            key="edit_category_" + product_id
                        )
                        edit_variety = st.text_input(
                            "Variety",
                            value=str(product.get("variety", "")),
                            key="edit_variety_" + product_id
                        )

                        try:
                            old_price = max(0.01, float(product.get("price", 0.01)))
                        except (TypeError, ValueError):
                            old_price = 0.01
                        try:
                            old_original_price = max(0.01, float(product.get("original_price", old_price)))
                        except (TypeError, ValueError):
                            old_original_price = old_price
                        try:
                            old_stock = max(0, int(product.get("stock", 0)))
                        except (TypeError, ValueError):
                            old_stock = 0

                        edit_price = st.number_input(
                            "Selling Price (₹)", min_value=0.01, value=old_price,
                            step=1.0, key="edit_price_" + product_id
                        )
                        edit_original_price = st.number_input(
                            "Original Price (₹)", min_value=0.01,
                            value=old_original_price, step=1.0,
                            key="edit_original_price_" + product_id
                        )
                        edit_quantity = st.text_input(
                            "Selling Unit / Quantity",
                            value=str(product.get("quantity", "")),
                            key="edit_quantity_" + product_id
                        )
                        edit_stock = st.number_input(
                            "Available Stock", min_value=0, value=old_stock,
                            step=1, key="edit_stock_" + product_id
                        )
                        edit_image = st.text_input(
                            "Product Image URL",
                            value=str(product.get("image", "")),
                            key="edit_image_" + product_id
                        )

                        update_clicked = st.form_submit_button(
                            "SAVE CHANGES", use_container_width=True
                        )

                    if update_clicked:
                        if not edit_name.strip():
                            st.error("Product name cannot be empty.")
                        elif not edit_farmer.strip():
                            st.error("Farmer name cannot be empty.")
                        elif not edit_location.strip():
                            st.error("Farm location cannot be empty.")
                        elif not edit_quantity.strip():
                            st.error("Please enter the selling unit / quantity.")
                        elif edit_price > edit_original_price:
                            st.error("Selling price cannot be greater than original price.")
                        else:
                            updated_product = {
                                "name": edit_name.strip(),
                                "farmer": edit_farmer.strip(),
                                "location": edit_location.strip(),
                                "category": edit_category,
                                "variety": edit_variety.strip(),
                                "price": edit_price,
                                "original_price": edit_original_price,
                                "quantity": edit_quantity.strip(),
                                "stock": int(edit_stock),
                                "image": edit_image.strip()
                            }
                            try:
                                update_product_in_database(product_id, updated_product, farmer_uid)
                                st.success("Product updated successfully!")
                                st.rerun()
                            except Exception as error:
                                st.error("Product could not be updated.")
                                st.error(str(error))

                # Two-step delete to reduce accidental removal.
                confirm_key = "confirm_delete_" + product_id
                if confirm_key not in st.session_state:
                    st.session_state[confirm_key] = False

                if not st.session_state[confirm_key]:
                    if st.button("🗑️ Delete Product", key="delete_start_" + product_id):
                        st.session_state[confirm_key] = True
                        st.rerun()
                else:
                    st.warning("Are you sure you want to delete this product?")
                    confirm_col, cancel_col = st.columns(2)
                    with confirm_col:
                        if st.button("Yes, Delete", key="delete_yes_" + product_id, type="primary"):
                            try:
                                delete_product_from_database(product_id, farmer_uid)
                                st.session_state.cart.pop(product_id, None)
                                st.session_state[confirm_key] = False
                                st.success("Product deleted successfully.")
                                st.rerun()
                            except Exception as error:
                                st.error("Product could not be deleted.")
                                st.error(str(error))
                    with cancel_col:
                        if st.button("Cancel", key="delete_cancel_" + product_id):
                            st.session_state[confirm_key] = False
                            st.rerun()


# =========================================================
# 13. CUSTOMER SHOPPING
# =========================================================

elif navigation == "Customer":

    if not st.session_state.get("auth_user"):
        st.error("Please create an account or log in to shop.")
        st.stop()

    st.title("🛒 Customer Shopping")
    st.write("Discover fresh products directly from farmers.")

    # Search products by name or farmer name.
    keyword = st.text_input(
        "Search Products",
        placeholder="🔍 Search vegetables, fruits and groceries..."
    )

    # Filter products by category.
    category = st.selectbox(
        "Choose Category",
        ["All", "Vegetables", "Fruits", "Dairy", "Grains", "Other"]
    )

    # Sort products by price.
    sorting = st.selectbox(
        "Sort by Price",
        ["Default", "Low to High", "High to Low"]
    )

    st.divider()

    # Load products saved by farmers in Firebase.
    products = load_products()

    if keyword:
        products = search_products(products, keyword)

    products = filter_products(products, category)
    products = sort_products(products, sorting)

    st.subheader("Available Farmer Products")

    if not products:
        st.info(
            "No products are available yet. Farmers can add products "
            "through the Farmer Dashboard."
        )
    else:
        # Display products in three columns.
        columns = st.columns(3)

        for index, product in enumerate(products):
            with columns[index % 3]:
                with st.container(border=True):

                    # Product image supplied by the farmer as a URL.
                    image_url = product.get("image", "").strip()

                    if image_url:
                        try:
                            st.image(
                                image_url,
                                use_container_width=True
                            )
                        except Exception:
                            st.info("🌱 Product image is unavailable.")
                    else:
                        st.markdown("### 🌱 Farm Fresh Product")

                    # Product name and variety.
                    st.subheader(product.get("name", "Product"))

                    variety = product.get("variety", "")
                    if variety:
                        st.caption(variety)

                    # Safely read product price and original price.
                    try:
                        price = float(product.get("price", 0))
                        original_price = float(
                            product.get("original_price", price)
                        )
                    except (TypeError, ValueError):
                        price = 0.0
                        original_price = 0.0

                    st.markdown(
                        f"<div class='product-price'>₹{price:.2f}</div>",
                        unsafe_allow_html=True
                    )

                    discount = calculate_discount(
                        original_price,
                        price
                    )

                    if discount > 0:
                        st.success(f"{discount}% OFF")
                        st.caption(f"Original Price: ₹{original_price:.2f}")

                    # Selling unit, farmer and location.
                    st.caption(
                        "Selling Unit: "
                        + str(product.get("quantity", "Not specified"))
                    )

                    st.write(
                        "👨‍🌾 Farmer:",
                        product.get("farmer", "Farmer")
                    )

                    st.write(
                        "📍 Location:",
                        product.get("location", "Location unavailable")
                    )

                    # Available stock and product document ID.
                    try:
                        stock = int(product.get("stock", 0))
                    except (TypeError, ValueError):
                        stock = 0

                    product_id = product.get("id", "")
                    st.write("Available Stock:", stock)
                    st.divider()

                    if stock > 0 and product_id:
                        # Customer chooses how many units to add.
                        selected_quantity = st.number_input(
                            "Select Quantity",
                            min_value=1,
                            max_value=stock,
                            value=1,
                            step=1,
                            key="quantity_" + product_id
                        )

                        st.write(
                            "Subtotal: ₹"
                            + f"{price * selected_quantity:.2f}"
                        )

                        # Add the selected quantity to the shopping cart.
                        if st.button(
                            "ADD TO CART +",
                            key="add_" + product_id,
                            type="primary",
                            use_container_width=True
                        ):
                            current_quantity = st.session_state.cart.get(
                                product_id,
                                0
                            )

                            new_quantity = (
                                current_quantity + selected_quantity
                            )

                            if new_quantity <= stock:
                                st.session_state.cart[product_id] = new_quantity
                                st.toast("Product added to cart!")
                            else:
                                st.warning(
                                    "Requested quantity exceeds available stock."
                                )
                    elif stock <= 0:
                        st.error("OUT OF STOCK")
                    else:
                        st.error("Product ID is missing. Please contact support.")


# =========================================================
# 14. SHOPPING CART
# =========================================================

elif navigation == "Cart":

    if not st.session_state.get("auth_user"):
        st.error("Please create an account or log in to view your cart.")
        st.stop()

    st.title("🛒 My Shopping Cart")

    products = load_products()

    total = 0

    if len(st.session_state.cart) == 0:

        st.info("Your shopping cart is empty.")

    else:

        # Read every item in the cart.

        for product_id, quantity in list(
            st.session_state.cart.items()
        ):

            selected_product = None

            # Find the matching product in Firebase data.

            for product in products:

                if product.get("id") == product_id:

                    selected_product = product

                    break

            if selected_product is None:

                continue

            product = selected_product

            price = float(
                product.get("price", 0)
            )

            stock = int(
                product.get("stock", 0)
            )

            amount = price * quantity

            total += amount

            with st.container(border=True):

                st.subheader(
                    product.get("name", "Product")
                )

                st.write("Price: ₹", price)

                st.write("Quantity:", quantity)

                st.write("Total: ₹", round(amount, 2))

                col1, col2, col3 = st.columns(3)

                # Decrease quantity.

                with col1:

                    if st.button(
                        "−",
                        key="minus_" + product_id
                    ):

                        if quantity > 1:

                            st.session_state.cart[product_id] = (
                                quantity - 1
                            )

                        else:

                            del st.session_state.cart[product_id]

                        st.rerun()

                # Increase quantity.

                with col2:

                    if st.button(
                        "+",
                        key="plus_" + product_id
                    ):

                        if quantity < stock:

                            st.session_state.cart[product_id] = (
                                quantity + 1
                            )

                        else:

                            st.warning(
                                "Maximum stock reached."
                            )

                        st.rerun()

                # Remove product.

                with col3:

                    if st.button(
                        "Remove",
                        key="remove_" + product_id
                    ):

                        del st.session_state.cart[product_id]

                        st.rerun()

        # Display final amount.

        st.divider()

        st.subheader(
            "Total Amount: ₹" + str(round(total, 2))
        )

        st.success(
            "Thank you for shopping with FIELD 2 HOME!"
        )

        st.divider()
        st.subheader("📍 Delivery Location on Google Maps")

        maps_key = st.secrets.get("google_maps", {}).get("api_key", "")
        map_search = st.text_input(
            "Search your delivery area on Google Maps",
            placeholder="Example: Bengaluru, Karnataka"
        )
        if maps_key and map_search.strip():
            map_query = quote_plus(map_search.strip())
            map_url = (
                "https://www.google.com/maps/embed/v1/place?key="
                + maps_key
                + "&q="
                + map_query
            )
            st.components.v1.iframe(map_url, height=350, scrolling=False)
            st.caption(
                "Use this map to confirm the area. Enter the exact latitude and longitude below if available."
            )
        elif not maps_key:
            st.warning(
                "Google Maps key was not found. Check [google_maps] api_key in .streamlit/secrets.toml."
            )
        else:
            st.info("Enter your area above to preview it on Google Maps.")

        st.divider()
        st.subheader("📍 Use My Current GPS Location")
        st.caption(
            "Allow location access in your browser. The browser will show your coordinates; "
            "copy them into the Latitude and Longitude fields below."
        )
        gps_html = """
        <div style="font-family:Arial,sans-serif;padding:8px;border:1px solid #ddd;border-radius:10px;">
          <button id="gpsBtn" style="padding:10px 16px;border:0;border-radius:7px;background:#16834a;color:white;cursor:pointer;">
            Detect My Current Location
          </button>
          <p id="gpsStatus" style="margin:10px 0 4px;color:#333;">Location has not been requested.</p>
          <p id="gpsCoords" style="font-weight:600;word-break:break-word;"></p>
          <button id="copyBtn" style="display:none;padding:8px 12px;border:1px solid #888;border-radius:6px;background:white;cursor:pointer;">
            Copy coordinates
          </button>
        </div>
        <script>
        const btn=document.getElementById('gpsBtn');
        const statusEl=document.getElementById('gpsStatus');
        const coordsEl=document.getElementById('gpsCoords');
        const copyBtn=document.getElementById('copyBtn');
        let coords='';
        btn.onclick=()=>{
          if(!navigator.geolocation){statusEl.textContent='Geolocation is not supported by this browser.';return;}
          statusEl.textContent='Requesting location permission...';
          navigator.geolocation.getCurrentPosition(pos=>{
            coords=pos.coords.latitude.toFixed(6)+', '+pos.coords.longitude.toFixed(6);
            coordsEl.textContent='Latitude, Longitude: '+coords;
            statusEl.textContent='Location detected. Copy the values into the checkout fields below.';
            copyBtn.style.display='inline-block';
          },err=>{
            const msgs={1:'Permission denied. Allow location access in browser settings.',2:'Location unavailable. Check device location/GPS.',3:'Location request timed out. Try again.'};
            statusEl.textContent=msgs[err.code]||'Could not detect location.';
          },{enableHighAccuracy:true,timeout:15000,maximumAge:60000});
        };
        copyBtn.onclick=async()=>{
          try{await navigator.clipboard.writeText(coords);statusEl.textContent='Coordinates copied. Paste latitude and longitude into the fields below.';}
          catch(e){statusEl.textContent='Select and copy the coordinates shown above manually.';}
        };
        </script>
        """
        st.components.v1.html(gps_html, height=145, scrolling=False)

        st.divider()
        st.subheader("📦 Delivery Details")

        with st.form("checkout_form"):
            delivery_name = st.text_input(
                "Recipient Name",
                value=st.session_state.auth_user.get("full_name", "")
            )
            phone_number = st.text_input("Mobile Number")
            address_line = st.text_area("Full Delivery Address")
            city = st.text_input("City / Town")
            state_name = st.text_input("State")
            pincode = st.text_input("PIN Code", max_chars=6)
            latitude = st.text_input("Latitude (optional)", placeholder="Example: 12.9716")
            longitude = st.text_input("Longitude (optional)", placeholder="Example: 77.5946")
            delivery_instructions = st.text_area(
                "Delivery Instructions (optional)"
            )

            st.info("Payment method: Cash on Delivery (COD)")
            place_order = st.form_submit_button(
                "PLACE ORDER – CASH ON DELIVERY",
                type="primary",
                use_container_width=True
            )

        if place_order:
            if not delivery_name.strip():
                st.error("Please enter the recipient name.")
            elif len(phone_number.strip()) < 10:
                st.error("Please enter a valid mobile number.")
            elif not address_line.strip() or not city.strip() or not state_name.strip():
                st.error("Please complete your delivery address.")
            elif not (pincode.isdigit() and len(pincode) == 6):
                st.error("Please enter a valid 6-digit PIN code.")
            else:
                try:
                    order_items = []
                    for product_id, quantity in st.session_state.cart.items():
                        matching = next(
                            (item for item in products if item.get("id") == product_id),
                            None
                        )
                        if matching is None:
                            raise ValueError(
                                "A cart product is no longer available. Please refresh your cart."
                            )
                        order_items.append({
                            "product_id": product_id,
                            "name": matching.get("name", "Product"),
                            "farmer": matching.get("farmer", ""),
                            "owner_uid": matching.get("owner_uid", ""),
                            "price": float(matching.get("price", 0)),
                            "quantity": int(quantity),
                            "unit": matching.get("quantity", ""),
                            "item_status": "placed"
                        })

                    order_id = create_order(
                        customer_uid=st.session_state.auth_user["uid"],
                        customer_name=delivery_name.strip(),
                        customer_email=st.session_state.auth_user.get("email", ""),
                        phone=phone_number.strip(),
                        address={
                            "address_line": address_line.strip(),
                            "city": city.strip(),
                            "state": state_name.strip(),
                            "pincode": pincode.strip(),
                            "latitude": latitude.strip(),
                            "longitude": longitude.strip(),
                            "instructions": delivery_instructions.strip()
                        },
                        items=order_items,
                        payment_method="Cash on Delivery"
                    )
                    st.session_state.cart = {}
                    st.success("Order placed successfully!")
                    st.code(order_id, language=None)
                    st.info("Your order is saved. You can track it in My Orders.")
                    st.rerun()
                except Exception as error:
                    st.error("Could not place order: " + str(error))


# =========================================================
# 15. CUSTOMER ORDER HISTORY
# =========================================================

elif navigation == "My Orders":

    user = st.session_state.get("auth_user")
    if not user or user.get("role") != "customer":
        st.error("Customer login is required.")
        st.stop()

    st.title("📦 My Orders")
    st.caption("Track the progress of your orders. Use Refresh to check the latest farmer updates.")

    if st.button("🔄 Refresh order status", key="refresh_customer_orders"):
        st.rerun()

    tracking_steps = [
        ("placed", "Order placed"),
        ("confirmed", "Confirmed"),
        ("processing", "Preparing"),
        ("ready_for_pickup", "Ready"),
        ("out_for_delivery", "On the way"),
        ("delivered", "Delivered"),
    ]

    try:
        orders = get_customer_orders(user["uid"])
    except Exception as error:
        st.error("Could not load your orders: " + str(error))
        orders = []

    if not orders:
        st.info("You have not placed any orders yet.")
    else:
        for order in orders:
            with st.container(border=True):
                st.subheader("Order: " + order.get("order_id", ""))
                current_status = order.get("status", "placed")
                st.write("Order Status:", current_status.replace("_", " ").title())
                if order.get("delivery_partner_name"):
                    st.write("Delivery partner:", order.get("delivery_partner_name"))
                    st.write(
                        "Delivery progress:",
                        order.get("delivery_status", "assigned").replace("_", " ").title()
                    )

                status_names = [step[0] for step in tracking_steps]
                current_index = status_names.index(current_status) if current_status in status_names else 0
                st.progress((current_index + 1) / len(tracking_steps))

                timeline_columns = st.columns(len(tracking_steps))
                for step_index, (step_code, step_label) in enumerate(tracking_steps):
                    marker = "✅" if step_index <= current_index else "⚪"
                    timeline_columns[step_index].markdown(
                        f"<div style='text-align:center;font-size:12px;'>"
                        f"<div style='font-size:20px;'>{marker}</div>"
                        f"<div>{step_label}</div></div>",
                        unsafe_allow_html=True,
                    )

                st.write("Payment:", order.get("payment_method", "Cash on Delivery"))
                st.write("Total: ₹", round(float(order.get("total", 0)), 2))
                address = order.get("address", {})
                st.write(
                    "Delivery Address:",
                    address.get("address_line", ""),
                    address.get("city", ""),
                    address.get("state", ""),
                    address.get("pincode", "")
                )
                st.write("Placed:", str(order.get("created_at", "Recently")))

                st.markdown("**Items**")
                for item in order.get("items", []):
                    st.write(
                        f"• {item.get('name', 'Product')} × {item.get('quantity', 0)} "
                        f"— ₹{float(item.get('price', 0)) * int(item.get('quantity', 0)):.2f}"
                    )
                    st.caption(
                        "Farmer status: "
                        + str(item.get("item_status", "placed")).replace("_", " ").title()
                    )


# =========================================================
# 16. FARMER ORDER MANAGEMENT
# =========================================================

elif navigation == "Farmer Orders":

    user = st.session_state.get("auth_user")
    if (
        not user
        or user.get("role") != "farmer"
        or user.get("verification_status") != "approved"
    ):
        st.error("Only approved farmers can access orders.")
        st.stop()

    st.title("📦 Farmer Order Management")

    try:
        orders = get_farmer_orders(user["uid"])
    except Exception as error:
        st.error("Could not load farmer orders: " + str(error))
        orders = []

    if not orders:
        st.info("No orders contain your products yet.")
    else:
        status_choices = [
            "confirmed",
            "processing",
            "ready_for_pickup",
            "out_for_delivery",
            "delivered"
        ]

        for order in orders:
            farmer_items = [
                item for item in order.get("items", [])
                if item.get("owner_uid") == user["uid"]
            ]
            if not farmer_items:
                continue

            with st.container(border=True):
                st.subheader("Order: " + order.get("order_id", ""))
                st.write("Customer:", order.get("customer_name", "Customer"))
                st.write("Delivery PIN:", order.get("address", {}).get("pincode", ""))

                for item in farmer_items:
                    st.markdown("---")
                    st.write(
                        f"**{item.get('name', 'Product')}** × {item.get('quantity', 0)} "
                        f"{item.get('unit', '')}"
                    )
                    current_status = item.get("item_status", "placed")
                    st.write(
                        "Current status:",
                        current_status.replace("_", " ").title()
                    )

                    selected_status = st.selectbox(
                        "Update item status",
                        status_choices,
                        index=(
                            status_choices.index(current_status)
                            if current_status in status_choices else 0
                        ),
                        key=f"order_status_{order.get('order_id')}_{item.get('product_id')}"
                    )

                    if st.button(
                        "SAVE ORDER STATUS",
                        key=f"save_status_{order.get('order_id')}_{item.get('product_id')}"
                    ):
                        try:
                            update_farmer_order_item_status(
                                order.get("order_id"),
                                item.get("product_id"),
                                user["uid"],
                                selected_status
                            )
                            st.success("Order status updated.")
                            st.rerun()
                        except Exception as error:
                            st.error("Could not update status: " + str(error))


# =========================================================
# DELIVERY PARTNER DASHBOARD
# =========================================================

elif navigation == "Delivery Partner":

    user = st.session_state.get("auth_user")
    if (
        not user
        or user.get("role") != "delivery_partner"
        or user.get("verification_status") != "approved"
    ):
        st.error("Only admin-approved delivery partners can access this dashboard.")
        st.stop()

    st.title("🚚 Delivery Partner Dashboard")
    st.caption("View orders assigned to you and update their delivery progress.")

    try:
        assigned_orders = get_delivery_partner_orders(user["uid"])
    except Exception as error:
        st.error("Could not load assigned orders: " + str(error))
        assigned_orders = []

    if not assigned_orders:
        st.info("You do not have any assigned deliveries yet.")
    else:
        delivery_steps = ["accepted", "picked_up", "out_for_delivery", "delivered"]
        for delivery_order in assigned_orders:
            order_id = delivery_order.get("order_id", "")
            with st.container(border=True):
                st.subheader("Order " + order_id)

                # Customer and delivery information
                st.markdown("#### 👤 Customer Details")
                st.write("**Customer:**", delivery_order.get("customer_name", "Not provided"))
                st.write("**Mobile:**", delivery_order.get("phone", "Not provided"))

                # Older orders may store address as a plain string; newer orders
                # store it as a dictionary. Handle both formats safely.
                address = delivery_order.get("address", {})
                if isinstance(address, dict):
                    address_line = str(address.get("address_line", "")).strip()
                    city = str(address.get("city", "")).strip()
                    state = str(address.get("state", "")).strip()
                    pincode = str(address.get("pincode", "")).strip()
                    instructions = str(address.get("instructions", "")).strip()
                    latitude = str(address.get("latitude", "")).strip()
                    longitude = str(address.get("longitude", "")).strip()

                    st.markdown("#### 📍 Delivery Address")
                    st.write(address_line or "Address line not provided")
                    location_parts = [part for part in [city, state] if part]
                    if location_parts:
                        st.write(", ".join(location_parts))
                    if pincode:
                        st.write("**PIN Code:**", pincode)
                    if instructions:
                        st.write("**Delivery instructions:**", instructions)

                    # Prefer GPS coordinates for precise navigation. Fall back
                    # to the entered address when coordinates are unavailable.
                    if latitude and longitude:
                        maps_url = (
                            "https://www.google.com/maps/dir/?api=1&destination="
                            + quote_plus(f"{latitude},{longitude}")
                        )
                        st.link_button("🗺️ Navigate to Customer", maps_url)
                    elif address_line or city:
                        destination = ", ".join(
                            part for part in [address_line, city, state, pincode] if part
                        )
                        maps_url = (
                            "https://www.google.com/maps/dir/?api=1&destination="
                            + quote_plus(destination)
                        )
                        st.link_button("🗺️ Find Address on Google Maps", maps_url)
                elif address:
                    st.markdown("#### 📍 Delivery Address")
                    st.write(str(address))
                else:
                    st.warning("No delivery address was saved for this order.")

                st.markdown("#### 📦 Order Summary")
                for ordered_item in delivery_order.get("items", []):
                    item_name = ordered_item.get("name", "Product")
                    item_qty = ordered_item.get("quantity", 0)
                    item_unit = ordered_item.get("unit", "")
                    st.write(f"• {item_name} × {item_qty} {item_unit}".strip())

                st.write("**Payment:**", delivery_order.get("payment_method", "Not provided"))
                st.write("**Order total:** ₹", delivery_order.get("total", 0))
                st.write("**Current delivery status:**", delivery_order.get("delivery_status", "assigned").replace("_", " ").title())
                current_delivery_status = delivery_order.get("delivery_status", "assigned")
                current_index = delivery_steps.index(current_delivery_status) if current_delivery_status in delivery_steps else 0
                selected_delivery_status = st.selectbox(
                    "Update delivery status",
                    delivery_steps,
                    index=current_index,
                    key="delivery_status_" + order_id
                )
                delivery_note = st.text_input("Delivery note (optional)", key="delivery_note_input_" + order_id)
                if st.button("SAVE DELIVERY UPDATE", key="save_delivery_" + order_id):
                    try:
                        update_delivery_status(
                            order_id, user["uid"], selected_delivery_status, delivery_note
                        )
                        st.success("Delivery status updated.")
                        st.rerun()
                    except Exception as error:
                        st.error("Could not update delivery status: " + str(error))


# =========================================================
# 17. FOOTER
# =========================================================

st.divider()

st.html("""
<div style="
    text-align:center;
    padding:25px;
    font-family:Arial;
">

    <h2 style="color:#188346;">
        🌱 FIELD 2 HOME
    </h2>

    <h4>BHOOMI TO BHAVAN</h4>

    <p>Fresh from Farmers to Your Home</p>

    <p>Direct Farmer to Customer Marketplace</p>

</div>
""")